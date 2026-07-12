"""
Forecasting Page — AirSense
ML-powered air quality forecasting using a trained LSTM model.
"""
import streamlit as st
import pandas as pd

from services.sensor_service import get_all_device_ids
from services.prediction_service import get_live_prediction, is_model_available, WINDOW_SIZE
from components.sidebar import render_sidebar
from components.charts import create_forecast_chart
from utils.helper import check_database_connection, convert_debu_adc_to_ugm3, calculate_ispu_pm10
from components.cards import render_forecast_summary_card

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
        <span style="font-size:2rem;">🔮</span>
        <div>
            <h1 style="margin:0; font-size:1.75rem; font-weight:700;">Air Quality Forecasting</h1>
            <p style="margin:0; color:#8b949e; font-size:0.88rem;">
                Prediksi kualitas udara menggunakan model LSTM (Long Short-Term Memory).
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# ── Model Status Card ───────────────────────────────────────────────────
model_available = is_model_available()

status_color = "#22c55e" if model_available else "#f59e0b"
status_text = "Active" if model_available else "Not Available"
status_icon = "✅" if model_available else "🔧"

st.markdown(
    f"""
    <div class="air-card" style="border-left: 4px solid {status_color};">
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

st.write("")

# ── Forecast Calculation ──────────────────────────────────────────────────
if model_available:
    with st.spinner("⏳ Memuat model dan menghasilkan prediksi..."):
        prediction = get_live_prediction(selected_device, steps=60)

    if prediction is None:
        st.error(
            f"⚠️ Tidak dapat menghasilkan prediksi untuk device **{selected_device}**. "
            f"Pastikan terdapat minimal **{WINDOW_SIZE} data** historis di database."
        )
        st.stop()

    st.markdown("---")
    st.markdown("### 📈 Hasil Prediksi (1 Jam ke Depan)")

    timestamps = prediction["timestamps"]
    suhu_pred = prediction["suhu_predicted"]
    kelembaban_pred = prediction["kelembaban_predicted"]
    debu_pred_raw = prediction["debu_predicted"]
    ispu_pred = prediction["ispu_predicted"]

    # Convert PM10 raw ADC to µg/m³
    debu_pred = [convert_debu_adc_to_ugm3(val) for val in debu_pred_raw]

    # Build combined actual + predicted arrays for the forecast chart
    hist_ts = prediction.get("history_timestamps", [])
    hist_debu_raw = prediction.get("history_debu", [])
    hist_debu = [convert_debu_adc_to_ugm3(val) for val in hist_debu_raw]

    # Combined timeline for debu/ISPU chart
    all_timestamps = list(hist_ts) + list(timestamps)
    # Actual values: historical data + NaN for future
    actual_debu = list(hist_debu) + [float("nan")] * len(timestamps)
    # Predicted values: NaN for past + predicted for future
    pred_debu_full = [float("nan")] * len(hist_ts) + list(debu_pred)

    # Calculate historical ISPU
    hist_ispu = [round(calculate_ispu_pm10(val), 1) for val in hist_debu]
    current_ispu = hist_ispu[-1] if hist_ispu else 0.0

    # Display analysis & mitigation summary card
    render_forecast_summary_card(ispu_pred, current_ispu)

    # ── Forecast Charts ──────────────────────────────────────────
    tab_debu, tab_suhu, tab_kelembaban, tab_ispu = st.tabs(
        ["PM10 (µg/m³)", "Suhu", "Kelembaban", "ISPU"]
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
            timestamps=timestamps,
            actual_values=[float("nan")] * len(timestamps),
            predicted_values=suhu_pred,
            title="Prediksi Suhu (°C)",
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab_kelembaban:
        fig = create_forecast_chart(
            timestamps=timestamps,
            actual_values=[float("nan")] * len(timestamps),
            predicted_values=kelembaban_pred,
            title="Prediksi Kelembaban (%)",
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
            title="Prediksi ISPU (dari PM10)",
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

else:
    st.markdown(
        """
        <div class="air-card" style="text-align:center; padding:60px 24px;">
            <span style="font-size:4rem;">🤖</span>
            <h3 style="margin:16px 0 8px;">Model Belum Tersedia</h3>
            <p style="color:#8b949e; max-width:420px; margin:0 auto;">
                File model LSTM (<code>.keras</code>) dan/atau scaler (<code>.pkl</code>)
                belum ditemukan di folder <code>models/</code>. Pastikan kedua file tersebut
                sudah ditempatkan dengan benar untuk mengaktifkan fitur forecasting.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
