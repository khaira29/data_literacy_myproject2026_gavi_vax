# ============================================================
# edit_dataset_country_analysis_final_30jan_excel_only.py
# ============================================================

from pathlib import Path
import pandas as pd
import numpy as np

INPUT_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/02_cleaned_data/dl_pro_final_dataset_country_jan29.xlsx"
SHEET_NAME = "Sheet1"

OUT_DIR = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/02_cleaned_data"
OUT_XLSX_NAME = "dataset_country_analysis_final_30jan.xlsx"

DROP_COLS = [
    "ANTIGEN",
    "ANTIGEN_DESCRIPTION",
    "COVERAGE_CATEGORY",
    "COVERAGE_CATEGORY_DESCRIPTION",
]

RENAME_MAP = {
    "TARGET_NUMBER": "vax_target",
    "DOSES": "vax_doses",
    "COVERAGE": "vax_fd_cov",
    "REGION": "who_reg",
    "HPV_NATIONAL_SCHEDULE": "has_vax_nat_schedule",
    "HPV_YEAR_INTRODUCTION": "first_year_vax_intro",
    "HPV_PRIM_DELIV_STRATEGY": "type_prim_deliv_vax",
    "HPV_AGEADMINISTERED": "age_adm_vax",
    "HPV_SEX": "sex_adm_vax",
}


def load_excel(path: str, sheet_name: str) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")


