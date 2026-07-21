"""
Forecasting & Alerts Page — AirSense
ML-powered air quality forecasting and alert management.
"""
import streamlit as st
import pandas as pd

from services.sensor_service import get_all_device_ids, get_latest_reading
from services.prediction_service import get_live_prediction, is_model_available, WINDOW_SIZE
from services.alert_service import get_alerts, get_alert_summary, acknowledge_alert
from components.sidebar import render_sidebar
from components.charts import create_forecast_chart
from components.tables import render_alert_table
from utils.constants import ISPU_CATEGORIES
from utils.helper import check_database_connection, convert_debu_adc_to_ugm3, calculate_ispu_pm10, convert_mq7_adc_to_co_ppm, convert_mq135_adc_to_co2_ppm, calculate_ispu
from components.cards import render_forecast_summary_card, render_status_badge

# ── Connection check ─────────────────────────────────────────────────────
check_database_connection()

# ── Sidebar ──────────────────────────────────────────────────────────────
device_ids = get_all_device_ids()
selected_device = render_sidebar(device_ids, st.session_state.get("selected_device", device_ids[0] if device_ids else None))
st.session_state.selected_device = selected_device

# ==========================================
# 1. FORECASTING SECTION
# ==========================================
st.markdown("## 🔮 Forecasting")

# ── Model Status Card ───────────────────────────────────────────────────
model_available = is_model_available()

status_color = "#22c55e" if model_available else "#f59e0b"
status_text = "Active" if model_available else "Not Available"
status_icon = "✅" if model_available else "🔧"

