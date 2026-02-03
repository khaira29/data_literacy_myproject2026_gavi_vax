import pandas as pd

# --------------------------------------------------
# File paths
# --------------------------------------------------
MASTER_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/02_cleaned_data/final_dataset_country_year.xlsx"
CERVIX_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/01_interm_data/Datlit_HPV_Project_Final_Database - females-2022-cervix-uteri.tsv"
OUTPUT_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/02_cleaned_data/dl_pro_final_dataset_country_jan29.xlsx"

# --------------------------------------------------
# Load master dataset
# --------------------------------------------------
df_master = pd.read_excel(MASTER_FILE, engine="openpyxl")

print("Master data shape:", df_master.shape)
print("Master columns:", df_master.columns.tolist())

# --------------------------------------------------
# Load cervix–uteri TSV (2022 only)
# --------------------------------------------------
df_cerv = pd.read_csv(CERVIX_FILE, sep="\t")

print("Cervix data shape (raw):", df_cerv.shape)
print("Cervix columns (raw):", df_cerv.columns.tolist())

# --------------------------------------------------
# Normalize cervix column names (robust to spaces/hyphens)
#   "Alpha-3 code" -> "Alpha3code"
#   "Crude rate"   -> "Cruderate"
# --------------------------------------------------
df_cerv.columns = (
    df_cerv.columns
        .str.strip()
        .str.replace(" ", "", regex=False)
        .str.replace("-", "", regex=False)
)

print("Cervix columns (normalized):", df_cerv.columns.tolist())

# --------------------------------------------------
# Select & clean required columns
# --------------------------------------------------
required_cols = ["Alpha3code", "Cruderate"]
missing = [c for c in required_cols if c not in df_cerv.columns]
if missing:
    raise KeyError(
        f"Missing expected columns in cervix file: {missing}\n"
        f"Available columns: {df_cerv.columns.tolist()}"
    )

df_cerv_2022 = (
    df_cerv[required_cols]
        .rename(columns={
            "Alpha3code": "country_code",
            "Cruderate": "cerv_can_cr_rate_2022"
        })
)

# Optional: ensure key is clean + check duplicates
df_cerv_2022["country_code"] = df_cerv_2022["country_code"].astype(str).str.strip()

dup_count = df_cerv_2022["country_code"].duplicated().sum()
print("Duplicate country_code in cervix extract:", dup_count)
if dup_count > 0:
    # keep first occurrence (or change to an aggregation rule if needed)
    df_cerv_2022 = df_cerv_2022.drop_duplicates(subset=["country_code"], keep="first")

# --------------------------------------------------
# Merge (LEFT JOIN: master stays intact)
# --------------------------------------------------
df_merged = df_master.merge(
    df_cerv_2022,
    on="country_code",
    how="left"
)

print("Merged data shape:", df_merged.shape)
print("New column missing values:", df_merged["cerv_can_cr_rate_2022"].isna().sum())

# --------------------------------------------------
# Save back to Excel
# --------------------------------------------------
df_merged.to_excel(OUTPUT_FILE, index=False)
print("✔ Merge completed successfully")
