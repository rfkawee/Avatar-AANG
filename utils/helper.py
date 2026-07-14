"""
Helper Utility Module
Provides Indonesian ISPU calculation, date parsing, and general utilities.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from utils.constants import (
    ISPU_PM10_BREAKPOINTS,
    ISPU_CO_BREAKPOINTS,
    ISPU_MQ135_BREAKPOINTS,
    ISPU_CATEGORIES,
    OUTLIER_TEMP_MIN,
    OUTLIER_TEMP_MAX,
    OUTLIER_HUM_MIN,
    OUTLIER_HUM_MAX,
    OUTLIER_MAX_TEMP_DELTA,
    OUTLIER_MAX_HUM_DELTA,
)


# ═══════════════════════════════════════════════════════════════════════════
# ISPU CALCULATION
# ═══════════════════════════════════════════════════════════════════════════

def _calculate_ispu_for_pollutant(concentration: float, breakpoints: list) -> float:
    """
    Calculate the ISPU sub-index for a single pollutant using linear interpolation.

    Formula:
        I = ((I_upper - I_lower) / (C_upper - C_lower)) * (C - C_lower) + I_lower

    Args:
        concentration: The measured concentration value.
        breakpoints: List of tuples (ispu_lower, ispu_upper, conc_lower, conc_upper).

    Returns:
        The calculated ISPU sub-index (float). Returns 500+ for values
        above the highest breakpoint.
    """
    if concentration < 0:
        return 0.0

    for ispu_lo, ispu_hi, conc_lo, conc_hi in breakpoints:
        if conc_lo <= concentration <= conc_hi:
            ispu = ((ispu_hi - ispu_lo) / (conc_hi - conc_lo)) * (
                concentration - conc_lo
            ) + ispu_lo
            return round(ispu, 1)

    # If concentration exceeds the highest breakpoint, extrapolate
    last = breakpoints[-1]
    ispu_lo, ispu_hi, conc_lo, conc_hi = last
    ispu = ((ispu_hi - ispu_lo) / (conc_hi - conc_lo)) * (
        concentration - conc_lo
    ) + ispu_lo
    return round(ispu, 1)


def calculate_ispu_pm10(pm10_ugm3: float) -> float:
    """Calculate ISPU sub-index for PM10 (µg/m³)."""
    return _calculate_ispu_for_pollutant(pm10_ugm3, ISPU_PM10_BREAKPOINTS)


def calculate_ispu_co(co_ppm: float) -> float:
    """Calculate ISPU sub-index for CO (ppm)."""
    return _calculate_ispu_for_pollutant(co_ppm, ISPU_CO_BREAKPOINTS)


def calculate_ispu_mq135(co2_ppm: float) -> float:
    """Calculate ISPU sub-index for MQ135 gas sensor using CO2-equivalent ppm."""
    return _calculate_ispu_for_pollutant(co2_ppm, ISPU_MQ135_BREAKPOINTS)


def calculate_ispu(
    pm10_ugm3: float,
    co_ppm: Optional[float] = None,
    co2_ppm: Optional[float] = None,
) -> dict:
    """
    Calculate the overall ISPU index from all available pollutant readings.
    The final ISPU is determined by the WORST (highest) sub-index among:
      - PM10  (from GP2Y10 dust sensor, converted to µg/m³)
      - CO    (from MQ7 sensor, converted to ppm)
      - MQ135 (from MQ135 gas sensor, CO2-equivalent ppm)

    Args:
        pm10_ugm3: PM10 concentration in µg/m³.
        co_ppm: Optional CO concentration in ppm (from MQ7).
        co2_ppm: Optional CO2-equivalent concentration in ppm (from MQ135).

    Returns:
        A dict with keys: ispu_pm10, ispu_co, ispu_mq135, ispu_final, category (dict).
    """
    ispu_pm10   = calculate_ispu_pm10(pm10_ugm3)
    ispu_co     = calculate_ispu_co(co_ppm)     if co_ppm  is not None else 0.0
    ispu_mq135  = calculate_ispu_mq135(co2_ppm) if co2_ppm is not None else 0.0

    # Final ISPU = the highest sub-index (worst pollutant dominates)
    ispu_final = max(ispu_pm10, ispu_co, ispu_mq135)
    category   = get_ispu_category(ispu_final)

    return {
        "ispu_pm10":  ispu_pm10,
        "ispu_co":    ispu_co,
        "ispu_mq135": ispu_mq135,
        "ispu_final": ispu_final,
        "category":   category,
    }


def convert_debu_adc_to_ugm3(adc_raw: float) -> float:
    """
    Convert raw ADC value of dust sensor GP2Y1014AU0F to PM10 concentration (µg/m³).

    IMPORTANT: The GP2Y sensor is connected to the Arduino Uno, which uses
    a 5.0 V ADC reference (NOT 3.3 V like the ESP8266). The raw ADC value
    is forwarded to Firebase unchanged, so conversion must use 5.0 V.

    Step 1: Convert raw ADC value (0–1023, 5.0 V reference) to voltage:
      Vout (V) = adc_raw * (5.0 / 1023.0)
    Step 2: Apply Chris Nafis / datasheet linear formula:
      Dust Density (mg/m³) = 0.17 * Vout - 0.1 
      (Note: The -0.1 offset is temporarily removed because the hardware 
      is reading abnormally low ADC values, likely due to missing capacitors)
    Step 3: Convert mg/m³ → µg/m³  (* 1000)
    """
    v_out = float(adc_raw) * (5.0 / 1023.0)
    # Temporary Fix: Removed - 0.1 offset 
    pm10 = max(0.0, (0.17 * v_out) * 1000)
    return round(pm10, 2)


def convert_mq7_adc_to_co_ppm(adc_raw: float) -> float:
    """
    Convert MQ7 raw ADC (0–1023, 5 V Arduino) to CO concentration in ppm.

    Method:
      1. Convert ADC → output voltage (Vout).
      2. Derive sensor resistance Rs using a 10 kΩ load resistor:
           Rs = ((Vcc / Vout) - 1) × RL
      3. Apply power-law from MQ7 datasheet CO curve:
           CO_ppm = 26.717 × (Rs / Ro)^(-1.2894)
         where Ro = 10 000 Ω (assumed clean-air baseline).

    Note: Accuracy depends on sensor warm-up and Ro calibration.
    """
    if adc_raw <= 0:
        return 0.0
    v_out = float(adc_raw) * (5.0 / 1023.0)
    if v_out <= 0:
        return 0.0
    rl = 10_000.0          # load resistor 10 kΩ
    ro = 10_000.0          # baseline resistance in clean air
    rs = ((5.0 / v_out) - 1.0) * rl
    ratio = rs / ro
    if ratio <= 0:
        return 0.0
    co_ppm = max(0.0, 26.717 * (ratio ** -1.2894))
    return round(co_ppm, 2)


def convert_mq135_adc_to_co2_ppm(adc_raw: float) -> float:
    """
    Convert MQ135 raw ADC (0–1023, 5 V Arduino) to CO2-equivalent concentration in ppm.

    Method:
      1. Convert ADC → output voltage (Vout).
      2. Derive Rs using a 20 kΩ load resistor:
           Rs = ((Vcc / Vout) - 1) × RL
      3. Apply power-law from MQ135 CO2 datasheet curve:
           CO2_ppm = 116.6 × (Rs / Ro)^(-2.769)
           
    Calibration:
      Berdasarkan data dari Firebase (ADC ~90 di udara bersih), kita mengatur 
      nilai Ro agar ADC 90 menghasilkan ~400 ppm (udara bersih).
      (Hitungan: di ADC 90, Rs = 207kΩ. Untuk hasil 400ppm, Rs/Ro ≈ 0.643 -> Ro = 322kΩ)
    """
    if adc_raw <= 0:
        return 400.0
    
    v_out = float(adc_raw) * (5.0 / 1023.0)
    if v_out <= 0:
        return 400.0
        
    rl = 20_000.0         # load resistor 20 kΩ 
    ro = 322_000.0        # Kalibrasi custom untuk hardware user (sebelumnya 76630)
    
    rs = ((5.0 / v_out) - 1.0) * rl
    ratio = rs / ro
    
    if ratio <= 0:
        return 400.0
        
    co2_ppm = max(400.0, 116.6020682 * (ratio ** -2.769034857))
    return round(co2_ppm, 1)


# ═══════════════════════════════════════════════════════════════════════════
# CATEGORY LOOKUP
# ═══════════════════════════════════════════════════════════════════════════

def get_ispu_category(ispu_value: float) -> dict:
    """
    Return the ISPU category dict for a given ISPU value.

    Args:
        ispu_value: The ISPU index value.

    Returns:
        The matching category dict from ISPU_CATEGORIES.
    """
    for cat in ISPU_CATEGORIES:
        if cat["min"] <= ispu_value <= cat["max"]:
            return cat
    # If above max, return the worst category
    return ISPU_CATEGORIES[-1]


# ═══════════════════════════════════════════════════════════════════════════
# DATE / TIME UTILITIES
# ═══════════════════════════════════════════════════════════════════════════

# WIB timezone (UTC+7)
WIB = timezone(timedelta(hours=7))


def now_wib() -> datetime:
    """Return the current datetime in WIB (UTC+7)."""
    return datetime.now(WIB)


def format_datetime(dt: Optional[datetime], fmt: str = "%d %b %Y, %H:%M WIB") -> str:
    """
    Format a datetime object to a human-readable string.

    Args:
        dt: The datetime object. If None, returns "-".
        fmt: The strftime format string.

    Returns:
        Formatted datetime string.
    """
    if dt is None:
        return "-"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=WIB)
    return dt.astimezone(WIB).strftime(fmt)


def parse_firestore_timestamp(ts) -> Optional[datetime]:
    """
    Convert a Firestore timestamp (or compatible object) to a Python datetime.

    Args:
        ts: A Firestore DatetimeWithNanoseconds, datetime, or None.

    Returns:
        A timezone-aware datetime in WIB, or None.
    """
    if ts is None:
        return None
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(WIB)
    # Firestore DatetimeWithNanoseconds has a .isoformat() method
    try:
        return datetime.fromisoformat(str(ts)).astimezone(WIB)
    except (ValueError, TypeError):
        return None


def check_database_connection() -> bool:
    """
    Check if the app is connected to the Firebase Firestore database.
    If it is running in offline mode, display a premium warning and stop execution.
    """
    from config.firebase_config import is_offline_mode
    import streamlit as st

    if is_offline_mode():
        # Render the sidebar brand and offline badge manually to keep consistent style
        from config.settings import APP_NAME
        st.sidebar.markdown(f"""
        <div class="sidebar-brand">
            <span class="brand-icon">🌬️</span>
            <p class="brand-name">{APP_NAME}</p>
            <p class="brand-sub">IoT Air Quality Monitoring</p>
        </div>
        """, unsafe_allow_html=True)
        st.sidebar.markdown("<div style='text-align: center;'><span class='conn-badge offline'><span class='pulse-dot'></span>🟠 Offline Mode</span></div>", unsafe_allow_html=True)
        st.sidebar.markdown("---")

        st.markdown(
            """
            <div style="text-align: center; margin-top: 100px;">
                <span style="font-size: 5rem;">🔌</span>
                <h2 style="font-weight: 700; color: #ef4444; margin-top: 20px;">Tidak Terhubung ke Database</h2>
                <p style="color: #8b949e; font-size: 1.1rem; max-width: 500px; margin: 10px auto;">
                    Halaman ini memerlukan koneksi ke database Firebase Firestore.
                    Aplikasi saat ini berjalan tanpa koneksi database. Harap periksa konfigurasi Firebase Anda pada file <code>.env</code>.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.stop()
    return True


