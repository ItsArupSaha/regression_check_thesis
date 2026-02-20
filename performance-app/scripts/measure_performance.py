import asyncio
import os
import sys
import argparse
from datetime import datetime
from playwright.async_api import async_playwright

# Configuration
DEFAULT_URL = "http://localhost:3000"
MAX_API_LATENCY_MS = 200

# Determine the absolute path for the output file
# Script is in /scripts, we want the file in the parent directory (root of performance-app)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)

async def measure_performance(url, show_ui=False, commit_id="manual"):
    # Lock File Mechanism
    LOCK_FILE = os.path.join(SCRIPT_DIR, "performance_test.lock")
    
    if os.path.exists(LOCK_FILE):
        print("⚠️ A performance test is already running. Please wait.")
        sys.exit(1)
        
    # Create lock file
    with open(LOCK_FILE, 'w') as f:
        f.write("running")
        
    try:
        print(f"Starting measurement for {url}...")
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=not show_ui)
            context = await browser.new_context()
            page = await context.new_page()

            # variables to store metrics
            api_latency = 0
            page_size_bytes = 0
            
            # Listen for responses to calculate page size and specific API latency
            def handle_response(response):
                nonlocal page_size_bytes, api_latency
                try:
                    # Sum up transfer size if available (approximation)
                    # Note: This might not be 100% accurate for all resources due to caching/headers
                    header_len = int(response.headers.get('content-length', 0))
                    page_size_bytes += header_len
                    
                    if "/api/products" in response.url:
                        # Calculate latency for this specific API
                        timing = response.request.timing
                        if timing:
                             pass
                except Exception:
                    pass

            page.on("response", handle_response)
            
            try:
                # Navigate and wait for network idle to ensure most resources are loaded
                start_time = datetime.now()
                await page.goto(url, wait_until="networkidle")
                
                # --- Measure API Latency via Performance API (More Accurate) ---
                api_metrics = await page.evaluate(r"""() => {
                    const entries = performance.getEntriesByType('resource');
                    const apiEntry = entries.find(e => e.name.includes('/api/products'));
                    return apiEntry ? apiEntry.duration : 0;
                }""")
                
                # --- Measure LCP ---
                lcp = await page.evaluate(r"""() => {
                    return new Promise((resolve) => {
                        new PerformanceObserver((entryList) => {
                            const entries = entryList.getEntries();
                            const lastEntry = entries[entries.length - 1];
                            resolve(lastEntry.startTime);
                        }).observe({ type: 'largest-contentful-paint', buffered: true });
                        
                        // Fallback if no LCP event fires in 2 seconds
                        setTimeout(() => resolve(0), 2000);
                    });
                }""")
                
                # --- Measure TTFB and Page Load Time ---
                nav_metrics = await page.evaluate(r"""() => {
                    const nav = performance.getEntriesByType('navigation')[0];
                    return {
                        ttfb: nav.responseStart - nav.requestStart,
                        loadTime: nav.loadEventEnd - nav.startTime,
                        transferSize: nav.transferSize // Main doc size
                    };
                }""")
                
                # --- Measure Total Page Size (Resource Timing API) ---
                total_size = await page.evaluate(r"""() => {
                    const resources = performance.getEntriesByType('resource');
                    let size = 0;
                    for (const r of resources) {
                        size += (r.transferSize || 0);
                    }
                    return size;
                }""")
                
                # Combine main document transfer size
                total_page_size_kb = (total_size + (nav_metrics['transferSize'] or 0)) / 1024

                results = {
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Commit_ID": commit_id,
                    "Page_Load_Time_ms": round(nav_metrics['loadTime'], 2),
                    "LCP_ms": round(lcp, 2),
                    "TTFB_ms": round(nav_metrics['ttfb'], 2),
                    "Total_Page_Size_KB": round(total_page_size_kb, 2),
                    "API_Latency_ms": round(api_metrics, 2)
                }

                print(f"Captured results: {results}")
                
                # --- Quality Gate Check ---
                if results["API_Latency_ms"] > MAX_API_LATENCY_MS:
                    print(f"❌ PERFORMANCE REGRESSION DETECTED! API Latency is {results['API_Latency_ms']}ms (Limit: {MAX_API_LATENCY_MS}ms).")
                    sys.exit(1)
                else:
                    print("✅ Performance check passed.")
                    sys.exit(0)

            except SystemExit:
                raise # Re-raise SystemExit to ensure proper exit code
            except Exception as e:
                print(f"Error measuring performance: {e}")
            finally:
                await browser.close()
    finally:
        # cleanup lock file
        if os.path.exists(LOCK_FILE):
            try:
                os.remove(LOCK_FILE)
            except Exception as e:
                print(f"Warning: Could not remove lock file: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Measure web app performance")
    parser.add_argument("--url", default=DEFAULT_URL, help="Target URL")
    parser.add_argument("--headed", action="store_true", help="Run in headed mode")
    parser.add_argument("--commit", default="manual", help="Commit ID tag")
    
    args = parser.parse_args()
    
    asyncio.run(measure_performance(args.url, args.headed, args.commit))