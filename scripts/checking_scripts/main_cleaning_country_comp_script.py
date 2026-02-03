# run clean_who_vax
# run wb_income_class
# run gavi and gavi mic country
# run market segment gavi vax price

#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path

SCRIPTS = [
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/clean_who_vax_cov_first_last_15f.py",
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/wb_income_class_cleaning.py",
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/gavi_and_gavi_mic_country.py",
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/market_segment_gavi_vax_price.py",
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/combine_cleaned_data.py",
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/final_hist_gavi_countries.py",
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/final_hist_income_countries.py", 
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/final_market_segment_vax_pricing.py", 
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/original_data_hpv_first_dose_hist.py", 
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/clean_meta-data_vax.py",
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/combine_part_1_historical_data_country.py",
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/combine_part_2_hist_data_vax_cov.py",
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/combine_part_3_hist_data_vax_info.py",
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/final_cervical_cancer_2022_crude_rate.py",
    r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/scripts/cleaning_scripts/cleaning_pre_analysis_country.py",
]

def run_one(script_path: str) -> None:
    p = Path(script_path)
    if not p.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    print("\n" + "=" * 90)
    print(f"RUNNING: {p.name}")
    print(f"PATH   : {p}")
    print("=" * 90)

    # Use same Python interpreter running this main script
    result = subprocess.run(
        [sys.executable, str(p)],
        text=True,
        capture_output=True,
    )

    # Print outputs
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        # stderr can include warnings; still print it so you see everything
        print(result.stderr)

    # Hard fail on error
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
