import asyncio
import csv
import os
import sys
import random
import json
from datetime import datetime
from playwright.async_api import async_playwright

# Configuration
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test-config.json")
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "performance_dataset.csv")

import argparse

# Configuration
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test-config.json")
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "performance_dataset.csv")

# Constants
DEFAULT_URL = "http://localhost:3000"

# Network Profiles (using CDP emulation)
NETWORK_PROFILES = {
    "WiFi": {
        "offline": False,
        "downloadThroughput": -1,  # No throttling
        "uploadThroughput": -1,    # No throttling
        "latency": 0
    },
    "4G": {
        "offline": False,
        "downloadThroughput": 4 * 1024 * 1024 / 8,  # 4 Mbps
        "uploadThroughput": 3 * 1024 * 1024 / 8,    # 3 Mbps
        "latency": 20
    },
    "3G": {
        "offline": False,
        "downloadThroughput": 750 * 1024 / 8,       # 750 kbps
        "uploadThroughput": 250 * 1024 / 8,         # 250 kbps
        "latency": 100
    }
}

async def generate_dataset(scenario="baseline", commit="current", is_regression=0, loops=50, output_file="performance_dataset.csv"):
    if not os.path.exists(CONFIG_PATH):
        print(f"Error: Config file not found at {CONFIG_PATH}")
        sys.exit(1)

    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
    
    routes = config.get("routes", [])
    if not routes:
        print("Error: No routes found in config")
        sys.exit(1)

    # Prepare CSV file
    # Allow absolute paths or relative to script's parent dir
    if os.path.isabs(output_file):
        target_file = output_file
    else:
        target_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), output_file)
        
    file_exists = os.path.isfile(target_file)
    fieldnames = [
        "Timestamp", "Page_Name", "Network_Type", 
        "Page_Load_Time_ms", "LCP_ms", "API_Latency_ms", "Total_Page_Size_KB",
        "Scenario", "Commit_ID", "Is_Regression"
    ]
    
    with open(target_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        
    print(f"Starting dataset generation ({loops} iterations)...")
    print(f"Scenario: {scenario}, Commit: {commit}, Regression: {is_regression}")
    print(f"Output File: {target_file}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True) # Run headless for speed
        
        for i in range(1, loops + 1):
            # Random selection
            route = random.choice(routes)
            network_name = random.choice(list(NETWORK_PROFILES.keys()))
            network_conditions = NETWORK_PROFILES[network_name]
            
            full_url = f"{DEFAULT_URL.rstrip('/')}{route['url']}"
            
            print(f"Run {i}/{loops}: Testing {route['url']} on {network_name}...")
            
            # Create a new context for each iteration with strict cleaning options
            context = await browser.new_context(
                java_script_enabled=True,
                ignore_https_errors=True
            )
            
            # Clear cookies to prevent caching
            await context.clear_cookies()
            
            try:
                # Apply network throttling via CDP
                cdp_session = await context.new_cdp_session(context.pages[0] if context.pages else await context.new_page())
                await cdp_session.send("Network.emulateNetworkConditions", network_conditions)
                
                page = context.pages[0]
                
                # Metrics variables
                api_latency = 0
                page_size_bytes = 0
                
                # Helper to calculate metrics
                def handle_response(response):
                    nonlocal page_size_bytes, api_latency
                    try:
                        header_len = int(response.headers.get('content-length', 0))
                        page_size_bytes += header_len
                        if "/api/products" in response.url:
                            if response.request.timing:
                                 pass 
                    except Exception:
                        pass

                page.on("response", handle_response)
                
                await page.goto(full_url, wait_until="networkidle")
                
                # Capture metrics
                api_metrics = await page.evaluate(r"""() => {
                    const entries = performance.getEntriesByType('resource');
                    const apiEntry = entries.find(e => e.name.includes('/api/products'));
                    return apiEntry ? apiEntry.duration : 0;
                }""")
                
                lcp = await page.evaluate(r"""() => {
                    return new Promise((resolve) => {
                        new PerformanceObserver((entryList) => {
                            const entries = entryList.getEntries();
                            const lastEntry = entries[entries.length - 1];
                            resolve(lastEntry.startTime);
                        }).observe({ type: 'largest-contentful-paint', buffered: true });
                        setTimeout(() => resolve(0), 2000);
                    });
                }""")
                
                nav_metrics = await page.evaluate(r"""() => {
                    const nav = performance.getEntriesByType('navigation')[0];
                    return {
                        loadTime: nav.loadEventEnd - nav.startTime,
                        transferSize: nav.transferSize
                    };
                }""")
                
                total_size = await page.evaluate(r"""() => {
                    const resources = performance.getEntriesByType('resource');
                    let size = 0;
                    for (const r of resources) {
                        size += (r.transferSize || 0);
                    }
                    return size;
                }""")
                
                total_page_size_kb = (total_size + (nav_metrics['transferSize'] or 0)) / 1024
                
                # Consolidate results
                result = {
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Page_Name": route['name'],
                    "Network_Type": network_name,
                    "Page_Load_Time_ms": round(nav_metrics['loadTime'], 2),
                    "LCP_ms": round(lcp, 2),
                    "API_Latency_ms": round(api_metrics, 2),
                    "Total_Page_Size_KB": round(total_page_size_kb, 2),
                    "Scenario": scenario,
                    "Commit_ID": commit,
                    "Is_Regression": is_regression
                }
                
                # Save to CSV immediately
                with open(target_file, 'a', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerow(result)
                    
            except Exception as e:
                print(f"Error measuring {route['url']} on {network_name}: {e}")
            finally:
                await context.close()
        
        await browser.close()
        print(f"✅ Dataset generation complete! Saved to {target_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate performance dataset with labeling")
    parser.add_argument("--scenario", default="baseline", help="Scenario label (e.g., baseline, regression)")
    parser.add_argument("--commit", default="current", help="Commit ID/Tag")
    parser.add_argument("--regression", type=int, default=0, help="1 if regression, 0 if healthy")
    parser.add_argument("--loops", type=int, default=50, help="Number of iterations")
    parser.add_argument("--output", default="performance_dataset.csv", help="Output CSV filename")
    
    args = parser.parse_args()
    
    asyncio.run(generate_dataset(
        scenario=args.scenario,
        commit=args.commit,
        is_regression=args.regression,
        loops=args.loops,
        output_file=args.output
    ))
