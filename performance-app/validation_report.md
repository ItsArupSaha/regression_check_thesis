# Thesis Validation Report
**Date:** 2026-02-18 17:27

## 1. Dataset Summary
- **Total Samples:** 400
- **Healthy Samples (Class 0):** 347
- **Regression Samples (Class 1):** 53
- **Source:** Real-world validation (Playwright Live Test)
- **Scenario Breakdown:**
    - `baseline_validation`: 200
    - `baseline_validation_control`: 147
    - `api_delay_2s_validation`: 53

## 2. Methodology
- **Ground Truth Design:**
    - **Baseline:** Application running normally (no injected delays).
    - **Regression:** Application with injected 2s API delay on `Products` page.
- **Model Type:** Random Forest (V2)
- **Feature Engineering:** Relative Metrics (Deltas from Baseline Median)
- **Features Used:** `Page_Load_Time_Delta, Perceived_Load_Time_Delta, LCP_Delta, API_Latency_Delta, API_Measured, Total_Page_Size_KB, Network_Type, Page_Name`
- **Threshold:** 0.5 (Standard)

## 3. Results
### Performance Metrics
- **Accuracy:** 0.8475
- **Precision (Regression):** 0.3889
- **Recall (Regression):** 0.2642
- **F1-Score:** 0.3146

### Confusion Matrix
| | Predicted Healthy (0) | Predicted Regression (1) |
|---|---|---|
| **Actual Healthy (0)** | **325** (True Negative) | **22** (False Positive) |
| **Actual Regression (1)** | **39** (False Negative) | **14** (True Positive) |

- **False Positive Rate:** 0.0634
- **False Negative Rate:** 0.7358

## 4. Error Analysis
### False Positives (Predicted Regression, Actual Healthy) - N=22
Top 5 by Confidence:
| Page_Name   | Network_Type   |   API_Latency_Delta |   Regression_Prob |
|:------------|:---------------|--------------------:|------------------:|
| Homepage    | WiFi           |             2016.45 |          0.726667 |
| Homepage    | WiFi           |             2012.41 |          0.716667 |
| Homepage    | WiFi           |             2017.21 |          0.713333 |
| Homepage    | WiFi           |             2010.98 |          0.713333 |
| Homepage    | WiFi           |             2015.08 |          0.713333 |

### False Negatives (Predicted Healthy, Actual Regression) - N=39
Top 5 by Low Confidence (Missed):
| Page_Name   | Network_Type   |   API_Latency_Delta |   Regression_Prob |
|:------------|:---------------|--------------------:|------------------:|
| Products    | 3G             |             1825.84 |              0.25 |
| Products    | 3G             |             1831.51 |              0.25 |
| Products    | 3G             |             1831.76 |              0.25 |
| Products    | 3G             |             1839.29 |              0.25 |
| Products    | 3G             |             1830.41 |              0.25 |
