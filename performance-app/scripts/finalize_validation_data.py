import pandas as pd
import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # scripts/
APP_DIR = os.path.dirname(BASE_DIR)

HEALTHY_PATH = os.path.join(APP_DIR, 'val_healthy.csv')
REGRESSION_PATH = os.path.join(APP_DIR, 'val_regression.csv')
OUTPUT_PATH = os.path.join(APP_DIR, 'real_validation_data.csv')

def finalize_validation_data():
    print("🚀 Merging and Labeling Validation Data...")

    # Load
    if not os.path.exists(HEALTHY_PATH) or not os.path.exists(REGRESSION_PATH):
        print("❌ Error: Missing temporary validation files.")
        return

    df_h = pd.read_csv(HEALTHY_PATH)
    df_r = pd.read_csv(REGRESSION_PATH)
    
    # Labeling Logic
    # 1. Healthy Run: Everything is 0
    df_h['Is_Regression'] = 0
    df_h['Scenario'] = 'baseline_validation'
    
    # 2. Regression Run: 
    # - Products Page has the 2s delay -> Is_Regression = 1
    # - Other pages (Home, About) are unaffected -> Is_Regression = 0 (Control Group)
    
    # Identify Products page
    regression_mask = df_r['Page_Name'] == 'Products'
    
    df_r.loc[regression_mask, 'Is_Regression'] = 1
    df_r.loc[regression_mask, 'Scenario'] = 'api_delay_2s_validation'
    
    df_r.loc[~regression_mask, 'Is_Regression'] = 0
    df_r.loc[~regression_mask, 'Scenario'] = 'baseline_validation_control'
    
    # Merge
    df_final = pd.concat([df_h, df_r], ignore_index=True)
    
    # Save
    df_final.to_csv(OUTPUT_PATH, index=False)
    print(f"✅ Final Balanced Validation Data Saved: {OUTPUT_PATH}")
    print(f"Total Rows: {len(df_final)}")
    print(f"Class Distribution:\n{df_final['Is_Regression'].value_counts()}")
    print("\nSample Regression Rows:")
    print(df_final[df_final['Is_Regression'] == 1][['Page_Name', 'Is_Regression', 'Scenario']].head())

if __name__ == "__main__":
    finalize_validation_data()
