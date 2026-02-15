from pathlib import Path
import pandas as pd

MONTH = "2024-01"

IN_PATH = Path("data/processed") / f"pickups_zone_hour_{MONTH}.parquet"
OUT_DIR = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / f"features_zone_hour_{MONTH}.parquet"

def main():
    df = pd.read_parquet(IN_PATH)

    # 1) Orden temporal por zona (imprescindible para lags)
    df["datetime_hour"] = pd.to_datetime(df["datetime_hour"])
    df = df.sort_values(["zone_id", "datetime_hour"]).reset_index(drop=True)

    # 2) Features de calendario (patrones diarios/semanales)
    df["hour"] = df["datetime_hour"].dt.hour
    df["day_of_week"] = df["datetime_hour"].dt.dayofweek
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["hour_of_week"] = df["day_of_week"] * 24 + df["hour"]

    # 3) Lags: memoria corta + estacionalidad diaria + estacionalidad semanal
    g = df.groupby("zone_id")["pickups"]
    df["lag_1"] = g.shift(1)
    df["lag_2"] = g.shift(2)
    df["lag_24"] = g.shift(24)
    df["lag_168"] = g.shift(168)  # 7 días * 24 horas

    # 4) Rolling means (siempre con shift(1) para no filtrar futuro)
    g_shift = g.shift(1)
    df["roll_mean_3"] = g_shift.rolling(3).mean().reset_index(level=0, drop=True)
    df["roll_mean_6"] = g_shift.rolling(6).mean().reset_index(level=0, drop=True)
    df["roll_mean_24"] = g_shift.rolling(24).mean().reset_index(level=0, drop=True)
    df["roll_mean_168"] = g_shift.rolling(168).mean().reset_index(level=0, drop=True)

    # 5) Quitamos filas sin historial suficiente (normal perder las primeras horas)

    # Indicadores (opcional, pero útil para que el modelo sepa si ya hay semana)
    df["has_lag_168"] = df["lag_168"].notna().astype(int)
    df["has_roll_168"] = df["roll_mean_168"].notna().astype(int)

    # Solo exigimos historial "básico" (NO forzamos semana)
    before = len(df)
    df_feat = df.dropna(
        subset=["lag_1", "lag_2", "lag_24", "roll_mean_24"]
    ).copy()
    after = len(df_feat)

    print(f"[features] kept {after}/{before} rows ({after/before:.1%})")

    df_feat.to_parquet(OUT_PATH, index=False)
    print("[save]", OUT_PATH)

if __name__ == "__main__":
    main()

