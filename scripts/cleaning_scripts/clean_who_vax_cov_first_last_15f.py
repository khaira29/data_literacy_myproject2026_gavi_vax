import pandas as pd
#RUN FIRST

FIRST_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/00_raw_data/who_hpv_vax_first_15f.xlsx"
LAST_FILE  = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/00_raw_data/who_hpv_vax_last_15f.xlsx"

# intermediate output
OUTPUT_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/01_interm_data/who_hpv_vax_15f_first_last_clean.xlsx"

# NEW: final 2024-only output
FINAL_2024_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/02_cleaned_data/dl_project_section_1.xlsx"
FINAL_2024_SHEET = "hpv_vax_2024"

# -----------------------------
# Load raw data
# -----------------------------
df_first_raw = pd.read_excel(FIRST_FILE, engine="openpyxl")
df_last_raw  = pd.read_excel(LAST_FILE, engine="openpyxl")

# -----------------------------
# Keep needed columns + rename
# -----------------------------
df_first = (
    df_first_raw[["CODE", "YEAR", "NAME", "COVERAGE"]]
    .rename(columns={
        "CODE": "country_code",
        "YEAR": "vax_year",
        "NAME": "country_name",
        "COVERAGE": "first_d_cov",
    })
)

df_last = (
    df_last_raw[["CODE", "YEAR", "COVERAGE"]]
    .rename(columns={
        "CODE": "country_code",
        "YEAR": "vax_year",
        "COVERAGE": "last_d_cov",
    })
)

# -----------------------------
# Availability check by year
# -----------------------------
print("\n=== Data availability by year ===")

first_availability = (
    df_first
    .groupby("vax_year")["first_d_cov"]
    .apply(lambda x: x.notna().sum())
    .sort_values(ascending=False)
)

last_availability = (
    df_last
    .groupby("vax_year")["last_d_cov"]
    .apply(lambda x: x.notna().sum())
    .sort_values(ascending=False)
)

print("\nFirst-dose coverage (first_d_cov): non-missing counts by year")
print(first_availability)

print("\nLast-dose coverage (last_d_cov): non-missing counts by year")
print(last_availability)

print("\nMost-covered year(s) for first-dose:")
print(first_availability[first_availability == first_availability.max()])

print("\nMost-covered year(s) for last-dose:")
print(last_availability[last_availability == last_availability.max()])

# -----------------------------
# Duplicate checks on MERGE KEYS
# -----------------------------
dup_first = df_first.duplicated(subset=["country_code", "vax_year"], keep=False)
dup_last  = df_last.duplicated(subset=["country_code", "vax_year"], keep=False)

print("\n=== Duplicate check on (country_code, vax_year) ===")
print(f"First-dose duplicates: {dup_first.sum()} rows")
print(f"Last-dose duplicates : {dup_last.sum()} rows")

# (Optional) preview a few duplicates if they exist
if dup_first.any():
    print("\nExample duplicates in FIRST (country_code, vax_year):")
    print(df_first.loc[dup_first, ["country_code", "vax_year", "first_d_cov"]]
          .sort_values(["country_code", "vax_year"])
          .head(10))

if dup_last.any():
    print("\nExample duplicates in LAST (country_code, vax_year):")
    print(df_last.loc[dup_last, ["country_code", "vax_year", "last_d_cov"]]
          .sort_values(["country_code", "vax_year"])
          .head(10))

# -----------------------------
# Merge on BOTH country_code and year
# -----------------------------
df_merged = df_first.merge(
    df_last,
    on=["country_code", "vax_year"],
    how="left",
    validate="m:1"   # df_last must be unique by (country_code, vax_year)
)

# -----------------------------
# Save intermediate output
# -----------------------------
df_merged.to_excel(OUTPUT_FILE, index=False)

print("\nSaved merged file to:")
print(OUTPUT_FILE)
print(f"Rows in merged file: {len(df_merged)}")

# ==================================================
# NEW: Create dl_project_section_1.xlsx with 2024 only
# ==================================================
df_2024 = df_merged.loc[df_merged["vax_year"] == 2024].copy()

print("\n=== 2024-only extract ===")
print(f"Rows in 2024 data: {len(df_2024)}")
print(f"Unique countries in 2024 data: {df_2024['country_code'].nunique()}")

