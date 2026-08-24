#!/usr/bin/env pwsh
# Re-plot the patch-antenna Gerbers + drill from the KiCad board, then zip them for JLCPCB.
#
# The Gerbers in ./gerbers/ are a PLOT of ./patch_antenna.kicad_pcb. Whenever the board
# changes they must be re-plotted or they go stale. This is the single source of that plot.
#
# Requires a kicad-cli whose major version is >= the board's format (a KiCad-10 board needs
# KiCad 10). Run:   pwsh groundstation/antenna/patch/fab/export_gerbers.ps1
$ErrorActionPreference = 'Stop'

$here = Split-Path -Parent $MyInvocation.MyCommand.Path        # .../patch/fab
$pcb  = Join-Path $here 'patch_antenna.kicad_pcb'
$gdir = Join-Path $here 'gerbers'
$zip  = Join-Path $here 'patch_antenna_gerbers.zip'
if (-not (Test-Path $pcb)) { throw "board not found: $pcb" }

# which KiCad version wrote the board (informational, for a clear error if the CLI is too old)
$hdr = (Get-Content $pcb -TotalCount 8) -join "`n"
$boardVer = if ($hdr -match 'generator_version "([\d.]+)"') { $Matches[1] } else { '?' }

# locate kicad-cli: PATH first, then standard install dirs; pick the highest version
$cands = @()
$p = (Get-Command kicad-cli -ErrorAction SilentlyContinue).Source
if ($p) { $cands += $p }
$cands += Get-ChildItem "C:\Program Files\KiCad\*\bin\kicad-cli.exe",
                        "${env:LOCALAPPDATA}\Programs\KiCad\*\bin\kicad-cli.exe" `
                        -ErrorAction SilentlyContinue | ForEach-Object FullName
$cands = $cands | Select-Object -Unique
if (-not $cands) { throw "kicad-cli not found. Install KiCad (>= v$boardVer) so it can load this board." }
$cli = $cands | Sort-Object { try { [version]((& $_ version) 2>$null) } catch { [version]'0.0' } } -Descending |
       Select-Object -First 1
$cliVer = (& $cli version) 2>$null
Write-Host "Board saved by KiCad ~$boardVer ; using kicad-cli $cliVer"

New-Item -ItemType Directory -Force -Path $gdir | Out-Null
# remove only previously-plotted outputs (never touches the .kicad_pcb / .kicad_pro sources)
Get-ChildItem $gdir -File -ErrorAction SilentlyContinue |
  Where-Object { $_.Extension -in '.gbr','.gbl','.gtl','.gbo','.gto','.gbs','.gts','.gm1','.gbrjob','.drl' } |
  Remove-Item -Force

$g = & $cli pcb export gerbers --board-plot-params -o $gdir $pcb 2>&1
if ($LASTEXITCODE -ne 0) {
  throw "gerber export failed (exit $LASTEXITCODE): $g`n" +
        "If it says 'Failed to load board', the installed kicad-cli ($cliVer) is older than the board (KiCad $boardVer). Install a matching KiCad."
}
& $cli pcb export drill --format excellon --drill-origin absolute --excellon-units mm -o $gdir $pcb
if ($LASTEXITCODE -ne 0) { throw "drill export failed (exit $LASTEXITCODE)" }

if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path (Join-Path $gdir '*') -DestinationPath $zip
Write-Host "OK - refreshed $gdir"
Write-Host "OK - wrote $zip  (upload THIS to JLCPCB)"
