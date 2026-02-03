import pandas as pd

# --------------------------------------------------
# Paths
# --------------------------------------------------
IN_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/01_interm_data/final_combined_part1_country.xlsx"
OUT_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/01_interm_data/final_combined_part1_country_with_segment.xlsx"

# --------------------------------------------------
# Load
# --------------------------------------------------
df = pd.read_excel(IN_FILE, engine="openpyxl")

# --------------------------------------------------
# Required columns
# --------------------------------------------------
required = ["country_code", "year", "gavi_spec", "income_class"]
missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"Missing required columns in combined file: {missing}")

# Make year numeric
df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def norm(x):
    if pd.isna(x):
        return ""
    return str(x).strip().casefold()

# Gavi statuses (from eligibility data) that imply "in Gavi support/transition"
IN_GAVI_KEYWORDS = [
    "poorest",
    "low income",
    "fragile",
    "intermediate",
    "least poor",
    "initial self-financing",
    "preparatory transition",
    "accelerated transition",
    "graduating",
]

# Status that implies transitioned out (former)
FORMER_GAVI_KEYWORDS = [
    "fully self-financing",
]

def assign_market_segment(row) -> str:
    gavi_val = norm(row.get("gavi_spec"))
    inc = row.get("income_class")
    inc = str(inc).strip().upper() if pd.notna(inc) else ""

    # 1) Use gavi_spec when available (country-year specific)
    if gavi_val:
        if any(k in gavi_val for k in FORMER_GAVI_KEYWORDS):
            return "gavi731"
        if any(k in gavi_val for k in IN_GAVI_KEYWORDS):
            return "Gavi73"
        # If it has some gavi label but doesn't match our keyword list,
        # still treat as "in Gavi list" rather than "not in gavi"
        return "Gavi73"

    # 2) If no gavi_spec: treat as NOT in gavi (fallback to income_class)
    if inc == "H":
        return "HIC"
    elif inc in {"LM", "UM"}:
        return "MICs7"
    else:
        return "NC"

# --------------------------------------------------
# Assign segment
# --------------------------------------------------
df["market_segment"] = df.apply(assign_market_segment, axis=1)

# --------------------------------------------------
# Quick checks
# --------------------------------------------------
print("Market segment counts:\n", df["market_segment"].value_counts(dropna=False))

# Check balanced panel (2008–2025 = 18 rows per country_code)
YEAR_MIN, YEAR_MAX = 2008, 2025
expected_n = YEAR_MAX - YEAR_MIN + 1

counts = df.groupby("country_code")["year"].nunique()
bad = counts[counts != expected_n]

print("\nExpected years per country:", expected_n)
print("Countries not balanced (should be empty):", len(bad))
if len(bad) > 0:
    print(bad.head(20).to_string())

# --------------------------------------------------
# Save
# --------------------------------------------------
df.to_excel(OUT_FILE, index=False)
print("\nSaved:", OUT_FILE)
print("Final shape:", df.shape)
