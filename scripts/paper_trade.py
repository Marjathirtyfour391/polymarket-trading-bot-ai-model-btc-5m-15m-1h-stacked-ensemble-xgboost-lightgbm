"""Paper trading entry point."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from polymarket_bot.main import main

if __name__ == "__main__":
    os.environ.setdefault("TRADING_MODE", "paper")
    main()
