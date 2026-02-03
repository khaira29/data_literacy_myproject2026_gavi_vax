import pandas as pd

# =============================
# INPUT / OUTPUT
# =============================
INPUT_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/02_cleaned_data/dl_project_section_1.xlsx"
OUTPUT_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/02_cleaned_data/dl_pro_final_dataset_country_analysis.xlsx"

BASE_SHEET = "gavi_mktseg_vaxprice_2024"
SHEET_VAX  = "hpv_vax_2024"

OUT_SHEET  = "country_analysis"

# =============================
# Load sheets
# =============================
base = pd.read_excel(INPUT_FILE, sheet_name=BASE_SHEET, engine="openpyxl")
vax  = pd.read_excel(INPUT_FILE, sheet_name=SHEET_VAX, engine="openpyxl")

# =============================
# Clean keys
# =============================
for df in (base, vax):
    df["country_code"] = df["country_code"].astype("string").str.strip().str.upper()

# =============================
# Duplicate checks
# =============================
def print_dups(df, label):
    d = df[df.duplicated("country_code", keep=False)]
    print(f"\n=== Duplicate country_code check: {label} ===")
    if d.empty:
        print("No duplicates ✅")
    else:
        print(f"Found {d['country_code'].nunique()} duplicated country_code(s) ❌")
        print(d.sort_values("country_code").to_string(index=False))

print_dups(base, BASE_SHEET)
print_dups(vax, SHEET_VAX)

# Enforce uniqueness
base = base.drop_duplicates("country_code", keep="first").copy()
vax  = vax.drop_duplicates("country_code", keep="first").copy()

# =============================
# 1) Start from base sheet
# =============================
df = base.copy()

# Rename country_name_inc → country_name
if "country_name_inc" not in df.columns:
    raise ValueError("Expected column 'country_name_inc' not found in base sheet.")

df = df.rename(columns={"country_name_inc": "country_name"})

# Ensure fallback name columns exist
for col in ["country_name", "country_name_vax", "country_name_gavi"]:
    if col not in df.columns:
        df[col] = pd.NA

# Clean strings
for col in ["country_name", "country_name_vax", "country_name_gavi"]:
    df[col] = df[col].astype("string").str.strip()

# Fill country_name: inc → vax → gavi
df["country_name"] = df["country_name"].fillna(df["country_name_vax"])
df["country_name"] = df["country_name"].fillna(df["country_name_gavi"])

# Drop extra name columns
df = df.drop(columns=["country_name_vax", "country_name_gavi"], errors="ignore")

# =============================
# 2) Add first_d_cov & last_d_cov from hpv_vax_2024
# =============================
needed_cols = ["country_code", "first_d_cov", "last_d_cov"]
missing = [c for c in needed_cols if c not in vax.columns]
if missing:
    raise ValueError(f"Missing columns in {SHEET_VAX}: {missing}")

vax_add = vax[needed_cols].copy()
df = df.merge(vax_add, on="country_code", how="left")

# =============================
# 3) Sort by market segment + country_code
# =============================
segment_col = "vax_market_segment"
if segment_col not in df.columns:
    raise ValueError("Column 'vax_market_segment' not found for sorting.")

df = df.sort_values(
    by=[segment_col, "country_code"],
    kind="mergesort"
).reset_index(drop=True)

# =============================
# 4) Write new Excel file
# =============================
with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name=OUT_SHEET, index=False)

print(f"\n✅ Saved new file: {OUTPUT_FILE}")
print(f"✅ Sheet created: {OUT_SHEET}")
print("Rows:", len(df))
