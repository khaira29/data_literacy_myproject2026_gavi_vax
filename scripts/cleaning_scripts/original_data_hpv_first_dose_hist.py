import pandas as pd

# --------------------------------------------------
# Paths
# --------------------------------------------------
INPUT_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/01_interm_data/coverage_cleaned.xlsx"
OUTPUT_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/01_interm_data/final_data_hpv_first_dose_hist.xlsx"

# --------------------------------------------------
# Load
# --------------------------------------------------
df = pd.read_excel(INPUT_FILE, engine="openpyxl")

# --------------------------------------------------
# Required columns check
# --------------------------------------------------
required = ["CODE", "YEAR", "COVERAGE", "ANTIGEN"]
missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"Missing required columns: {missing}")

# --------------------------------------------------
# Keep + rename columns
# --------------------------------------------------
df_out = (
    df[required]
    .rename(columns={
        "CODE": "country_code",
        "YEAR": "year",
        "COVERAGE": "ori_dat_cov",
        "ANTIGEN": "ori_dat_antigen",
    })
)

# --------------------------------------------------
# Clean types
# --------------------------------------------------
df_out["country_code"] = df_out["country_code"].astype(str).str.strip()
df_out["year"] = pd.to_numeric(df_out["year"], errors="coerce").astype("Int64")
df_out["ori_dat_antigen"] = df_out["ori_dat_antigen"].astype(str).str.strip()

# --------------------------------------------------
# DUPLICATE CHECKS
# --------------------------------------------------
# 1) Multiple rows per country-year (often due to multiple antigens)
dups_cy = df_out.duplicated(subset=["country_code", "year"]).sum()
print("Duplicates on (country_code, year):", dups_cy)

if dups_cy > 0:
    print("\n=== Example duplicates on (country_code, year) (up to 50 rows) ===")
    dup_rows = df_out[df_out.duplicated(subset=["country_code", "year"], keep=False)] \
        .sort_values(["country_code", "year", "ori_dat_antigen"])
    print(dup_rows.head(50).to_string(index=False))

# 2) Duplicate within same antigen for the same country-year (more serious)
dups_cya = df_out.duplicated(subset=["country_code", "year", "ori_dat_antigen"]).sum()
print("\nDuplicates on (country_code, year, ori_dat_antigen):", dups_cya)

if dups_cya > 0:
    print("\n=== Example duplicates on (country_code, year, ori_dat_antigen) (up to 50 rows) ===")
    dup_rows2 = df_out[df_out.duplicated(subset=["country_code", "year", "ori_dat_antigen"], keep=False)] \
        .sort_values(["country_code", "year", "ori_dat_antigen"])
    print(dup_rows2.head(50).to_string(index=False))

# Quick summary: how many antigens per country-year?
antigens_per_cy = df_out.groupby(["country_code", "year"])["ori_dat_antigen"].nunique(dropna=True)
print("\nAntigens per (country_code, year) summary:")
print(antigens_per_cy.describe())

# --------------------------------------------------
# Save
# --------------------------------------------------
df_out.to_excel(OUTPUT_FILE, index=False)
print("\nSaved cleaned coverage file to:", OUTPUT_FILE)
print("Columns:", df_out.columns.tolist())
print("Rows:", len(df_out))
