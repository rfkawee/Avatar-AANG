"""
Devices Page — AirSense
View, add, edit, and delete IoT devices.
"""
import streamlit as st
import pandas as pd

from services.sensor_service import get_all_device_ids
from services.firebase_service import get_collection, add_document, update_document, delete_document
from components.sidebar import render_sidebar
from components.cards import render_status_badge
from config.settings import COLLECTION_DEVICES
from config.firebase_config import is_offline_mode

# ── Sidebar ──────────────────────────────────────────────────────────────
device_ids = get_all_device_ids()
selected_device = render_sidebar(device_ids, st.session_state.get("selected_device", device_ids[0] if device_ids else None))
st.session_state.selected_device = selected_device

# ── Header ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
        <span style="font-size:2rem;">🔧</span>
        <div>
            <h1 style="margin:0; font-size:1.75rem; font-weight:700;">Device Management</h1>
            <p style="margin:0; color:#8b949e; font-size:0.88rem;">
                Register, update, and manage your IoT sensor nodes.
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# ── Current Devices Table ────────────────────────────────────────────────
st.markdown("### 📋 Registered Devices")

devices = get_collection(COLLECTION_DEVICES) if not is_offline_mode() else []

# Fallback for offline/mock mode
if not devices:
    devices = [
        {"id": did, "device_id": did, "name": f"Sensor {did}", "location": "Default Location", "status": "active"}
        for did in device_ids
    ]

if devices:
    display_data = []
    for d in devices:
        status = d.get("status", "active")
        display_data.append({
            "Device ID": d.get("device_id", d.get("id", "-")),
            "Name": d.get("name", "-"),
            "Location": d.get("location", "-"),
            "Status": "🟢 Active" if status == "active" else "🔴 Inactive",
        })

    df = pd.DataFrame(display_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("📭 No devices registered yet.")

st.write("")

# ── Add Device Form ──────────────────────────────────────────────────────
st.markdown("### ➕ Add New Device")

with st.form("add_device_form", clear_on_submit=True):
    col_id, col_name, col_loc = st.columns(3)
    with col_id:
        new_device_id = st.text_input("Device ID", placeholder="e.g. AQM-003")
    with col_name:
        new_device_name = st.text_input("Device Name", placeholder="e.g. Sensor Lab A")
    with col_loc:
        new_device_location = st.text_input("Location", placeholder="e.g. Building A, Floor 2")

    submitted = st.form_submit_button("➕ Register Device", type="primary")

    if submitted:
        if not new_device_id.strip():
            st.error("⚠️ Device ID is required.")
        elif is_offline_mode():
            st.warning("🔌 Cannot add devices in offline mode. Connect to Firebase first.")
        else:
            try:
                add_document(COLLECTION_DEVICES, {
                    "device_id": new_device_id.strip(),
                    "name": new_device_name.strip() or new_device_id.strip(),
                    "location": new_device_location.strip() or "Unknown",
                    "status": "active",
                })
                st.success(f"✅ Device **{new_device_id.strip()}** registered successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to add device: {e}")

st.write("")

# ── Edit / Delete Devices ────────────────────────────────────────────────
st.markdown("### ✏️ Edit / Remove Device")

if devices:
    for device in devices:
        device_id = device.get("device_id", device.get("id", "unknown"))
        doc_id = device.get("id", device_id)

        with st.expander(f"🔧 {device_id} — {device.get('name', '')}"):
            edit_col1, edit_col2 = st.columns(2)

            with edit_col1:
                edit_name = st.text_input(
                    "Name", value=device.get("name", ""),
                    key=f"edit_name_{doc_id}",
                )
            with edit_col2:
                edit_location = st.text_input(
                    "Location", value=device.get("location", ""),
                    key=f"edit_loc_{doc_id}",
                )

            status_options = ["active", "inactive"]
            current_status = device.get("status", "active")
            edit_status = st.selectbox(
                "Status",
                options=status_options,
                index=status_options.index(current_status) if current_status in status_options else 0,
                key=f"edit_status_{doc_id}",
            )

            btn_col1, btn_col2 = st.columns(2)

            with btn_col1:
                if st.button("💾 Save Changes", key=f"save_{doc_id}", type="primary"):
                    if is_offline_mode():
                        st.warning("🔌 Cannot edit devices in offline mode.")
                    else:
                        try:
                            update_document(COLLECTION_DEVICES, doc_id, {
                                "name": edit_name,
                                "location": edit_location,
                                "status": edit_status,
                            })
                            st.success(f"✅ Device **{device_id}** updated.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to update: {e}")

            with btn_col2:
                if st.button("🗑️ Delete Device", key=f"del_{doc_id}", type="secondary"):
                    st.session_state[f"confirm_delete_{doc_id}"] = True

                if st.session_state.get(f"confirm_delete_{doc_id}", False):
                    st.warning(f"⚠️ Are you sure you want to delete **{device_id}**?")
                    confirm_col1, confirm_col2 = st.columns(2)
                    with confirm_col1:
                        if st.button("Yes, delete", key=f"confirm_yes_{doc_id}", type="primary"):
                            if is_offline_mode():
                                st.warning("🔌 Cannot delete devices in offline mode.")
                            else:
                                try:
                                    delete_document(COLLECTION_DEVICES, doc_id)
                                    st.success(f"🗑️ Device **{device_id}** deleted.")
                                    st.session_state.pop(f"confirm_delete_{doc_id}", None)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Failed to delete: {e}")
                    with confirm_col2:
                        if st.button("Cancel", key=f"confirm_no_{doc_id}"):
                            st.session_state.pop(f"confirm_delete_{doc_id}", None)
                            st.rerun()
else:
    st.info("No devices to edit.")
