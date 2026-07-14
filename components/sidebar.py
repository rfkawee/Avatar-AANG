"""
Sidebar Component
Renders the premium dark-themed sidebar with app branding,
connection status, device selector, and refresh info.
"""
import streamlit as st
from datetime import timedelta
from config.firebase_config import is_offline_mode
from config.settings import APP_NAME, REFRESH_INTERVAL_SECONDS, COLLECTION_DEVICES
from utils.helper import now_wib, format_datetime
from services.sensor_service import get_latest_reading
from services.firebase_service import get_collection, add_document, update_document, delete_document


@st.dialog("➕ Add New Device")
def add_device_dialog():
    st.markdown(
        """
        <div style="font-size:0.9rem; color:#8b949e; margin-bottom:12px;">
            Register a new IoT sensor node by specifying its Device ID, Name, and Location.
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    st.info(
        "**💡 Cara Kerja (Workflow):**\n"
        "1. Daftarkan **Device ID** unik di sini (misal: `ESP-32-Taman`).\n"
        "2. Masukkan ID yang sama ke dalam *source code* hardware IoT milikmu.\n"
        "3. Hardware akan mengirim data ke Firebase di path `kualitas_udara/{Device ID}/logs`.\n"
        "4. Pilih device dari menu *sidebar* untuk mulai memantau datanya."
    )
    
    new_device_id = st.text_input("Device ID (Harus sama dengan di Hardware)", placeholder="contoh: ESP-32-Taman")
    new_device_name = st.text_input("Device Name", placeholder="contoh: Sensor Taman Kota")
    new_device_location = st.text_input("Location", placeholder="contoh: Jl. Sudirman")
    
    st.write("")
    
    col_submit, col_cancel = st.columns(2)
    with col_submit:
        submitted = st.button("➕ Register Device", type="primary", use_container_width=True)
    with col_cancel:
        cancelled = st.button("Cancel", use_container_width=True)
        
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
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to add device: {e}")
    if cancelled:
        st.rerun()


@st.dialog("✏️ Edit / Remove Device")
def edit_device_dialog(device_id: str, device_doc: dict):
    doc_id = device_doc.get("id", device_id)
    edit_name = st.text_input("Name", value=device_doc.get("name", ""))
    edit_location = st.text_input("Location", value=device_doc.get("location", ""))
    
    status_options = ["active", "inactive"]
    current_status = device_doc.get("status", "active")
    edit_status = st.selectbox(
        "Status",
        options=status_options,
        index=status_options.index(current_status) if current_status in status_options else 0,
    )
    
    st.divider()
    
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    
    with btn_col1:
        if st.button("💾 Save", type="primary", use_container_width=True):
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
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to update: {e}")
                    
    with btn_col2:
        if st.button("🗑️ Delete", type="secondary", use_container_width=True):
            st.session_state[f"confirm_delete_{doc_id}"] = True
            st.rerun()
            
    with btn_col3:
        if st.button("Close", use_container_width=True):
            st.rerun()
            
    if st.session_state.get(f"confirm_delete_{doc_id}", False):
        st.warning(f"⚠️ Are you sure you want to delete **{device_id}**?")
        confirm_col1, confirm_col2 = st.columns(2)
        with confirm_col1:
            if st.button("Yes, delete", type="primary", use_container_width=True, key=f"conf_del_yes_{doc_id}"):
                if is_offline_mode():
                    st.warning("🔌 Cannot delete devices in offline mode.")
                else:
                    try:
                        delete_document(COLLECTION_DEVICES, doc_id)
                        st.success(f"🗑️ Device **{device_id}** deleted.")
                        st.session_state.pop(f"confirm_delete_{doc_id}", None)
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Failed to delete: {e}")
        with confirm_col2:
            if st.button("Cancel", use_container_width=True, key=f"conf_del_no_{doc_id}"):
                st.session_state.pop(f"confirm_delete_{doc_id}", None)
                st.rerun()


def render_sidebar(device_ids: list, selected_device: str) -> str:
    """
    Render the AirSense sidebar with branding, status, and device selector.

    Args:
        device_ids: List of available device ID strings.
        selected_device: Currently selected device ID.

    Returns:
        The selected device_id string from the dropdown.
    """

    # ── Inject premium sidebar CSS ──────────────────────────────────────
    sidebar_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Sidebar container ───────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0e1a 0%, #111827 50%, #0f172a 100%) !important;
        border-right: 1px solid rgba(6, 182, 212, 0.08);
    }

    [data-testid="stSidebarUserContent"] {
        display: flex !important;
        flex-direction: column !important;
    }

    [data-testid="stSidebarUserContent"] > div:has(.sidebar-brand) {
        order: -2 !important;
    }

    [data-testid="stSidebarNav"] {
        order: -1 !important;
    }

    [data-testid="stSidebar"] * {
        font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    }

    /* ── Selectbox styling ───────────────────────────────────────── */
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background: rgba(17, 25, 40, 0.8) !important;
        border: 1px solid rgba(6, 182, 212, 0.2) !important;
        border-radius: 10px !important;
        color: #e5e7eb !important;
        transition: all 0.3s ease !important;
    }

    [data-testid="stSidebar"] .stSelectbox > div > div:hover {
        border-color: rgba(6, 182, 212, 0.5) !important;
        box-shadow: 0 0 15px rgba(6, 182, 212, 0.1) !important;
    }

    [data-testid="stSidebar"] .stSelectbox > div > div:focus-within {
        border-color: #06b6d4 !important;
        box-shadow: 0 0 20px rgba(6, 182, 212, 0.15) !important;
    }

    /* ── Header brand area ───────────────────────────────────────── */
    .sidebar-brand {
        text-align: center;
        padding: 20px 16px 10px;
    }

    .sidebar-brand .brand-icon {
        font-size: 48px;
        display: block;
        margin-bottom: 8px;
        animation: float 3s ease-in-out infinite;
    }

    .sidebar-brand .brand-name {
        font-size: 28px;
        font-weight: 800;
        background: linear-gradient(135deg, #06b6d4, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.5px;
        margin: 0;
        line-height: 1.2;
    }

    .sidebar-brand .brand-sub {
        font-size: 12px;
        color: #6b7280;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-top: 4px;
        font-weight: 500;
    }

    /* ── Connection badge ─────────────────────────────────────────── */
    .conn-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 18px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 600;
        margin: 12px auto;
        transition: all 0.3s ease;
    }

    .conn-badge.live {
        background: rgba(34, 197, 94, 0.12);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.25);
        box-shadow: 0 0 20px rgba(34, 197, 94, 0.1);
    }

    .conn-badge.offline {
        background: rgba(245, 158, 11, 0.12);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.25);
        box-shadow: 0 0 20px rgba(245, 158, 11, 0.1);
    }

    .conn-badge .pulse-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        animation: pulse-ring 2s ease-in-out infinite;
    }

    .conn-badge.live .pulse-dot {
        background: #4ade80;
        box-shadow: 0 0 8px #4ade80;
    }

    .conn-badge.offline .pulse-dot {
        background: #fbbf24;
        box-shadow: 0 0 8px #fbbf24;
    }

    /* ── Refresh info card ────────────────────────────────────────── */
    .refresh-card {
        background: rgba(17, 25, 40, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 14px 16px;
        margin: 12px 0;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
    }

    .refresh-card .refresh-time {
        font-size: 13px;
        color: #9ca3af;
        margin: 0 0 4px 0;
    }

    .refresh-card .refresh-interval {
        font-size: 11px;
        color: #6b7280;
        margin: 0;
    }

    /* ── Footer ───────────────────────────────────────────────────── */
    .sidebar-footer {
        text-align: center;
        padding: 16px;
        margin-top: 10px;
    }

    .sidebar-footer .footer-version {
        font-size: 11px;
        color: #4b5563;
        font-weight: 500;
        letter-spacing: 0.05em;
    }

    .sidebar-footer .footer-copy {
        font-size: 10px;
        color: #374151;
        margin-top: 4px;
    }

    /* ── Section header ───────────────────────────────────────────── */
    .section-header {
        font-size: 13px;
        font-weight: 600;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 16px 0 8px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* ── Animations ───────────────────────────────────────────────── */
    @keyframes pulse-ring {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.5); }
    }

    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-6px); }
    }

    /* ── Sidebar divider override ─────────────────────────────────── */
    [data-testid="stSidebar"] hr {
        border: none;
        height: 1px;
        background: linear-gradient(
            90deg,
            transparent,
            rgba(6, 182, 212, 0.2),
            transparent
        );
        margin: 16px 0;
    }
    </style>
    """
    st.sidebar.markdown(sidebar_css, unsafe_allow_html=True)

    # ── Brand / Logo area ───────────────────────────────────────────────
    brand_html = f"""
    <div class="sidebar-brand">
        <span class="brand-icon">🌬️</span>
        <p class="brand-name">{APP_NAME}</p>
        <p class="brand-sub">IoT Air Quality Monitoring</p>
    </div>
    """
    st.sidebar.markdown(brand_html, unsafe_allow_html=True)

    # ── Connection status badge ─────────────────────────────────────────
    is_offline = is_offline_mode()
    if is_offline:
        badge_class = "offline"
        badge_text = "🟠 Offline Mode"
    else:
        # Check if the latest data is outdated (more than 5 minutes old)
        reading = get_latest_reading(selected_device) if selected_device else None
        is_outdated = True
        if reading:
            data_ts = reading.get("timestamp")
            if data_ts:
                time_diff = now_wib() - data_ts
                if time_diff <= timedelta(minutes=5):
                    is_outdated = False
        
        if is_outdated:
            badge_class = "offline"
            badge_text = "🔴 Device Offline"
        else:
            badge_class = "live"
            badge_text = "🟢 Live Connected"

    status_html = f"""
    <div style="text-align: center;">
        <span class="conn-badge {badge_class}">
            <span class="pulse-dot"></span>
            {badge_text}
        </span>
    </div>
    """
    st.sidebar.markdown(status_html, unsafe_allow_html=True)

    # ── Separator ───────────────────────────────────────────────────────
    st.sidebar.markdown("---")

    # ── Device selector ─────────────────────────────────────────────────
    st.sidebar.markdown(
        '<p class="section-header">📡 Device Selection</p>',
        unsafe_allow_html=True,
    )

    chosen_device = selected_device

    # Fetch registered devices to display custom name if available
    devices = get_collection(COLLECTION_DEVICES) if not is_offline_mode() else []
    device_map = {d.get("device_id", d.get("id")): d for d in devices}

    for dev_id in device_ids:
        dev_doc = device_map.get(dev_id, {})
        dev_name = dev_doc.get("name", dev_id)

        col_btn, col_gear = st.sidebar.columns([4, 1])

        is_selected = (dev_id == selected_device)
        btn_type = "primary" if is_selected else "secondary"

        with col_btn:
            if st.button(f"📡 {dev_name}", key=f"btn_sel_{dev_id}", type=btn_type, use_container_width=True):
                chosen_device = dev_id
                st.session_state.selected_device = dev_id
                st.rerun()

        with col_gear:
            if st.button("⚙️", key=f"btn_edit_{dev_id}", use_container_width=True, help=f"Edit {dev_name}"):
                edit_device_dialog(dev_id, dev_doc)

    st.sidebar.markdown('<div style="margin-top: 10px;"></div>', unsafe_allow_html=True)
    if st.sidebar.button("➕ Add New Device", key="btn_add_device", use_container_width=True):
        add_device_dialog()

    # ── Separator ───────────────────────────────────────────────────────
    st.sidebar.markdown("---")

    # ── Last refresh info ───────────────────────────────────────────────
    current_time = format_datetime(now_wib())
    refresh_html = f"""
    <div class="refresh-card">
        <p class="refresh-time">🕐 Last Refresh: <strong style="color:#e5e7eb;">{current_time}</strong></p>
        <p class="refresh-interval">Auto-refresh: every {REFRESH_INTERVAL_SECONDS}s</p>
    </div>
    """
    st.sidebar.markdown(refresh_html, unsafe_allow_html=True)

    # ── Separator ───────────────────────────────────────────────────────
    st.sidebar.markdown("---")

    # ── Footer ──────────────────────────────────────────────────────────
    footer_html = """
    <div class="sidebar-footer">
        <p class="footer-version">AirSense v1.0.0</p>
        <p class="footer-copy">© 2025 AirSense IoT Platform</p>
    </div>
    """
    st.sidebar.markdown(footer_html, unsafe_allow_html=True)

    return chosen_device
