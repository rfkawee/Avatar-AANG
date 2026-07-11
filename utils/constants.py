"""
Constants Module
Contains Indonesian ISPU (Indeks Standar Pencemar Udara) breakpoints
based on Keputusan Kepala Bapedal No. 107 Tahun 1997 / PP 41 Tahun 1999
and default configuration values.
"""

# ═══════════════════════════════════════════════════════════════════════════
# ISPU BREAKPOINTS
# Each entry: (ispu_lower, ispu_upper, concentration_lower, concentration_upper)
# ═══════════════════════════════════════════════════════════════════════════

# PM10 breakpoints — concentration in µg/m³ (24-hour average)
ISPU_PM10_BREAKPOINTS = [
    (0,   50,    0,    50),
    (51,  100,   51,   150),
    (101, 200,   151,  350),
    (201, 300,   351,  420),
    (301, 400,   421,  500),
    (401, 500,   501,  600),
]

# CO breakpoints — concentration in ppm (8-hour average)
# Converted from mg/m³ standard: 1 ppm CO ≈ 1.145 mg/m³
ISPU_CO_BREAKPOINTS = [
    (0,   50,    0.0,   4.4),
    (51,  100,   4.5,   8.7),
    (101, 200,   8.8,   14.8),
    (201, 300,   14.9,  29.7),
    (301, 400,   29.8,  40.2),
    (401, 500,   40.3,  50.2),
]

# ═══════════════════════════════════════════════════════════════════════════
# ISPU CATEGORIES
# ═══════════════════════════════════════════════════════════════════════════

ISPU_CATEGORIES = [
    {
        "label": "Baik",
        "label_en": "Good",
        "min": 0,
        "max": 50,
        "color": "#22c55e",       # green-500
        "emoji": "🟢",
        "recommendation": (
            "Kualitas udara baik dan tidak memberikan efek negatif "
            "terhadap manusia, hewan, dan tumbuhan."
        ),
    },
    {
        "label": "Sedang",
        "label_en": "Moderate",
        "min": 51,
        "max": 100,
        "color": "#3b82f6",       # blue-500
        "emoji": "🔵",
        "recommendation": (
            "Kualitas udara masih dapat diterima. Kelompok sensitif "
            "sebaiknya mengurangi aktivitas di luar ruangan yang terlalu lama."
        ),
    },
    {
        "label": "Tidak Sehat",
        "label_en": "Unhealthy",
        "min": 101,
        "max": 200,
        "color": "#f59e0b",       # amber-500
        "emoji": "🟡",
        "recommendation": (
            "Tingkat kualitas udara tidak sehat. Kurangi aktivitas "
            "di luar ruangan, terutama bagi kelompok sensitif."
        ),
    },
    {
        "label": "Sangat Tidak Sehat",
        "label_en": "Very Unhealthy",
        "min": 201,
        "max": 300,
        "color": "#ef4444",       # red-500
        "emoji": "🔴",
        "recommendation": (
            "Tingkat kualitas udara sangat tidak sehat. Hindari "
            "aktivitas di luar ruangan. Gunakan masker jika terpaksa keluar."
        ),
    },
    {
        "label": "Berbahaya",
        "label_en": "Hazardous",
        "min": 301,
        "max": 500,
        "color": "#1e1b4b",       # indigo-950
        "emoji": "⚫",
        "recommendation": (
            "Tingkat kualitas udara berbahaya! Semua orang harus "
            "menghindari aktivitas di luar ruangan."
        ),
    },
]

# ═══════════════════════════════════════════════════════════════════════════
# SENSOR DEFAULTS
# ═══════════════════════════════════════════════════════════════════════════

DEFAULT_DEVICE_IDS = ["AQM-001", "AQM-002"]

# Sensor value ranges for mock data generation
MOCK_RANGES = {
    "temperature": (20.0, 40.0),
    "humidity":    (30.0, 90.0),
    "pm10":        (5.0, 300.0),
    "co":          (0.5, 30.0),
}

# Number of historical records to generate in mock mode (per device)
MOCK_HISTORY_COUNT = 1440   # 24 hours × 60 readings/hour

# Alert-worthy ISPU threshold (alerts generated at this level and above)
ALERT_ISPU_THRESHOLD = 101  # "Tidak Sehat" and above
