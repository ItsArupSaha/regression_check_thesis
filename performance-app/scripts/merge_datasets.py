import pandas as pd
import os

# Define file paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE_FILE = os.path.join(BASE_DIR, "performance_dataset.csv")
REGRESSION_A_FILE = os.path.join(BASE_DIR, "regression_a.csv")
REGRESSION_B_FILE = os.path.join(BASE_DIR, "regression_b.csv")
REGRESSION_C_FILE = os.path.join(BASE_DIR, "regression_c.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "final_thesis_dataset.csv")

def merge_datasets():
    dfs = []
    
    # Process Baseline
    if os.path.exists(BASELINE_FILE):
        print(f"Loading {BASELINE_FILE}...")
        try:
            # handle cases where accidental appends caused mixed columns
            df_baseline = pd.read_csv(BASELINE_FILE, on_bad_lines='skip')
        except TypeError:
             # Fallback for older pandas
            df_baseline = pd.read_csv(BASELINE_FILE, error_bad_lines=False)
        # Backfill missing columns
        if "Scenario" not in df_baseline.columns:
            df_baseline["Scenario"] = "baseline"
        if "Commit_ID" not in df_baseline.columns:
            df_baseline["Commit_ID"] = "initial"
        if "Is_Regression" not in df_baseline.columns:
            df_baseline["Is_Regression"] = 0
        dfs.append(df_baseline)
    else:
        print(f"Warning: {BASELINE_FILE} not found!")

    # Process Regressions
    for fpath in [REGRESSION_A_FILE, REGRESSION_B_FILE, REGRESSION_C_FILE]:
        if os.path.exists(fpath):
            print(f"Loading {fpath}...")
            df = pd.read_csv(fpath)
            dfs.append(df)
        else:
            print(f"Warning: {fpath} not found!")
    
    if not dfs:
        print("No data found to merge.")
        return

    # Concatenate
    final_df = pd.concat(dfs, ignore_index=True)
    
    # Sort by Timestamp (Crucial for Thesis Narrative)
    if 'Timestamp' in final_df.columns:
        final_df['Timestamp'] = pd.to_datetime(final_df['Timestamp'])
        final_df = final_df.sort_values(by='Timestamp')
    
    # Save
    final_df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Successfully created {OUTPUT_FILE} with {len(final_df)} rows.")
    
    # Show summary
    print("\nDataset Summary (Scenario):")
    print(final_df['Scenario'].value_counts())
    print("\nRegression Counts:")
    if 'Is_Regression' in final_df.columns:
        print(final_df['Is_Regression'].value_counts())

if __name__ == "__main__":
    merge_datasets()
