import pandas as pd
import joblib
import os
import numpy as np
import datetime
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report, precision_recall_fscore_support

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PERFORMANCE_APP_DIR = os.path.dirname(SCRIPT_DIR)

VALIDATION_FILE = os.path.join(PERFORMANCE_APP_DIR, 'real_validation_data.csv')
MODEL_DIR = os.path.join(PERFORMANCE_APP_DIR, 'models')
MODEL_PATH = os.path.join(MODEL_DIR, 'final_thesis_model.pkl')
BASELINE_PATH = os.path.join(MODEL_DIR, 'baseline_stats.pkl')
REPORT_PATH = os.path.join(PERFORMANCE_APP_DIR, 'validation_report.md')

FEATURES = [
    'Page_Load_Time_Delta',
    'Perceived_Load_Time_Delta',
    'LCP_Delta',
    'API_Latency_Delta',
    'API_Measured',          
    'Total_Page_Size_KB', 
    'Network_Type', 
    'Page_Name'
]
TARGET = 'Is_Regression'

def validate_model():
    print(f"🚀 Starting Comprehensive Validation Report Generation...")
    
    if not os.path.exists(VALIDATION_FILE) or not os.path.exists(MODEL_PATH) or not os.path.exists(BASELINE_PATH):
        print("❌ Error: Missing data, model, or baseline stats.")
        return
        
    df = pd.read_csv(VALIDATION_FILE)
    model = joblib.load(MODEL_PATH)
    baselines = joblib.load(BASELINE_PATH)
    
    print(f"✅ Data Loaded ({len(df)} rows).")

    # Preprocessing
    if 'API_Measured' not in df.columns:
         df['API_Measured'] = (df['API_Latency_ms'] > 0).astype(int)
    df['API_Latency_ms'] = df['API_Latency_ms'].fillna(0)
    
    # Calculate Deltas
    def calculate_deltas(row):
        key = (row['Page_Name'], row['Network_Type'])
        if key in baselines:
            base = baselines[key]
            return pd.Series([
                row['Page_Load_Time_ms'] - base['Page_Load_Time_ms'],
                row['Perceived_Load_Time_ms'] - base['Perceived_Load_Time_ms'],
                row['LCP_ms'] - base['LCP_ms'],
                row['API_Latency_ms'] - base['API_Latency_ms']
            ])
        else:
            return pd.Series([0, 0, 0, 0])

    delta_cols = ['Page_Load_Time_Delta', 'Perceived_Load_Time_Delta', 'LCP_Delta', 'API_Latency_Delta']
    df[delta_cols] = df.apply(calculate_deltas, axis=1)

    X_val = df[FEATURES]
    y_true = df[TARGET]
    
    # Predict with optimized threshold (0.25) to maximize Recall for CI
    # y_pred = model.predict(X_val) # Default 0.5 threshold
    y_prob = model.predict_proba(X_val)[:, 1]
    y_pred = (y_prob >= 0.25).astype(int)
    
    df['Predicted_Label'] = y_pred
    df['Regression_Prob'] = y_prob
    
    # --- Generate Report ---
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(f"# Thesis Validation Report\n")
        f.write(f"**Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

        # 1. Dataset Summary
        f.write("## 1. Dataset Summary\n")
        f.write(f"- **Total Samples:** {len(df)}\n")
        f.write(f"- **Healthy Samples (Class 0):** {(y_true == 0).sum()}\n")
        f.write(f"- **Regression Samples (Class 1):** {(y_true == 1).sum()}\n")
        f.write(f"- **Source:** Real-world validation (Playwright Live Test)\n")
        f.write("- **Scenario Breakdown:**\n")
        scenario_counts = df['Scenario'].value_counts()
        for scenario, count in scenario_counts.items():
            f.write(f"    - `{scenario}`: {count}\n")
        f.write("\n")

        # 2. Methodology
        f.write("## 2. Methodology\n")
        f.write("- **Ground Truth Design:**\n")
        f.write("    - **Baseline:** Application running normally (no injected delays).\n")
        f.write("    - **Regression:** Application with injected 2s API delay on `Products` page.\n")
        f.write("- **Model Type:** Random Forest (V2)\n")
        f.write("- **Feature Engineering:** Relative Metrics (Deltas from Baseline Median)\n")
        f.write(f"- **Features Used:** `{', '.join(FEATURES)}`\n")
        f.write("- **Threshold:** 0.25 (Optimized for 100% Recall in CI)\n\n")

        # 3. Results
        accuracy = accuracy_score(y_true, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='binary')
        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel()

        f.write("## 3. Results\n")
        f.write(f"### Performance Metrics\n")
        f.write(f"- **Accuracy:** {accuracy:.4f}\n")
        f.write(f"- **Precision (Regression):** {precision:.4f}\n")
        f.write(f"- **Recall (Regression):** {recall:.4f}\n")
        f.write(f"- **F1-Score:** {f1:.4f}\n\n")
        
        f.write("### Confusion Matrix\n")
        f.write("| | Predicted Healthy (0) | Predicted Regression (1) |\n")
        f.write("|---|---|---|\n")
        f.write(f"| **Actual Healthy (0)** | **{tn}** (True Negative) | **{fp}** (False Positive) |\n")
        f.write(f"| **Actual Regression (1)** | **{fn}** (False Negative) | **{tp}** (True Positive) |\n\n")

        f.write(f"- **False Positive Rate:** {fp / (fp + tn):.4f}\n")
        f.write(f"- **False Negative Rate:** {fn / (fn + tp):.4f}\n\n")

        # 4. Error Analysis
        f.write("## 4. Error Analysis\n")
        
        # False Positives
        fps = df[(y_true == 0) & (y_pred == 1)]
        f.write(f"### False Positives (Predicted Regression, Actual Healthy) - N={len(fps)}\n")
        if not fps.empty:
            f.write("Top 5 by Confidence:\n")
            f.write(fps.sort_values('Regression_Prob', ascending=False)[['Page_Name', 'Network_Type', 'API_Latency_Delta', 'Regression_Prob']].head(5).to_markdown(index=False))
            f.write("\n")
        else:
            f.write("None.\n")

        # False Negatives
        fns = df[(y_true == 1) & (y_pred == 0)]
        f.write(f"\n### False Negatives (Predicted Healthy, Actual Regression) - N={len(fns)}\n")
        if not fns.empty:
            f.write("Top 5 by Low Confidence (Missed):\n")
            f.write(fns.sort_values('Regression_Prob', ascending=True)[['Page_Name', 'Network_Type', 'API_Latency_Delta', 'Regression_Prob']].head(5).to_markdown(index=False))
            f.write("\n")
        else:
            f.write("None.\n")
            
    print(f"✅ Report Generated: {REPORT_PATH}")
    # Print content to stdout for user
    with open(REPORT_PATH, 'r') as f:
        print(f.read())

if __name__ == "__main__":
    validate_model()
