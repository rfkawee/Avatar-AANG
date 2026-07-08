"""
AirSense — IoT Air Quality Monitoring Dashboard
Main application entrypoint.
"""
import streamlit as st
from config.settings import APP_NAME
from config.firebase_config import initialize_firebase, is_offline_mode

# ── Page Config (must be the first Streamlit command) ────────────────────
st.set_page_config(
    page_title=APP_NAME,
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Firebase initialisation (runs once per session) ──────────────────────
if "firebase_initialized" not in st.session_state:
    initialize_firebase()
    st.session_state.firebase_initialized = True

# ── Offline banner ───────────────────────────────────────────────────────
if is_offline_mode():
    st.toast("🔌 Running in **offline mock mode** — no Firebase connection.", icon="⚠️")

# ── Global Premium Dark-Theme CSS ────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Import Google Font ─────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ── Root variables ─────────────────────────────────────────────── */
    :root {
        --bg-primary:    #0e1117;
        --bg-secondary:  #161b22;
        --bg-card:       #1c2333;
        --bg-hover:      #242d3d;
        --border-subtle: #30363d;
        --text-primary:  #e6edf3;
        --text-secondary:#8b949e;
        --accent-green:  #22c55e;
        --accent-blue:   #3b82f6;
        --accent-amber:  #f59e0b;
        --accent-red:    #ef4444;
        --radius:        12px;
        --shadow-card:   0 4px 24px rgba(0,0,0,.35);
    }

    /* ── Global ─────────────────────────────────────────────────────── */
    html, body, [data-testid="stAppViewContainer"],
    [data-testid="stApp"] {
        font-family: 'Inter', sans-serif;
        color: var(--text-primary) !important;
    }

    /* Force Material Icons to use the correct font family */
    [data-testid="stIconMaterial"], .stIcon, [class*="material-symbols"] {
        font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons" !important;
    }

    /* ── Sidebar ────────────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111827 0%, #0f172a 100%) !important;
        border-right: 1px solid var(--border-subtle) !important;
    }
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: var(--text-primary) !important;
    }

    /* ── Metric cards ───────────────────────────────────────────────── */
    [data-testid="stMetric"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius) !important;
        padding: 18px 20px !important;
        box-shadow: var(--shadow-card) !important;
        transition: transform .2s ease, box-shadow .2s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 32px rgba(0,0,0,.5) !important;
    }

    /* ── Expander ────────────────────────────────────────────────────── */
    details {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius) !important;
    }

    /* ── Buttons ─────────────────────────────────────────────────────── */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all .2s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px rgba(59,130,246,.35) !important;
    }

    /* ── DataFrames / Tables ─────────────────────────────────────────── */
    [data-testid="stDataFrame"] {
        border-radius: var(--radius) !important;
        overflow: hidden;
    }

    /* ── Scrollbar ───────────────────────────────────────────────────── */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
    }
    ::-webkit-scrollbar-thumb {
        background: var(--border-subtle);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #484f58;
    }

    /* ── Tabs ────────────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0 !important;
        font-weight: 500 !important;
    }

    /* ── Card utility class (injected via st.markdown) ───────────── */
    .air-card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius);
        padding: 24px;
        box-shadow: var(--shadow-card);
        margin-bottom: 16px;
        transition: transform .2s ease;
    }
    .air-card:hover {
        transform: translateY(-2px);
    }
    .air-card h3 {
        margin: 0 0 8px 0;
        font-weight: 600;
    }

    /* ── Status badges ──────────────────────────────────────────────── */
    .status-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.03em;
    }

    /* ── Hide default Streamlit footer ──────────────────────────────── */
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Navigation ───────────────────────────────────────────────────────────
pg = st.navigation(
    [
        st.Page("pages/dashboard.py",    title="Dashboard",             icon="📊", default=True),
        st.Page("pages/monitoring.py",   title="Real-Time Monitoring",  icon="📡"),
        st.Page("pages/historical.py",   title="Historical Data",       icon="📈"),
        st.Page("pages/forecasting.py",  title="Forecasting",           icon="🔮"),
        st.Page("pages/alerts.py",       title="Alerts",                icon="🚨"),
        st.Page("pages/devices.py",      title="Devices",               icon="🔧"),
        st.Page("pages/about.py",        title="About",                 icon="ℹ️"),
    ]
)

pg.run()
