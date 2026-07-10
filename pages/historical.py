"""
Historical Data Page — AirSense
Browse, chart, and export historical sensor readings.
"""
import streamlit as st
import pandas as pd
from datetime import timedelta

from services.sensor_service import get_readings_dataframe, get_all_device_ids
from components.sidebar import render_sidebar
from components.charts import create_line_chart
from components.tables import render_data_table
from utils.helper import now_wib, check_database_connection

# ── Connection check ─────────────────────────────────────────────────────
check_database_connection()

# ── Sidebar ──────────────────────────────────────────────────────────────
device_ids = get_all_device_ids()
selected_device = render_sidebar(device_ids, st.session_state.get("selected_device", device_ids[0] if device_ids else None))
st.session_state.selected_device = selected_device

# ── Header ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
        <span style="font-size:2rem;">📈</span>
        <div>
            <h1 style="margin:0; font-size:1.75rem; font-weight:700;">Historical Data</h1>
            <p style="margin:0; color:#8b949e; font-size:0.88rem;">
                Explore and export past sensor readings.
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# ── Date Range Picker ────────────────────────────────────────────────────
today = now_wib().date()
default_start = today - timedelta(days=7)

col_start, col_end = st.columns(2)
with col_start:
    start_date = st.date_input("📅 Start Date", value=default_start, key="hist_start")
with col_end:
    end_date = st.date_input("📅 End Date", value=today, key="hist_end")

if start_date > end_date:
    st.error("⚠️ Start date must be before or equal to end date.")
    st.stop()

st.write("")

# ── Fetch Data ───────────────────────────────────────────────────────────
with st.spinner("Loading historical data…"):
    df = get_readings_dataframe(selected_device, start_date=start_date, end_date=end_date)

if df is None or df.empty:
    st.info(
        f"📭 No readings found for **{selected_device}** between "
        f"**{start_date}** and **{end_date}**."
    )
    st.stop()

# ── Descriptive Statistics ───────────────────────────────────────────────
st.markdown("### 📐 Descriptive Statistics")

numeric_cols = [c for c in ["pm10", "co", "temperature", "humidity", "ispu_final"] if c in df.columns]
if numeric_cols:
    stats_df = df[numeric_cols].describe().round(2)
    st.dataframe(stats_df, use_container_width=True)

st.write("")

# ── Charts ───────────────────────────────────────────────────────────────
st.markdown("### 📊 Trend Charts")

chart_cols_left, chart_cols_right = st.columns(2)

with chart_cols_left:
    if "pm10" in df.columns and "timestamp" in df.columns:
        fig = create_line_chart(df, x_col="timestamp", y_cols=["pm10"],
                                title="PM10 (µg/m³)", y_label="µg/m³")
        st.plotly_chart(fig, use_container_width=True)

    if "temperature" in df.columns and "timestamp" in df.columns:
        fig = create_line_chart(df, x_col="timestamp", y_cols=["temperature"],
                                title="Temperature (°C)", y_label="°C")
        st.plotly_chart(fig, use_container_width=True)

with chart_cols_right:
    if "co" in df.columns and "timestamp" in df.columns:
        fig = create_line_chart(df, x_col="timestamp", y_cols=["co"],
                                title="CO (ppm)", y_label="ppm")
        st.plotly_chart(fig, use_container_width=True)

    if "humidity" in df.columns and "timestamp" in df.columns:
        fig = create_line_chart(df, x_col="timestamp", y_cols=["humidity"],
                                title="Humidity (%)", y_label="%")
        st.plotly_chart(fig, use_container_width=True)

st.write("")

# ── Download CSV ─────────────────────────────────────────────────────────
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️  Download CSV",
    data=csv,
    file_name=f"airsense_{selected_device}_{start_date}_{end_date}.csv",
    mime="text/csv",
    type="primary",
)

st.write("")

# ── Data Table ───────────────────────────────────────────────────────────
st.markdown("### 🗂️ Raw Data")
render_data_table(df, title=f"Readings — {selected_device}")
