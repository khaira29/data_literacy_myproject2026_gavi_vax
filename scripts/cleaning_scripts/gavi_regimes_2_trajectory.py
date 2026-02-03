#!/usr/bin/env python3
# ============================================================
# build_gavi_policy_trajectory.py
#
# Starts from:
#   dataset_country_analysis_with_gavi_regimes.xlsx
#
# Creates:
#   gavi_trajectory (time-invariant, 4-category)
# ============================================================

from pathlib import Path
import pandas as pd
import numpy as np

# -----------------------------
# Paths
# -----------------------------
INPUT_XLSX = Path(
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/02_cleaned_data/"
    r"dataset_country_analysis_with_gavi_regimes.xlsx"
)

OUT_XLSX = Path(
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/02_cleaned_data/"
    r"dataset_country_analysis_with_gavi_trajectory.xlsx"
)

# -----------------------------
# Load
# -----------------------------
df = pd.read_excel(INPUT_XLSX, engine="openpyxl")

# Safety checks
required_cols = {
    "country_code",
    "year",
    "gavi_regime_it",
    "ever_classic_gavi",
    "ever_supported_by_gavi"
}
missing = required_cols - set(df.columns)
if missing:
    raise ValueError(f"Missing required columns: {missing}")

# -----------------------------
# Build country-level trajectory
# -----------------------------
# We classify countries based on their EVER status
# and whether they EVER appear as MICs approach / post-Gavi

def classify_trajectory(sub: pd.DataFrame) -> str:
    regimes = set(sub["gavi_regime_it"].dropna().unique().tolist())

    ever_classic = int(sub["ever_classic_gavi"].iloc[0])
    ever_supported = int(sub["ever_supported_by_gavi"].iloc[0])

    if ever_classic == 1:
        if "MICs approach / post-Gavi" in regimes:
            return "Classic → MIC (graduated)"
        else:
            return "Classic Gavi (always)"
    else:
        if ever_supported == 1:
            return "Never → MIC (MICs entry)"
        else:
            return "Never Gavi (always)"

trajectory_map = (
    df.groupby("country_code")
      .apply(classify_trajectory)
      .reset_index()
      .rename(columns={0: "gavi_trajectory"})
)


# Merge back
df = df.merge(trajectory_map, on="country_code", how="left")

# -----------------------------
# Optional: numeric coding (useful for modeling)
# -----------------------------
trajectory_order = {
    "Classic Gavi (always)": 1,
    "Classic → MIC (graduated)": 2,
    "Never → MIC (MICs entry)": 3,
    "Never Gavi (always)": 4,
}

df["gavi_trajectory_code"] = df["gavi_trajectory"].map(trajectory_order)

# -----------------------------
# Sanity checks
# -----------------------------
print("\n=== Gavi policy trajectory: country counts ===")
print(
    df.drop_duplicates("country_code")["gavi_trajectory"]
      .value_counts()
      .to_string()
)

print("\n=== Cross-tab: trajectory × ever_classic_gavi ===")
print(
    pd.crosstab(
        df.drop_duplicates("country_code")["gavi_trajectory"],
        df.drop_duplicates("country_code")["ever_classic_gavi"]
    ).to_string()
)

print("\n=== Cross-tab: trajectory × ever_supported_by_gavi ===")
print(
    pd.crosstab(
        df.drop_duplicates("country_code")["gavi_trajectory"],
        df.drop_duplicates("country_code")["ever_supported_by_gavi"]
    ).to_string()
)

# Quick check: no country should have missing trajectory
if df["gavi_trajectory"].isna().any():
    bad = df.loc[df["gavi_trajectory"].isna(), "country_code"].unique()
    raise ValueError(f"Countries with missing trajectory: {bad}")

# -----------------------------
# Save
# -----------------------------
df.to_excel(OUT_XLSX, index=False, engine="openpyxl")
print(f"\nSaved: {OUT_XLSX}")
