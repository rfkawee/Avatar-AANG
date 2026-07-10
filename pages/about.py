"""
About Page — AirSense
System information, sensor specs, ISPU reference, and credits.
"""
import streamlit as st
import pandas as pd

from config.settings import APP_NAME
from utils.constants import ISPU_CATEGORIES

# ── Header ───────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="text-align:center; padding:40px 0 20px;">
        <span style="font-size:4rem;">🌿</span>
        <h1 style="margin:12px 0 4px; font-size:2.2rem; font-weight:700;">
            {APP_NAME}
        </h1>
        <p style="color:#8b949e; font-size:1rem; margin:0;">
            IoT Air Quality Monitoring System
        </p>
        <p style="color:#58a6ff; font-size:0.85rem; margin:6px 0 0;">
            Version 1.0.0
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# ── Description ──────────────────────────────────────────────────────────
st.markdown(
    """
    **AirSense** is an IoT-based air quality monitoring system that collects real-time 
    data from distributed sensor nodes and visualises it through an interactive web dashboard.

    The system calculates the **ISPU** (Indeks Standar Pencemar Udara — Indonesian Air 
    Pollution Standard Index) based on PM10 particulate matter and carbon monoxide (CO) 
    concentrations, providing actionable health recommendations to users.
    """
)

st.write("")

# ── System Architecture ─────────────────────────────────────────────────
st.markdown("### 🏗️ System Architecture")

st.markdown(
    """
    ```mermaid
    graph LR
        A["🌡️ Sensor Nodes<br/>(ESP32 + Sensors)"] -->|Wi-Fi / MQTT| B["☁️ Firebase<br/>Cloud Firestore"]
        B -->|REST API| C["📊 Streamlit<br/>Dashboard"]
        C --> D["👤 User<br/>(Web Browser)"]
        B -->|Triggers| E["🚨 Alert<br/>Service"]
        C -->|Reads| F["🤖 Prediction<br/>Engine"]
    ```
    """,
)

st.info(
    "**Data Flow:** Sensor nodes (ESP32) collect environmental data and push it to "
    "Firebase Cloud Firestore over Wi-Fi. The Streamlit dashboard reads from Firestore "
    "in near real-time, computes the ISPU index, and renders interactive visualisations.",
    icon="ℹ️",
)

st.write("")

# ── Sensor Specifications ───────────────────────────────────────────────
st.markdown("### 📟 Sensor Specifications")

sensor_data = pd.DataFrame([
    {
        "Sensor": "DHT22",
        "Parameter": "Temperature & Humidity",
        "Range": "-40°C – 80°C / 0–100% RH",
        "Accuracy": "±0.5°C / ±2% RH",
        "Interface": "Digital (1-Wire)",
    },
    {
        "Sensor": "GP2Y1010AU0F",
        "Parameter": "PM10 Dust Density",
        "Range": "0 – 600 µg/m³",
        "Accuracy": "±15%",
        "Interface": "Analog (ADC)",
    },
    {
        "Sensor": "MQ-135",
        "Parameter": "Air Quality (CO₂, NH₃, Benzene)",
        "Range": "10 – 1000 ppm",
        "Accuracy": "Varies by gas",
        "Interface": "Analog (ADC)",
    },
    {
        "Sensor": "MQ-7",
        "Parameter": "Carbon Monoxide (CO)",
        "Range": "20 – 2000 ppm",
        "Accuracy": "±5%",
        "Interface": "Analog (ADC)",
    },
])

st.dataframe(sensor_data, use_container_width=True, hide_index=True)

st.write("")

# ── ISPU Reference Table ────────────────────────────────────────────────
st.markdown("### 📊 ISPU Category Reference")

ispu_rows = []
for cat in ISPU_CATEGORIES:
    ispu_rows.append({
        "": cat["emoji"],
        "Category (ID)": cat["label"],
        "Category (EN)": cat["label_en"],
        "ISPU Range": f'{cat["min"]} – {cat["max"]}',
        "Color": cat["color"],
        "Recommendation": cat["recommendation"],
    })

ispu_df = pd.DataFrame(ispu_rows)
st.dataframe(ispu_df, use_container_width=True, hide_index=True)

# Render colour swatches
cols = st.columns(len(ISPU_CATEGORIES))
for i, cat in enumerate(ISPU_CATEGORIES):
    with cols[i]:
        st.markdown(
            f"""
            <div style="
                background:{cat['color']};
                border-radius:8px;
                padding:12px 8px;
                text-align:center;
                color:#fff;
                font-weight:600;
                font-size:0.78rem;
                text-shadow: 0 1px 3px rgba(0,0,0,.5);
            ">
                {cat['emoji']} {cat['label']}<br/>
                <span style="font-size:0.7rem; opacity:0.85;">{cat['min']}–{cat['max']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.write("")

# ── ISPU Calculation Method ──────────────────────────────────────────────
st.markdown("### 📐 ISPU Calculation Method")

st.markdown(
    r"""
    The ISPU sub-index for each pollutant is calculated using **linear interpolation** 
    based on government-defined breakpoints:

    $$I = \frac{I_{upper} - I_{lower}}{C_{upper} - C_{lower}} \times (C - C_{lower}) + I_{lower}$$

    Where:
    - $I$ = ISPU sub-index value
    - $C$ = measured pollutant concentration
    - $I_{upper}, I_{lower}$ = ISPU breakpoint boundaries
    - $C_{upper}, C_{lower}$ = concentration breakpoint boundaries

    The **final ISPU** is calculated from the PM10 sub-index.

    > *Reference: Keputusan Kepala Bapedal No. 107 Tahun 1997*
    """
)

st.write("")

# ── Credits ──────────────────────────────────────────────────────────────
st.markdown("### 🙏 Credits")

st.markdown(
    """
    <div class="air-card" style="text-align:center;">
        <p style="font-size:0.95rem; color:#c9d1d9; margin-bottom:12px;">
            Developed as part of the <b>Metodologi Penelitian</b> course project.
        </p>
        <p style="font-size:0.85rem; color:#8b949e; margin:0;">
            Built with ❤️ using
            <a href="https://streamlit.io" target="_blank" style="color:#ff4b4b;">Streamlit</a> · 
            <a href="https://firebase.google.com" target="_blank" style="color:#ffca28;">Firebase</a> · 
            <a href="https://plotly.com" target="_blank" style="color:#636efa;">Plotly</a> · 
            <a href="https://www.espressif.com" target="_blank" style="color:#e7352c;">ESP32</a>
        </p>
        <p style="font-size:0.78rem; color:#484f58; margin:12px 0 0;">
            © 2026 AirSense Project — All rights reserved
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
