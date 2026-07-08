"""
Alerts Page — AirSense
Alert centre with summary cards, history table, and recommendations.
"""
import streamlit as st

from services.sensor_service import get_latest_reading, get_all_device_ids
from services.alert_service import get_alerts, get_alert_summary, acknowledge_alert
from components.sidebar import render_sidebar
from components.cards import render_status_badge
from components.tables import render_alert_table
from utils.constants import ISPU_CATEGORIES

# ── Sidebar ──────────────────────────────────────────────────────────────
device_ids = get_all_device_ids()
selected_device = render_sidebar(device_ids, st.session_state.get("selected_device", device_ids[0] if device_ids else None))
st.session_state.selected_device = selected_device

# ── Header ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
        <span style="font-size:2rem;">🚨</span>
        <div>
            <h1 style="margin:0; font-size:1.75rem; font-weight:700;">Alert Centre</h1>
            <p style="margin:0; color:#8b949e; font-size:0.88rem;">
                Monitor, acknowledge, and act on air quality alerts.
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# ── Alert Summary Cards ─────────────────────────────────────────────────
summary = get_alert_summary()

if summary:
    cols = st.columns(len(summary) if summary else 1)
    for idx, (category_label, count) in enumerate(summary.items()):
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

# ── Recommendations based on current ISPU ────────────────────────────────
st.markdown("### 💡 Current Recommendations")

reading = get_latest_reading(selected_device) if selected_device else None

if reading and reading.get("category"):
    cat = reading["category"]
    rec_color = cat.get("color", "#8b949e")
    st.markdown(
        f"""
        <div class="air-card" style="border-left:4px solid {rec_color};">
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