st.markdown(
    f"""
    <div class="air-card" style="border-left: 4px solid {status_color}; margin-bottom:16px;">
        <div style="display:flex; align-items:center; gap:12px;">
            <span style="font-size:2rem;">{status_icon}</span>
            <div>
                <h3 style="margin:0; font-size:1.1rem;">Model Status: {status_text}</h3>
                <p style="margin:4px 0 0; color:#8b949e; font-size:0.85rem;">
                    {"Model LSTM telah terlatih dan siap menghasilkan prediksi."
                     if model_available else
                     "Model forecasting belum tersedia. Pastikan file model (.keras) dan scaler (.pkl) "
                     "sudah berada di folder models/."}
                </p>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Forecast Calculation ──────────────────────────────────────────────────
if model_available:
    with st.spinner("⏳ Memuat model dan menghasilkan prediksi..."):
        prediction = get_live_prediction(selected_device, steps=60)

    if prediction is None:
        st.error(
            f"⚠️ Tidak dapat menghasilkan prediksi untuk device **{selected_device}**. "
            f"Pastikan terdapat minimal **{WINDOW_SIZE} data** historis di database."
        )
    else:
        st.markdown("### 📈 Hasil Prediksi (1 Jam ke Depan)")

        timestamps = prediction["timestamps"]
        suhu_pred = prediction["suhu_predicted"]
        kelembaban_pred = prediction["kelembaban_predicted"]
        debu_pred_raw = prediction["debu_predicted"]
        mq7_pred_raw = prediction["gas_mq7_predicted"]
        mq135_pred_raw = prediction["gas_mq135_predicted"]
        ispu_pred = prediction["ispu_predicted"]

        # Convert raw ADC values to physical units
        debu_pred = [convert_debu_adc_to_ugm3(val) for val in debu_pred_raw]
        mq7_pred = [convert_mq7_adc_to_co_ppm(val) for val in mq7_pred_raw]
        mq135_pred = [convert_mq135_adc_to_co2_ppm(val) for val in mq135_pred_raw]

        # Build combined actual + predicted arrays for forecast charts
        hist_ts = prediction.get("history_timestamps", [])
        hist_debu_raw = prediction.get("history_debu", [])
        hist_debu = [convert_debu_adc_to_ugm3(val) for val in hist_debu_raw]

        hist_mq7_raw = prediction.get("history_mq7", [])
        hist_mq7 = [convert_mq7_adc_to_co_ppm(val) for val in hist_mq7_raw]

        hist_mq135_raw = prediction.get("history_mq135", [])
        hist_mq135 = [convert_mq135_adc_to_co2_ppm(val) for val in hist_mq135_raw]

        hist_suhu = prediction.get("history_suhu", [])
        hist_kelembaban = prediction.get("history_kelembaban", [])

        # Combined timelines
        all_timestamps = list(hist_ts) + list(timestamps)

        # PM10
        actual_debu = list(hist_debu) + [float("nan")] * len(timestamps)
        pred_debu_full = [float("nan")] * len(hist_ts) + list(debu_pred)

        # MQ-7 (CO)
        actual_mq7 = list(hist_mq7) + [float("nan")] * len(timestamps)
        pred_mq7_full = [float("nan")] * len(hist_ts) + list(mq7_pred)

        # MQ-135 (CO2)
        actual_mq135 = list(hist_mq135) + [float("nan")] * len(timestamps)
        pred_mq135_full = [float("nan")] * len(hist_ts) + list(mq135_pred)

        # Suhu
        actual_suhu = list(hist_suhu) + [float("nan")] * len(timestamps)
        pred_suhu_full = [float("nan")] * len(hist_ts) + list(suhu_pred)

        # Kelembaban
        actual_kelembaban = list(hist_kelembaban) + [float("nan")] * len(timestamps)
        pred_kelembaban_full = [float("nan")] * len(hist_ts) + list(kelembaban_pred)

        # Calculate multi-pollutant historical ISPU
        hist_ispu = []
        for idx in range(len(hist_debu)):
            h_pm10 = hist_debu[idx]
            h_co = hist_mq7[idx] if idx < len(hist_mq7) else 0.0
            h_co2 = hist_mq135[idx] if idx < len(hist_mq135) else 400.0
            res = calculate_ispu(h_pm10, h_co, h_co2)
            hist_ispu.append(res["ispu_final"])

        current_ispu = hist_ispu[-1] if hist_ispu else 0.0

        # Display analysis & mitigation summary card
        render_forecast_summary_card(ispu_pred, current_ispu)

        # ── Forecast Charts ──────────────────────────────────────────
        tab_debu, tab_suhu, tab_kelembaban, tab_mq7, tab_mq135, tab_ispu = st.tabs(
            ["PM10 (µg/m³)", "Suhu (°C)", "Kelembaban (%)", "CO MQ-7 (ppm)", "CO2 MQ-135 (ppm)", "ISPU"]
        )

        with tab_debu:
            fig = create_forecast_chart(
                timestamps=all_timestamps,
                actual_values=actual_debu,
                predicted_values=pred_debu_full,
                title="Prediksi PM10 (µg/m³)",
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab_suhu:
            fig = create_forecast_chart(
                timestamps=all_timestamps,
                actual_values=actual_suhu,
                predicted_values=pred_suhu_full,
                title="Prediksi Suhu (°C)",
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab_kelembaban:
            fig = create_forecast_chart(
                timestamps=all_timestamps,
                actual_values=actual_kelembaban,
                predicted_values=pred_kelembaban_full,
                title="Prediksi Kelembaban (%)",
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab_mq7:
            fig = create_forecast_chart(
                timestamps=all_timestamps,
                actual_values=actual_mq7,
                predicted_values=pred_mq7_full,
                title="Prediksi CO MQ-7 (ppm)",
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab_mq135:
            fig = create_forecast_chart(
                timestamps=all_timestamps,
                actual_values=actual_mq135,
                predicted_values=pred_mq135_full,
                title="Prediksi CO2 MQ-135 (ppm)",
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab_ispu:
            # ISPU combined chart
            actual_ispu = list(hist_ispu) + [float("nan")] * len(timestamps)
            pred_ispu_full = [float("nan")] * len(hist_ts) + list(ispu_pred)

            fig = create_forecast_chart(
                timestamps=all_timestamps,
                actual_values=actual_ispu,
                predicted_values=pred_ispu_full,
                title="Prediksi ISPU (Multi-polutan)",
            )
            st.plotly_chart(fig, use_container_width=True)

        st.write("")
        # ── Info note ────────────────────────────────────────────────
        st.info(
            "**ℹ️ Catatan:** Prediksi dihasilkan secara **autoregresif** — "
            "model memprediksi 1 langkah ke depan, lalu menggunakan hasil prediksi "
            "tersebut sebagai input untuk langkah berikutnya. Semakin jauh prediksi "
            "ke depan, semakin besar kemungkinan terjadi deviasi dari nilai aktual."
        )

st.write("")
st.write("")
st.divider()

# ==========================================
# 2. ALERTS SECTION
# ==========================================
st.markdown("## 🚨 Alert Centre")

# ── Recommendations based on current ISPU ────────────────────────────────
st.markdown("### 💡 Current Recommendations")

reading = get_latest_reading(selected_device) if selected_device else None

if reading and reading.get("category"):
    cat = reading["category"]
    rec_color = cat.get("color", "#8b949e")
    st.markdown(
        f"""
        <div class="air-card" style="border-left:4px solid {rec_color}; margin-bottom: 24px;">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
                <span style="font-size:1.6rem;">{cat.get("emoji", "")}</span>
                <h3 style="margin:0; color:{rec_color};">{cat.get("label", "")} — {cat.get("label_en", "")}</h3>
            </div>
            <p style="margin:0; color:#c9d1d9; font-size:0.92rem;">
                {cat.get("recommendation", "No recommendation available.")}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.info("No current reading available to generate recommendations.")


# ── Alert Summary Cards ─────────────────────────────────────────────────
st.markdown("### 📊 Alert Summary")
summary = get_alert_summary()

total_alerts    = summary.get("total", 0) if summary else 0
unack_alerts    = summary.get("unacknowledged", 0) if summary else 0
by_category     = summary.get("by_category", {}) if summary else {}

# Metric row: total & unacknowledged
mc1, mc2 = st.columns(2)
with mc1:
    st.metric("🔔 Total Alerts", total_alerts)
with mc2:
    st.metric("⚠️ Unacknowledged", unack_alerts)

st.write("")

if by_category:
    cols = st.columns(len(by_category))
    for idx, (category_label, count) in enumerate(by_category.items()):
        # Find colour from constants
        cat_color = "#8b949e"
        for cat in ISPU_CATEGORIES:
            if cat["label"] == category_label or cat["label_en"] == category_label:
                cat_color = cat["color"]
                break

        with cols[idx % len(cols)]:
            st.markdown(
                f"""
                <div class="air-card" style="text-align:center; border-top:3px solid {cat_color};">
                    <p style="font-size:2rem; margin:0; font-weight:700; color:{cat_color};">{count}</p>
                    <p style="margin:4px 0 0; font-size:0.82rem; color:#8b949e;">{category_label}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
else:
    st.success("✅ No alerts recorded. Air quality has been within safe limits.")

st.write("")

# ── Filters ──────────────────────────────────────────────────────────────
st.markdown("### 🔍 Filter Alerts")

filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    filter_device = st.selectbox(
        "Device",
        options=["All"] + device_ids,
        key="alert_filter_device",
    )

with filter_col2:
    category_labels = ["All"] + [c["label"] for c in ISPU_CATEGORIES]
    filter_category = st.selectbox(
        "Category",
        options=category_labels,
        key="alert_filter_category",
    )

st.write("")

# ── Fetch & display alerts ──────────────────────────────────────────────
device_filter = None if filter_device == "All" else filter_device
alerts = get_alerts(device_id=device_filter, limit=100)

# Apply category filter client-side
if alerts and filter_category != "All":
    alerts = [a for a in alerts if a.get("category", "") == filter_category]

if alerts:
    st.markdown(f"### 📋 Alert History ({len(alerts)} records)")
    render_alert_table(alerts)

    # ── Acknowledge buttons ──────────────────────────────────────────
    st.write("")
    st.markdown("#### ✅ Acknowledge Alert")
    unacknowledged = [a for a in alerts if not a.get("acknowledged", False)]
    if unacknowledged:
        alert_options = {
            f"{a.get('device_id','?')} — {a.get('timestamp','?')} — ISPU {a.get('ispu_value','?')}": a.get("id")
            for a in unacknowledged
        }
        selected_alert_label = st.selectbox("Select alert to acknowledge", list(alert_options.keys()), key="ack_select")
        if st.button("Acknowledge", key="ack_btn", type="primary"):
            alert_id = alert_options[selected_alert_label]
            acknowledge_alert(alert_id)
            st.success(f"✅ Alert **{alert_id}** acknowledged.")
            st.rerun()
    else:
        st.info("All alerts have been acknowledged.")
else:
    st.info("📭 No alerts match the current filters.")

st.write("")
