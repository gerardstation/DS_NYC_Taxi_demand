from pathlib import Path
import pandas as pd
import numpy as np

MONTH = "2024-01"

PRED_PATH = Path("data/processed") / f"lgbm_pred_{MONTH}.parquet"
ZONES_PATH = Path("data/raw") / "taxi_zone_lookup.csv"

OUT_DIR = Path("reports")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_CSV = OUT_DIR / f"errors_by_zone_{MONTH}.csv"
OUT_MD = OUT_DIR / f"errors_by_zone_{MONTH}.md"
OUT_HOUR_CSV = OUT_DIR / f"errors_by_hour_{MONTH}.csv"

def pick_column(df, candidates, label):
    for c in candidates:
        if c in df.columns:
            return c
    raise KeyError(f"No encuentro columna para {label}. Busqué: {candidates}. Columnas: {list(df.columns)}")

def main():
    # 1) Cargar predicciones (por qué: es el “resultado final” del modelo en test)
    if not PRED_PATH.exists():
        raise FileNotFoundError(f"No existe: {PRED_PATH}")

    df = pd.read_parquet(PRED_PATH)

    # Normalizamos nombres 
    if "zone_id" not in df.columns and "PULocationID" in df.columns:
        df = df.rename(columns={"PULocationID": "zone_id"})

    y_col = pick_column(df, ["pickups", "y_true", "actual", "target"], "valor real (pickups)")
    p_col = pick_column(df, ["pred", "y_pred", "prediction"], "predicción")

    if "datetime_hour" in df.columns:
        df["datetime_hour"] = pd.to_datetime(df["datetime_hour"], errors="coerce")

    df = df.dropna(subset=["zone_id", y_col, p_col]).copy()
    df["zone_id"] = df["zone_id"].astype(int)

    # 2) Calcular errores (por qué: con MAE/RMSE detectas volumen vs outliers)
    df["abs_err"] = (df[y_col] - df[p_col]).abs()
    df["sq_err"] = (df[y_col] - df[p_col]) ** 2

    overall_mae = df["abs_err"].mean()
    overall_rmse = np.sqrt(df["sq_err"].mean())

    # 3) Enriquecer con nombres de zona (por qué: el reporte tiene que “hablar humano”)
    zones = pd.read_csv(ZONES_PATH)
    zones = zones.rename(columns={"LocationID": "zone_id", "Borough": "borough", "Zone": "zone_name"})
    zones = zones[["zone_id", "borough", "zone_name", "service_zone"]].drop_duplicates()

    # 4) Errores por zona (por qué: ranking de “puntos débiles” del modelo)
    by_zone = (
        df.groupby("zone_id")
          .agg(
              n=("abs_err", "size"),
              mae=("abs_err", "mean"),
              rmse=("sq_err", lambda s: float(np.sqrt(s.mean()))),
              avg_pickups=(y_col, "mean"),
              p95_pickups=(y_col, lambda s: float(np.quantile(s, 0.95))),
          )
          .reset_index()
          .merge(zones, on="zone_id", how="left")
    )

    # Métrica relativa (por qué: zonas de baja demanda pueden “parecer fáciles” en MAE absoluto)
    by_zone["mae_perc_of_avg"] = (by_zone["mae"] / by_zone["avg_pickups"].replace(0, np.nan)).fillna(np.inf)

    by_zone = by_zone.sort_values("mae", ascending=False)
    by_zone.to_csv(OUT_CSV, index=False)

    # 5) Error por hora/día (por qué: descubrir patrones temporales)
    if "datetime_hour" in df.columns and df["datetime_hour"].notna().any():
        df["hour"] = df["datetime_hour"].dt.hour
        df["day_of_week"] = df["datetime_hour"].dt.dayofweek
        by_hour = (
            df.groupby(["day_of_week", "hour"])
              .agg(n=("abs_err", "size"), mae=("abs_err", "mean"), rmse=("sq_err", lambda s: float(np.sqrt(s.mean()))))
              .reset_index()
              .sort_values("mae", ascending=False)
        )
        by_hour.to_csv(OUT_HOUR_CSV, index=False)
    else:
        by_hour = None

    # 6) Escribir reporte MD 
    top15 = by_zone.head(15).copy()

    def md_table(df_in):
        # tabla simple en markdown
        cols = ["zone_id", "borough", "zone_name", "n", "mae", "rmse", "avg_pickups", "p95_pickups"]
        t = df_in[cols].copy()
        t["mae"] = t["mae"].map(lambda x: f"{x:.3f}")
        t["rmse"] = t["rmse"].map(lambda x: f"{x:.3f}")
        t["avg_pickups"] = t["avg_pickups"].map(lambda x: f"{x:.2f}")
        t["p95_pickups"] = t["p95_pickups"].map(lambda x: f"{x:.2f}")
        return t.to_markdown(index=False)

    worst_relative = by_zone.replace([np.inf, -np.inf], np.nan).dropna(subset=["mae_perc_of_avg"])
    worst_relative = worst_relative.sort_values("mae_perc_of_avg", ascending=False).head(10)

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(f"# Errors by zone ({MONTH})\n\n")
        f.write("This report ranks zones by error on the test predictions.\n\n")
        f.write(f"**Overall metrics**\n\n- MAE: {overall_mae:.3f}\n- RMSE: {overall_rmse:.3f}\n\n")

        f.write("## Top 15 zones by MAE\n\n")
        f.write(md_table(top15) + "\n\n")

        f.write("## Zones with highest relative error (MAE / avg_pickups)\n\n")
        f.write("Useful to spot low-demand zones where a small absolute error is still big vs typical demand.\n\n")
        f.write(worst_relative[["zone_id","borough","zone_name","n","mae","avg_pickups","mae_perc_of_avg"]]
                .assign(
                    mae=lambda d: d["mae"].map(lambda x: f"{x:.3f}"),
                    avg_pickups=lambda d: d["avg_pickups"].map(lambda x: f"{x:.2f}"),
                    mae_perc_of_avg=lambda d: d["mae_perc_of_avg"].map(lambda x: f"{x:.2f}"),
                ).to_markdown(index=False) + "\n\n")

        if by_hour is not None:
            f.write("## Worst (day_of_week, hour) segments by MAE\n\n")
            f.write("day_of_week: 0=Mon ... 6=Sun\n\n")
            f.write(by_hour.head(15).to_markdown(index=False) + "\n\n")

        f.write("## Notes (how to explain it)\n\n")
        f.write("- High-MAE zones are often **high-volume and volatile** (airports, Midtown, Times Sq): spikes are harder.\n")
        f.write("- Relative error highlights **low-demand zones** where small absolute misses look fine but are large proportionally.\n")
        f.write("- Hour/day patterns can indicate **rush hours / weekend nightlife / weather sensitivity**.\n")

    print("[ok] zone report saved:", OUT_MD)
    print("[ok] zone csv saved:", OUT_CSV)
    if by_hour is not None:
        print("[ok] hour csv saved:", OUT_HOUR_CSV)
    print(f"[metrics] overall MAE={overall_mae:.3f} RMSE={overall_rmse:.3f}")

if __name__ == "__main__":
    main()
