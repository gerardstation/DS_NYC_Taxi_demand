from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")
OUT_DIR = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

MONTH = "2024-01"

TRIPS_PATH = RAW_DIR / f"yellow_tripdata_{MONTH}.parquet"
ZONES_PATH = RAW_DIR / "taxi_zone_lookup.csv"
OUT_PATH = OUT_DIR / f"pickups_zone_hour_{MONTH}.parquet"

def main():
    print("[load] trips:", TRIPS_PATH)
    trips = pd.read_parquet(TRIPS_PATH)

    print("[load] zones:", ZONES_PATH)
    zones = pd.read_csv(ZONES_PATH)

    # --- EDA mínima (para saber qué tenemos) ---
    print("[eda] rows:", len(trips), "cols:", trips.shape[1])
    print("[eda] columns:", list(trips.columns))

    # Columnas esperadas en Yellow Taxi:
    # tpep_pickup_datetime, tpep_dropoff_datetime, PULocationID, trip_distance
    trips["tpep_pickup_datetime"] = pd.to_datetime(trips["tpep_pickup_datetime"], errors="coerce")
    trips["tpep_dropoff_datetime"] = pd.to_datetime(trips["tpep_dropoff_datetime"], errors="coerce")

    # Duración en minutos (para filtrar)
    duration_min = (trips["tpep_dropoff_datetime"] - trips["tpep_pickup_datetime"]).dt.total_seconds() / 60.0
    trips = trips.assign(duration_min=duration_min)

    # --- Limpieza mínima ---
    before = len(trips)
    trips = trips.dropna(subset=["tpep_pickup_datetime", "tpep_dropoff_datetime", "PULocationID"])
    trips = trips[(trips["duration_min"] > 0) & (trips["duration_min"] < 240)]  # 0-4h
    trips = trips[trips["trip_distance"] > 0]
    after = len(trips)
    print(f"[clean] kept {after}/{before} rows ({after/before:.1%})")

    # --- Agregación por hora ---
    trips["datetime_hour"] = trips["tpep_pickup_datetime"].dt.floor("h")
    pickups = (
        trips.groupby(["PULocationID", "datetime_hour"])
             .size()
             .reset_index(name="pickups")
             .rename(columns={"PULocationID": "zone_id"})
    )

    # Join con lookup para borough/zone
    zones = zones.rename(columns={"LocationID": "zone_id", "Zone": "zone_name"})
    pickups = pickups.merge(zones[["zone_id", "Borough", "zone_name"]], on="zone_id", how="left")
    pickups = pickups.rename(columns={"Borough": "borough"})

    print("[result] rows:", len(pickups), "unique zones:", pickups["zone_id"].nunique())
    print("[save]", OUT_PATH)
    pickups.to_parquet(OUT_PATH, index=False)

    # Guardamos una nota rápida de EDA
    notes_path = Path("reports/eda_notes.md")
    notes_path.parent.mkdir(parents=True, exist_ok=True)
    with open(notes_path, "w", encoding="utf-8") as f:
        f.write(f"# EDA Notes ({MONTH})\n\n")
        f.write(f"- Raw rows: {before}\n")
        f.write(f"- Clean rows: {after}\n")
        f.write(f"- Aggregated rows (zone-hour): {len(pickups)}\n")
        f.write(f"- Unique zones: {pickups['zone_id'].nunique()}\n")
    print("[ok] wrote reports/eda_notes.md")

if __name__ == "__main__":
    main()