# ═══════════════════════════════════════════════════════════════════════════
# OUTLIER DETECTION
# ═══════════════════════════════════════════════════════════════════════════

def is_outlier_reading(
    reading: dict,
    prev_reading: Optional[dict] = None,
) -> bool:
    """
    Determine whether a sensor reading is an outlier based on:
      1. Absolute physical bounds  (outdoor Indonesia thresholds).
      2. Implausible delta from the previous clean reading.

    A reading is flagged as an outlier if:
      - Temperature is 0 °C AND humidity is 0 % at the same time  → DHT22 error
      - Temperature is outside [OUTLIER_TEMP_MIN, OUTLIER_TEMP_MAX]
      - Humidity is outside [OUTLIER_HUM_MIN, OUTLIER_HUM_MAX]
      - The jump from the previous reading exceeds OUTLIER_MAX_*_DELTA

    Args:
        reading:      Current reading dict (must contain 'temperature', 'humidity').
        prev_reading: Previous clean reading dict (optional; enables delta check).

    Returns:
        True  — the reading looks like an outlier / sensor error.
        False — the reading is within acceptable bounds.
    """
    temp = float(reading.get("temperature", 0.0))
    hum  = float(reading.get("humidity",    0.0))

    # 1. DHT22 failure signature: both values collapse to exactly 0
    if temp == 0.0 and hum == 0.0:
        return True

    # 2. Absolute physical bounds
    if not (OUTLIER_TEMP_MIN <= temp <= OUTLIER_TEMP_MAX):
        return True
    if not (OUTLIER_HUM_MIN  <= hum  <= OUTLIER_HUM_MAX):
        return True

    # 3. Delta check vs previous clean reading
    if prev_reading is not None:
        prev_temp = float(prev_reading.get("temperature", temp))
        prev_hum  = float(prev_reading.get("humidity",    hum))
        if abs(temp - prev_temp) > OUTLIER_MAX_TEMP_DELTA:
            return True
        if abs(hum  - prev_hum)  > OUTLIER_MAX_HUM_DELTA:
            return True

    return False


def filter_outlier_readings(readings: list) -> tuple:
    """
    Walk through a **time-sorted** (ascending) list of readings and remove
    outliers using both absolute bounds and consecutive-delta checks.

    Args:
        readings: List of reading dicts sorted by timestamp ascending.

    Returns:
        (clean_readings, removed_count) — a tuple where:
          - clean_readings: readings that passed all outlier checks.
          - removed_count:  number of readings discarded as outliers.
    """
    if not readings:
        return [], 0

    clean: list = []
    removed: int = 0
    prev_clean: Optional[dict] = None

    for r in readings:
        if is_outlier_reading(r, prev_clean):
            removed += 1
        else:
            clean.append(r)
            prev_clean = r

    return clean, removed
