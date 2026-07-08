"""
Real-Time Monitoring Page — AirSense
Live charts for all four sensor metrics with auto-refresh.
"""
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from config.settings import REFRESH_INTERVAL_SECONDS
from services.sensor_service import get_latest_reading, get_readings_dataframe, get_all_device_ids
from components.sidebar import render_sidebar
from components.cards import render_metric_card
from components.charts import create_line_chart
from utils.helper import format_datetime, now_wib

# ── Auto-refresh ─────────────────────────────────────────────────────────
st_autorefresh(
    interval=REFRESH_INTERVAL_SECONDS * 1000,
    limit=None,
    key="monitoring_autorefresh",
)

# ── Sidebar ──────────────────────────────────────────────────────────────
device_ids = get_all_device_ids()
selected_device = render_sidebar(device_ids, st.session_state.get("selected_device", device_ids[0] if device_ids else None))
st.session_state.selected_device = selected_device

# ── Current Status (metric cards) ────────────────────────────────────────
reading = get_latest_reading(selected_device) if selected_device else None

if reading is None:
    st.info("📭 No live data available for this device.")
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
        <span style="font-size:2rem;">📡</span>
        <div>
            <h1 style="margin:0; font-size:1.75rem; font-weight:700;">Real-Time Monitoring</h1>
            <p style="margin:0; color:#8b949e; font-size:0.88rem;">
                Device <b>{selected_device}</b> · {status_html}
            </p>
        </div>
    </div>
    """.replace('\n', ' '),
    unsafe_allow_html=True,
)

st.divider()

c1, c2, c3, c4 = st.columns(4)
with c1:
    render_metric_card("ISPU", reading.get("ispu_final", "-"), "", "🌡️",
                       color=reading.get("category", {}).get("color"))
with c2:
    render_metric_card("PM10", reading.get("pm10", "-"), "µg/m³", "💨")
with c3:
    render_metric_card("CO", reading.get("co", "-"), "ppm", "🏭")
with c4:
    render_metric_card("Temperature", reading.get("temperature", "-"), "°C", "🌡️")

st.write("")

# ── Live Charts (last 120 readings ≈ 2 hours) ────────────────────────────
st.markdown("### 📊 Sensor Trends (Last ~2 Hours)")

df = get_readings_dataframe(selected_device)

if df is not None and not df.empty:
    df_recent = df.tail(120).copy()

    col_a, col_b = st.columns(2)

    with col_a:
        if "pm10" in df_recent.columns:
            fig = create_line_chart(
                df_recent, x_col="timestamp", y_cols=["pm10"],
                title="PM10 Concentration", y_label="µg/m³",
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        if "co" in df_recent.columns:
            fig = create_line_chart(
                df_recent, x_col="timestamp", y_cols=["co"],
                title="CO Concentration", y_label="ppm",
            )
            st.plotly_chart(fig, use_container_width=True)

    col_c, col_d = st.columns(2)

    with col_c:
        if "temperature" in df_recent.columns:
            fig = create_line_chart(
                df_recent, x_col="timestamp", y_cols=["temperature"],
                title="Temperature", y_label="°C",
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_d:
        if "humidity" in df_recent.columns:
            fig = create_line_chart(
                df_recent, x_col="timestamp", y_cols=["humidity"],
                title="Humidity", y_label="%",
            )
            st.plotly_chart(fig, use_container_width=True)
else:
    st.info("📊 Waiting for sensor data…")
