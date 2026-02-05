# ============================================================
# Master runner for DL Pro country pipeline
# ============================================================

import sys
import subprocess
from pathlib import Path

# ------------------------------------------------------------
# Ordered pipeline (close to your original logic):
#   1) WHO vax coverage core
#   2) WB income class (hist)
#   3) Gavi eligibility (hist + MIC approach)
#   4) Vaccine pricing / market segment
#   5) Combine historical country-year dataset
#   6) Add HPV vaccine program meta / info
#   7) Add DTP (first/third dose) comparators
#   8) Add cervical cancer context
#   9) Final combine + pre-analysis cleaning
# ------------------------------------------------------------

SCRIPTS = [
    # --------------------------------------------------
    # 1) Core WHO HPV vaccination coverage
    # --------------------------------------------------
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/clean_who_vax_cov_first_last_15f.py",
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/original_data_hpv_first_dose_hist.py",

    # --------------------------------------------------
    # 2) World Bank income classifications
    # --------------------------------------------------
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/wb_income_class_cleaning.py",
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/final_hist_income_countries.py",

    # --------------------------------------------------
    # 3) Gavi eligibility & MIC approach
    # --------------------------------------------------
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/gavi_and_gavi_mic_country.py",
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/final_hist_gavi_countries.py",

    # --------------------------------------------------
    # 4) Vaccine pricing & market segments
    # --------------------------------------------------
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/market_segment_gavi_vax_price.py",
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/final_market_segment_vax_pricing.py",

    # --------------------------------------------------
    # 5) Combine historical country-year datasets
    # --------------------------------------------------
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/combine_part_1_historical_data_country.py",
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/combine_part_2_hist_data_vax_cov.py",
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/combine_part_3_hist_data_vax_info.py",
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/combine_cleaned_data.py",

    # --------------------------------------------------
    # 6) Vaccine program meta-data
    # --------------------------------------------------
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/clean_meta-data_vax.py",

    # --------------------------------------------------
    # 7) Cervical cancer context (single-year)
    # --------------------------------------------------
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/final_cervical_cancer_2022_crude_rate.py",

    # --------------------------------------------------
    # 8) Final pre-analysis harmonisation
    # --------------------------------------------------
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/cleaning_pre_analysis_country.py",
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/cleaning_for_analysis_2015_2024.py",
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/gavi_regimes.py",
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/gavi_regimes_2_trajectory.py",
]


# ------------------------------------------------------------
# Runner
# ------------------------------------------------------------
def run_one(script_path: str) -> None:
    p = Path(script_path)
    if not p.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    print("\n" + "=" * 90)
    print(f"RUNNING: {p.name}")
    print(f"PATH   : {p}")
    print("=" * 90)

    result = subprocess.run(
        [sys.executable, str(p)],
        text=True,
        capture_output=True,
    )

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if result.returncode != 0:
        raise RuntimeError(f"❌ Script failed ({p.name}) with exit code {result.returncode}")

    print(f"✅ DONE: {p.name}")

def main():
    print("Starting full cleaning pipeline...\n")
    for s in SCRIPTS:
        run_one(s)
    print("\n🎉 All cleaning scripts finished successfully.")

if __name__ == "__main__":
    main()