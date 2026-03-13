# stage4: apply unified labels from stage3 mapping to stage2.2 tags
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd


DEFAULT_STAGE2_GLOB = "stageX_official_ingredients_*.xlsx"
DEFAULT_STAGE3_GLOB = "freq_counter_*.xlsx"

BONUS_TERMS = {
    "乾燥",
    "粗糙",
    "老廢角質",
    "髒污",
    "脫屑",
    "彩妝殘留",
    "缺水",
    "緊繃",
    "脫皮",
    "乾癢",
    "水分散失",
    "乾繃",
    "換季乾燥",
    "保濕",
    "防曬",
    "去角質",
    "清潔",
    "鎖水",
    "滋潤",
    "補水",
    "卸妝",
    "預防曬黑",
    "預防光老化",
    "改善粗糙",
    "淨化",
    "潤色",
    "深層清潔",
    "煥膚",
    "煥活",
    "鎖水保濕",
    "代謝角質",
    "充盈肌膚",
    "細緻肌膚",
    "潤色提亮",
    "澎潤",
    "保濕潤澤",
    "提升柔嫩度",
    "爆水",
    "深潤",
    "柔軟肌膚",
    "改善乾燥",
    "長效保濕",
    "隔離",
    "阻隔紫外線",
    "阻隔紅外線",
    "防空污",
    "潤澤",
    "保濕鎖水",
    "細緻膚質",
    "柔嫩",
    "加速更新",
    "煥顏",
    "代謝更新",
    "補水保濕",
    "滲透保濕",
    "溫和煥膚",
    "煥活肌膚",
    "促進角質代謝",
    "平滑肌膚",
    "隔離空污",
    "平滑粗糙",
    "撫平粗糙",
    "改善膚",
}


def build_mapping(stage3_path: Path, sheet_name: str) -> dict[str, str]:
    df = pd.read_excel(stage3_path, sheet_name=sheet_name)
    if df.empty:
        return {}
    token_col = df.columns[0]
    unified_col = df.columns[2] if len(df.columns) >= 3 else None
    mapping: dict[str, str] = {}
    for _, row in df.iterrows():
        token = row.get(token_col)
        if pd.isna(token):
            continue
        token = str(token).strip()
        if not token:
            continue
        unified_val = token
        if unified_col:
            unified = row.get(unified_col)
            if not pd.isna(unified) and str(unified).strip():
                unified_val = str(unified).strip()
        mapping[token] = unified_val
    return mapping


def split_tags(text: object) -> list[str]:
    if pd.isna(text):
        return []
    raw = str(text).strip()
    if not raw:
        return []
    # Accept both comma and ideographic comma separators.
    normalized = (
        raw.replace("、", ",")
        .replace("；", ",")
        .replace(";", ",")
        .replace("\n", ",")
    )
    return [p.strip() for p in normalized.split(",") if p.strip()]


def add_unique(target: list[str], seen: set[str], tag: str) -> None:
    if tag and tag not in seen:
        seen.add(tag)
        target.append(tag)


def map_from_text(text: str, mapping: dict[str, str], allowed: set[str] | None = None) -> list[str]:
    if not text:
        return []
    result: list[str] = []
    seen: set[str] = set()
    for token, unified in mapping.items():
        if allowed is not None and token not in allowed:
            continue
        if token and token in text:
            add_unique(result, seen, unified)
    return result


