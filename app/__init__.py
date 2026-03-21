"""Application package bootstrap.

Ensures legacy top-level imports like `pipeline`, `modules`, and `utils`
continue to resolve when importing via `app.*` from repository root.
"""

from __future__ import annotations

import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parent
_APP_DIR_STR = str(_APP_DIR)

if _APP_DIR_STR not in sys.path:
    sys.path.insert(0, _APP_DIR_STR)
