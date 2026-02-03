import pandas as pd

INPUT_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/02_cleaned_data/dl_project_section_1.xlsx"
NEW_SHEET  = "gavi_mktseg_vaxprice_2024"

SHEET_VAX  = "hpv_vax_2024"
SHEET_INC  = "income_class_2024"
SHEET_GAVI = "gavi_country_2024"   # must have country_code, country_name, gavi_2024

# -----------------------------
# Reference lists
# -----------------------------
MICs4 = [
    "Botswana", "Maldives", "Morocco", "Seychelles", "Turkmenistan"
]

MICs5 = [
    "Egypt", "Algeria", "Venezuela", "Jordan", "Tunisia", "El Salvador",
    "Lebanon", "Eswatini", "Fiji", "Cape Verde", "Dominica", "Belize",
    "Vanuatu", "Maldives", "Samoa", "Tonga", "Saint Lucia",
    "Saint Vincent and the Grenadines", "Grenada", "Kosovo",
    "Tuvalu", "Micronesia"
]

MICs6 = [
    "Iraq", "Namibia", "Libya", "Serbia", "Bulgaria", "Costa Rica",
    "Botswana", "Jamaica", "Gabon", "Equatorial Guinea",
    "Northern Macedonia", "Mauritius", "Suriname", "Montenegro",
    "Palau", "Marshall Islands", "Georgia"
]

# -----------------------------
# PRICE RULES (updated)
# - No price for HIC and NC
# - MICs7 has price 23.375
# -----------------------------
PRICE_BY_SEGMENT = {
    "Gavi73": 2.9,
    "gavi731": 2.9,
    "MICs5": 2.9,
    "MICs6": 4.5,
    "MICs4": 20.125,
    "MICs7": 23.375,
    "HIC": 31,
    # "NC": no price
}

# -----------------------------
# Helpers
# -----------------------------
def norm_name(x) -> str:
    """Normalize country names for matching (lowercase, stripped)."""
    if pd.isna(x):
        return ""
    return str(x).strip().casefold()

ALIASES = {
    norm_name("North Macedonia"): norm_name("Northern Macedonia"),
    norm_name("Cabo Verde"): norm_name("Cape Verde"),
    norm_name("Micronesia (Federated States of)"): norm_name("Micronesia"),
}

def apply_alias(n: str) -> str:
    return ALIASES.get(n, n)

def make_name_set(*cols) -> set:
    s = set()
    for c in cols:
        # IMPORTANT FIX: don't use `if c:` with pd.NA
        if pd.notna(c):
            txt = str(c).strip()
            if txt != "":
                n = apply_alias(norm_name(txt))
                if n:
                    s.add(n)
    return s


def prep_country_names(df: pd.DataFrame, name_col_new: str, sheet_label: str) -> pd.DataFrame:
    """Keep country_code + country_name, clean, and check duplicates."""
    out = df[["country_code", "country_name"]].copy()
    out["country_code"] = out["country_code"].astype("string").str.strip().str.upper()
    out["country_name"] = out["country_name"].astype("string").str.strip()

    # Duplicate check
    dup = out[out.duplicated(subset=["country_code"], keep=False)]
    print(f"\n=== Duplicate country_code check: {sheet_label} ===")
    if dup.empty:
        print("No duplicates ✅")
    else:
        print(f"Found {dup['country_code'].nunique()} duplicated country_code(s) ❌")
        print(dup.sort_values("country_code").to_string(index=False))

    out = out.dropna(subset=["country_code"])
    out = out.drop_duplicates(subset=["country_code"], keep="first")
    out = out.rename(columns={"country_name": name_col_new})
    return out


def prep_income_with_class(df: pd.DataFrame, sheet_label: str) -> pd.DataFrame:
    """
    For income_class_2024 sheet: keep country_code, country_name_inc, and income_class.
    Tries to find the income class column robustly.
    """
    cols = list(df.columns)

    # try exact-ish names first
    possible = [c for c in cols if str(c).strip().casefold() in {"income_class", "income_class_2024"}]

    # fallback: any col containing both 'income' and 'class'
    if not possible:
        possible = [c for c in cols if ("income" in str(c).casefold() and "class" in str(c).casefold())]

    if not possible:
        raise ValueError(
            f"Couldn't find an income class column in {sheet_label}. "
            f"Available columns: {cols}"
        )

    income_col = possible[0]

    out = df[["country_code", "country_name", income_col]].copy()
    out["country_code"] = out["country_code"].astype("string").str.strip().str.upper()
    out["country_name"] = out["country_name"].astype("string").str.strip()
    out[income_col] = out[income_col].astype("string").str.strip().str.upper()

    # Duplicate check
    dup = out[out.duplicated(subset=["country_code"], keep=False)]
    print(f"\n=== Duplicate country_code check: {sheet_label} ===")
    if dup.empty:
        print("No duplicates ✅")
    else:
        print(f"Found {dup['country_code'].nunique()} duplicated country_code(s) ❌")
        print(dup.sort_values("country_code").to_string(index=False))

    out = out.dropna(subset=["country_code"])
    out = out.drop_duplicates(subset=["country_code"], keep="first")
    out = out.rename(columns={"country_name": "country_name_inc", income_col: "income_class"})
    return out


