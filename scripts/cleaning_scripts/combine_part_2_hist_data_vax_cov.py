#this version is just to compare between the coverage_cleaned and the original data downloaded from WHO website

import pandas as pd

# --------------------------------------------------
# Paths
# --------------------------------------------------
PANEL_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/01_interm_data/final_combined_part1_country_with_segment.xlsx"
COV_FILE   = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/01_interm_data/coverage_cleaned.xlsx"
HPV_FILE   = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/01_interm_data/final_data_hpv_first_dose_hist.xlsx"

OUT_FILE   = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/01_interm_data/final_combined_part2_country.xlsx"

# --------------------------------------------------
# Load
# --------------------------------------------------
panel = pd.read_excel(PANEL_FILE, engine="openpyxl")
cov   = pd.read_excel(COV_FILE, engine="openpyxl")
hpv   = pd.read_excel(HPV_FILE, engine="openpyxl")

# --------------------------------------------------
# Required columns
# --------------------------------------------------
req_panel = ["country_code", "year"]
req_cov   = ["CODE", "YEAR"]
req_hpv   = ["country_code", "year"]  

for name, df, req in [
    ("PANEL", panel, req_panel),
    ("COVERAGE", cov, req_cov),
    ("HPV", hpv, req_hpv),
]:
    missing = [c for c in req if c not in df.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")

# --------------------------------------------------
# Normalize merge keys
# --------------------------------------------------
panel["country_code"] = panel["country_code"].astype(str).str.strip()
panel["year"] = pd.to_numeric(panel["year"], errors="coerce").astype("Int64")

cov["CODE"] = cov["CODE"].astype(str).str.strip()
cov["YEAR"] = pd.to_numeric(cov["YEAR"], errors="coerce").astype("Int64")

hpv["country_code"] = hpv["country_code"].astype(str).str.strip()
hpv["year"] = pd.to_numeric(hpv["year"], errors="coerce").astype("Int64")

# --------------------------------------------------
# Drop rows with missing keys (cannot be merged meaningfully)
# --------------------------------------------------
panel = panel.dropna(subset=["country_code", "year"]).copy()
cov   = cov.dropna(subset=["CODE", "YEAR"]).copy()
hpv   = hpv.dropna(subset=["country_code", "year"]).copy()

# --------------------------------------------------
# Duplicates checks (avoid row explosion)
# --------------------------------------------------
panel_dups = panel.duplicated(subset=["country_code", "year"]).sum()
cov_dups   = cov.duplicated(subset=["CODE", "YEAR"]).sum()
hpv_dups   = hpv.duplicated(subset=["country_code", "year"]).sum()

print("Duplicates in PANEL (country_code, year):", panel_dups)
print("Duplicates in COVERAGE (CODE, YEAR):", cov_dups)
print("Duplicates in HPV (country_code, year):", hpv_dups)

if cov_dups > 0:
    print("WARNING: coverage has duplicate (CODE, YEAR). Keeping first.")
    cov = cov.drop_duplicates(subset=["CODE", "YEAR"], keep="first").copy()

if hpv_dups > 0:
    print("WARNING: HPV has duplicate (country_code, year). Keeping first.")
    hpv = hpv.drop_duplicates(subset=["country_code", "year"], keep="first").copy()


# =================================================
# STEP 1: OUTER merge PANEL + COVERAGE
# =================================================
merged_pc = panel.merge(
    cov,
    left_on=["country_code", "year"],
    right_on=["CODE", "YEAR"],
    how="outer",
    indicator=True
)

print("\nPANEL + COVERAGE merge diagnostics:")
print("Rows only in PANEL:", (merged_pc["_merge"] == "left_only").sum())
print("Rows only in COVERAGE:", (merged_pc["_merge"] == "right_only").sum())
print("Rows in BOTH:", (merged_pc["_merge"] == "both").sum())
print("Total rows:", len(merged_pc))

# Harmonize keys after outer merge
merged_pc["country_code"] = merged_pc["country_code"].fillna(merged_pc["CODE"])
merged_pc["year"] = merged_pc["year"].fillna(merged_pc["YEAR"])

# Drop redundant key columns + indicator
merged_pc = merged_pc.drop(columns=[c for c in ["CODE", "YEAR", "_merge"] if c in merged_pc.columns])

# =================================================
# STEP 2: OUTER merge (PANEL+COV) + HPV
# =================================================
merged_all = merged_pc.merge(
    hpv,
    on=["country_code", "year"],
    how="outer",
    indicator=True
)

print("\n(Panel+Coverage) + HPV merge diagnostics:")
print("Rows only in (Panel+Coverage):", (merged_all["_merge"] == "left_only").sum())
print("Rows only in HPV:", (merged_all["_merge"] == "right_only").sum())
print("Rows in BOTH:", (merged_all["_merge"] == "both").sum())
print("Total rows:", len(merged_all))

merged_all = merged_all.drop(columns=[c for c in ["_merge"] if c in merged_all.columns])



# --------------------------------------------------
# DROP ori_dat_* if identical to COVERAGE everywhere
# (comparison-only version vs original WHO data)
# --------------------------------------------------
cols_needed = ["ori_dat_cov", "ori_dat_antigen", "COVERAGE"]
missing_cols = [c for c in cols_needed if c not in merged_all.columns]

if not missing_cols:
    # Compare only rows where both values are non-missing
    compare_mask = (
        merged_all["ori_dat_cov"].notna()
        & merged_all["COVERAGE"].notna()
    )

    identical = (
        merged_all.loc[compare_mask, "ori_dat_cov"]
        .astype(str)
        .eq(merged_all.loc[compare_mask, "COVERAGE"].astype(str))
        .all()
    )

    print("\nori_dat_cov identical to COVERAGE for all comparable rows:", identical)

    if identical:
        merged_all = merged_all.drop(columns=["ori_dat_cov", "ori_dat_antigen"])
        print("Dropped columns: ori_dat_cov, ori_dat_antigen")
    else:
        print("Keeping ori_dat_cov / ori_dat_antigen (differences detected).")
else:
    print("Skipping ori_dat_* comparison; missing columns:", missing_cols)

# --------------------------------------------------
# Drop unnecessary columns and reorder
# --------------------------------------------------
# Drop GROUP and NAME if present
merged_all = merged_all.drop(
    columns=[c for c in ["GROUP", "NAME"] if c in merged_all.columns],
    errors="ignore"
)

# Move country_name right after country_code
cols = merged_all.columns.tolist()
if "country_code" in cols and "country_name" in cols:
    cols.remove("country_name")
    cols.insert(cols.index("country_code") + 1, "country_name")
    merged_all = merged_all[cols]



# --------------------------------------------------
# Optional: sort nicely
# --------------------------------------------------
merged_all = merged_all.sort_values(["country_code", "year"]).reset_index(drop=True)

# --------------------------------------------------
# Save
# --------------------------------------------------
merged_all.to_excel(OUT_FILE, index=False)
print("\nSaved merged dataset:", OUT_FILE)
print("Final shape:", merged_all.shape)


