import pandas as pd

# --------------------------------------------------
# Paths
# --------------------------------------------------
GAVI_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/01_interm_data/final_gavi_historical_data.xlsx"
INCOME_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/01_interm_data/final_wb_hist_income.xlsx"

OUT_FILE  = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/01_interm_data/final_combined_part1_country.xlsx"

# --------------------------------------------------
# Load
# --------------------------------------------------
gavi = pd.read_excel(GAVI_FILE, engine="openpyxl")
income = pd.read_excel(INCOME_FILE, engine="openpyxl")

# --------------------------------------------------
# Required columns
# --------------------------------------------------
required = ["country_code", "year"]
for df, name in [(gavi, "GAVI"), (income, "INCOME")]:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{name} file missing required columns: {missing}")

# Make year comparable
gavi["year"] = pd.to_numeric(gavi["year"], errors="coerce").astype("Int64")
income["year"] = pd.to_numeric(income["year"], errors="coerce").astype("Int64")

# --------------------------------------------------
# Rename country_name columns to avoid collisions
# --------------------------------------------------
if "country_name" in gavi.columns:
    gavi = gavi.rename(columns={"country_name": "country_name_gavi"})
if "country_name" in income.columns:
    income = income.rename(columns={"country_name": "country_name_income"})
else:
    raise ValueError("INCOME file must contain country_name.")

# --------------------------------------------------
# Check duplicates on merge keys
# --------------------------------------------------
gavi_dups = gavi.duplicated(subset=["country_code", "year"]).sum()
income_dups = income.duplicated(subset=["country_code", "year"]).sum()
print("Duplicate (country_code, year) in GAVI:", gavi_dups)
print("Duplicate (country_code, year) in INCOME:", income_dups)

# Optional: fail fast if duplicates exist (recommended)
if gavi_dups > 0 or income_dups > 0:
    print("\nWARNING: Duplicates detected on (country_code, year).")
    print("You should fix duplicates before merging to avoid inflating rows.\n")

# --------------------------------------------------
# OUTER merge: keep rows that exist only in GAVI or only in INCOME
# --------------------------------------------------
merged = income.merge(
    gavi,
    on=["country_code", "year"],
    how="outer",
    indicator=True
)

print("\nRows in INCOME:", len(income))
print("Rows in GAVI:", len(gavi))
print("Rows after OUTER merge:", len(merged))
print("Matched rows (both):", (merged["_merge"] == "both").sum())
print("Only in INCOME:", (merged["_merge"] == "left_only").sum())
print("Only in GAVI:", (merged["_merge"] == "right_only").sum())

# --------------------------------------------------
# Country name rule:
# prefer INCOME name; if missing, use GAVI name
# --------------------------------------------------
merged["country_name"] = merged["country_name_income"]
if "country_name_gavi" in merged.columns:
    merged["country_name"] = merged["country_name"].fillna(merged["country_name_gavi"])

# --------------------------------------------------
# BALANCE THE PANEL: ensure each country_code has years 2008–2025
# --------------------------------------------------
YEAR_MIN, YEAR_MAX = 2008, 2025
all_years = list(range(YEAR_MIN, YEAR_MAX + 1))

# all country codes appearing in either file (after merge)
all_codes = merged["country_code"].dropna().unique()

full_index = pd.MultiIndex.from_product(
    [all_codes, all_years],
    names=["country_code", "year"]
)

merged_balanced = (
    merged
    .set_index(["country_code", "year"])
    .reindex(full_index)
    .reset_index()
)

# Re-attach country_name for newly created rows:
# (take first non-missing name per country_code)
name_map = (
    merged[["country_code", "country_name"]]
    .dropna()
    .drop_duplicates(subset=["country_code"])
    .set_index("country_code")["country_name"]
)

merged_balanced["country_name"] = merged_balanced["country_name"].fillna(
    merged_balanced["country_code"].map(name_map)
)

# --------------------------------------------------
# Clean up helper columns
# (note: _merge will be NaN for newly created balanced rows)
# --------------------------------------------------
drop_cols = ["country_name_income", "country_name_gavi", "_merge"]
merged_balanced = merged_balanced.drop(columns=[c for c in drop_cols if c in merged_balanced.columns])

# --------------------------------------------------
# Final checks: each country_code should have 18 rows (2008–2025 inclusive)
# --------------------------------------------------
expected_n = YEAR_MAX - YEAR_MIN + 1  # 18
counts = merged_balanced.groupby("country_code")["year"].nunique()
bad = counts[counts != expected_n]

print("\nExpected years per country:", expected_n)
print("Countries not balanced (should be empty):", len(bad))
if len(bad) > 0:
    print(bad.head(20).to_string())

# Optional: sort nicely
merged_balanced = merged_balanced.sort_values(["country_code", "year"]).reset_index(drop=True)

# --------------------------------------------------
# ADD gavi_supported column (based on gavi_spec)
# --------------------------------------------------
if "gavi_spec" not in merged_balanced.columns:
    raise ValueError("Column 'gavi_spec' not found. Cannot create gavi_supported.")

gavi_nonblank = (
    merged_balanced["gavi_spec"].notna()
    & (merged_balanced["gavi_spec"].astype(str).str.strip() != "")
)

merged_balanced["gavi_supported"] = gavi_nonblank.map(
    {True: "supported by gavi", False: "not supported by gavi"}
)

# --------------------------------------------------
# Save
# --------------------------------------------------
merged_balanced.to_excel(OUT_FILE, index=False)
print("\nSaved merged + balanced panel file:", OUT_FILE)
print("Final shape:", merged_balanced.shape)