# -----------------------------
# Load sheets
# -----------------------------
vax  = pd.read_excel(INPUT_FILE, sheet_name=SHEET_VAX, engine="openpyxl")
inc  = pd.read_excel(INPUT_FILE, sheet_name=SHEET_INC, engine="openpyxl")
gavi = pd.read_excel(INPUT_FILE, sheet_name=SHEET_GAVI, engine="openpyxl")[["country_code", "country_name", "gavi_2024"]].copy()

# Prepare
vax2 = prep_country_names(vax, "country_name_vax", SHEET_VAX)
inc2 = prep_income_with_class(inc, SHEET_INC)   # <-- now includes income_class

gavi["country_code"] = gavi["country_code"].astype("string").str.strip().str.upper()
gavi["country_name"] = gavi["country_name"].astype("string").str.strip()
gavi = gavi.dropna(subset=["country_code"]).drop_duplicates(subset=["country_code"], keep="first")
gavi = gavi.rename(columns={"country_name": "country_name_gavi"})

# -----------------------------
# Combine into one table (outer join on country_code)
# -----------------------------
combo = (
    vax2.merge(inc2, on="country_code", how="outer")
        .merge(gavi, on="country_code", how="outer")
)

# Keep requested columns + income_class (needed for HIC/MICs7/NC rule)
combo = combo[[
    "country_code",
    "country_name_inc",
    "country_name_vax",
    "country_name_gavi",
    "gavi_2024",
    "income_class",
]].copy()

# Post-merge duplicate check (should never happen if keys were unique)
dup_out = combo[combo.duplicated(subset=["country_code"], keep=False)]
print("\n=== Duplicate country_code check: merged combo ===")
if dup_out.empty:
    print("No duplicates after merge ✅")
else:
    print("❌ Duplicate country_code found after merge!")
    print(dup_out.sort_values("country_code").to_string(index=False))

# -----------------------------
# Assign market segment
# Precedence:
#   1) MICs4 / MICs5 / MICs6 by name match (any of inc/vax/gavi)
#   2) gavi731 if gavi_2024 == "mic_former_gavi"
#   3) Gavi73 for remaining countries that exist in gavi list but not assigned
#   4) If NOT in gavi:
#        - if income_class == "H" -> HIC
#        - if income_class in {"LM","UM"} (and non-empty) -> MICs7
#        - else -> NC
#      (HIC and NC have no price)
# -----------------------------
MICs4_set = set(apply_alias(norm_name(x)) for x in MICs4)
MICs5_set = set(apply_alias(norm_name(x)) for x in MICs5)
MICs6_set = set(apply_alias(norm_name(x)) for x in MICs6)

def assign_segment(row) -> str:
    names = make_name_set(row["country_name_inc"], row["country_name_vax"], row["country_name_gavi"])

    # 1) Name-based buckets
    if names & MICs4_set:
        return "MICs4"
    if names & MICs5_set:
        return "MICs5"
    if names & MICs6_set:
        return "MICs6"

    # 2) Former gavi marker
    gavi_val = row.get("gavi_2024")
    if pd.notna(gavi_val) and str(gavi_val).strip().casefold() == "mic_former_gavi":
        return "gavi731"

    # 3) In GAVI list but not assigned -> Gavi73
    if pd.notna(gavi_val):
        return "Gavi73"

    # 4) NOT in GAVI -> use income_class_2024 rules
    inc_class = row.get("income_class")
    inc_class = str(inc_class).strip().upper() if pd.notna(inc_class) else ""
    
    if inc_class == "H":
        return "HIC"
    elif inc_class in {"LM", "UM"}:
        return "MICs7"
    else:
        return "NC"

combo["vax_market_segment"] = combo.apply(assign_segment, axis=1)
combo["vax_price_2024"] = combo["vax_market_segment"].map(PRICE_BY_SEGMENT)

# -----------------------------
# Print checks
# -----------------------------
print("\n=== Segment counts ===")
print(combo["vax_market_segment"].value_counts(dropna=False))

print("\n=== Missing vax_price_2024 (expected for HIC/NC) ===")
print(combo.loc[combo["vax_price_2024"].isna(), "vax_market_segment"].value_counts(dropna=False))

# -----------------------------
# Write as NEW SHEET into existing workbook
# -----------------------------
with pd.ExcelWriter(INPUT_FILE, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
    combo.to_excel(writer, sheet_name=NEW_SHEET, index=False)

print(f"\n✅ Added/updated sheet '{NEW_SHEET}' in: {INPUT_FILE}")
print("Rows written:", len(combo))
