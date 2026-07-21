"""
Dashboard Page — AirSense
Overview with KPI cards, ISPU status, and quick trend charts.
"""
import streamlit as st

try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except Exception as e:
    HAS_AUTOREFRESH = False

from config.settings import APP_NAME, REFRESH_INTERVAL_SECONDS
from services.sensor_service import get_latest_reading, get_readings_dataframe, get_all_device_ids
from components.sidebar import render_sidebar
from components.cards import render_metric_card, render_ispu_card
from components.charts import create_line_chart
from utils.helper import format_datetime, now_wib, check_database_connection, filter_outlier_readings

# ── Connection check ─────────────────────────────────────────────────────
check_database_connection()

# ── Auto-refresh / Fallback ──────────────────────────────────────────────
if HAS_AUTOREFRESH:
    try:
        st_autorefresh(
            interval=REFRESH_INTERVAL_SECONDS * 1000,
            limit=None,
            key="dashboard_autorefresh",
        )
    except Exception:
        pass  # Silently fallback if component crashes on hot-reload

# ── Sidebar ──────────────────────────────────────────────────────────────
device_ids = get_all_device_ids()
selected_device = render_sidebar(device_ids, st.session_state.get("selected_device", device_ids[0] if device_ids else None))
st.session_state.selected_device = selected_device

# Manual refresh fallback if autorefresh is not available
if not HAS_AUTOREFRESH:
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

# ── Latest Reading ───────────────────────────────────────────────────────
reading = get_latest_reading(selected_device) if selected_device else None

if reading is None:
    st.info("📭 No data available for this device yet. Check back soon or verify the device is sending data.")
    st.stop()

# Check if data is outdated (older than 5 minutes)
from datetime import timedelta
data_ts = reading.get("timestamp")
is_outdated = False
if data_ts:
    time_diff = now_wib() - data_ts
    if time_diff > timedelta(minutes=5):
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

# ── KPI Metric Cards (Row 1) ────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
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
        color="#06b6d4",
    )
with c3:
    render_metric_card(
        title="CO (MQ7)",
        value=reading.get("co", 0.0),
        unit="ppm",
        icon="🏭",
        color="#f59e0b",
    )

c4, c5, c6 = st.columns(3)
with c4:
    render_metric_card(
        title="CO₂ / Gas (MQ135)",
        value=reading.get("co2", 400.0),
        unit="ppm",
        icon="🌫️",
        color="#a855f7",
    )
with c5:
    render_metric_card(
        title="Temperature",
        value=reading.get("temperature", "-"),
        unit="°C",
        icon="🌡️",
        color="#ef4444",
    )
with c6:
    render_metric_card(
        title="Humidity",
        value=reading.get("humidity", "-"),
        unit="%",
        icon="💧",
        color="#22c55e",
    )

st.write("")

# # ── ISPU Sub-Index Breakdown ────────────────────────────────────────────
# st.markdown("### 🔬 ISPU Sub-Index Breakdown")

# ispu_pm10_val  = reading.get("ispu_pm10",  0.0)
# ispu_co_val    = reading.get("ispu_co",    0.0)
# ispu_mq135_val = reading.get("ispu_mq135", 0.0)
# ispu_final_val = reading.get("ispu_final", 0.0)

# cat_color = reading.get("category", {}).get("color", "#3b82f6")

# def _ispu_bar(label: str, value: float, color: str, icon: str) -> str:
#     pct = min((value / 500) * 100, 100)
#     is_dominant = (value == ispu_final_val and value > 0)
#     border = f"border: 2px solid {color};" if is_dominant else "border: 1px solid rgba(255,255,255,0.08);"
#     crown  = " 👑" if is_dominant else ""
#     return f"""
#     <div style="background:rgba(17,25,40,0.6);{border}border-radius:12px;padding:16px 20px;">
#         <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
#             <span style="font-size:0.85rem;font-weight:600;color:#9ca3af;">{icon} {label}{crown}</span>
#             <span style="font-size:1.4rem;font-weight:800;color:{color};">{value:.1f}</span>
#         </div>
#         <div style="background:rgba(255,255,255,0.05);border-radius:6px;height:6px;overflow:hidden;">
#             <div style="background:{color};height:100%;width:{pct:.1f}%;border-radius:6px;"></div>
#         </div>
#     </div>"""