def main():
    out_dir = Path(OUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    # -----------------------------
    # Load
    # -----------------------------
    df = load_excel(INPUT_FILE, SHEET_NAME)

    # Normalize column names robustly
    df.columns = (
        df.columns.astype(str)
        .str.replace("\u00a0", " ", regex=False)  # non-breaking space
        .str.strip()
    )

    # -----------------------------
    # 1) Fix country names
    # -----------------------------
    if "country_code" not in df.columns or "country_name" not in df.columns:
        raise ValueError(
            "Expected 'country_code' and 'country_name' columns not found.\n"
            f"Columns seen: {df.columns.tolist()}"
        )

    df["country_code"] = df["country_code"].astype(str).str.strip()

    df.loc[df["country_code"].eq("COK"), "country_name"] = "Cook Island"
    df.loc[df["country_code"].eq("NIU"), "country_name"] = "NIUE"

    # -----------------------------
    # 2) Replace blank strings + NaN with "N/A"
    # -----------------------------
    df = df.replace(r"^\s*$", np.nan, regex=True)  # empty/whitespace -> NaN
    df = df.fillna("N/A")

    # -----------------------------
    # 3) Drop columns
    # -----------------------------
    df = df.drop(columns=[c for c in DROP_COLS if c in df.columns], errors="ignore")

    # -----------------------------
    # 4) Rename columns
    # -----------------------------
    df = df.rename(columns={k: v for k, v in RENAME_MAP.items() if k in df.columns})

    # -----------------------------
    # Ensure year is numeric BEFORE window logic
    # -----------------------------
    if "year" not in df.columns:
        raise ValueError("Column 'year' not found.")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")

    # -----------------------------
    # 4.6) Country-level completeness flags over different year windows
    # -----------------------------
    KEY_COLS = [
        "income_class",
        "vax_fd_cov",
        "has_vax_nat_schedule",
        "type_prim_deliv_vax",
        "first_year_vax_intro",
    ]

    missing_keys = [c for c in KEY_COLS if c not in df.columns]
    if missing_keys:
        raise ValueError(
            f"Missing required KEY_COLS after renaming: {missing_keys}\n"
            f"Columns seen: {df.columns.tolist()}"
        )

    # Row completeness: no key columns are N/A and not missing
    row_complete = df[KEY_COLS].apply(
        lambda s: s.notna() & (s.astype(str) != "N/A")
    ).all(axis=1)

    def country_complete_in_window(df_in: pd.DataFrame, y_min: int, y_max: int) -> pd.Series:
        """
        True if for ALL years within [y_min, y_max]:
        - the country has at least one row for each year, and
        - all rows are complete on KEY_COLS within that window.
        Returns a Series indexed by country_code.
        """
        sub = df_in[df_in["year"].between(y_min, y_max)].copy()

        # attach row completeness
        sub["_row_complete"] = row_complete.loc[sub.index]

        # must have all years present
        years_needed = set(range(y_min, y_max + 1))
        years_present = sub.groupby("country_code")["year"].apply(
            lambda s: set(s.dropna().astype(int).unique())
        )
        has_all_years = years_present.apply(lambda ys: years_needed.issubset(ys))

        # must be complete on all rows in window
        all_complete = sub.groupby("country_code")["_row_complete"].all()

        # align to all countries in df_in
        all_countries = pd.Index(df_in["country_code"].unique(), name="country_code")
        out = (has_all_years & all_complete).reindex(all_countries, fill_value=False)
        return out

    # Create flags
    y1 = country_complete_in_window(df, 2010, 2024)
    y2 = country_complete_in_window(df, 2015, 2024)
    y3 = country_complete_in_window(df, 2020, 2024)
    y4 = country_complete_in_window(df, 2022, 2024)

    # 2024-only flag
    sub_2024 = df[df["year"].eq(2024)].copy()
    sub_2024["_row_complete"] = row_complete.loc[sub_2024.index]
    y5 = sub_2024.groupby("country_code")["_row_complete"].all()
    y5 = y5.reindex(pd.Index(df["country_code"].unique(), name="country_code"), fill_value=False)

    # Merge flags back to df (repeat per row per country)
    flag_df = pd.DataFrame({
        "country_code": df["country_code"].unique(),
        "y1_10_24": y1.values,
        "y2_15_24": y2.values,
        "y3_20_24": y3.values,
        "y4_22_24": y4.values,
        "y5_24": y5.values,
    })

    # Attach gavi_supported per country_code (take first non-missing per country)
    if "gavi_supported" in df.columns:
        gavi_map = (
            df[["country_code", "gavi_supported"]]
            .replace("N/A", np.nan)
            .dropna(subset=["gavi_supported"])
            .drop_duplicates(subset=["country_code"])
            .set_index("country_code")["gavi_supported"]
    )
     
        flag_df["gavi_supported"] = flag_df["country_code"].map(gavi_map)
    else:
        flag_df["gavi_supported"] = pd.NA

    df = df.merge(flag_df, on="country_code", how="left")

    # -----------------------------
    # 4.7) For each flag: how many country_code are missing vs not missing
    #      + within each (missing / not missing), how many are gavi supported vs not
    # -----------------------------
    print("\n=== Completeness flags: missing vs not-missing, with Gavi support breakdown (by country_code) ===")

    if "gavi_supported" not in flag_df.columns:
        raise ValueError("Column 'gavi_supported' not found in flag_df.")

    # Normalize gavi_supported into two categories
    flag_df["_gavi_flag"] = (
        flag_df["gavi_supported"]
        .astype("string")
        .str.strip()
        .str.casefold()
        .map({
            "supported by gavi": "supported",
            "not supported by gavi": "not_supported",
        })
        .fillna("unknown")
    )

    FLAG_COLS = ["y1_10_24", "y2_15_24", "y3_20_24", "y4_22_24", "y5_24"]

    for col in FLAG_COLS:
        print(f"\n--- {col} ---")

        # Interpret True = not-missing/complete; False = missing/incomplete
        n_not_missing = int((flag_df[col] == True).sum())
        n_missing = int((flag_df[col] == False).sum())
        print(f"Not-missing (True) : {n_not_missing:,}")
        print(f"Missing (False)    : {n_missing:,}")
        print(f"Total countries    : {n_not_missing + n_missing:,}")

        # Crosstab: rows=True/False, cols=gavi status
        ctab = pd.crosstab(flag_df[col], flag_df["_gavi_flag"])

        # Ensure stable columns for printing
        for g in ["supported", "not_supported", "unknown"]:
            if g not in ctab.columns:
                ctab[g] = 0
        for v in [True, False]:
            if v not in ctab.index:
                ctab.loc[v] = 0

        # NOT missing group (True)
        print(
            "  Among NOT-missing (True): "
            f"supported={int(ctab.loc[True, 'supported']):,} | "
            f"not_supported={int(ctab.loc[True, 'not_supported']):,} | "
            f"unknown={int(ctab.loc[True, 'unknown']):,}"
        )

        # Missing group (False)
        print(
            "  Among MISSING (False)   : "
            f"supported={int(ctab.loc[False, 'supported']):,} | "
            f"not_supported={int(ctab.loc[False, 'not_supported']):,} | "
            f"unknown={int(ctab.loc[False, 'unknown']):,}"
        )

    # Cleanup helper col
    flag_df.drop(columns=["_gavi_flag"], inplace=True, errors="ignore")

    # -----------------------------
    # Drop duplicate Gavi column (safety cleanup)
    # -----------------------------
    df = df.drop(columns=["gavi_supported_y"], errors="ignore")
    df = df.rename(columns={"gavi_supported_x": "gavi_supported"})

    # -----------------------------
    # 5) Write Excel
    # -----------------------------
    out_path = out_dir / OUT_XLSX_NAME
    sheet_out = "data"

    with pd.ExcelWriter(out_path, engine="openpyxl", mode="w") as writer:
        df.to_excel(writer, sheet_name=sheet_out, index=False)

    print("\nSaved Excel:", out_path)

    # Quick verification prints
    print("COK country_name:", df.loc[df["country_code"].eq("COK"), "country_name"].head(1).tolist())
    print("NIU country_name:", df.loc[df["country_code"].eq("NIU"), "country_name"].head(1).tolist())


if __name__ == "__main__":
    main()
