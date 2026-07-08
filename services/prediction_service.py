"""
Prediction Service Module
Placeholder for future ML-based air quality predictions.
Currently provides a mock 24-hour forecast using sinusoidal patterns for
demonstration and UI development purposes.
"""
import math
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from utils.constants import MOCK_RANGES
from utils.helper import calculate_ispu_pm10, calculate_ispu_co, now_wib, WIB
from utils.logger import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════

def is_model_available() -> bool:
    """
    Check whether a trained prediction model is available.

    Returns:
        False — no real model is integrated yet. This is a placeholder.
    """
    return False


def get_prediction(device_id: str) -> Optional[Dict[str, Any]]:
    """
    Generate a real prediction for the given device.

    This is a placeholder that always returns None until a trained model
    (e.g. LSTM, Prophet, or ARIMA) is integrated.

    Args:
        device_id: The device identifier.

    Returns:
        None — no model available.
    """
    if not is_model_available():
        logger.debug(
            "No prediction model available for device '%s'. "
            "Use get_mock_prediction() for simulated data.",
            device_id,
        )
        return None
    return None


def get_mock_prediction(device_id: str) -> Dict[str, Any]:
    """
    Generate a simulated 24-hour forecast using sinusoidal patterns.

    The mock forecast produces hourly data points starting from the current
    time. PM10 and CO values follow a diurnal cycle with two peaks (rush-hour
    pattern), and ISPU is derived from those values.

    Args:
        device_id: The device identifier (used for labelling only).

    Returns:
        A dict containing:

        - ``device_id`` (str): The device identifier.
        - ``generated_at`` (datetime): When the forecast was created.
        - ``timestamps`` (list[datetime]): 24 hourly timestamps.
        - ``pm10_predicted`` (list[float]): Predicted PM10 (µg/m³).
        - ``co_predicted`` (list[float]): Predicted CO (ppm).
        - ``ispu_predicted`` (list[float]): Predicted ISPU index values.
    """
    current = now_wib()
    timestamps: List[datetime] = []
    pm10_predicted: List[float] = []
    co_predicted: List[float] = []
    ispu_predicted: List[float] = []

    # Parameter ranges
    pm_min, pm_max = MOCK_RANGES["pm10"]
    co_min, co_max = MOCK_RANGES["co"]

    pm_base = (pm_min + pm_max) / 2 * 0.45
    pm_amp = (pm_max - pm_min) / 2 * 0.35
    co_base = (co_min + co_max) / 2 * 0.40
    co_amp = (co_max - co_min) / 2 * 0.30

    for hour_offset in range(24):
        ts = current + timedelta(hours=hour_offset)
        timestamps.append(ts)

        # Minutes since midnight for this forecast hour
        mins = ts.hour * 60 + ts.minute

        # PM10: 12-hour cycle (two peaks per day)
        angle_pm = 2 * math.pi * mins / 720
        noise_pm = random.gauss(0, pm_amp * 0.08)
        pm10_val = pm_base + pm_amp * math.sin(angle_pm) + noise_pm
        pm10_val = max(pm_min, min(pm_max, round(pm10_val, 1)))

        # CO: same rhythm, slightly phase-shifted
        angle_co = 2 * math.pi * (mins + 30) / 720
        noise_co = random.gauss(0, co_amp * 0.08)
        co_val = co_base + co_amp * math.sin(angle_co) + noise_co
        co_val = max(co_min, min(co_max, round(co_val, 2)))

        # ISPU: derived from pm10 and co predictions
        ispu_pm10 = calculate_ispu_pm10(pm10_val)
        ispu_co = calculate_ispu_co(co_val)
        ispu_val = round(max(ispu_pm10, ispu_co), 1)

        pm10_predicted.append(pm10_val)
        co_predicted.append(co_val)
        ispu_predicted.append(ispu_val)

    logger.debug(
        "[MOCK] Generated 24-hour forecast for device '%s'.", device_id
    )

    return {
        "device_id": device_id,
        "generated_at": current,
        "timestamps": timestamps,
        "pm10_predicted": pm10_predicted,
        "co_predicted": co_predicted,
        "ispu_predicted": ispu_predicted,
    }
