import os
import random
import time
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright

# --- Configuration ---
BASE_URL = "http://localhost:3000"
OUTPUT_FILE = "performance-app/performance-app/real_validation_data.csv" # Adjusting path based on user's folder structure confusion or relative to root
# User said "save to real_validation_data.csv". I'll put it in performance-app to be safe or root? 
# Helper: The user seems to be in root `thesis`, and has `performance-app`.
# Let's write to `performance-app/real_validation_data.csv`.

OUTPUT_PATH = 'performance-app/real_validation_data.csv'
TOTAL_SAMPLES = 200

PAGES = [
    {'path': '/', 'name': 'Homepage'},
    {'path': '/products', 'name': 'Products'},
    {'path': '/about', 'name': 'About'}
]

NETWORK_PROFILES = {
    'WiFi': None, # No throttling
    '4G': {
        'offline': False,
        'downloadThroughput': 4 * 1024 * 1024 / 8, # 4MB/s
        'uploadThroughput': 4 * 1024 * 1024 / 8,
        'latency': 20
    },
    '3G': {
        'offline': False,
        'downloadThroughput': 750 * 1024 / 8, # 750kb/s
        'uploadThroughput': 250 * 1024 / 8,
        'latency': 100
    }
}

COLUMNS = [
    'Timestamp', 'Page_Name', 'Network_Type', 
    'Page_Load_Time_ms', 'Perceived_Load_Time_ms', 'LCP_ms', 
    'API_Latency_ms', 'API_Measured', 'Total_Page_Size_KB', 
    'Scenario', 'Commit_ID', 'Is_Regression'
]

def get_lcp(page):
    return page.evaluate("""() => {
        return new Promise((resolve) => {
            new PerformanceObserver((entryList) => {
                const entries = entryList.getEntries();
                const lastEntry = entries[entries.length - 1];
                resolve(lastEntry.startTime);
            }).observe({ type: 'largest-contentful-paint', buffered: true });
            
            // Fallback if no LCP after timeout (e.g. 5s)
            setTimeout(() => resolve(0), 5000);
        });
    }""")

def measure_performance():
    data = []
    
    print(f"🚀 Starting Validation Data Generation ({TOTAL_SAMPLES} samples)...")
    
    with sync_playwright() as p:
        # Launch Chrome (headless)
        browser = p.chromium.launch(headless=True)
        
        for i in range(TOTAL_SAMPLES):
            # 1. Random Selection
            page_def = random.choice(PAGES)
            network_name = random.choice(list(NETWORK_PROFILES.keys()))
            url = f"{BASE_URL}{page_def['path']}"
            
            # 2. Setup Context (Clean Slate)
            context = browser.new_context(bypass_csp=True)
            context.clear_cookies()
            
            # 3. Apply Network Conditions (CDP)
            if NETWORK_PROFILES[network_name]:
                cdp = context.new_cdp_session(context.pages[0] if context.pages else context.new_page())
                cdp.send('Network.emulateNetworkConditions', NETWORK_PROFILES[network_name])
            
            page = context.new_page()
            
            # 4. Metrics Setup
            api_latency = 0
            api_called = 0
            total_size_bytes = 0
            
            def handle_response(response):
                nonlocal api_latency, api_called, total_size_bytes
                
                # Check for API calls (customize path if needed)
                if "/api/products" in response.url:
                    api_called = 1
                    # Approximate latency from timing
                    timing = response.request.timing
                    if timing:
                        # end - start approx latency
                        # Playwright timing: startTime, domainLookupStart, etc.
                        # responseEnd - responseStart is download. 
                        # responseStart - requestStart is TTFB (latency).
                        # Let's use simplified: response received timestamp - request timestamp? 
                        # response.timing is detailed.
                        # responseStart - startTime is mostly latency + server proc.
                         if timing.get('responseStart') and timing.get('requestStart'):
                             api_latency = max(0, timing['responseStart'] - timing['requestStart'])
                
                # Sum body size
                try:
                    s = int(response.header_value("content-length") or 0)
                    total_size_bytes += s
                except:
                    pass

            page.on("response", handle_response)
            
            # 5. Navigate
            start_time = time.time()
            try:
                page.goto(url, wait_until='networkidle')
            except Exception as e:
                print(f"❌ Error loading {url}: {e}")
                context.close()
                continue
                
            # 6. Collect Metrics
            # Page Load
            # Using Navigation Timing API for precision
            nav_timing = page.evaluate("() => JSON.stringify(window.performance.timing)")
            import json
            timings = json.loads(nav_timing)
            load_time = timings['loadEventEnd'] - timings['navigationStart']
            if load_time < 0: load_time = (time.time() - start_time) * 1000 # Fallback
            
            # LCP
            try:
                lcp = get_lcp(page)
            except:
                lcp = 0
            
            # Perceived
            perceived_load = load_time + api_latency if api_called else load_time
            
            # API Latency Handling
            # Dataset expects empty or value. "Capture 0 or NaN if the page has no API call"
            # But we are putting it into a DataFrame that likely expects floats.
            # Thesis dataset has 0 or empty. Our training script fills with 0.
            # Validation request: "Capture 0 or NaN".
            final_api_latency = api_latency if api_called else None # will be NaN in pandas
            
            # 7. Record Row
            row = {
                'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'Page_Name': page_def['name'],
                'Network_Type': network_name,
                'Page_Load_Time_ms': round(load_time, 2),
                'Perceived_Load_Time_ms': round(perceived_load, 2),
                'LCP_ms': round(float(lcp), 2),
                'API_Latency_ms': round(api_latency, 2) if api_called else None,
                'API_Measured': api_called,
                'Total_Page_Size_KB': round(total_size_bytes / 1024, 2),
                'Scenario': 'live_validation',
                'Commit_ID': 'live',
                'Is_Regression': 0
            }
            
            data.append(row)
            print(f"[{i+1}/{TOTAL_SAMPLES}] {page_def['name']} ({network_name}): Load={row['Page_Load_Time_ms']}ms, LCP={row['LCP_ms']}ms")
            
            context.close()
        
        browser.close()
        
    # Save
    df = pd.DataFrame(data, columns=COLUMNS)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\n✅ Validation data saved to: {OUTPUT_PATH}")
    print(df.describe())

if __name__ == "__main__":
    import sys
    # Simple arg parsing: python script.py [filename] [is_regression_run]
    if len(sys.argv) > 1:
        OUTPUT_PATH = sys.argv[1]
    
    # Optional: Logic to override labels if we know this is a regression run
    # For now, we'll let the merging step handle the explicit labeling to keep this script simple 
    # or we can pass a flag.
    # Let's keep it simple: Record metrics as is. We will post-process usage.
    
    measure_performance()
