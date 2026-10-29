"""Run without installing: python scripts/demo_indicators.py"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from qslab.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["demo", "--tail", "8"]))