def map_from_list(tokens: list[str], mapping: dict[str, str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        if token in mapping:
            add_unique(result, seen, mapping[token])
    return result


def pick_sheet(xls: pd.ExcelFile, candidates: list[str]) -> str | None:
    for name in candidates:
        if name in xls.sheet_names:
            return name
    return None


def main() -> int:
    base_dir = Path(__file__).resolve().parent / "output"
    if len(sys.argv) > 1:
        stage2_path = base_dir / sys.argv[1]
    else:
        stage2_candidates = list(base_dir.glob(DEFAULT_STAGE2_GLOB))
        if not stage2_candidates:
            raise FileNotFoundError(f"No files match {DEFAULT_STAGE2_GLOB}")
        stage2_path = max(stage2_candidates, key=lambda p: p.stat().st_mtime)

    if len(sys.argv) > 2:
        stage3_path = base_dir / sys.argv[2]
    else:
        stage3_candidates = list(base_dir.glob(DEFAULT_STAGE3_GLOB))
        if not stage3_candidates:
            stage3_candidates = list(base_dir.glob(FALLBACK_STAGE3_GLOB))
        if not stage3_candidates:
            raise FileNotFoundError(
                f"No files match {DEFAULT_STAGE3_GLOB} or {FALLBACK_STAGE3_GLOB}"
            )
        stage3_path = max(stage3_candidates, key=lambda p: p.stat().st_mtime)

    if not stage2_path.exists():
        raise FileNotFoundError(stage2_path)
    if not stage3_path.exists():
        raise FileNotFoundError(stage3_path)

    df = pd.read_excel(stage2_path, sheet_name=0)
    xls = pd.ExcelFile(stage3_path)

    ingredients_sheet = pick_sheet(xls, ["ingredients", "成分"])
    features_sheet = pick_sheet(xls, ["特徵", "effects"])
    skintype_sheet = pick_sheet(xls, ["skintype", "膚質"])
    sensitivity_sheet = pick_sheet(xls, ["sensitivity", "敏感"])
    age_sheet = pick_sheet(xls, ["age", "年齡"])
    bonus_sheet = pick_sheet(xls, ["加分條件", "concerns", "問題"])

    ingredients_map = build_mapping(stage3_path, ingredients_sheet) if ingredients_sheet else {}
    features_map = build_mapping(stage3_path, features_sheet) if features_sheet else {}
    skintype_map = build_mapping(stage3_path, skintype_sheet) if skintype_sheet else {}
    sensitivity_map = build_mapping(stage3_path, sensitivity_sheet) if sensitivity_sheet else {}
    age_map = build_mapping(stage3_path, age_sheet) if age_sheet else {}
    bonus_map = build_mapping(stage3_path, bonus_sheet) if bonus_sheet else {}

    name_col = "品名" if "品名" in df.columns else (df.columns[2] if len(df.columns) > 2 else None)
    if "產品描述" in df.columns:
        text_col = "產品描述"
    elif "產品特色" in df.columns:
        text_col = "產品特色"
    else:
        text_col = df.columns[4] if len(df.columns) > 4 else None
    ingredients_col = "ingredients" if "ingredients" in df.columns else (
        "ingredients_official" if "ingredients_official" in df.columns else None
    )

    out_rows = []
    for _, row in df.iterrows():
        text = str(row.get(text_col, "")).strip() if text_col else ""
        name = str(row.get(name_col, "")).strip() if name_col else ""

        ing_tokens = split_tags(row.get(ingredients_col, "")) if ingredients_col else []
        ingredients = map_from_list(ing_tokens, ingredients_map)
        features = map_from_text(text, features_map)
        skintype = map_from_text(text, skintype_map)
        sensitivity = map_from_text(text, sensitivity_map)
        age = map_from_text(text, age_map)
        bonus = map_from_text(text, bonus_map, allowed=BONUS_TERMS)

        out_rows.append(
            {
                "品牌": row.get("品牌", ""),
                "產品分類": row.get("產品分類", ""),
                "品名": name,
                "價格": row.get("價格", ""),
                "產品描述": row.get(text_col, "") if text_col else "",
                "ingredients": ", ".join(ingredients),
                "特徵": ", ".join(features),
                "skintype": ", ".join(skintype),
                "sensitivity": ", ".join(sensitivity),
                "age": ", ".join(age),
                "加分條件": ", ".join(bonus),
                "商品網址": row.get("商品網址", ""),
                "圖片網址": row.get("圖片網址", ""),
                "爬蟲時間": row.get("爬蟲時間", ""),
            }
        )

    out_df = pd.DataFrame(out_rows)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_name = f"stage4_apply_mapping_{stamp}.xlsx"
    out_path = base_dir / out_name
    ordered_cols = [
        "品牌",
        "產品分類",
        "品名",
        "價格",
        "產品描述",
        "ingredients",
        "特徵",
        "skintype",
        "sensitivity",
        "age",
        "加分條件",
        "商品網址",
        "圖片網址",
        "爬蟲時間",
    ]
    cols = [c for c in ordered_cols if c in out_df.columns]
    remaining = [c for c in out_df.columns if c not in cols]
    out_df = out_df[cols + remaining]
    out_df.to_excel(out_path, index=False)

    print(f"Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# python crawler\stage4_apply_mapping.py
