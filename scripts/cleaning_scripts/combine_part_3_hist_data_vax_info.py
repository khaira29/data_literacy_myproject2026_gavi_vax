import pandas as pd

# --------------------------------------------------
# Paths
# --------------------------------------------------
MAIN_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/01_interm_data/final_combined_part2_country.xlsx"
META_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/01_interm_data/vax_metadata.xlsx" ##data since 2000

OUT_FILE  = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/02_cleaned_data/final_dataset_country_year.xlsx"

# --------------------------------------------------
# Load
# --------------------------------------------------
main = pd.read_excel(MAIN_FILE, engine="openpyxl")
meta = pd.read_excel(META_FILE, engine="openpyxl")

# --------------------------------------------------
# Required columns
# --------------------------------------------------
if "country_code" not in main.columns:
    raise ValueError("MAIN file missing required column: country_code")
if "ISO_3_CODE" not in meta.columns:
    raise ValueError("META file missing required column: ISO_3_CODE")
if "year" not in main.columns:
    raise ValueError("MAIN file missing required column: year")

# --------------------------------------------------
# Standardize country code in metadata
# --------------------------------------------------
meta = meta.rename(columns={"ISO_3_CODE": "country_code"})

# --------------------------------------------------
# Clean keys
# --------------------------------------------------
main["country_code"] = main["country_code"].astype(str).str.strip()
meta["country_code"] = meta["country_code"].astype(str).str.strip()
main["year"] = pd.to_numeric(main["year"], errors="coerce").astype("Int64")

# --------------------------------------------------
# Keep only requested metadata columns (plus key)
# --------------------------------------------------
keep_meta_cols = [
    "country_code",
    "HPV_NATIONAL_SCHEDULE",
    "HPV_YEAR_INTRODUCTION",
    "HPV_PRIM_DELIV_STRATEGY",
    "HPV_AGEADMINISTERED",
    "HPV_SEX",
]

missing_meta = [c for c in keep_meta_cols if c not in meta.columns]
if missing_meta:
    raise ValueError(f"META file missing required columns: {missing_meta}")

meta_small = meta[keep_meta_cols].copy()

# --------------------------------------------------
# Check duplicates in metadata (should be 1 row per country)
# --------------------------------------------------
dup_meta = meta_small.duplicated(subset=["country_code"]).sum()
print("Duplicates in META (country_code):", dup_meta)

if dup_meta > 0:
    print("\nWARNING: META has duplicate country_code. Showing examples (up to 30):")
    dups = meta_small[meta_small.duplicated(subset=["country_code"], keep=False)] \
        .sort_values(["country_code"])
    print(dups.head(30).to_string(index=False))

    # keep first to avoid row explosion
    meta_small = meta_small.drop_duplicates(subset=["country_code"], keep="first").copy()
    print("Keeping first occurrence per country_code in META.")

# --------------------------------------------------
# Merge (left join keeps all country–year rows)
# --------------------------------------------------
merged = main.merge(meta_small, on="country_code", how="left", indicator=True)

print("\nMerge diagnostics:")
print("Rows in MAIN:", len(main))
print("Rows after merge:", len(merged))
print("Rows with metadata:", (merged["_merge"] == "both").sum())
print("Rows without metadata:", (merged["_merge"] == "left_only").sum())

merged = merged.drop(columns=["_merge"])

# --------------------------------------------------
# Ensure metadata is constant within country across years
# --------------------------------------------------
meta_cols = keep_meta_cols[1:]  # exclude country_code

bad_const = []
for c in meta_cols:
    nunq = merged.groupby("country_code")[c].nunique(dropna=True)
    bad = nunq[nunq > 1]
    if len(bad) > 0:
        bad_const.append((c, bad))

if bad_const:
    print("\nWARNING: Some metadata columns vary within country across years.")
    for c, bad in bad_const:
        print(f"\nColumn: {c} | Countries with >1 unique value: {len(bad)}")
        print(bad.head(20).to_string())

# --------------------------------------------------
# Check each country has at least 15 year-rows
# --------------------------------------------------
counts = merged.groupby("country_code")["year"].nunique()
bad_years = counts[counts < 15]

print("\nCountries with < 15 year-rows:", len(bad_years))
if len(bad_years) > 0:
    print(bad_years.sort_values().head(30).to_string())

# Optional: sort
merged = merged.sort_values(["country_code", "year"]).reset_index(drop=True)

# --------------------------------------------------
# Save
# --------------------------------------------------
merged.to_excel(OUT_FILE, index=False)
print("\nSaved final dataset:", OUT_FILE)
print("Final shape:", merged.shape)
