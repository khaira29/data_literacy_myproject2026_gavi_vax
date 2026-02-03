import pandas as pd

FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/02_cleaned_data/dl_project_section_1.xlsx"

SHEET_A = "hpv_vax_2024"
SHEET_B = "income_class_2024"

# -----------------------------
# Load sheets
# -----------------------------
df_a = pd.read_excel(FILE, sheet_name=SHEET_A, engine="openpyxl")
df_b = pd.read_excel(FILE, sheet_name=SHEET_B, engine="openpyxl")

# Keep only relevant columns and clean
def clean_df(df):
    return (
        df[["country_code", "country_name"]]
        .astype("string")
        .apply(lambda col: col.str.strip())
        .dropna()
        .drop_duplicates()
        .reset_index(drop=True)
    )

df_a = clean_df(df_a)
df_b = clean_df(df_b)

# -----------------------------
# 1. Check country_code sets
# -----------------------------
codes_a = set(df_a["country_code"])
codes_b = set(df_b["country_code"])

print("\n=== COUNTRY CODE CHECK ===")
print("Only in hpv_vax_2024:", sorted(codes_a - codes_b))
print("Only in income_class_2024:", sorted(codes_b - codes_a))

# -----------------------------
# 2. Check country_name sets
# -----------------------------
names_a = set(df_a["country_name"])
names_b = set(df_b["country_name"])

print("\n=== COUNTRY NAME CHECK ===")
print("Only in hpv_vax_2024:", sorted(names_a - names_b))
print("Only in income_class_2024:", sorted(names_b - names_a))

# -----------------------------
# 3. Check code–name mapping consistency
# -----------------------------
merged = df_a.merge(
    df_b,
    on="country_code",
    how="inner",
    suffixes=("_hpv", "_income")
)

mismatch = merged[merged["country_name_hpv"] != merged["country_name_income"]]

print("\n=== COUNTRY CODE → NAME MISMATCHES ===")
if mismatch.empty:
    print("Perfect match ✅ No mismatches found.")
else:
    print(f"Found {len(mismatch)} mismatches ❌")
    print(
        mismatch[
            ["country_code", "country_name_hpv", "country_name_income"]
        ]
        .sort_values("country_code")
        .to_string(index=False)
    )

# -----------------------------
# 4. Final verdict
# -----------------------------
if (
    not (codes_a - codes_b)
    and not (codes_b - codes_a)
    and mismatch.empty
):
    print("\n🎉 FINAL RESULT: Sheets match perfectly (codes + names).")
else:
    print("\n⚠️ FINAL RESULT: Differences detected. See details above.")
