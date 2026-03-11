"""CLI entry for running brand crawlers."""

import argparse
import inspect
import sys
from datetime import datetime
from pathlib import Path

# Ensure the crawler modules can be imported after moving this script into pipeline/
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# import brands.dior as dior
import brands.drwu as drwu
import brands.lrp as lrp
import brands.neutrogena as neutrogena
import brands.paula as paula
import brands.lorealparis as lorealparis
import brands.watsons_olay as watsons_olay
import brands.ahc as ahc
import brands.shuuemura as shuuemura
import brands.clarins as clarins
import brands.chanel_manual as chanel_manual
import brands.chanel_category_list as chanel_category_list

from engine.fetch import Fetcher
from engine.output import write_products_csv
from engine.auto_runner import Runner
from engine.manual_runner import run_manual

STAGE = "stage1"

# Mapping from CLI brand key to crawler module.
BRANDS = {
    "drwu": drwu,
    "drwu": drwu,
    "lrp": lrp,
    "neutrogena": neutrogena,
    "neutrogena": neutrogena,
    "paula": paula,
    "lorealparis": lorealparis,
    "watsons_olay": watsons_olay,
    "ahc": ahc,
    "shuuemura": shuuemura,
    "clarins": clarins,
    "chanel_manual": chanel_manual,
    "chanel_categories": chanel_category_list,
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a brand crawler")
    parser.add_argument(
        "brand",
        nargs="?",
        choices=list(BRANDS.keys()),
        help="brand key to crawl (leave empty to run all)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="optional product limit when supported by brand runner",
    )
    parser.add_argument(
        "--stage",
        default=STAGE,
        help="stage name used in output filename",
    )
    return parser.parse_args()


def _build_output_path(base_dir: Path, brand_key: str, stage: str) -> Path:
    """
    Create output directory if needed and return the CSV path for this run.
    """
    output_dir = base_dir / "output"  # crawler/output
    output_dir.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now().strftime("%y%m%d_%H%M")
    return output_dir / f"{brand_key}_{stage}_{run_id}.csv"


def _run_brand(brand_key: str, brand_module, limit: int | None, stage: str) -> None:
    print(f"Start crawl: {brand_key} ({stage})")

    fetcher = Fetcher()
    runner = Runner(fetcher)

    try:
        if getattr(brand_module, "MODE", "").lower() == "manual":
            products = run_manual(fetcher, brand_module)
        elif hasattr(brand_module, "run"):
            sig = inspect.signature(brand_module.run)
            if "limit" in sig.parameters:
                products = brand_module.run(fetcher, limit=limit)
            else:
                products = brand_module.run(fetcher)
        else:
            products = runner.run_brand(brand_module, limit=limit)

        # Write outputs under the crawler root so downstream stages can find them.
        base_dir = ROOT_DIR  # crawler/
        output_path = _build_output_path(base_dir, brand_key, stage)
        write_products_csv(products, str(output_path))

        print("=" * 60)
        print(f"Done: {brand_key}")
        print(f"Items exported: {len(products)}")
        print(f"Output file: {output_path}")
        print("=" * 60)
    except Exception as e:  # noqa: BLE001 - keep behavior identical to previous broad except
        print(f"Error crawling {brand_key}: {e}")
        print("=" * 60)


def main() -> None:
    args = _parse_args()
    
    if args.brand:
        target_brands = [args.brand.lower().strip()]
    else:
        target_brands = list(BRANDS.keys())

    for brand_key in target_brands:
        brand_module = BRANDS[brand_key]
        _run_brand(brand_key, brand_module, args.limit, args.stage)


if __name__ == "__main__":
    main()

# python crawler\main.py drwu
# python crawler\main.py lrp
# python crawler\main.py neutrogena
# python crawler\main.py paula
# python crawler\main.py lorealparis
# python crawler\main.py watsons_olay
# python crawler\main.py ahc
# python crawler\main.py shuuemura
# python crawler\main.py clarins
# python crawler\main.py chanel_manual
