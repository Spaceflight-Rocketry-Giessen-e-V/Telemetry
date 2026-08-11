close all; clear; clc;

%% --- Names derived from this file ---
% Everything the run writes is named after the script itself, so a renamed
% copy of it keeps its own results apart from the original.
[script_dir, script_name] = fileparts(mfilename('fullpath'));
if isempty(script_dir),  script_dir  = pwd;               end
if isempty(script_name), script_name = 'Helical_Antenna'; end

aux_dir_name = 'Simulation_auxiliary_files';
Sim_Path = fullfile(script_dir, aux_dir_name);
Sim_CSX  = [script_name '.xml'];

%% --- What should this run do? ---
disp('  [1] Full run       -- build, simulate, post-process');
disp(sprintf('  [2] Post-proc only -- re-use existing %s/ results', aux_dir_name));
disp('  [3] Geometry check -- open AppCSXCAD, then stop');
disp('  [4] Preview + run  -- geometry check first, then simulate');
disp('');
choice = input('Select [1]: ', 's');
if isempty(choice), choice = '1'; end

switch choice
    case '1', run_fdtd = true;  show_geometry = false; do_postproc = true;
    case '2', run_fdtd = false; show_geometry = false; do_postproc = true;
    case '3', run_fdtd = false; show_geometry = true;  do_postproc = false;
    case '4', run_fdtd = true;  show_geometry = true;  do_postproc = true;
    otherwise, error('%s: unknown choice "%s"', script_name, choice);
end


threads_default = 6; 
thread_opt = sprintf(' --numThreads=%d', threads_default);

if (run_fdtd)
    disp('');
    disp('Threads: a number, or "auto" to let openEMS find the fastest count itself.');
    thr = strtrim(input(sprintf('Threads [%d]: ', threads_default), 's'));

    if isempty(thr)
        
    elseif strcmpi(thr, 'auto')
        thread_opt = '';
    else
        n = str2double(thr);
        if (isnan(n) || n < 1 || n ~= fix(n))
            error('%s: threads must be a positive integer or "auto", got "%s"', script_name, thr);
        end
        if (n > nproc())
            warning('%d threads asked for, %d cores available -- openEMS will clamp.', n, nproc());
        end
        thread_opt = sprintf(' --numThreads=%d', n);
    end
end

physical_constants;
unit = 1e-3; % Dimensions in mm
f0 = 869.525e6;
lambda0 = c0/f0/unit;
fc = 100e6;

% --- Antenna Geometry ---
C_over_lambda = 1;
alpha_deg     = 6;
C = C_over_lambda * lambda0;
Helix.radius = C/(2*pi);
Helix.pitch  = C*tan(alpha_deg*pi/180);
Helix.turns  = 13.25;
Helix.wire_rad = 3;
Helix.mesh_res = 1.5;

% --- Feeding & Ground ---
feed.height = 15;
feed.R = 140*(C_over_lambda);
gnd_size = 400;

% --- Simulation Box ---
air_gap = 0.75 * lambda0;
sim_r   = gnd_size/2 + air_gap;

%% 1. Setup FDTD & Excitation
FDTD = InitFDTD('NrTS', 1e6, 'EndCriteria', 1e-5);
FDTD = SetGaussExcite(FDTD, f0, fc);
BC = {'PML_8' 'PML_8' 'PML_8' 'PML_8' 'PML_8' 'PML_8'};
FDTD = SetBoundaryCond(FDTD, BC);

%% 2. Setup CSXCAD & Mesh
max_res = floor(c0 / (f0+fc) / unit / 30);
grade   = 1.2;
CSX = InitCSX();

% X and Y Mesh
mesh.x = SmoothMeshLines([-Helix.radius 0 Helix.radius], Helix.mesh_res);
mesh_x_tmp = [mesh.x, -gnd_size/2, gnd_size/2, -sim_r, sim_r];
mesh.x = AutoSmoothMeshLines(mesh_x_tmp, max_res, grade);
mesh.y = mesh.x;

% Z Mesh
z_max_ant = Helix.turns * Helix.pitch + feed.height;
mesh.z = SmoothMeshLines([0 feed.height z_max_ant], Helix.mesh_res);
mesh_z_tmp = [mesh.z, -air_gap, z_max_ant+air_gap];
mesh.z = AutoSmoothMeshLines(mesh_z_tmp, max_res, grade);
CSX = DefineRectGrid(CSX, unit, mesh);

