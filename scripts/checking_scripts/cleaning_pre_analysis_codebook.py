# ============================================================
# clean_and_codebook_hpv_panel.py
# ============================================================
# Input:
#   dl_pro_final_dataset_country_jan29.xlsx
#
# Outputs:
#   1) cleaned_renamed_dataset.csv
#   2) missingness_report.csv
#   3) codebook.csv
#
# What it does:
#   (1) Checks missingness for specified columns
#   (2) Renames columns (keeps mapping in codebook: old -> new)
#   (3) Creates a codebook with types, unique counts, examples, missingness
# ============================================================

from __future__ import annotations

from pathlib import Path
import pandas as pd
import numpy as np


# -----------------------------
# USER SETTINGS (EDIT)
# -----------------------------
INPUT_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/02_cleaned_data/dl_pro_final_dataset_country_jan29.xlsx"
SHEET_NAME = None  # put sheet name if needed, else None
OUTPUT_DIR = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/02_cleaned_data/_documentation_outputs"


# -----------------------------
# Columns you want to check
# (exactly as you wrote)
# -----------------------------
COLUMNS_TO_CHECK = [
    "country_code",
    "country_name",
    "year",
    "income_class",
    "gavi_spec",
    "gavi_supported",
    "ANTIGEN",
    "ANTIGEN_DESCRIPTION",
    "COVERAGE_CATEGORY",
    "COVERAGE_CATEGORY_DESCRIPTION",
    "TARGET_NUMBER",
    "DOSES",
    "COVERAGE",
    "REGION",
    "HPV_INT_DOSES",
    "HPV_NATIONAL_SCHEDULE",
    "HPV_YEAR_INTRODUCTION",
    "HPV_PRIM_DELIV_STRATEGY",
    "HPV_AGEADMINISTERED",
    "HPV_SEX",
    "cerv_can_cr_rate_2022",
]


# -----------------------------
# Rename map: old -> new
# You can change the new names here.
# (Old names will be preserved in the codebook.)
# -----------------------------
RENAME_MAP = {
    "country_code": "iso3",
    "country_name": "country",
    "year": "year",

    "income_class": "wb_income",

    "gavi_spec": "gavi_status",
    "gavi_supported": "gavi_supported",

    "ANTIGEN": "antigen",
    "ANTIGEN_DESCRIPTION": "antigen_desc",

    "COVERAGE_CATEGORY": "coverage_category",
    "COVERAGE_CATEGORY_DESCRIPTION": "coverage_category_desc",

    "TARGET_NUMBER": "target_n",
    "DOSES": "doses",
    "COVERAGE": "coverage",

    "REGION": "region",

    "HPV_INT_DOSES": "hpv_int_doses",
    "HPV_NATIONAL_SCHEDULE": "hpv_national_schedule",
    "HPV_YEAR_INTRODUCTION": "hpv_intro_year",
    "HPV_PRIM_DELIV_STRATEGY": "hpv_primary_delivery",
    "HPV_AGEADMINISTERED": "hpv_age_administered",
    "HPV_SEX": "hpv_sex",

    "cerv_can_cr_rate_2022": "cervical_cancer_crude_rate_2022",
}


# -----------------------------
# Short descriptions for codebook
# (Edit anytime — these will appear in the codebook file)
# -----------------------------
DESCRIPTION_MAP = {
    "country_code": "ISO3 country code identifier.",
    "country_name": "Country name (text label).",
    "year": "Calendar year of observation (panel index).",
    "income_class": "World Bank income classification (varies by year).",
    "gavi_spec": "Gavi eligibility/status category (varies by year).",
    "gavi_supported": "Indicator/category whether country is supported by Gavi (varies by year).",

    "ANTIGEN": "Antigen identifier (dataset-level; HPV assumed but column retained here).",
    "ANTIGEN_DESCRIPTION": "Antigen description (human-readable).",
    "COVERAGE_CATEGORY": "Coverage metric category (e.g., first dose/last dose; should match COVERAGE).",
    "COVERAGE_CATEGORY_DESCRIPTION": "Description of coverage category.",
    "TARGET_NUMBER": "Target population number for the vaccination program.",
    "DOSES": "Dose indicator/number associated with the COVERAGE variable.",
    "COVERAGE": "Vaccination coverage value (percentage) for specified antigen/category.",
    "REGION": "Region grouping variable (e.g., WHO region or similar).",

    "HPV_INT_DOSES": "Number of doses in the HPV national immunization schedule.",
    "HPV_NATIONAL_SCHEDULE": "Whether HPV vaccination is included in national schedule (category/indicator).",
    "HPV_YEAR_INTRODUCTION": "Year HPV vaccine was introduced (country-level policy event; may repeat across panel rows).",
    "HPV_PRIM_DELIV_STRATEGY": "Primary delivery strategy for HPV vaccination (e.g., school-based).",
    "HPV_AGEADMINISTERED": "Age group at which HPV vaccine is administered.",
    "HPV_SEX": "Sex targeted by HPV vaccination program (e.g., female/both).",

    "cerv_can_cr_rate_2022": "Cervical cancer crude incidence rate (2022), country-level cross-sectional covariate.",
}


# -----------------------------
# Helpers
# -----------------------------
def ensure_dir(path: str) -> Path:
    out = Path(path)
    out.mkdir(parents=True, exist_ok=True)
    return out


def load_excel(path: str, sheet_name: str | None = None) -> pd.DataFrame:
    if sheet_name is None:
        return pd.read_excel(path, engine="openpyxl")
    return pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")


