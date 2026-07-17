from __future__ import annotations

import sys
from pathlib import Path

from latex_pic.app import run


if __name__ == "__main__":
    log_path = Path(__file__).with_name("startup.log")
    with log_path.open("a", encoding="utf-8") as log:
        sys.stdout = log
        sys.stderr = log
        raise SystemExit(run())
