"""Pytest bootstrap — make repo sources importable without ``pip install -e .``.

Adds the repo's source roots to ``sys.path``. Order matters: ``src/`` must
come first so ``health_agent_infra`` resolves to the installable package,
not the ``safety/health_agent_infra/`` compatibility wrappers (which shadow
the name until commit 4a deletes them).
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
for _entry in (_ROOT, _ROOT / "safety", _ROOT / "clean", _ROOT / "src"):
    if str(_entry) not in sys.path:
        sys.path.insert(0, str(_entry))
