"""
Sidebar Component
Renders the premium dark-themed sidebar with app branding,
connection status, device selector, and refresh info.
"""
import streamlit as st
from config.firebase_config import is_offline_mode
from config.settings import APP_NAME, REFRESH_INTERVAL_SECONDS
from utils.helper import now_wib, format_datetime


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
    offline = is_offline_mode()
    if offline:
        badge_class = "offline"
        badge_text = "🟠 Offline Mode"
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

    default_index = 0
    if selected_device in device_ids:
        default_index = device_ids.index(selected_device)

    chosen_device = st.sidebar.selectbox(
        "Select Device",
        options=device_ids,
        index=default_index,
        label_visibility="collapsed",
    )

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
