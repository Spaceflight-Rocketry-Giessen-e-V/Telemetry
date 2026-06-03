# -*- coding: utf-8 -*-
"""Convert patch antenna simulation results to a KiCad 7/8 PCB file.

Can be called programmatically via write_kicad_pcb() from run.py,
or used as a standalone CLI (same interface as the original sim_to_kicad.py).

CLI usage:
  python -m src.kicad_export results.json
  python -m src.kicad_export --W 80.5 --delta 8.3 --y_inset 12.7
  python -m src.kicad_export results.json -o my_board.kicad_pcb
"""

import argparse
import json
import os

from src.geometry import patch_vertices_sim, to_kicad, SUBSTRATE_MM

BOARD_MARGIN = 1.0   # gap between substrate edge and Edge.Cuts [mm]


def _pts_str(verts) -> str:
    return ' '.join(f'(xy {x:.4f} {y:.4f})' for x, y in verts)


def write_kicad_pcb(W: float, delta: float, y_inset: float,
                    substrate_h: float, output_path: str,
                    sub_hw_mm: float | None = None) -> None:
    """Write a KiCad 7/8 .kicad_pcb file for the truncated-corner patch antenna.

    sub_hw_mm = half-width of the square substrate / ground plane [mm].
    Default None → SUBSTRATE_MM / 2 (75 → 150 × 150 mm legacy board).

    Layers written:
      F.Cu       — patch copper polygon
      B.Cu       — full ground plane
      Edge.Cuts  — board outline (substrate + BOARD_MARGIN)
      F.Fab      — circle at SMA centre-pin location
      F.SilkS    — "SMA_CENTER" label
    """
    if sub_hw_mm is None:
        sub_hw_mm = SUBSTRATE_MM / 2.0
    sub    = 2.0 * sub_hw_mm
    margin = BOARD_MARGIN

    patch_k   = [to_kicad(x, y, substrate_mm=sub)
                 for x, y in patch_vertices_sim(W, delta)]
    feed_kx, feed_ky = to_kicad(0.0, -W / 2 + y_inset, substrate_mm=sub)
    gnd_verts = [(0.0, 0.0), (sub, 0.0), (sub, sub), (0.0, sub)]
    e0, e1    = -margin, sub + margin

    lines = [
        '(kicad_pcb (version 20231231) (generator "sim_to_kicad")',
        f'  (general (thickness {substrate_h:.2f}))',
        '  (paper "A4")',
        '  (layers',
        '    (0 "F.Cu" signal)',
        '    (31 "B.Cu" signal)',
        '    (36 "B.SilkS" user "B.Silkscreen")',
        '    (37 "F.SilkS" user "F.Silkscreen")',
        '    (44 "Edge.Cuts" user)',
        '    (49 "F.Fab" user)',
        '  )',
        '  (setup (pad_to_mask_clearance 0))',
        '  (net 0 "")',
        '',
        '  (gr_poly',
        f'    (pts {_pts_str(patch_k)})',
        '    (layer "F.Cu") (width 0) (fill solid)',
        '  )',
        '',
        '  (gr_poly',
        f'    (pts {_pts_str(gnd_verts)})',
        '    (layer "B.Cu") (width 0) (fill solid)',
        '  )',
        '',
        '  (gr_rect',
        f'    (start {e0:.4f} {e0:.4f}) (end {e1:.4f} {e1:.4f})',
        '    (layer "Edge.Cuts") (width 0.05)',
        '  )',
        '',
        '  (gr_circle',
        f'    (center {feed_kx:.4f} {feed_ky:.4f}) (end {feed_kx:.4f} {feed_ky + 1.5:.4f})',
        '    (layer "F.Fab") (width 0.15)',
        '  )',
        '  (gr_text "SMA_CENTER"',
        f'    (at {feed_kx:.4f} {feed_ky - 3.0:.4f})',
        '    (layer "F.SilkS")',
        '    (effects (font (size 1.5 1.5) (thickness 0.15)))',
        '  )',
        ')',
    ]

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    print(f'KiCad PCB written : {output_path}')
    print(f'  Patch side   W  = {W:.4f} mm')
    print(f'  Corner cut   Δ  = {delta:.4f} mm  (Δ/W = {delta/W:.4f})')
    print(f'  Feed inset   yi = {y_inset:.4f} mm')
    print(f'  Feed (KiCad)    = ({feed_kx:.4f}, {feed_ky:.4f}) mm from board TL')
    print(f'  Board size      = {sub + 2*margin:.0f} × {sub + 2*margin:.0f} mm')
    print()
    print('Next steps in KiCad:')
    print('  1. Open the .kicad_pcb — verify patch on F.Cu, ground plane on B.Cu.')
    print('  2. Place an SMA footprint (Connector_Coaxial library) at the F.Fab circle.')
    print('     Wire its centre pin to F.Cu; ground tabs to B.Cu.')
    print('  3. File → Fabrication Outputs → Gerbers → Generate.')


def main():
    ap = argparse.ArgumentParser(
        description='Patch antenna sim results → KiCad 7/8 PCB file')
    ap.add_argument('json_file', nargs='?',
                    help='Path to results.json written by run.py')
    ap.add_argument('--W',           type=float, help='Patch side [mm]')
    ap.add_argument('--delta',       type=float, help='Corner truncation Δ [mm]')
    ap.add_argument('--y_inset',     type=float, help='Feed inset from bottom edge [mm]')
    ap.add_argument('--substrate_h', type=float, default=1.6,
                    help='Substrate thickness [mm] (default 1.6)')
    ap.add_argument('--sub_hw',     type=float, default=None,
                    help='Substrate / GP half-width [mm] (default 75 → 150 mm board)')
    ap.add_argument('-o', '--output', default=None,
                    help='Output path (default: patch_antenna.kicad_pcb next to JSON)')
    args = ap.parse_args()

    if args.json_file:
        with open(args.json_file, encoding='utf-8') as f:
            data = json.load(f)
        W       = data['W_mm']
        delta   = data['delta_mm']
        y_inset = data['y_inset_mm']
        sub_h   = data.get('substrate_h_mm', args.substrate_h)
        sub_hw  = args.sub_hw if args.sub_hw is not None else data.get('sub_hw_mm', None)
    elif args.W is not None and args.delta is not None and args.y_inset is not None:
        W       = args.W
        delta   = args.delta
        y_inset = args.y_inset
        sub_h   = args.substrate_h
        sub_hw  = args.sub_hw
    else:
        ap.error('Provide a results.json path, or all three of --W / --delta / --y_inset')

    if args.output:
        output = args.output
    elif args.json_file:
        output = os.path.join(os.path.dirname(os.path.abspath(args.json_file)),
                              'patch_antenna.kicad_pcb')
    else:
        output = 'patch_antenna.kicad_pcb'

    write_kicad_pcb(W, delta, y_inset, sub_h, output, sub_hw_mm=sub_hw)


if __name__ == '__main__':
    main()
