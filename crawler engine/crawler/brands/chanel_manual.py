"""Manual-URL crawler for Chanel (uses requests + text parsing)."""

from pathlib import Path

from . import chanel_parser as chanel_base

# Mark this brand as manual mode for main.py
MODE = "manual"

# URL list path (one URL per line)
URL_LIST = Path(__file__).resolve().parent.parent / "urls" / "chanel.txt"

# Re-export parser used by the generic manual runner.
parse_product_with_text = chanel_base.parse_product_with_text