with pd.ExcelWriter(FINAL_2024_FILE, engine="openpyxl") as writer:
    df_2024.to_excel(writer, sheet_name=FINAL_2024_SHEET, index=False)

print("\nSaved dl_project_section_1 (2024 only) to:")
print(FINAL_2024_FILE)
print(f"Sheet name: {FINAL_2024_SHEET}")


# ==================================================
# STATISTICAL TEST:
# Do first-dose and last-dose coverage differ?
# (Paired comparison, 2024 only)
# ==================================================
from scipy import stats

# Keep only rows with both measures observed
df_test = df_2024[["country_code", "first_d_cov", "last_d_cov"]].dropna()

print("\n=== Statistical comparison: first vs last dose (2024) ===")
print(f"Number of countries with both measures: {len(df_test)}")

# Compute difference
df_test["diff"] = df_test["first_d_cov"] - df_test["last_d_cov"]

print("\nSummary of differences (first - last):")
print(df_test["diff"].describe())

# -----------------------------
# Paired t-test
# -----------------------------
t_stat, t_pval = stats.ttest_rel(
    df_test["first_d_cov"],
    df_test["last_d_cov"],
    nan_policy="omit"
)

print("\nPaired t-test:")
print(f"t-statistic = {t_stat:.3f}")
print(f"p-value     = {t_pval:.4g}")

# -----------------------------
# Wilcoxon signed-rank test
# (safer if distribution is skewed)
# -----------------------------
w_stat, w_pval = stats.wilcoxon(
    df_test["first_d_cov"],
    df_test["last_d_cov"]
)

print("\nWilcoxon signed-rank test:")
print(f"W-statistic = {w_stat:.3f}")
print(f"p-value     = {w_pval:.4g}")

# -----------------------------
# Effect size (Cohen's dz)
# -----------------------------
cohen_dz = df_test["diff"].mean() / df_test["diff"].std(ddof=1)
print("\nEffect size:")
print(f"Cohen's dz = {cohen_dz:.3f}")



# ==================================================
# ADDITIONAL ANALYSIS:
# Year-by-year paired tests (2015–2024)
# Each year analyzed separately (no pooling)
# ==================================================

START_YEAR = 2015
END_YEAR = 2024

print(f"\n=== Year-by-year comparison: first vs last dose ({START_YEAR}–{END_YEAR}) ===")

results = []

for year in range(START_YEAR, END_YEAR + 1):
    df_y = (
        df_merged
        .loc[df_merged["vax_year"] == year, ["country_code", "first_d_cov", "last_d_cov"]]
        .dropna()
    )

    n = len(df_y)

    if n < 5:
        print(f"\nYear {year}: n={n} (too few paired observations, skipped)")
        continue

    diff = df_y["first_d_cov"] - df_y["last_d_cov"]

    # Paired t-test
    t_stat, t_pval = stats.ttest_rel(
        df_y["first_d_cov"],
        df_y["last_d_cov"],
        nan_policy="omit"
    )

    # Wilcoxon (only if differences are not all zero)
    if (diff != 0).sum() > 0:
        w_stat, w_pval = stats.wilcoxon(
            df_y["first_d_cov"],
            df_y["last_d_cov"]
        )
    else:
        w_stat, w_pval = None, None

    # Effect size
    sd_diff = diff.std(ddof=1)
    cohen_dz = diff.mean() / sd_diff if sd_diff > 0 else None

    results.append({
        "year": year,
        "n_pairs": n,
        "mean_diff": diff.mean(),
        "cohen_dz": cohen_dz,
        "t_stat": t_stat,
        "t_pval": t_pval,
        "w_stat": w_stat,
        "w_pval": w_pval
    })

    print(f"\nYear {year} (n={n})")
    print(f"  Mean(first − last) = {diff.mean():.3f}")
    print(f"  Paired t-test      : t={t_stat:.3f}, p={t_pval:.4g}")
    if w_pval is not None:
        print(f"  Wilcoxon           : W={w_stat:.3f}, p={w_pval:.4g}")
    if cohen_dz is not None:
        print(f"  Cohen's dz         : {cohen_dz:.3f}")

# Save summary table
results_df = pd.DataFrame(results)

SUMMARY_OUT = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/01_interm_data/hpv_first_last_yearly_tests_2015_2024.xlsx"
results_df.to_excel(SUMMARY_OUT, index=False)

print("\nSaved year-by-year test summary to:")
print(SUMMARY_OUT)
