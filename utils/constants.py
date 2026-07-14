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

# MQ135 CO2-equivalent breakpoints (ppm) — custom air quality thresholds
# Based on WHO/ASHRAE indoor air quality standards for CO2
# Note: MQ135 output is converted to CO2-equivalent ppm before lookup
ISPU_MQ135_BREAKPOINTS = [
    (0,   50,    400,    600),    #  0– 50 ISPU: 400–600 ppm   (Udara luar / sangat bersih)
    (51,  100,   601,    1000),   # 51–100 ISPU: 601–1000 ppm  (Udara dalam ruangan baik)
    (101, 200,   1001,   2000),   #101–200 ISPU: 1001–2000 ppm (Kualitas sedang–buruk)
    (201, 300,   2001,   5000),   #201–300 ISPU: 2001–5000 ppm (Tidak sehat)
    (301, 400,   5001,   10000),  #301–400 ISPU: 5001–10000 ppm (Sangat tidak sehat)
    (401, 500,   10001,  40000),  #401–500 ISPU: >10000 ppm    (Berbahaya — zona narkosis CO2)
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
    "co2":         (400.0, 2000.0),   # CO2 equivalent ppm (MQ135)
}

# Number of historical records to generate in mock mode (per device)
MOCK_HISTORY_COUNT = 1440   # 24 hours × 60 readings/hour

# Alert-worthy ISPU threshold (alerts generated at this level and above)
ALERT_ISPU_THRESHOLD = 101  # "Tidak Sehat" and above

# ═══════════════════════════════════════════════════════════════════════════
# OUTLIER DETECTION THRESHOLDS  (outdoor environment — Indonesia)
# ═══════════════════════════════════════════════════════════════════════════

# Absolute physical bounds for outdoor sensors in Indonesia
OUTLIER_TEMP_MIN: float = 10.0    # °C — highlands (e.g. Dieng) can reach this
OUTLIER_TEMP_MAX: float = 45.0    # °C — extreme heat in dry lowland areas
OUTLIER_HUM_MIN:  float = 20.0    # %  — very dry / desert-like conditions
OUTLIER_HUM_MAX:  float = 100.0   # %  — saturated (rain / fog)

# Maximum plausible change between two consecutive 1-minute readings
# Outdoor environments can change faster than indoor, so we allow larger deltas
OUTLIER_MAX_TEMP_DELTA: float = 8.0    # °C  per reading-interval
OUTLIER_MAX_HUM_DELTA:  float = 25.0   # %   per reading-interval
