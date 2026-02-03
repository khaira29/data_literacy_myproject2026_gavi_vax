#!/usr/bin/env python3
# ============================================================
# clean_dtp_fd_cov_2015_2024_official.py
# ============================================================

from pathlib import Path
import pandas as pd

INPUT_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/00_raw_data/Diphtheria tetanus toxoid and pertussis (DTP) vaccination coverage 1st dose 2026-15-01 12-07 UTC.xlsx"
OUTPUT_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/01_interm_data/dpt_vax_fd_2015_2024.xlsx"
OUT_SHEET = "dtp_fd_2015_2024"

YEAR_MIN, YEAR_MAX = 2015, 2024

KEEP_COLS = ["CODE", "YEAR", "COVERAGE_CATEGORY", "COVERAGE"]

RENAME_MAP = {
    "CODE": "country_code",
    "YEAR": "year",
    "COVERAGE_CATEGORY": "dtp_data_source",
    "COVERAGE": "dtp_fd_cov",
}

def main():
    df = pd.read_excel(INPUT_FILE, engine="openpyxl")

    # Normalize column names
    df.columns = (
        df.columns.astype(str)
        .str.replace("\u00a0", " ", regex=False)
        .str.strip()
        .str.upper()
    )

    missing = [c for c in KEEP_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns: {missing}\nColumns seen: {df.columns.tolist()}")

    # Keep only needed columns
    df = df[KEEP_COLS].copy()

    # Year filter
    df["YEAR"] = pd.to_numeric(df["YEAR"], errors="coerce")
    df = df[df["YEAR"].between(YEAR_MIN, YEAR_MAX)].copy()

    # Keep only OFFICIAL source
    df["COVERAGE_CATEGORY"] = df["COVERAGE_CATEGORY"].astype("string").str.strip().str.upper()
    df = df[df["COVERAGE_CATEGORY"].eq("OFFICIAL")].copy()

    # Clean country code
    df["CODE"] = df["CODE"].astype("string").str.strip().str.upper()

    # Optional: make coverage numeric (keeps NaN if not parseable)
    df["COVERAGE"] = pd.to_numeric(df["COVERAGE"], errors="coerce")

    # Rename
    df = df.rename(columns=RENAME_MAP)

    # Save
    out_path = Path(OUTPUT_FILE)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out_path, engine="openpyxl", mode="w") as writer:
        df.to_excel(writer, sheet_name=OUT_SHEET, index=False)

    print("✅ Saved:", str(out_path))
    print("Rows:", len(df))
    print("Unique countries:", df["country_code"].nunique())
    print("Years:", int(df["year"].min()), "-", int(df["year"].max()))
    print("dtp_data_source unique:", df["dtp_data_source"].unique().tolist())

if __name__ == "__main__":
    main()
