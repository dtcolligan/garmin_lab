"""Pytest bootstrap — make the installable package importable from ``src/``.

This avoids requiring ``pip install -e .`` for the test suite.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
