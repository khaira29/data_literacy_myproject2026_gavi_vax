import pandas as pd
import re

# --------------------------------------------------
# File paths
# --------------------------------------------------
TARGET_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/01_interm_data/gavi_eligibility_country_wide.xlsx"
REF_FILE    = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/02_cleaned_data/dl_project_section_1.xlsx"
REF_SHEET   = "gavi_country_2024"

OUTPUT_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/01_interm_data/final_gavi_historical_data.xlsx"

# --------------------------------------------------
# Load data
# --------------------------------------------------
target = pd.read_excel(TARGET_FILE, engine="openpyxl")
ref = pd.read_excel(REF_FILE, sheet_name=REF_SHEET, engine="openpyxl")[["country_name", "country_code"]]

# --------------------------------------------------
# Clean join keys
# --------------------------------------------------
target["country_name_clean"] = target["country_name"].astype(str).str.strip().str.lower()
ref["country_name_clean"]    = ref["country_name"].astype(str).str.strip().str.lower()

# --------------------------------------------------
# Merge country_code
# --------------------------------------------------
merged = target.merge(
    ref[["country_name_clean", "country_code"]],
    on="country_name_clean",
    how="left"
).drop(columns=["country_name_clean"])

# --------------------------------------------------
# Sanity checks (merge)
# --------------------------------------------------
print("Rows in target:", target.shape[0])
print("Rows after merge:", merged.shape[0])
print("Missing country_code:", merged["country_code"].isna().sum())

unmatched = merged.loc[merged["country_code"].isna(), "country_name"].dropna().unique()
print("\nUnmatched country names:")
print(unmatched)

# --------------------------------------------------
# Wide -> Long: gavi_2008 ... gavi_2025
# --------------------------------------------------
gavi_cols = [c for c in merged.columns if re.fullmatch(r"gavi_(200[8-9]|201\d|202[0-5])", str(c))]
if not gavi_cols:
    raise ValueError("No columns found matching gavi_2008 ... gavi_2025. Check your column names.")

# keep id columns (add more if you want)
id_cols = [c for c in ["country_code", "country_name"] if c in merged.columns]
if "country_code" not in id_cols:
    raise ValueError("country_code column not found after merge.")

long_df = merged.melt(
    id_vars=id_cols,
    value_vars=gavi_cols,
    var_name="gavi_year_col",
    value_name="gavi_spec"
)

long_df["year"] = long_df["gavi_year_col"].str.replace("gavi_", "", regex=False).astype(int)
long_df = long_df.drop(columns=["gavi_year_col"])

# Optional: sort nicely
long_df = long_df.sort_values(["country_code", "year"]).reset_index(drop=True)

# --------------------------------------------------
# Sanity checks (reshape)
# --------------------------------------------------
print("\nWide shape:", merged.shape)
print("Long shape:", long_df.shape)
print("Year range:", long_df["year"].min(), "-", long_df["year"].max())
print("Missing gavi_spec:", long_df["gavi_spec"].isna().sum())

# --------------------------------------------------
# Save ONE final output (long format)
# --------------------------------------------------
long_df.to_excel(OUTPUT_FILE, index=False)
print("\nSaved final long dataset to:", OUTPUT_FILE)
