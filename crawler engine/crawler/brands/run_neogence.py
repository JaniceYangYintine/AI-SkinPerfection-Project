from crawler.engine.fetch import Fetcher
from crawler.brands.neogence import CATEGORY_PAGES, get_product_urls_by_category, parse_product
import pandas as pd

def main():
    fetcher = Fetcher()

    pairs = get_product_urls_by_category(fetcher, CATEGORY_PAGES)
    print("total urls:", len(pairs))

    rows = []
    for category, url in pairs:
        html = fetcher.get(url)
        product = parse_product(html, url, category)
        rows.append(product.__dict__)

    df = pd.DataFrame(rows)
    df.to_csv("neogence_products.csv", index=False, encoding="utf-8-sig")
    df.to_json("neogence_products.json", force_ascii=False, indent=2)

    print("✅ 已輸出 neogence_products.csv / neogence_products.json")

if __name__ == "__main__":
    main()
