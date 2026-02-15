from pathlib import Path
import pandas as pd

MONTH = "2024-01"
DATA_PATH = Path("data/processed") / f"pickups_zone_hour_{MONTH}.parquet"
OUT_PATH = Path("data/processed") / f"baseline_pred_{MONTH}.parquet"
REPORT_PATH = Path("reports") / f"baseline_report_{MONTH}.md"

def main():
    df = pd.read_parquet(DATA_PATH).sort_values("datetime_hour")

    # Feature: hour_of_week (0-167)
    dt = pd.to_datetime(df["datetime_hour"])
    df["hour_of_week"] = dt.dt.dayofweek * 24 + dt.dt.hour

    # Split temporal: 75% train / 25% test (por orden temporal)
    split_idx = int(len(df) * 0.75)
    train = df.iloc[:split_idx].copy()
    test  = df.iloc[split_idx:].copy()

    # Baseline: media histórica por zona y hora_de_la_semana
    mean_table = (
        train.groupby(["zone_id", "hour_of_week"])["pickups"]
        .mean()
        .reset_index()
        .rename(columns={"pickups": "pred"})
    )

    test = test.merge(mean_table, on=["zone_id", "hour_of_week"], how="left")

    # Fallback si alguna combinación no existe en train
    zone_mean = train.groupby("zone_id")["pickups"].mean().rename("zone_mean")
    test = test.merge(zone_mean, on="zone_id", how="left")
    test["pred"] = test["pred"].fillna(test["zone_mean"])

    # Métricas
    mae = (test["pickups"] - test["pred"]).abs().mean()
    rmse = ((test["pickups"] - test["pred"]) ** 2).mean() ** 0.5

    # Guardar predicciones
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    test[["zone_id", "datetime_hour", "pickups", "pred"]].to_parquet(OUT_PATH, index=False)

    # Report
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    top_err = (
        test.assign(abs_err=(test["pickups"] - test["pred"]).abs())
        .groupby("zone_id")["abs_err"]
        .mean()
        .sort_values(ascending=False)
        .head(10)
    )

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(f"# Baseline report ({MONTH})\n\n")
        f.write(f"- MAE: {mae:.3f}\n")
        f.write(f"- RMSE: {rmse:.3f}\n\n")
        f.write("## Top 10 zones by mean absolute error\n\n")
        for zone_id, val in top_err.items():
            f.write(f"- zone_id {zone_id}: {val:.3f}\n")

    print("[ok] baseline saved:", OUT_PATH)
    print("[ok] report saved:", REPORT_PATH)
    print(f"[metrics] MAE={mae:.3f} RMSE={rmse:.3f}")

if __name__ == "__main__":
    main()
