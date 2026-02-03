#!/usr/bin/env python3
# ============================================================
# clean_country_analysis_2015_2024_hpv_rules.py
# ============================================================

from pathlib import Path
import pandas as pd
import numpy as np

INPUT_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/02_cleaned_data/dataset_country_analysis_final_30jan.xlsx"
OUTPUT_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/02_cleaned_data/dataset_country_analysis_final_30jan_clean_2015_2024.xlsx"
SHEET_OUT = "data"

YEAR_MIN, YEAR_MAX = 2015, 2024

def to_na(x):
    """Standardize various N/A strings / blanks to actual NaN."""
    if pd.isna(x):
        return np.nan
    s = str(x).strip()
    if s == "" or s.casefold() in {"n/a", "na", "nan"}:
        return np.nan
    return x

def main():
    df = pd.read_excel(INPUT_FILE, engine="openpyxl")

    required = ["country_code", "year", "gavi_supported", "vax_fd_cov", "first_year_vax_intro", "HPV_INT_DOSES"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}\nColumns seen: {list(df.columns)}")

    # Normalize
    df["country_code"] = df["country_code"].astype("string").str.strip().str.upper()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")

    # Keep only 2015–2024
    df = df[df["year"].between(YEAR_MIN, YEAR_MAX)].copy()

    # Drop missing/blank/N/A gavi_supported
    gavi_clean = df["gavi_supported"].astype("string").str.strip()
    df = df[gavi_clean.notna() & ~gavi_clean.isin(["", "N/A", "n/a", "NA", "na"])].copy()

    # Standardize columns
    df["first_year_vax_intro"] = df["first_year_vax_intro"].apply(to_na)
    intro_year = pd.to_numeric(df["first_year_vax_intro"], errors="coerce")

    df["HPV_INT_DOSES"] = df["HPV_INT_DOSES"].apply(to_na)
    hpv_int = df["HPV_INT_DOSES"].astype("string").str.strip()

    df["vax_fd_cov"] = df["vax_fd_cov"].apply(to_na)
    vax_num = pd.to_numeric(df["vax_fd_cov"], errors="coerce")  # numeric coverage where possible

    # --------------------------------------------------
    # NEW RULE D:
    # If intro_year is missing AND vax_fd_cov is missing -> HPV_INT_DOSES = "no information report vax"
    # --------------------------------------------------
    mask_intro_missing = intro_year.isna()
    mask_vax_missing = vax_num.isna()
    mask_rule_d = mask_intro_missing & mask_vax_missing
    df.loc[mask_rule_d, "HPV_INT_DOSES"] = "no information report vax"

    # --------------------------------------------------
    # NEW RULE E:
    # If intro_year is present AND HPV_INT_DOSES is missing/blank -> HPV_INT_DOSES = "vaccine introduced"
    # --------------------------------------------------
    mask_hpv_int_missing = hpv_int.isna() | (hpv_int.str.strip() == "")
    mask_rule_e = intro_year.notna() & mask_hpv_int_missing
    df.loc[mask_rule_e, "HPV_INT_DOSES"] = "vaccine introduced"

    # Recompute hpv_int after edits (for downstream logic)
    hpv_int = df["HPV_INT_DOSES"].astype("string").str.strip()

    # --------------------------------------------------
    # RULE A:
    # intro_year known AND intro_year > year:
    #   HPV_INT_DOSES = "Not_yet_introduced"
    #   vax_fd_cov = 0
    # --------------------------------------------------
    mask_pre_intro = intro_year.notna() & (intro_year > df["year"])
    df.loc[mask_pre_intro, "HPV_INT_DOSES"] = "Not_yet_introduced"
    df.loc[mask_pre_intro, "vax_fd_cov"] = 0

    # --------------------------------------------------
    # RULE B:
    # intro_year known AND intro_year <= year:
    #   if vax_fd_cov is NA or non-numeric -> set to 0
    # --------------------------------------------------
    mask_post_intro = intro_year.notna() & (intro_year <= df["year"])
    # vax_num is based on original conversion; recompute missingness after any vax edits
    vax_num2 = pd.to_numeric(df["vax_fd_cov"], errors="coerce")
    mask_vax_missing_or_nonnumeric = vax_num2.isna()
    df.loc[mask_post_intro & mask_vax_missing_or_nonnumeric, "vax_fd_cov"] = 0

    # --------------------------------------------------
    # RULE C (previous rule stays when intro year unknown):
    # intro_year missing AND HPV_INT_DOSES == "Not yet introduced" -> vax_fd_cov = NA
    # --------------------------------------------------
    mask_intro_unknown = intro_year.isna()
    mask_not_yet_text = hpv_int.astype("string").str.strip().str.casefold().eq("not yet introduced")
    df.loc[mask_intro_unknown & mask_not_yet_text, "vax_fd_cov"] = np.nan

    # Diagnostics
    print("Rows kept (2015–2024, valid gavi_supported):", len(df))
    print("Unique countries:", df["country_code"].nunique())
    print("Rule D (intro missing & vax missing -> HPV_INT_DOSES='no information report vax') rows:", int(mask_rule_d.sum()))
    print("Rule E (intro present & HPV_INT_DOSES blank -> 'vaccine introduced') rows:", int(mask_rule_e.sum()))
    print("Rule A (pre-intro) rows:", int(mask_pre_intro.sum()))
    print("Rule B (post-intro fill-to-zero) rows:", int((mask_post_intro & mask_vax_missing_or_nonnumeric).sum()))
    print("Rule C (unknown intro & 'not yet introduced' -> vax NA) rows:", int((mask_intro_unknown & mask_not_yet_text).sum()))


    # --------------------------------------------------
    # FINAL harmonization:
    # Treat "Not yet introduced" as "no information report vax"
    # (label-only cleanup; no numeric logic affected)
    # --------------------------------------------------
    df["HPV_INT_DOSES"] = (
    df["HPV_INT_DOSES"]
        .astype("string")
        .str.strip()
        .replace({
            "Not yet introduced": "no information report vax",
        })
    )

    df = df.drop(
    columns=["y1_10_24", "y2_15_24", "y3_20_24", "y4_22_24", "y5_24"],
    errors="ignore"
    )

    
    # --------------------------------------------------
    # Merge DTP first-dose coverage data (OFFICIAL, 2015–2024)
    # --------------------------------------------------
    DTP_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/01_interm_data/dpt_vax_fd_2015_2024.xlsx"

    dtp = pd.read_excel(DTP_FILE, engine="openpyxl")

    # Basic checks
    required_dtp = ["country_code", "year", "dtp_data_source", "dtp_fd_cov"]
    missing = [c for c in required_dtp if c not in dtp.columns]
    if missing:
        raise ValueError(f"DTP file missing required columns: {missing}")

    # Normalize merge keys
    dtp["country_code"] = dtp["country_code"].astype("string").str.strip().str.upper()
    dtp["year"] = pd.to_numeric(dtp["year"], errors="coerce")

    df["country_code"] = df["country_code"].astype("string").str.strip().str.upper()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")

    # Optional: ensure DTP coverage is numeric
    dtp["dtp_fd_cov"] = pd.to_numeric(dtp["dtp_fd_cov"], errors="coerce")

    # Merge (keep all HPV rows)
    df = df.merge(
        dtp,
        on=["country_code", "year"],
        how="left",
        validate="m:1"   # many HPV rows to one DTP row per country-year
)

    # --------------------------------------------------
    # Diagnostics
    # --------------------------------------------------
    print("\n=== DTP merge diagnostics ===")
    print("Rows after merge:", len(df))
    print("Countries with DTP data:", df.loc[df["dtp_fd_cov"].notna(), "country_code"].nunique())
    print("Rows with missing DTP:", df["dtp_fd_cov"].isna().sum())
    print("DTP data source values:", df["dtp_data_source"].dropna().unique().tolist())

    # --------------------------------------------------
    # Merge DTP third-dose coverage data (OFFICIAL, 2015–2024)
    # --------------------------------------------------
    DTP_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/01_interm_data/dpt_vax_ld_2015_2024.xlsx"

    dtp = pd.read_excel(DTP_FILE, engine="openpyxl")

    # Basic checks
    required_dtp = ["country_code", "year", "dtp_data_source_ld", "dtp_ld_cov"]
    missing = [c for c in required_dtp if c not in dtp.columns]
    if missing:
        raise ValueError(f"DTP file missing required columns: {missing}")

    # Normalize merge keys
    dtp["country_code"] = dtp["country_code"].astype("string").str.strip().str.upper()
    dtp["year"] = pd.to_numeric(dtp["year"], errors="coerce")

    df["country_code"] = df["country_code"].astype("string").str.strip().str.upper()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")

    # Optional: ensure DTP coverage is numeric
    dtp["dtp_ld_cov"] = pd.to_numeric(dtp["dtp_ld_cov"], errors="coerce")

    # Merge (keep all HPV rows)
    df = df.merge(
        dtp,
        on=["country_code", "year"],
        how="left",
        validate="m:1"   # many HPV rows to one DTP row per country-year
)

    # --------------------------------------------------
    # Diagnostics
    # --------------------------------------------------
    print("\n=== DTP merge diagnostics ===")
    print("Rows after merge:", len(df))
    print("Countries with DTP data:", df.loc[df["dtp_ld_cov"].notna(), "country_code"].nunique())
    print("Rows with missing DTP:", df["dtp_ld_cov"].isna().sum())
    print("DTP data source values:", df["dtp_data_source_ld"].dropna().unique().tolist())

    # Save
    out_path = Path(OUTPUT_FILE)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(out_path, engine="openpyxl", mode="w") as writer:
        df.to_excel(writer, sheet_name=SHEET_OUT, index=False)

    print("\n✅ Saved cleaned file:", str(out_path))

if __name__ == "__main__":
    main()

