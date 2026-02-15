# DS NYC Taxi Demand Forecasting

Forecasting **hourly taxi demand (pickups)** per NYC taxi zone using the TLC Yellow Taxi dataset.  
The project builds a clean ETL + feature engineering pipeline, trains a **LightGBM** model, evaluates errors by zone/time, and exposes results through a **Streamlit dashboard**.

---

## Objective

Predict the number of **pickups per zone and hour** for a given month (example: **2024-01**), and understand:
- Which zones are hardest to predict (airports, Midtown, etc.)
- Which time segments create larger errors (weekend nights, peaks, etc.)

---

## Data

Source (NYC TLC):
- `yellow_tripdata_YYYY-MM.parquet` (trip-level records)
- `taxi_zone_lookup.csv` (zone dictionary)

This repository expects:
- Raw data in: `data/raw/`
- Processed outputs in: `data/processed/`
- Reports in: `reports/`

---

## Pipeline (ETL → Features → Train → Evaluate)

### 1) ETL (trip-level → hourly demand)
- Loads the trip dataset
- Aggregates to: **(zone_id, datetime_hour) → pickups**
- Saves: `data/processed/pickups_zone_hour_YYYY-MM.parquet`

### 2) Feature Engineering
Creates time-series features per zone:
- Calendar features: `hour`, `day_of_week`, `is_weekend`, `hour_of_week`
- Lags: `lag_1`, `lag_2`, `lag_24`, `lag_168`
- Rolling means (no leakage): `roll_mean_3`, `roll_mean_6`, `roll_mean_24`, `roll_mean_168`
- Flags for availability of weekly history:
  - `has_lag_168`, `has_roll_168`

Saves: `data/processed/features_zone_hour_YYYY-MM.parquet`

### 3) Train (LightGBM)
- Time-based split: last **7 days** as test
- Model: LightGBM Regressor
- Saves:
  - Model: `models/lgbm_YYYY-MM.txt`
  - Predictions: `data/processed/lgbm_pred_YYYY-MM.parquet`
  - Report: `reports/lgbm_report_YYYY-MM.md`

### 4) Evaluate (credibility / insights)
Computes:
- Overall metrics: MAE, RMSE
- Errors by zone (Top MAE zones, relative error)
- Worst time segments (day_of_week, hour)

Saves:
- `reports/errors_by_zone_YYYY-MM.md`
- `reports/errors_by_zone_YYYY-MM.csv`
- `reports/errors_by_hour_YYYY-MM.csv`

### 5) Dashboard (Streamlit)
Interactive UI:
- Select month & zone
- View actual vs predicted series
- View error tables (worst zones & worst time segments)

---

## Results (example: 2024-01)

Overall performance (test period):
- **MAE:** 6.179  
- **RMSE:** 13.431

Typical failure patterns:
- High-volume and volatile zones (airports / Midtown) show higher MAE
- Weekend night segments tend to produce larger errors due to spikes
- Low-demand zones can have high *relative* error even with low absolute MAE

(See reports in `reports/`.)

---

## How to Run

### 0) Environment
Create/activate conda environment:

```bash
conda env create -f environment.yml
conda activate nyc_taxi
