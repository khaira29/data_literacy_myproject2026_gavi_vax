import pandas as pd

INPUT_FILE = r"/Users/khaira_abdillah/Documents/dl_pro_country_comp/01_interm_data/wb_hist_income_2015_2024_clean.xlsx"

ALLOWED = {"L", "LM", "UM", "H"}
RANK = {"L": 1, "LM": 2, "UM": 3, "H": 4}


def run_income_change_check(df: pd.DataFrame, start_year: int, end_year: int, code_col: str = "country_code") -> None:
    """
    Checks missing/invalid values and changes in income groups within a year window [start_year, end_year].
    Splits changed countries into:
      - Returned to initial by end_year
      - Not returned to initial by end_year
        - Not returned + UP overall
        - Not returned + DOWN overall
    """

    # --- build year columns that might be int or str in Excel ---
    expected_years = list(range(start_year, end_year + 1))
    year_cols = []
    for y in expected_years:
        if y in df.columns:
            year_cols.append(y)
        elif str(y) in df.columns:
            year_cols.append(str(y))
        else:
            raise ValueError(f"Missing expected year column: {y}. Available: {list(df.columns)}")

    # --- clean year values as strings ---
    dfw = df.copy()
    for c in year_cols:
        dfw[c] = dfw[c].astype("string").str.strip().str.upper()
        dfw[c] = dfw[c].replace({"": pd.NA})
        dfw[c] = dfw[c].where(dfw[c].isin(ALLOWED), pd.NA)

    def year_as_int(col):
        return int(col) if isinstance(col, str) and col.isdigit() else int(col)

    def change_list(row):
        """Return list like ['2018 LM -> UM', '2022 UM -> H'] within the chosen window."""
        changes = []
        prev_val = row[year_cols[0]]
        for c in year_cols[1:]:
            y = year_as_int(c)
            val = row[c]
            if val != prev_val:
                changes.append(f"{y} {prev_val} -> {val}")
                prev_val = val
        return changes

    # -----------------------------
    # Missing data check
    # -----------------------------
    mask_incomplete = dfw[year_cols].isna().any(axis=1)

    missing_country_codes = (
        dfw.loc[mask_incomplete, code_col]
        .astype("string")
        .str.strip()
        .dropna()
        .unique()
    )

    print(f"\n{'='*80}")
    print(f"WINDOW: {start_year}–{end_year}")
    print(f"{'='*80}")

    print(f"=== Countries with missing/invalid income-group value (any year {start_year}–{end_year}) ===")
    if len(missing_country_codes) == 0:
        print("None ✅")
    else:
        print(f"Count: {len(missing_country_codes)}")
        print(sorted([str(x) for x in missing_country_codes]))

    # Use only complete rows for change logic
    dfw = dfw.loc[~mask_incomplete].copy()

    # Identify rows with changes within the window
    nunique = dfw[year_cols].nunique(axis=1, dropna=True)
    df_changed = dfw.loc[nunique > 1, [code_col] + year_cols].copy()

    returned_to_initial = []
    not_returned_to_initial = []

    for _, row in df_changed.iterrows():
        code = str(row[code_col]).strip()
        initial = row[year_cols[0]]
        final = row[year_cols[-1]]
        changes = change_list(row)

        if final == initial:
            returned_to_initial.append((code, initial, final, changes))
        else:
            not_returned_to_initial.append((code, initial, final, changes))

    # ---- Print results ----
    print(f"\n=== Group 1: Returned to initial by {end_year} ({start_year} value == {end_year} value) ===")
    if not returned_to_initial:
        print("None ✅")
    else:
        print(f"Count: {len(returned_to_initial)}")
        for code, initial, final, changes in sorted(returned_to_initial, key=lambda x: x[0]):
            print(f"{code}: {initial} -> {final} | " + "; ".join(changes))

    print(f"\n=== Group 2: Did NOT return to initial by {end_year} ({start_year} value != {end_year} value) ===")
    if not not_returned_to_initial:
        print("None ✅")
    else:
        print(f"Count: {len(not_returned_to_initial)}")
        for code, initial, final, changes in sorted(not_returned_to_initial, key=lambda x: x[0]):
            print(f"{code}: {initial} -> {final} | " + "; ".join(changes))

    # -----------------------------
    # UP vs DOWN (based only on start_year vs end_year)
    # -----------------------------
    up_not_returned = []
    down_not_returned = []

    for code, initial, final, changes in not_returned_to_initial:
        if RANK[final] > RANK[initial]:
            up_not_returned.append((code, initial, final, changes))
        elif RANK[final] < RANK[initial]:
            down_not_returned.append((code, initial, final, changes))

    print(f"\n=== Group 2A: Not returned + UP overall ({end_year} higher than {start_year}) ===")
    if not up_not_returned:
        print("None ✅")
    else:
        print(f"Count: {len(up_not_returned)}")
        for code, initial, final, changes in sorted(up_not_returned, key=lambda x: x[0]):
            print(f"{code}: {initial} -> {final} | " + "; ".join(changes))

    print(f"\n=== Group 2B: Not returned + DOWN overall ({end_year} lower than {start_year}) ===")
    if not down_not_returned:
        print("None ✅")
    else:
        print(f"Count: {len(down_not_returned)}")
        for code, initial, final, changes in sorted(down_not_returned, key=lambda x: x[0]):
            print(f"{code}: {initial} -> {final} | " + "; ".join(changes))


def main():
    df = pd.read_excel(INPUT_FILE, engine="openpyxl")

    # Run both windows (your Code 1 and Code 2) in one go
    run_income_change_check(df, start_year=2015, end_year=2024, code_col="country_code")
    run_income_change_check(df, start_year=2020, end_year=2024, code_col="country_code")


if __name__ == "__main__":
    main()
