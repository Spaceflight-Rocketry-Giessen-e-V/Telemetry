# Setup — RHCP Patch Antenna Optimizer

This project drives the [openEMS](https://www.openems.de/) FDTD solver through its
Python bindings. Those bindings (`CSXCAD`, `openEMS`) are **not on PyPI or conda**,
so `pip install -r requirements.txt` alone is **not** enough — `python run.py` will
otherwise fail with `ModuleNotFoundError: No module named 'CSXCAD'`.

There are three things that must all be in place; `run.py` checks for them on launch
and prints an actionable message if any is missing.

| # | Requirement | Why |
|---|-------------|-----|
| 1 | A native **openEMS** install (`CSXCAD.dll`, `openEMS.dll`, VTK/Qt5/boost DLLs) | The Python wheels are thin Cython wrappers; the actual solver lives in these DLLs. |
| 2 | **`OPENEMS_INSTALL_PATH`** pointing at that folder | The bindings call `os.add_dll_directory(os.environ['OPENEMS_INSTALL_PATH'])` at import to find the DLLs. `run.py` auto-detects `C:\Program Files\openEMS` if the variable is unset. |
| 3 | The `csxcad` + `openems` **wheels matching your Python minor** (`cp314` ⇄ Python 3.14) | A compiled-extension wheel only loads on the exact CPython minor it was built for. |

## Prerequisites

- **Python 3.14** (see [`.python-version`](.python-version)). The bundled bindings are
  `cp314` wheels; a 3.12/3.13 venv will reject them with *"not a supported wheel on
  this platform"*.
- A native **openEMS** install. The bindings are version-locked to it.

## Install (Windows)

```powershell
# 1. Native openEMS — install it so CSXCAD.dll / openEMS.dll exist on disk,
#    e.g. at C:\Program Files\openEMS, and (optionally) set the env var:
#       setx OPENEMS_INSTALL_PATH "C:\Program Files\openEMS"
#    run.py auto-detects C:\Program Files\openEMS, so the env var is optional
#    only when openEMS lives there.

# 2. Create the venv with Python 3.14 and install the PyPI deps:
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# 3. Install the openEMS bindings from the wheels bundled in your openEMS
#    install (adjust the path; the cp tag must match your Python — cp314 here):
python -m pip install `
    "C:\Program Files\openEMS\python\csxcad-*-cp314-*.whl" `
    "C:\Program Files\openEMS\python\openems-*-cp314-*.whl"

# 4. Verify and run (run from this folder — run.py uses `import config` / `src.*`):
python -c "import CSXCAD, openEMS; print('bindings OK')"
python run.py
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: No module named 'CSXCAD'` | Step 3 not done — bindings not in this venv. | Install the wheels (step 3) into the venv you launch with. |
| `ImportError: DLL load failed while importing CSXCAD` | DLLs not found: no native openEMS, or `OPENEMS_INSTALL_PATH` wrong/unset and openEMS isn't at `C:\Program Files\openEMS`. | Install native openEMS (step 1) and set `OPENEMS_INSTALL_PATH` to its folder. |
| `... is not a supported wheel on this platform` | Python minor ≠ the wheel's `cp` tag (e.g. `cp310` wheel into a 3.14 venv). | Use a Python whose version matches the wheels, or get wheels built for your Python. |

## A note on reproducibility

The bindings are **not redistributable from any public index**, and the openEMS build
currently in use here is a **local/custom build** (its `cp313`/`cp314` wheels were built
in Oct 2025; the only public release, `v0.0.36`, is from Oct 2023 and ships `cp310`
wheels). That means a teammate **cannot** reproduce this exact setup from an upstream
download — they need the same openEMS build and matching wheels.

How to distribute that build to teammates (self-host your wheels + native runtime, or
standardize on a Python version that has an official openEMS release) is an **open
decision** — this document and `run.py`'s preflight check are the interim safety net so
launches fail with clear guidance rather than a stack trace.