# sub_col1, sub_col2, sub_col3 = st.columns(3)
# with sub_col1:
#     st.markdown(_ispu_bar("PM10 (Debu)",   ispu_pm10_val,  "#06b6d4", "💨"), unsafe_allow_html=True)
# with sub_col2:
#     st.markdown(_ispu_bar("CO (MQ7)",       ispu_co_val,    "#f59e0b", "🏭"), unsafe_allow_html=True)
# with sub_col3:
#     st.markdown(_ispu_bar("Gas CO₂ (MQ135)", ispu_mq135_val, "#a855f7", "🌫️"), unsafe_allow_html=True)

# st.caption("👑 = Sub-index paling tinggi yang menentukan nilai ISPU final.")

# st.write("")

# ── ISPU Status Card ────────────────────────────────────────────────────
category = reading.get("category", {})
render_ispu_card(reading.get("ispu_final", 0), category)

st.write("")

# ── Quick Trend Charts (last 60 readings ≈ 1 hour) ──────────────────────────────────────
df = get_readings_dataframe(selected_device, limit=60)

# ── Data Quality Badge ───────────────────────────────────────────────────────────
if df is not None and not df.empty:
    # Re-check raw readings count vs clean count to compute quality %
    _all_cols = ["temperature", "humidity"]
    _total_raw = len(df)
    _raw_list  = df[[c for c in _all_cols if c in df.columns]].to_dict("records")
    _, _removed = filter_outlier_readings(
        [dict(temperature=r.get("temperature", 0), humidity=r.get("humidity", 0))
         for r in df.to_dict("records")]
    )
    _clean_count  = _total_raw - _removed
    _quality_pct  = int((_clean_count / _total_raw) * 100) if _total_raw else 100

    if _quality_pct >= 95:
        _q_color, _q_icon = "#22c55e", "✅"
    elif _quality_pct >= 80:
        _q_color, _q_icon = "#f59e0b", "⚠️"
    else:
        _q_color, _q_icon = "#ef4444", "🚨"

    dq_col, title_col = st.columns([1, 3])
    with title_col:
        st.markdown("### 📈 Last Hour Trend")
    with dq_col:
        st.markdown(
            f"""
            <div style="
                display:inline-flex;align-items:center;gap:6px;
                background:{_q_color}18;border:1px solid {_q_color}44;
                border-radius:999px;padding:6px 14px;
                font-size:0.82rem;font-weight:600;color:{_q_color};
                margin-top:12px;
            ">
                {_q_icon} Data Quality: {_quality_pct}%
                <span style="color:#6b7280;font-weight:400;">({_removed} outlier dibuang)</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.markdown("### 📈 Last Hour Trend")

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
                title="CO ppm (MQ7) — Last Hour", y_label="ppm",
            )
            st.plotly_chart(fig_co, use_container_width=True)

    col_left2, col_right2 = st.columns(2)

    with col_left2:
        if "co2" in df_recent.columns and "timestamp" in df_recent.columns:
            fig_co2 = create_line_chart(
                df_recent, x_col="timestamp", y_cols=["co2"],
                title="CO₂ Equiv. ppm (MQ135) — Last Hour", y_label="ppm",
            )
            st.plotly_chart(fig_co2, use_container_width=True)

    with col_right2:
        if "ispu_final" in df_recent.columns and "timestamp" in df_recent.columns:
            fig_ispu = create_line_chart(
                df_recent, x_col="timestamp", y_cols=["ispu_final"],
                title="ISPU Index — Last Hour", y_label="ISPU",
            )
            st.plotly_chart(fig_ispu, use_container_width=True)

else:
    st.info("📊 No historical readings available yet to render trend charts.")
