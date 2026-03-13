# crawler/main.py
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

# =====================================================
# 品牌 modules（新增品牌一定要在這裡 import）
# =====================================================
from crawler.brands import (
    drwu,
    lrp,
    dior,
    neutrogena,
    paula,
    kiehls,
    drmorita,
    neogence,
    bioessence,
    shiseido,
    clinique,
    sulwhasoo,    # ✅ 已加入
    esteelauder,  # ✅ 新增 esteelauder
)

from crawler.engine.fetch import Fetcher
from crawler.engine.output import write_products_csv
from crawler.engine.runner import Runner

# =====================================================
# 設定
# =====================================================
STAGE = "stage1"

BRANDS = {
    "drwu": drwu,
    "lrp": lrp,
    "neutrogena": neutrogena,
    "paula": paula,
    "dior": dior,
    "kiehls": kiehls,
    "drmorita": drmorita,
    "neogence": neogence,
    "bioessence": bioessence,
    "shiseido": shiseido,
    "clinique": clinique,
    "sulwhasoo": sulwhasoo,
    "esteelauder": esteelauder,  # ✅ 註冊 esteelauder
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("brand", help=f"brand key: {', '.join(BRANDS.keys())}")
    parser.add_argument("--download-images", action="store_true", help="download product images")
    parser.add_argument("--images-dir", default="data/images", help="images output dir")
    parser.add_argument("--timeout", type=float, default=25.0, help="request timeout seconds")
    args = parser.parse_args()

    brand_key = args.brand.lower().strip()
    if brand_key not in BRANDS:
        print(f"[error] unknown brand: {brand_key}")
        print(f"available: {', '.join(BRANDS.keys())}")
        sys.exit(1)

    fetcher = Fetcher(timeout=args.timeout)
    runner = Runner(fetcher=fetcher, stage=STAGE)

    brand_module = BRANDS[brand_key]
    print(f"Start crawl: {brand_key} ({STAGE})")
    print(f"[main] using Runner for {brand_key}")

    products = runner.run_brand(
        brand_module,
        download_images=args.download_images,
        images_dir=Path(args.images_dir),
    )

    out_dir = Path("data") / STAGE
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{brand_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    write_products_csv(products, out_path)

    print(f"[done] products: {len(products)}")
    print(f"[done] csv: {out_path}")


if __name__ == "__main__":
    main()
