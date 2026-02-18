import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

# Setup paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "final_thesis_dataset.csv")
OUTPUT_DIR = BASE_DIR

def visualize_thesis():
    if not os.path.exists(DATA_FILE):
        print(f"Error: {DATA_FILE} not found!")
        return

    print("Loading dataset...")
    df = pd.read_csv(DATA_FILE)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    # Set global style
    sns.set_theme(style="whitegrid")

    # --- Chart 1: The Database Crash (Regression A) ---
    print("Generating Regression A Plot...")
    plt.figure(figsize=(12, 6))
    
    # Filter for products page and specific scenarios
    df_a = df[(df['Page_Name'].str.contains('products', case=False)) & 
              (df['Scenario'].isin(['baseline', 'api_delay_2s']))]
    
    sns.scatterplot(
        data=df_a,
        x='Timestamp', 
        y='API_Latency_ms', 
        hue='Scenario',
        palette={'baseline': 'blue', 'api_delay_2s': 'red'},
        s=50,
        alpha=0.7
    )
    plt.title("Regression A: Impact of Backend Delay on API Latency", fontsize=14)
    plt.ylabel("API Latency (ms)")
    plt.xlabel("Timestamp")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "plot_regression_a.png"))
    plt.close()

    # --- Chart 2: The CPU Freeze (Regression B) ---
    print("Generating Regression B Plot...")
    plt.figure(figsize=(12, 6))
    
    # Filter for relevant scenarios
    df_b = df[df['Scenario'].isin(['baseline', 'client_cpu_block'])]
    
    sns.scatterplot(
        data=df_b,
        x='Timestamp', 
        y='LCP_ms', 
        hue='Scenario',
        palette={'baseline': 'green', 'client_cpu_block': 'orange'},
        s=50,
        alpha=0.7
    )
    plt.title("Regression B: Impact of Client-Side CPU Block on LCP", fontsize=14)
    plt.ylabel("Largest Contentful Paint (ms)")
    plt.xlabel("Timestamp")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "plot_regression_b.png"))
    plt.close()

    # --- Chart 3: The Bloat (Regression C) ---
    print("Generating Regression C Plot...")
    plt.figure(figsize=(12, 6))
    
    # Filter for relevant scenarios
    df_c = df[df['Scenario'].isin(['baseline', 'payload_bloat'])]
    
    sns.boxplot(
        data=df_c,
        x='Network_Type',
        y='Page_Load_Time_ms',
        hue='Scenario',
        palette={'baseline': 'cyan', 'payload_bloat': 'purple'},
        order=['WiFi', '4G', '3G']
    )
    plt.title("Regression C: Impact of Payload Bloat across Network Conditions", fontsize=14)
    plt.ylabel("Page Load Time (ms)")
    plt.xlabel("Network Type")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "plot_regression_c.png"))
    plt.close()

    print("✅ All plots generated successfully!")

if __name__ == "__main__":
    visualize_thesis()
