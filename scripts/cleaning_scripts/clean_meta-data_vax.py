import pandas as pd

# --------------------------------------------------
# File paths (just save to excel)
# --------------------------------------------------
INPUT_FILE = "/Users/khaira_abdillah/Documents/dl_pro_country_comp/01_interm_data/vax_metadata.csv"
OUTPUT_FILE = "/Users/khaira_abdillah/Documents/dl_pro_country_comp/01_interm_data/vax_metadata.xlsx"

# --------------------------------------------------
# Load CSV
# --------------------------------------------------
df = pd.read_csv(INPUT_FILE)

# Quick checks
print(df.head())
print(df.shape)
print(df.columns)

# --------------------------------------------------
# Write to Excel
# --------------------------------------------------
df.to_excel(OUTPUT_FILE, index=False)
