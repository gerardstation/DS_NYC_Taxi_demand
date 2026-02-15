from pathlib import Path
import pandas as pd

MONTH = "2024-01"

PRED_PATH = Path("data/processed") / f"lgbm_pred_{MONTH}.parquet"
OUT_MD = Path("reports") / f"errors_by_zone_{MONTH}.md"
OUT_CSV = Path("reports") / f"errors_by_zone_{MONTH}.csv"

def main():
    df = pd.read_parquet(PRED_PATH)

    df["abs_err"] = (df["pickups"] - df["pred"]).abs()
    df["sq_err"] = (df["pickups"] - df["pred"]) ** 2

    group_cols = ["zone_id"]
    
    for c in ["borough", "zone_name"]:
        if c in df.columns:
            group_cols.append(c)

    by_zone = (
        df.groupby(group_cols)
          .agg(
              n=("abs_err", "size"),
              mae=("abs_err", "mean"),
              rmse=("sq_err", lambda s: (s.mean()) ** 0.5),
              avg_pickups=("pickups", "mean"),
              p95_pickups=("pickups", lambda s: s.quantile(0.95)),
          )
          .reset_index()
          .sort_values("mae", ascending=False)
    )

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    by_zone.to_csv(OUT_CSV, index=False)

    top = by_zone.head(15)

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(f"# Errors by zone ({MONTH})\n\n")
        f.write("This report ranks zones by mean absolute error (MAE) on the test period.\n\n")
        f.write("## Top 15 zones by MAE\n\n")
        f.write(top.to_string(index=False))
        f.write("\n")

    print("[ok] saved:", OUT_MD)
    print("[ok] saved:", OUT_CSV)

if __name__ == "__main__":
    main()
