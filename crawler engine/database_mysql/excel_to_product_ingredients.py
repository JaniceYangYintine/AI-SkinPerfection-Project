import sys
from datetime import datetime
from pathlib import Path

import pandas as pd


def split_ingredients(value: str) -> list[str]:
    if pd.isna(value):
        return []
    return [part.strip() for part in str(value).split(",") if part.strip()]


def main() -> int:
    base = Path(__file__).resolve().parent
    ingredients_path = base / "Ingredients.xlsx"
    products_path = base / "products.xlsx"
    output_path = base / "product_ingredients.xlsx"

    ingredients_df = pd.read_excel(ingredients_path)
    products_df = pd.read_excel(products_path)

    required_ingredients_cols = {"ingredient_id", "ingredient_name_zh"}
    required_products_cols = {"product_id", "category", "name", "ingredients"}

    if not required_ingredients_cols.issubset(ingredients_df.columns):
        missing = sorted(required_ingredients_cols - set(ingredients_df.columns))
        raise ValueError(f"Ingredients.xlsx missing columns: {missing}")
    if not required_products_cols.issubset(products_df.columns):
        missing = sorted(required_products_cols - set(products_df.columns))
        raise ValueError(f"products.xlsx missing columns: {missing}")

    name_to_id = (
        ingredients_df.set_index("ingredient_name_zh")["ingredient_id"]
        .astype(object)
        .to_dict()
    )

    rows = []
    missing_names = set()
    relation_id = 1
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for _, prod in products_df.iterrows():
        ingredients = split_ingredients(prod["ingredients"])
        for name in ingredients:
            ingredient_id = name_to_id.get(name)
            if ingredient_id is None:
                missing_names.add(name)
                continue
            rows.append(
                {
                    "relation_id": relation_id,
                    "ingredient_id": ingredient_id,
                    "ingredient_name_zh": name,
                    "product_id": prod["product_id"],
                    "category": prod["category"],
                    "name": prod["name"],
                    "created_at": created_at,
                }
            )
            relation_id += 1

    if missing_names:
        missing_list = ", ".join(sorted(missing_names))
        raise ValueError(f"Missing ingredient_name_zh in Ingredients.xlsx: {missing_list}")

    output_df = pd.DataFrame(
        rows,
        columns=[
            "relation_id",
            "ingredient_id",
            "ingredient_name_zh",
            "product_id",
            "category",
            "name",
            "created_at",
        ],
    )
    output_df.to_excel(output_path, index=False)
    print(f"Wrote: {output_path}")
    print(f"Rows: {len(output_df)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
