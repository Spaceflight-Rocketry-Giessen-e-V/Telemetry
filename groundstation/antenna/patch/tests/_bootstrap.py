# -*- coding: utf-8 -*-
"""Shared test-harness bootstrap: openEMS DLL discovery + project root on sys.path.

Import this as the FIRST import of any harness in this folder (``import _bootstrap``)
so the per-file boilerplate lives in exactly one place. It does two things:

1. On Windows, point ``OPENEMS_INSTALL_PATH`` at a local openEMS install (mirrors
   run.preflight_check) so ``from CSXCAD import ...`` / ``from openEMS import ...``
   can find the native DLLs.
2. Put the project root (the parent of tests/) on ``sys.path`` so ``import config``
   and ``from src.* import ...`` resolve when a harness is run as a script.

Harnesses are run as ``python tests/<harness>.py``, so the tests/ directory is on
sys.path[0] and ``import _bootstrap`` resolves before the project root is added.
Keep it first, ahead of any config / CSXCAD / openEMS import (its side effects must
run before those imports).
"""

import os
import sys

if os.name == 'nt' and not os.environ.get('OPENEMS_INSTALL_PATH'):
    for _c in (r'C:\Program Files\openEMS', r'C:\opt\openEMS',
               os.path.join(os.environ.get('LOCALAPPDATA', ''), 'openEMS')):
        if _c and os.path.exists(os.path.join(_c, 'CSXCAD.dll')):
            os.environ['OPENEMS_INSTALL_PATH'] = _c
            break

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