%% 3. Create Helix
CSX = AddMetal(CSX, 'helix');

pts = 60;
t = linspace(0, 2*pi*Helix.turns, pts*ceil(Helix.turns));
coil_x = Helix.radius * cos(t);
coil_y = Helix.radius * sin(t);
coil_z = (t/(2*pi)) * Helix.pitch + feed.height;
p = [coil_x(:)'; coil_y(:)'; coil_z(:)'];
CSX = AddWire(CSX, 'helix', 0, p, Helix.wire_rad);

%% 4. Ground Plane (round)
CSX = AddMetal(CSX, 'gnd');
gnd_radius = gnd_size / 2;
num_gnd_pts = 64;
theta_gnd = (0:num_gnd_pts-1) * 2*pi/num_gnd_pts;
p_gnd = [gnd_radius * cos(theta_gnd); gnd_radius * sin(theta_gnd)];
CSX = AddPolygon(CSX, 'gnd', 10, 'z', 0, p_gnd, 'CoordSystem', 0);

%% 5. Feed
start = [Helix.radius, 0, 0];
stop  = [Helix.radius, 0, feed.height];
[CSX, port] = AddLumpedPort(CSX, 5, 1, feed.R, start, stop, [0 0 1], true);

%% 6. Near-Field to Far-Field Box (NF2FF)
% Index 11 / end-10 keeps the box in real air, clear of the 8-cell PML lining.
start_nf = [mesh.x(11) mesh.y(11) mesh.z(11)];
stop_nf  = [mesh.x(end-10) mesh.y(end-10) mesh.z(end-10)];
[CSX, nf2ff] = CreateNF2FFBox(CSX, 'nf2ff', start_nf, stop_nf, 'OptResolution', lambda0/25);

%% 7. Run Simulation
% Sim_Path / Sim_CSX come from the header block at the top of the file.

% Only wipe the results when we are actually going to regenerate them.
if (run_fdtd && isfolder(Sim_Path))
    rmdir(Sim_Path, 's');
end
if ~isfolder(Sim_Path)
    mkdir(Sim_Path);
end

if (run_fdtd || show_geometry)
    WriteOpenEMS([Sim_Path '/' Sim_CSX], FDTD, CSX);
end

if (show_geometry)
    CSXGeomPlot([Sim_Path '/' Sim_CSX]);
end

if (run_fdtd)
    RunOpenEMS(Sim_Path, Sim_CSX, ['--engine=multithreaded' thread_opt ' --dump-statistics']);
end

if (~do_postproc)
    disp('Geometry check done -- stopping before post-processing.');
    return;
end

if (~run_fdtd && ~exist([Sim_Path '/port_ut1'], 'file'))
    error('No simulation results in %s -- run mode [1] first.', Sim_Path);
end

function draw_impedance(hax, f_MHz, Zin)
    h_re = plot(hax, f_MHz, real(Zin), 'k', 'LineWidth', 2);
    hold(hax, 'on');
    h_im = plot(hax, f_MHz, imag(Zin), 'r--', 'LineWidth', 2);
    plot(hax, f_MHz, zeros(size(f_MHz)), 'k:');
    grid(hax, 'on');
    title(hax, 'Feedpoint impedance');
    xlabel(hax, 'frequency (MHz)');
    ylabel(hax, 'Z_{in} (\Omega)');
    xlim(hax, [f_MHz(1) f_MHz(end)]);
    legend([h_re h_im], 'Re(Z_{in})', 'Im(Z_{in})', 'location', 'northeast');
end

function draw_s11(hax, f_MHz, s11, s11_feed, Z0, R_feed)
    h_50   = plot(hax, f_MHz, 20*log10(abs(s11)), 'k', 'LineWidth', 2);
    hold(hax, 'on');
    h_feed = plot(hax, f_MHz, 20*log10(abs(s11_feed)), 'b--', 'LineWidth', 1.5);
    h_ref  = plot(hax, f_MHz, -10*ones(size(f_MHz)), 'k:');
    grid(hax, 'on');
    title(hax, 'Reflection coefficient');
    xlabel(hax, 'frequency (MHz)');
    ylabel(hax, '|S_{11}| (dB)');
    xlim(hax, [f_MHz(1) f_MHz(end)]);
    y_lo = min(-40, 5*floor(min(20*log10(abs([s11(:); s11_feed(:)])))/5));
    ylim(hax, [y_lo 0]);
    legend([h_50 h_feed h_ref], ['|S_{11}| re ' num2str(Z0) ' \Omega'], ...
                                ['|S_{11}| re ' num2str(R_feed) ' \Omega'], ...
                                '-10 dB', 'location', 'southwest');
end

function draw_pattern(hax, theta_deg, D_tot, D_cprh, D_cplh, Dmax_dBi, phi_deg, f_MHz)
    h_tot  = plot(hax, theta_deg, D_tot,  'k-',  'LineWidth', 2);
    hold(hax, 'on');
    h_cprh = plot(hax, theta_deg, D_cprh, 'g--', 'LineWidth', 2);
    h_cplh = plot(hax, theta_deg, D_cplh, 'r-.', 'LineWidth', 2);
    grid(hax, 'on');
    title(hax, sprintf('Directivity cut, \\phi = %g\\circ, f = %.1f MHz', phi_deg, f_MHz));
    xlabel(hax, '\theta (deg)');
    ylabel(hax, 'directivity (dBi)');
    xlim(hax, [theta_deg(1) theta_deg(end)]);
    ylim(hax, [-30 Dmax_dBi+5]);
    legend([h_tot h_cprh h_cplh], 'total', 'RHCP', 'LHCP', 'location', 'northeast');
end

%% 8. Post-Processing: S11 & Impedance
freq = linspace(f0-fc, f0+fc, 501);
Z0 = 50;

port = calcPort(port, Sim_Path, freq, 'RefImpedance', Z0);

Zin = port.uf.tot ./ port.if.tot;
s11      = (Zin - Z0)     ./ (Zin + Z0);
s11_feed = (Zin - feed.R) ./ (Zin + feed.R);


h_all = figure('Name', 'Helix results', 'Position', [100 100 1400 900]);
set(h_all, 'toolbar', 'figure');
zoom(h_all, 'on');

pos_topleft  = [0.07 0.60 0.40 0.33];
pos_topright = [0.57 0.60 0.40 0.33];
pos_bottom   = [0.07 0.08 0.90 0.37];

ax1 = axes('Parent', h_all, 'Position', pos_topleft);
draw_impedance(ax1, freq/1e6, Zin);

ax2 = axes('Parent', h_all, 'Position', pos_topright);
draw_s11(ax2, freq/1e6, s11, s11_feed, Z0, feed.R);

[~, i0] = min(abs(freq - f0));
disp('-----------------------------------------');
disp(['Zin(f0)        = ' num2str(real(Zin(i0)),'%.1f') ' + j' num2str(imag(Zin(i0)),'%.1f') ' Ohm']);
disp(['S11(f0) @ ' num2str(Z0) 'R  = ' num2str(20*log10(abs(s11(i0))),'%.2f') ' dB']);
disp(['S11(f0) @ ' num2str(feed.R) 'R = ' num2str(20*log10(abs(s11_feed(i0))),'%.2f') ' dB']);

%% 9. Far-Field & Diagnostics
disp('calculating the 3D far field...');
f_res = f0;

P_in_0 = interp1(freq, port.P_acc, f0);

thetaRange = unique([0:0.5:90 90:180]);
phiRange = (0:2:360) - 180;

nf2ff = CalcNF2FF(nf2ff, Sim_Path, f_res, thetaRange*pi/180, phiRange*pi/180, 'Mode', 0, 'Outfile', '3D_Pattern.h5', 'Verbose', 1);


phi_idx = find(phiRange == 0);
if isempty(phi_idx), phi_idx = 1; end
E_slice = nf2ff.E_norm{1}(:, phi_idx);

half = 1/sqrt(2);
[E_pk, pk_idx] = max(E_slice);
E_norm_rel = E_slice / E_pk;

drop = find(E_norm_rel(pk_idx:end) <= half, 1);
if isempty(drop) || drop < 2
    theta_HPBW = NaN; 
else
    i2 = pk_idx + drop - 1;
    i1 = i2 - 1;
    theta_edge = thetaRange(i1) + (thetaRange(i2) - thetaRange(i1)) * ...
                 (E_norm_rel(i1) - half) / (E_norm_rel(i1) - E_norm_rel(i2));
    theta_HPBW = 2 * (theta_edge - thetaRange(pk_idx));
end

% --- Power and Directivity Diagnostics ---
disp('-----------------------------------------');
disp(['radiated power: Prad = ' num2str(nf2ff.Prad) ' Watt']);
disp(['directivity: Dmax = ' num2str(nf2ff.Dmax) ' (' num2str(10*log10(nf2ff.Dmax)) ' dBi)']);
disp(['efficiency: nu_rad = ' num2str(100*nf2ff.Prad./P_in_0) ' %']);
disp(['theta_HPBW = ' num2str(theta_HPBW) ' °']);
disp('-----------------------------------------');

D_dBi = 10*log10(nf2ff.Dmax);

ML_50   = 10*log10(1 - abs(s11(i0))^2);
ML_feed = 10*log10(1 - abs(s11_feed(i0))^2);

disp('--- Link budget (at f0) -----------------');
disp(['Dmax                  = ' num2str(D_dBi,'%.2f') ' dBi   (pattern only)']);
disp(['mismatch loss @ ' num2str(Z0) 'R   = ' num2str(ML_50,'%.2f') ' dB    (S11 = ' num2str(20*log10(abs(s11(i0))),'%.2f') ' dB)']);
disp(['-> realized gain @ ' num2str(Z0) 'R = ' num2str(D_dBi + ML_50,'%.2f') ' dBi  <-- unmatched, straight into coax']);
disp(['-> realized gain matched = ' num2str(D_dBi + ML_feed,'%.2f') ' dBi  <-- with a ' num2str(Z0) '->' num2str(feed.R) ' matching network']);
disp('NOTE: PEC metal -- no conductor loss included. Optimistic.');
disp('-----------------------------------------');

% --- CPRH and CPLH Directivity ---
directivity = nf2ff.P_rad{1} / nf2ff.Prad * 4 * pi;
directivity_CPRH = abs(nf2ff.E_cprh{1}).^2 ./ max(nf2ff.E_norm{1}(:)).^2 * nf2ff.Dmax;
directivity_CPLH = abs(nf2ff.E_cplh{1}).^2 ./ max(nf2ff.E_norm{1}(:)).^2 * nf2ff.Dmax;

phi_cut = phiRange(phi_idx);
D_tot  = 10*log10(directivity(:, phi_idx)');
D_cprh = 10*log10(directivity_CPRH(:, phi_idx)');
D_cplh = 10*log10(directivity_CPLH(:, phi_idx)');

ax4 = axes('Parent', h_all, 'Position', pos_bottom);
draw_pattern(ax4, thetaRange, D_tot, D_cprh, D_cplh, D_dBi, phi_cut, f_res/1e6);

%% 9b. Save the figures

drawnow();
print(h_all, [Sim_Path '/00_overview.png'], '-dpng', '-S1400,900');

panels = { @(hax) draw_impedance(hax, freq/1e6, Zin),                             '01_impedance'; ...
           @(hax) draw_s11(hax, freq/1e6, s11, s11_feed, Z0, feed.R),             '02_s11'; ...
           @(hax) draw_pattern(hax, thetaRange, D_tot, D_cprh, D_cplh, ...
                               D_dBi, phi_cut, f_res/1e6),                        '03_polarization' };

full_pos = [0.11 0.11 0.85 0.80];

panel_px = [1350 975];

for k = 1:size(panels, 1)
    tmp = figure('visible', 'off', 'Position', [0 0 panel_px]);
    hax = axes('Parent', tmp, 'Position', full_pos);
    panels{k,1}(hax);
    print(tmp, [Sim_Path '/' panels{k,2} '.png'], '-dpng', sprintf('-S%d,%d', panel_px));
    close(tmp);
end

hgsave(h_all, [Sim_Path '/results.ofig']);

disp(['figures saved to ' Sim_Path '/  (00_overview.png + 3 panels + results.ofig)']);

%% 10. Dump to VTK for Paraview

DumpFF2VTK([Sim_Path '/3D_Pattern.vtk'], directivity, thetaRange, phiRange, 'scale', 1e-3);

disp('VTK dump complete:');
disp(['  ' Sim_Path '/3D_Pattern.vtk  -- linear directivity (peak = Dmax = ' num2str(nf2ff.Dmax,'%.2f') ')']);
disp('In Paraview: colour by "gain". No Calculator needed.');

%% 11. Hold the figures open
interactive_stdin = (isunix() && system('test -t 0') == 0);
if (~isempty(findall(0, 'type', 'figure')) && interactive_stdin)
    input('Plots open -- press <Enter> to close: ', 's');
end
