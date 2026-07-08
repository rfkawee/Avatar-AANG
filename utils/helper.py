"""
Helper Utility Module
Provides Indonesian ISPU calculation, date parsing, and general utilities.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from utils.constants import (
    ISPU_PM10_BREAKPOINTS,
    ISPU_CO_BREAKPOINTS,
    ISPU_CATEGORIES,
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


def calculate_ispu(pm10_ugm3: float, co_ppm: float) -> dict:
    """
    Calculate the overall ISPU index from PM10 and CO readings.
    The final ISPU is the maximum of the individual sub-indices.

    Args:
        pm10_ugm3: PM10 concentration in µg/m³.
        co_ppm: CO concentration in ppm.

    Returns:
        A dict with keys: ispu_pm10, ispu_co, ispu_final, category (dict).
    """
    ispu_pm10 = calculate_ispu_pm10(pm10_ugm3)
    ispu_co = calculate_ispu_co(co_ppm)
    ispu_final = max(ispu_pm10, ispu_co)
    category = get_ispu_category(ispu_final)

    return {
        "ispu_pm10": ispu_pm10,
        "ispu_co": ispu_co,
        "ispu_final": ispu_final,
        "category": category,
    }


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