def missingness_table(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    rows = []
    n = len(df)
    for c in cols:
        if c not in df.columns:
            rows.append({
                "column": c,
                "present_in_file": False,
                "n_missing": np.nan,
                "pct_missing": np.nan,
                "n_rows": n
            })
            continue
        miss = df[c].isna().sum()
        rows.append({
            "column": c,
            "present_in_file": True,
            "n_missing": int(miss),
            "pct_missing": float(miss / n) if n > 0 else np.nan,
            "n_rows": n
        })
    return pd.DataFrame(rows).sort_values(["present_in_file", "pct_missing"], ascending=[False, False])


def infer_type(series: pd.Series) -> str:
    dtype = series.dtype
    if pd.api.types.is_integer_dtype(dtype):
        return "integer"
    if pd.api.types.is_float_dtype(dtype):
        return "float"
    if pd.api.types.is_bool_dtype(dtype):
        return "boolean"
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "datetime"
    return "string/object"


def top_examples(series: pd.Series, k: int = 5) -> str:
    """
    For categorical-ish columns: show top values.
    For numeric-ish columns: show min/median/max.
    """
    s = series.dropna()
    if s.empty:
        return ""

    if pd.api.types.is_numeric_dtype(s):
        return f"min={s.min():.3g}; median={s.median():.3g}; max={s.max():.3g}"

    vc = s.astype(str).value_counts().head(k)
    parts = [f"{idx} ({cnt})" for idx, cnt in vc.items()]
    return "; ".join(parts)


def make_codebook(df_raw: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """
    Codebook includes: old_name, new_name, description, dtype, n_unique, examples, missingness.
    """
    n = len(df_raw)
    rows = []

    for old in cols:
        present = old in df_raw.columns
        new = RENAME_MAP.get(old, old)
        desc = DESCRIPTION_MAP.get(old, "")

        if not present:
            rows.append({
                "old_name": old,
                "new_name": new,
                "description": desc,
                "present_in_file": False,
                "dtype_inferred": "",
                "n_unique_nonmissing": np.nan,
                "examples_or_summary": "",
                "n_missing": np.nan,
                "pct_missing": np.nan,
            })
            continue

        s = df_raw[old]
        miss = s.isna().sum()
        nunique = s.dropna().nunique()
        dtype_inf = infer_type(s)
        ex = top_examples(s)

        rows.append({
            "old_name": old,
            "new_name": new,
            "description": desc,
            "present_in_file": True,
            "dtype_inferred": dtype_inf,
            "n_unique_nonmissing": int(nunique),
            "examples_or_summary": ex,
            "n_missing": int(miss),
            "pct_missing": float(miss / n) if n > 0 else np.nan,
        })

    return pd.DataFrame(rows)


def rename_and_basic_clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply renaming and a few safe type cleanups.
    (No heavy transformations—this is mainly for documentation + consistency.)
    """
    out = df.copy()

    # Rename
    out = out.rename(columns=RENAME_MAP)

    # Normalize a few common fields if present
    if "iso3" in out.columns:
        out["iso3"] = out["iso3"].astype(str).str.strip()

    if "country" in out.columns:
        out["country"] = out["country"].astype(str).str.strip()

    if "year" in out.columns:
        out["year"] = pd.to_numeric(out["year"], errors="coerce").astype("Int64")

    if "coverage" in out.columns:
        out["coverage"] = pd.to_numeric(out["coverage"], errors="coerce")

    if "hpv_intro_year" in out.columns:
        out["hpv_intro_year"] = pd.to_numeric(out["hpv_intro_year"], errors="coerce")

    return out


# -----------------------------
# Main
# -----------------------------
def main():
    outdir = ensure_dir(OUTPUT_DIR)

    # Load
    df_raw = load_excel(INPUT_FILE, sheet_name=SHEET_NAME)
    print("\nLoaded:", INPUT_FILE)
    print("Shape:", df_raw.shape)

    # 1) Missingness check
    miss_tbl = missingness_table(df_raw, COLUMNS_TO_CHECK)
    print("\n=== Missingness (top 10 by pct_missing) ===")
    print(miss_tbl.head(10).to_string(index=False))

    # 2) Codebook (includes old->new mapping)
    codebook = make_codebook(df_raw, COLUMNS_TO_CHECK)

    # 3) Rename + basic cleaning
    df_clean = rename_and_basic_clean(df_raw)

    # Save outputs
    miss_tbl.to_csv(outdir / "missingness_report.csv", index=False)
    codebook.to_csv(outdir / "codebook.csv", index=False)

    # Also save excel version for nicer viewing
    with pd.ExcelWriter(outdir / "documentation_outputs.xlsx", engine="openpyxl") as writer:
        miss_tbl.to_excel(writer, sheet_name="missingness", index=False)
        codebook.to_excel(writer, sheet_name="codebook", index=False)

    # Save cleaned dataset
    df_clean.to_csv(outdir / "dl_pro_final_dataset_country_jan29_cleaned_renamed.csv", index=False)

    print("\nSaved:")
    print("-", (outdir / "missingness_report.csv").resolve())
    print("-", (outdir / "codebook.csv").resolve())
    print("-", (outdir / "documentation_outputs.xlsx").resolve())
    print("-", (outdir / "dl_pro_final_dataset_country_jan29_cleaned_renamed.csv").resolve())


if __name__ == "__main__":
    main()



print("\n=== Missingness by variable (country_code) ===\n")

for col in COLUMNS_TO_CHECK:
    if col not in df_raw.columns:
        print(f"{col}: NOT FOUND IN DATASET\n")
        continue

    missing_countries = (
        df_raw.loc[df_raw[col].isna(), "country_code"]
        .dropna()
        .unique()
    )

    if len(missing_countries) == 0:
        print(f"{col}: no missing values\n")
    else:
        print(f"{col}: missing for {len(missing_countries)} countries")
        print(sorted(missing_countries))
        print()
