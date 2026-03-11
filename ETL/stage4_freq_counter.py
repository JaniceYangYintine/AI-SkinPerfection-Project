import os
import sys
from collections import Counter
from datetime import datetime

import pandas as pd

DEFAULT_COLUMNS = [
    "matched_ingredients",
    "matched_effects",
    "matched_concerns",
    "matched_skintype_sensitivity",
    "matched_age",
    "matched_usage_frequency",
]

ALT_COLUMNS = [c.replace("matched_", "") for c in DEFAULT_COLUMNS]
DEFAULT_RANGE = "F:J"


def split_tokens(cell):
    if pd.isna(cell):
        return []
    text = str(cell).strip()
    if not text:
        return []
    parts = [p.strip() for p in text.split(",")]
    return [p for p in parts if p]


def pick_columns(df):
    if all(c in df.columns for c in DEFAULT_COLUMNS):
        return DEFAULT_COLUMNS
    if all(c in df.columns for c in ALT_COLUMNS):
        return ALT_COLUMNS

    missing_default = [c for c in DEFAULT_COLUMNS if c not in df.columns]
    missing_alt = [c for c in ALT_COLUMNS if c not in df.columns]

    print("Missing columns. Expected one full set:")
    print("- Default:", ", ".join(missing_default) if missing_default else "(all found)")
    print("- Alternate:", ", ".join(missing_alt) if missing_alt else "(all found)")
    sys.exit(1)


def columns_from_range(df, col_range: str):
    if not col_range:
        return []
    if ":" not in col_range:
        return []
    start, end = col_range.split(":", 1)
    start = start.strip().upper()
    end = end.strip().upper()
    if not (start.isalpha() and end.isalpha()):
        return []

    # Convert Excel letters to 0-based index.
    def col_to_idx(col):
        idx = 0
        for ch in col:
            idx = idx * 26 + (ord(ch) - ord("A") + 1)
        return idx - 1

    s = col_to_idx(start)
    e = col_to_idx(end)
    if s < 0 or e < 0 or e < s:
        return []
    return list(df.columns[s : e + 1])


def main():
    path = input("Enter file path (csv/xlsx): ").strip().strip('"')
    if not path:
        print("No file path provided")
        sys.exit(1)

    ext = os.path.splitext(path)[1].lower()
    if ext in [".xlsx", ".xls"]:
        df = pd.read_excel(path)
    elif ext == ".csv":
        try:
            df = pd.read_csv(path, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(path, encoding="big5")
    else:
        print("Only csv or xlsx is supported")
        sys.exit(1)

    columns = columns_from_range(df, DEFAULT_RANGE) or pick_columns(df)

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(output_dir, f"freq_counter_{timestamp}.xlsx")

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        for col in columns:
            counter = Counter()
            for cell in df[col]:
                counter.update(split_tokens(cell))

            out = pd.DataFrame(counter.most_common(), columns=["token", "count"])
            sheet_name = col[:31]
            out.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()

# python crawler/stage3_freq_counter.py
# C:\Users\TMP-214\Desktop\cji102_project\crawler\output\stageX_official_ingredients_20260111_205950.xlsx