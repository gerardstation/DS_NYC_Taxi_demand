from pathlib import Path
import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(page_title="NYC Taxi Demand", layout="wide")

DATA_PROCESSED = Path("data/processed")
DATA_RAW = Path("data/raw")
REPORTS = Path("reports")


def infer_months():
    months = []
    for p in DATA_PROCESSED.glob("lgbm_pred_*.parquet"):
        months.append(p.stem.replace("lgbm_pred_", ""))
    months = sorted(set(months))
    return months if months else ["2024-01"]


@st.cache_data
def load_zones():
    path = DATA_RAW / "taxi_zone_lookup.csv"
    df = pd.read_csv(path)
    df = df.rename(columns={"LocationID": "zone_id", "Zone": "zone_name"})
    return df


@st.cache_data
def load_preds(month: str):
    path = DATA_PROCESSED / f"lgbm_pred_{month}.parquet"
    if not path.exists():
        st.error(f"No existe {path}. Ejecuta antes: python src/models/train_lightgbm.py")
        st.stop()

    df = pd.read_parquet(path)

    needed = {"datetime_hour", "zone_id", "pickups", "pred"}
    missing = needed - set(df.columns)
    if missing:
        st.error(f"Faltan columnas en pred parquet: {missing}. Columnas: {list(df.columns)}")
        st.stop()

    df["datetime_hour"] = pd.to_datetime(df["datetime_hour"])
    return df.sort_values(["zone_id", "datetime_hour"]).reset_index(drop=True)


@st.cache_data
def load_errors(month: str):
    z_path = REPORTS / f"errors_by_zone_{month}.csv"
    h_path = REPORTS / f"errors_by_hour_{month}.csv"
    z = pd.read_csv(z_path) if z_path.exists() else None
    h = pd.read_csv(h_path) if h_path.exists() else None
    return z, h


def mae_rmse(y_true, y_pred):
    mae = (y_true - y_pred).abs().mean()
    rmse = ((y_true - y_pred) ** 2).mean() ** 0.5
    return float(mae), float(rmse)


st.title("DS NYC Taxi Demand Forecasting")

months = infer_months()
month = st.sidebar.selectbox("Month", months, index=0)

zones_lookup = load_zones()
preds = load_preds(month)
errors_zone, errors_hour = load_errors(month)

# --- merge nombre zona (robusto) ---
preds = preds.merge(
    zones_lookup[["zone_id", "Borough", "zone_name", "service_zone"]],
    on="zone_id",
    how="left",
    suffixes=("", "_lk"),
)


if "zone_name" not in preds.columns:
    for cand in ["zone_name_lk", "zone_name_x", "zone_name_y", "Zone", "zone"]:
        if cand in preds.columns:
            preds["zone_name"] = preds[cand]
            break

if "Borough" not in preds.columns:
    for cand in ["Borough_lk", "Borough_x", "Borough_y", "borough"]:
        if cand in preds.columns:
            preds["Borough"] = preds[cand]
            break

# (Opcional) debug de rango temporal 
# st.sidebar.write("min dt:", preds["datetime_hour"].min(), "max dt:", preds["datetime_hour"].max())

# Sidebar: seleccionar zona
zone_options = (
    preds[["zone_id", "Borough", "zone_name"]]
    .drop_duplicates()
    .sort_values(["Borough", "zone_name"])
)

zone_label_map = {
    int(r.zone_id): f"{int(r.zone_id)} — {r.Borough} — {r.zone_name}"
    for _, r in zone_options.iterrows()
}

selected_zone = st.sidebar.selectbox(
    "Zone",
    options=list(zone_label_map.keys()),
    format_func=lambda z: zone_label_map[z],
)

dfz = preds[preds["zone_id"] == selected_zone].copy()

# KPIs
overall_mae, overall_rmse = mae_rmse(preds["pickups"], preds["pred"])
zone_mae, zone_rmse = mae_rmse(dfz["pickups"], dfz["pred"])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Overall MAE", f"{overall_mae:.3f}")
c2.metric("Overall RMSE", f"{overall_rmse:.3f}")
c3.metric("Zone MAE", f"{zone_mae:.3f}")
c4.metric("Zone RMSE", f"{zone_rmse:.3f}")

st.subheader("Actual vs Predicted (hourly)")

# Eje X: mostrar día + hora para evitar “06 AM / 06 PM” repetido sin fecha
x_axis = alt.Axis(format="%d %b %H:%M", labelAngle=-45, tickCount=10)

chart = (
    alt.Chart(dfz)
    .transform_fold(["pickups", "pred"], as_=["series", "value"])
    .mark_line()
    .encode(
        x=alt.X("datetime_hour:T", title="Datetime (hour)", axis=x_axis),
        y=alt.Y("value:Q", title="Pickups"),
        color=alt.Color("series:N", title=""),
        tooltip=[
            alt.Tooltip("datetime_hour:T", title="Datetime"),
            alt.Tooltip("series:N", title="Series"),
            alt.Tooltip("value:Q", title="Value", format=",.2f"),
        ],
    )
    .properties(height=320)
)

st.altair_chart(chart, width="stretch")

st.subheader("Error analysis")
colA, colB = st.columns(2)

with colA:
    st.markdown("### Top zones by MAE (test)")
    if errors_zone is not None:
        top = errors_zone.sort_values("mae", ascending=False).head(15)
        st.dataframe(top, width="stretch")
    else:
        st.info("No encuentro reports/errors_by_zone_*.csv. Ejecuta evaluate_errors_by_zone.py")

with colB:
    st.markdown("### Worst (day_of_week, hour) by MAE")
    if errors_hour is not None:
        worst = errors_hour.sort_values("mae", ascending=False).head(15)
        st.dataframe(worst, width="stretch")
    else:
        st.info("No encuentro reports/errors_by_hour_*.csv. Ejecuta evaluate_errors_by_zone.py")

