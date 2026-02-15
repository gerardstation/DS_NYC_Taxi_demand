from pathlib import Path
import pandas as pd
from lightgbm import LGBMRegressor

MONTH = "2024-01"

DATA_PATH = Path("data/processed") / f"features_zone_hour_{MONTH}.parquet"
REPORT_PATH = Path("reports") / f"lgbm_report_{MONTH}.md"
MODEL_PATH = Path("models") / f"lgbm_{MONTH}.txt"
PRED_PATH = Path("data/processed") / f"lgbm_pred_{MONTH}.parquet"

FEATURES = [
    "zone_id",
    "hour", "day_of_week", "is_weekend", "hour_of_week",
    "lag_1", "lag_2", "lag_24", "lag_168",
    "roll_mean_3", "roll_mean_6", "roll_mean_24", "roll_mean_168",
    "has_lag_168", "has_roll_168"
]

TARGET = "pickups"

def main():
    df = pd.read_parquet(DATA_PATH).sort_values("datetime_hour")

    max_dt = df["datetime_hour"].max()
    cutoff = max_dt - pd.Timedelta(days=7)

    train = df[df["datetime_hour"] < cutoff].copy()
    test = df[df["datetime_hour"] >= cutoff].copy()

    print("[split] train max dt:", train["datetime_hour"].max())
    print("[split] test min dt:", test["datetime_hour"].min())
    print("[split] sizes:", len(train), len(test))


    train["zone_id"] = train["zone_id"].astype("category")
    test["zone_id"] = test["zone_id"].astype("category")

    X_train = train[FEATURES]
    y_train = train[TARGET]
    X_test = test[FEATURES]
    y_test = test[TARGET]

    # Modelo
    model = LGBMRegressor(
        n_estimators=800,
        learning_rate=0.05,
        num_leaves=64,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X_train, y_train)

    # Predicción y métricas
    test["pred"] = model.predict(X_test)
    mae = (y_test - test["pred"]).abs().mean()
    rmse = ((y_test - test["pred"]) ** 2).mean() ** 0.5

    # Guardar predicciones 
    PRED_PATH.parent.mkdir(parents=True, exist_ok=True)

    cols = ["zone_id", "datetime_hour", "pickups", "pred"]
    # Si existen, añadimos info descriptiva
    for extra in ["borough", "zone_name"]:
        if extra in test.columns:
            cols.insert(1, extra)

    test_out = test[cols].copy()
    test_out.to_parquet(PRED_PATH, index=False)
    print("[ok] predictions saved:", PRED_PATH)

    # Feature importances
    fi = pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=False)

    # Guardar modelo (formato LightGBM)
    Path("models").mkdir(parents=True, exist_ok=True)
    model.booster_.save_model(MODEL_PATH.as_posix())

    # Guardar reporte
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(f"# LightGBM report ({MONTH})\n\n")
        f.write(f"- MAE: {mae:.3f}\n")
        f.write(f"- RMSE: {rmse:.3f}\n\n")
        f.write("## Feature importance\n\n")
        for k, v in fi.items():
            f.write(f"- {k}: {int(v)}\n")

    print("[metrics] MAE=", round(mae, 3), " RMSE=", round(rmse, 3))
    print("[ok] model saved:", MODEL_PATH)
    print("[ok] report saved:", REPORT_PATH)

if __name__ == "__main__":
    main()
