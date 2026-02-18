import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score
import joblib
import os

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PERFORMANCE_APP_DIR = os.path.dirname(SCRIPT_DIR)

INPUT_FILE = os.path.join(PERFORMANCE_APP_DIR, 'thesis_final_dataset.csv')
MODEL_DIR = os.path.join(PERFORMANCE_APP_DIR, 'models')
MODEL_PATH = os.path.join(MODEL_DIR, 'final_thesis_model.pkl')
BASELINE_PATH = os.path.join(MODEL_DIR, 'baseline_stats.pkl')
PLOT_PATH = os.path.join(MODEL_DIR, 'feature_importance.png')

# Original Raw Features (for baseline calc)
RAW_METRICS = [
    'Page_Load_Time_ms', 
    'Perceived_Load_Time_ms', 
    'LCP_ms', 
    'API_Latency_ms'
]

# Features to Train On (Relative + Context)
TRAINING_FEATURES = [
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

def train_model():
    print(f"🚀 Starting Model Training (Feature Engineering 2.0: Relative Metrics)...")
    
    # 1. Load Data
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: Dataset {INPUT_FILE} not found.")
        return
    
    df = pd.read_csv(INPUT_FILE)
    print(f"✅ Data Loaded. Shape: {df.shape}")

    # 2. Preprocessing & Cleaning
    if 'API_Measured' not in df.columns:
         df['API_Measured'] = (df['API_Latency_ms'] > 0).astype(int)

    df['API_Latency_ms'] = df['API_Latency_ms'].fillna(0)
    
    # 3. Calculate Baselines (from Healthy Data Only)
    print("📊 Calculating Baselines from Healthy Data...")
    healthy_df = df[df['Scenario'] == 'baseline']
    
    # Group by (Page_Name, Network_Type) and calculate Median
    # We use Median to be robust against outliers in the "healthy" set
    baselines = healthy_df.groupby(['Page_Name', 'Network_Type'])[RAW_METRICS].median().to_dict('index')
    
    # Save Baselines for Validation Script
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
    joblib.dump(baselines, BASELINE_PATH)
    print(f"💾 Baseline Stats Saved: {BASELINE_PATH}")
    
    # 4. Feature Engineering: Create Delta Columns
    print("🛠️ Creating Relative Features (Deltas)...")
    
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
            # Fallback if no baseline (shouldn't happen in thesis data)
            return pd.Series([0, 0, 0, 0])

    delta_cols = ['Page_Load_Time_Delta', 'Perceived_Load_Time_Delta', 'LCP_Delta', 'API_Latency_Delta']
    df[delta_cols] = df.apply(calculate_deltas, axis=1)
    
    # 5. Train on Full Dataset
    X = df[TRAINING_FEATURES]
    y = df[TARGET]
    
    print(f"📊 Training on full dataset: {len(X)} rows")
    print(f"Features: {TRAINING_FEATURES}")

    # Define Transformers
    numeric_features = [
        'Page_Load_Time_Delta',
        'Perceived_Load_Time_Delta',
        'LCP_Delta',
        'API_Latency_Delta',
        'API_Measured', 
        'Total_Page_Size_KB'
    ]
    categorical_features = ['Network_Type', 'Page_Name']

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])

    # 6. Model Pipeline
    clf = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(
            n_estimators=300, 
            random_state=42,
            class_weight='balanced',
            n_jobs=-1
        ))
    ])

    # 7. Train
    print("🧠 Training RandomForest Model...")
    clf.fit(X, y)

    # 8. Sanity Check
    y_pred = clf.predict(X)
    accuracy = accuracy_score(y, y_pred)
    print(f"🏆 Training Accuracy: {accuracy:.4f}")

    # 9. Feature Importance
    try:
        ohe = clf.named_steps['preprocessor'].named_transformers_['cat']
        ohe_features = list(ohe.get_feature_names_out(categorical_features))
    except:
        ohe_features = []
        
    feature_names = numeric_features + ohe_features
    
    if hasattr(clf.named_steps['classifier'], 'feature_importances_'):
        importances = clf.named_steps['classifier'].feature_importances_
        
        if len(feature_names) != len(importances):
             feature_names = [f"Feature_{i}" for i in range(len(importances))]

        feat_df = pd.DataFrame({'Feature': feature_names, 'Importance': importances})
        feat_df = feat_df.sort_values(by='Importance', ascending=True)

        plt.figure(figsize=(10, 6))
        plt.barh(feat_df['Feature'], feat_df['Importance'], color='teal')
        plt.xlabel('Importance')
        plt.title('RF Feature Importance (Relative Metrics)')
        plt.tight_layout()
        plt.savefig(PLOT_PATH)
        print(f"📊 Importance Plot Saved: {PLOT_PATH}")

    # 10. Save Model
    joblib.dump(clf, MODEL_PATH)
    print(f"💾 Model Saved: {MODEL_PATH}")

if __name__ == "__main__":
    train_model()
