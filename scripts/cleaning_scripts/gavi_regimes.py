#!/usr/bin/env python3
# ============================================================
# build_gavi_regimes_and_everclassic.py
#
# Adjustments:
#  1) income_class original coding is H / UM / LM / L (not HIC/UMIC/LMIC/LIC)
#  2) restrict dataset to observations with non-missing HPV first-dose coverage
#     (vax_fd_cov is FIRST-DOSE coverage)
#  3) hic_flag uses income_class == "H" and is NA-safe
#  4) optional: add income_class_lbl (LIC/LMIC/UMIC/HIC) for nicer plots
# ============================================================

from pathlib import Path
import pandas as pd
import numpy as np

# -----------------------------
# Paths
# -----------------------------
INPUT_XLSX = Path(
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/02_cleaned_data/"
    r"dataset_country_analysis_final_30jan_clean_2015_2024.xlsx"
)

OUT_DIR = Path(
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/02_cleaned_data"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_XLSX = OUT_DIR / "dataset_country_analysis_with_gavi_regimes.xlsx"

# -----------------------------
# Load
# -----------------------------
df = pd.read_excel(INPUT_XLSX, engine="openpyxl")

# -----------------------------
# Basic cleaning
# -----------------------------
df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

# income_class in file: H / UM / LM / L
df["income_class"] = df["income_class"].astype("string").str.strip().str.upper()

# HPV coverage (FIRST-DOSE)
df["vax_fd_cov"] = pd.to_numeric(df["vax_fd_cov"], errors="coerce")

# >>> Restrict to rows with observed HPV first-dose coverage <<<
df = df.dropna(subset=["vax_fd_cov"]).copy()

# Normalize gavi_supported + gavi_spec
df["gavi_supported"] = df["gavi_supported"].astype("string").str.strip().str.lower()
df["gavi_spec"] = df["gavi_spec"].astype("string").str.strip().str.lower()

# Optional: nice labels for income classes (useful for plots)
income_map = {"L": "LIC", "LM": "LMIC", "UM": "UMIC", "H": "HIC"}
df["income_class_lbl"] = df["income_class"].map(income_map).fillna(df["income_class"])

# -----------------------------
# 1) Build time-varying Gavi regime (3-level)
# -----------------------------
# Definitions:
# - Classic Gavi:
#     supported by gavi AND gavi_spec NOT in {mic_former_gavi, mic_never_gavi}
# - MICs approach / post-Gavi:
#     supported by gavi AND gavi_spec in {mic_former_gavi, mic_never_gavi}
# - Never Gavi:
#     gavi_supported == not supported by gavi

MIC_TAGS = {"mic_former_gavi", "mic_never_gavi"}

def classify_regime(gs: str, spec: str) -> str:
    if gs == "not supported by gavi":
        return "Never Gavi"
    # supported by gavi
    if spec in MIC_TAGS:
        return "MICs approach / post-Gavi"
    return "Classic Gavi"

df["gavi_regime_it"] = [
    classify_regime(gs, spec) for gs, spec in zip(df["gavi_supported"], df["gavi_spec"])
]

# -----------------------------
# 2) Build country-level "ever classic Gavi" (time-invariant)
# -----------------------------
if "country_code" not in df.columns:
    raise ValueError("country_code is missing; needed to build ever_classic_gavi.")

classic_by_country = (
    df.loc[df["gavi_regime_it"] == "Classic Gavi", "country_code"]
    .dropna()
    .astype("string")
    .unique()
)

df["ever_classic_gavi"] = df["country_code"].astype("string").isin(classic_by_country).astype(int)

# Optional: also define "ever_supported_by_gavi" (includes MIC approach)
supported_by_country = (
    df.loc[df["gavi_supported"] != "not supported by gavi", "country_code"]
    .dropna()
    .astype("string")
    .unique()
)

df["ever_supported_by_gavi"] = df["country_code"].astype("string").isin(supported_by_country).astype(int)

# -----------------------------
# 3) Convenience: HIC flag (time-varying)
# -----------------------------
# income_class uses "H" for high income
df["hic_flag"] = (df["income_class"] == "H").fillna(False).astype(int)

# -----------------------------
# 4) Sanity checks
# -----------------------------
print("\n=== SAMPLE RESTRICTION: non-missing HPV first-dose coverage (vax_fd_cov) ===")
print("Rows (country-years) kept:", df.shape[0])
print("Unique countries kept:", df["country_code"].nunique())

print("\n=== income_class distribution (kept sample) ===")
print(df["income_class"].value_counts(dropna=False).to_string())

print("\n=== Basic counts (rows) by Gavi regime (kept sample) ===")
print(df["gavi_regime_it"].value_counts(dropna=False).to_string())

print("\n=== Unique countries by Gavi regime (ever) (kept sample) ===")
country_regime = (
    df[["country_code", "gavi_regime_it"]]
    .dropna()
    .drop_duplicates()
)
print(country_regime.groupby("gavi_regime_it")["country_code"].nunique().to_string())

print("\n=== How many countries are ever classic Gavi? (kept sample) ===")
print(int(df.drop_duplicates("country_code")["ever_classic_gavi"].sum()))

print("\n=== How many countries are ever supported by Gavi (any support)? (kept sample) ===")
print(int(df.drop_duplicates("country_code")["ever_supported_by_gavi"].sum()))

# -----------------------------
# 5) Detect transitions (regime changes) over time
# -----------------------------
tmp = (
    df[["country_code", "year", "gavi_regime_it"]]
    .dropna()
    .sort_values(["country_code", "year"])
    .copy()
)
tmp["regime_prev"] = tmp.groupby("country_code")["gavi_regime_it"].shift(1)
tmp["changed"] = (tmp["gavi_regime_it"] != tmp["regime_prev"]) & tmp["regime_prev"].notna()

transitions = tmp.groupby("country_code")["changed"].sum().sort_values(ascending=False)

print("\n=== Countries with regime transitions (top 20 by #changes) ===")
print(transitions.head(20).to_string())

print("\nTotal countries with >=1 transition:",
      int((transitions >= 1).sum()))

# Optional: focus on 2021 -> 2022 transitions specifically
pivot_2122 = (
    df[df["year"].isin([2021, 2022])]
    .dropna(subset=["country_code", "year"])
    .pivot_table(index="country_code", columns="year", values="gavi_regime_it", aggfunc="first")
)

switch_2122 = pivot_2122.dropna()
switch_2122 = switch_2122[switch_2122[2021] != switch_2122[2022]]

print("\n=== Regime switchers between 2021 and 2022 (kept sample) ===")
print("Count:", switch_2122.shape[0])

if switch_2122.shape[0] > 0:
    name_map = (
        df.dropna(subset=["country_code", "country_name"])
        .groupby("country_code")["country_name"]
        .agg(lambda s: s.mode().iloc[0] if not s.mode().empty else s.iloc[0])
    )
    out = switch_2122.join(name_map, how="left")
    out = out.rename(columns={2021: "regime_2021", 2022: "regime_2022"})
    print(
        out[["country_name", "regime_2021", "regime_2022"]]
        .sort_values(["regime_2021", "regime_2022", "country_name"])
        .to_string()
    )

# -----------------------------
# 6) Save
# -----------------------------
df.to_excel(OUT_XLSX, index=False, engine="openpyxl")
print(f"\nSaved: {OUT_XLSX}")
