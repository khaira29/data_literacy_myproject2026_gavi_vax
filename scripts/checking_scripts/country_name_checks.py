import pandas as pd

INPUT_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/02_cleaned_data/dl_project_section_1.xlsx"
OUTPUT_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/02_cleaned_data/dl_project_section_1_country_code_compare.xlsx"

SHEET_VAX  = "hpv_vax_2024"
SHEET_INC  = "income_class_2024"
SHEET_GAVI = "gavi_country_2024"   # has country_code, country_name, gavi_2024

# -----------------------------
# Load minimal columns (NOW include country_name for vax/inc too)
# -----------------------------
vax = pd.read_excel(INPUT_FILE, sheet_name=SHEET_VAX, engine="openpyxl")[["country_code", "country_name"]].copy()
inc = pd.read_excel(INPUT_FILE, sheet_name=SHEET_INC, engine="openpyxl")[["country_code", "country_name"]].copy()
gavi = pd.read_excel(INPUT_FILE, sheet_name=SHEET_GAVI, engine="openpyxl")[["country_code", "country_name"]].copy()

# -----------------------------
# Clean country_code format
# -----------------------------
def clean_code(s):
    return s.astype("string").str.strip().str.upper()

for df_ in (vax, inc, gavi):
    df_["country_code"] = clean_code(df_["country_code"])
    df_["country_name"] = df_["country_name"].astype("string").str.strip()

# -----------------------------
# Duplicate checks (pre-merge)
# -----------------------------
def dup_check(df, label):
    dup = df[df.duplicated(subset=["country_code"], keep=False)]
    print(f"\n=== Duplicate country_code check: {label} ===")
    if dup.empty:
        print("No duplicates ✅")
    else:
        print(f"Found {dup['country_code'].nunique()} duplicated code(s) ❌")
        print(dup.sort_values("country_code").to_string(index=False))

dup_check(vax, "hpv_vax_2024")
dup_check(inc, "income_class_2024")
dup_check(gavi, "gavi_country_2024")

# Enforce one row per code (keep first)
vax = vax.dropna(subset=["country_code"]).drop_duplicates(subset=["country_code"], keep="first")
inc = inc.dropna(subset=["country_code"]).drop_duplicates(subset=["country_code"], keep="first")
gavi = gavi.dropna(subset=["country_code"]).drop_duplicates(subset=["country_code"], keep="first")

# Rename name columns before merge
vax = vax.rename(columns={"country_name": "country_name_vax"})
inc = inc.rename(columns={"country_name": "country_name_inc"})
gavi = gavi.rename(columns={"country_name": "country_name_gavi"})

# -----------------------------
# Compare codes: outer merge on country_code only
# -----------------------------
combo = inc.merge(vax, on="country_code", how="outer", indicator=False)
combo = combo.merge(
    gavi[["country_code", "country_name_gavi"]],
    on="country_code",
    how="left"
)

# Presence flags
combo["in_income"] = combo["country_name_inc"].notna()
combo["in_vax"] = combo["country_name_vax"].notna()
combo["in_gavi"] = combo["country_name_gavi"].notna()

# -----------------------------
# Duplicate check (post-merge)
# -----------------------------
dup_out = combo[combo.duplicated(subset=["country_code"], keep=False)]
print("\n=== Duplicate country_code check: merged output ===")
if dup_out.empty:
    print("No duplicates after merge ✅")
else:
    print("❌ Duplicate country_code found after merge!")
    print(dup_out.sort_values("country_code").to_string(index=False))

combo = combo.sort_values("country_code").reset_index(drop=True)

# -----------------------------
# Summary
# -----------------------------
print("\n=== Summary: country_code comparison ===")
print("Total unique country_code (union):", len(combo))
print("Only in income:", int((combo["in_income"] & ~combo["in_vax"]).sum()))
print("Only in vax:", int((combo["in_vax"] & ~combo["in_income"]).sum()))
print("In both income & vax:", int((combo["in_income"] & combo["in_vax"]).sum()))
print("Codes with Gavi info attached:", int(combo["in_gavi"].sum()))

# Optional: list codes missing in income or vax
missing_in_income = combo.loc[~combo["in_income"], ["country_code", "country_name_vax"]]
missing_in_vax = combo.loc[~combo["in_vax"], ["country_code", "country_name_inc"]]

if not missing_in_income.empty:
    print("\n--- country_code present in vax but missing in income ---")
    print(missing_in_income.sort_values("country_code").to_string(index=False))

if not missing_in_vax.empty:
    print("\n--- country_code present in income but missing in vax ---")
    print(missing_in_vax.sort_values("country_code").to_string(index=False))

# -----------------------------
# Save output
# -----------------------------
with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    combo.to_excel(writer, sheet_name="country_code_compare", index=False)

print("\n✅ Saved:", OUTPUT_FILE)

# ------------------------------------------------------------
# Detailed country_code set comparisons
# ------------------------------------------------------------
set_vax = set(vax["country_code"])
set_inc = set(inc["country_code"])
set_gavi = set(gavi["country_code"])

print("\n=== Detailed country_code presence checks ===")

print("\nGAVI but NOT in VAX:")
only_gavi_not_vax = sorted(set_gavi - set_vax)
if only_gavi_not_vax:
    print(f"Count: {len(only_gavi_not_vax)}")
    print(only_gavi_not_vax)
else:
    print("None ✅")

print("\nGAVI but NOT in INCOME:")
only_gavi_not_inc = sorted(set_gavi - set_inc)
if only_gavi_not_inc:
    print(f"Count: {len(only_gavi_not_inc)}")
    print(only_gavi_not_inc)
else:
    print("None ✅")

print("\nVAX but NOT in GAVI:")
only_vax_not_gavi = sorted(set_vax - set_gavi)
if only_vax_not_gavi:
    print(f"Count: {len(only_vax_not_gavi)}")
    print(only_vax_not_gavi)
else:
    print("None ✅")

print("\nINCOME but NOT in GAVI:")
only_inc_not_gavi = sorted(set_inc - set_gavi)
if only_inc_not_gavi:
    print(f"Count: {len(only_inc_not_gavi)}")
    print(only_inc_not_gavi)
else:
    print("None ✅")
