"""
Dashboard Page — AirSense
Overview with KPI cards, ISPU status, and quick trend charts.
"""
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from config.settings import APP_NAME, REFRESH_INTERVAL_SECONDS
from services.sensor_service import get_latest_reading, get_readings_dataframe, get_all_device_ids
from components.sidebar import render_sidebar
from components.cards import render_metric_card, render_ispu_card
from components.charts import create_line_chart
from utils.helper import format_datetime, now_wib

# ── Auto-refresh ─────────────────────────────────────────────────────────
st_autorefresh(
    interval=REFRESH_INTERVAL_SECONDS * 1000,
    limit=None,
    key="dashboard_autorefresh",
)

# ── Sidebar ──────────────────────────────────────────────────────────────
device_ids = get_all_device_ids()
selected_device = render_sidebar(device_ids, st.session_state.get("selected_device", device_ids[0] if device_ids else None))
st.session_state.selected_device = selected_device

# ── Latest Reading ───────────────────────────────────────────────────────
reading = get_latest_reading(selected_device) if selected_device else None

if reading is None:
    st.info("📭 No data available for this device yet. Check back soon or verify the device is sending data.")
    st.stop()

# Check if data is outdated (older than 10 minutes)
from datetime import timedelta
data_ts = reading.get("timestamp")
is_outdated = False
if data_ts:
    time_diff = now_wib() - data_ts
    if time_diff > timedelta(minutes=10):
        is_outdated = True

data_time_str = format_datetime(data_ts) if data_ts else "Unknown"
status_html = f"<span style='color:#ef4444; font-weight:600;'>⚠️ Offline (Last data: {data_time_str})</span>" if is_outdated else f"<span style='color:#22c55e;'>🟢 Online (Updated: {data_time_str})</span>"

# ── Header ───────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
        <span style="font-size:2.2rem;">🌿</span>
        <div>
            <h1 style="margin:0; font-size:1.75rem; font-weight:700;">{APP_NAME} Dashboard</h1>
            <p style="margin:0; color:#8b949e; font-size:0.88rem;">
                Device <b>{selected_device}</b> · {status_html}
            </p>
        </div>
    </div>
    """.replace('\n', ' '),
    unsafe_allow_html=True,
)

st.divider()

# ── KPI Metric Cards ────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    render_metric_card(
        title="ISPU Index",
        value=reading.get("ispu_final", "-"),
        unit="",
        icon="🌡️",
        color=reading.get("category", {}).get("color", "#3b82f6"),
    )
with c2:
    render_metric_card(
        title="PM10",
        value=reading.get("pm10", "-"),
        unit="µg/m³",
        icon="💨",
    )
with c3:
    co_val = reading.get("co", "-")
    if co_val in (1, 1.0, "1", "1.0"):
        co_display = "Baik"
        co_unit = ""
    elif co_val in (0, 0.0, "0", "0.0"):
        co_display = "Tidak Baik"
        co_unit = ""
    else:
        co_display = co_val
        co_unit = "ppm"

    render_metric_card(
        title="CO",
        value=co_display,
        unit=co_unit,
        icon="🏭",
    )
with c4:
    render_metric_card(
        title="Temperature",
        value=reading.get("temperature", "-"),
        unit="°C",
        icon="🌡️",
    )
with c5:
    render_metric_card(
        title="Humidity",
        value=reading.get("humidity", "-"),
        unit="%",
        icon="💧",
    )

st.write("")

# ── ISPU Status Card ────────────────────────────────────────────────────
category = reading.get("category", {})
render_ispu_card(reading.get("ispu_final", 0), category)

st.write("")

# ── Quick Trend Charts (last 60 readings ≈ 1 hour) ──────────────────────
st.markdown("### 📈 Last Hour Trend")

df = get_readings_dataframe(selected_device)

if df is not None and not df.empty:
    df_recent = df.tail(60).copy()

    col_left, col_right = st.columns(2)

    with col_left:
        if "pm10" in df_recent.columns and "timestamp" in df_recent.columns:
            fig_pm10 = create_line_chart(
                df_recent, x_col="timestamp", y_cols=["pm10"],
                title="PM10 (µg/m³) — Last Hour", y_label="µg/m³",
            )
            st.plotly_chart(fig_pm10, use_container_width=True)

    with col_right:
        if "co" in df_recent.columns and "timestamp" in df_recent.columns:
            fig_co = create_line_chart(
                df_recent, x_col="timestamp", y_cols=["co"],
                title="CO (ppm) — Last Hour", y_label="ppm",
            )
            st.plotly_chart(fig_co, use_container_width=True)
else:
    st.info("📊 No historical readings available yet to render trend charts.")
