"""
Forecasting Page — AirSense
Placeholder for ML-based air quality forecasting with demo mode.
"""
import streamlit as st
import pandas as pd

from services.sensor_service import get_all_device_ids
from services.prediction_service import get_mock_prediction, is_model_available
from components.sidebar import render_sidebar
from components.charts import create_forecast_chart

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
                ML-powered predictions for proactive air quality management.
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
                    {"The forecasting model is trained and ready to generate predictions."
                     if model_available else
                     "The forecasting model is not yet deployed. You can preview simulated "
                     "forecasts using the demo toggle below."}
                </p>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")

# ── Demo Toggle ──────────────────────────────────────────────────────────
demo_mode = st.toggle(
    "🎯 Preview Simulated Forecast (Demo Mode)",
    value=False,
    key="forecast_demo_toggle",
)

if demo_mode:
    st.markdown("---")
    st.markdown("### 📈 Simulated Forecast")

    prediction = get_mock_prediction(selected_device)

    if prediction is None:
        st.warning("⚠️ Could not generate simulated forecast data.")
        st.stop()

    timestamps = prediction.get("timestamps", [])
    pm10_pred = prediction.get("pm10_predicted", [])
    co_pred = prediction.get("co_predicted", [])
    ispu_pred = prediction.get("ispu_predicted", [])

    # ── Forecast Charts ──────────────────────────────────────────────
    tab_pm10, tab_co, tab_ispu = st.tabs(["PM10 Forecast", "CO Forecast", "ISPU Forecast"])

    with tab_pm10:
        fig = create_forecast_chart(
            timestamps=timestamps,
            actual_values=None,
            predicted_values=pm10_pred,
            title="PM10 Predicted (µg/m³)",
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab_co:
        fig = create_forecast_chart(
            timestamps=timestamps,
            actual_values=None,
            predicted_values=co_pred,
            title="CO Predicted (ppm)",
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab_ispu:
        fig = create_forecast_chart(
            timestamps=timestamps,
            actual_values=None,
            predicted_values=ispu_pred,
            title="ISPU Predicted",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.write("")

    # ── Summary Table ────────────────────────────────────────────────
    st.markdown("### 📋 Forecast Summary")

    summary_df = pd.DataFrame({
        "Timestamp": timestamps,
        "PM10 (µg/m³)": pm10_pred,
        "CO (ppm)": co_pred,
        "ISPU": ispu_pred,
    })
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    # ── Disclaimer ───────────────────────────────────────────────────
    st.markdown(
        """
        <div class="air-card" style="border-left: 4px solid #f59e0b; background: #1c1a00;">
            <p style="margin:0; font-size:0.85rem; color:#f59e0b;">
                ⚠️ <b>Disclaimer:</b> These values are <u>simulated</u> for demonstration 
                purposes only and do not represent actual predictions. A trained ML model 
                will replace this data once deployed.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

elif not model_available:
    st.markdown(
        """
        <div class="air-card" style="text-align:center; padding:60px 24px;">
            <span style="font-size:4rem;">🤖</span>
            <h3 style="margin:16px 0 8px;">Forecasting Coming Soon</h3>
            <p style="color:#8b949e; max-width:420px; margin:0 auto;">
                The prediction engine is under development. Toggle the demo mode above 
                to preview how forecasts will look once the model is trained and deployed.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
