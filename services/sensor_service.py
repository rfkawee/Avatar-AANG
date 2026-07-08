"""
Sensor Service Module
Provides access to sensor readings from Firestore, mapped from ESP8266's 
Indonesian field names (suhu, kelembaban, debu, gas_co_mq7, waktu).
Generates realistic mock data with sinusoidal variation when running in offline mode.
"""
import math
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
import pandas as pd

from config.firebase_config import is_offline_mode
from config.settings import COLLECTION_DEVICES
from services.firebase_service import get_collection, query_collection
from utils.constants import (
    DEFAULT_DEVICE_IDS,
    MOCK_RANGES,
    MOCK_HISTORY_COUNT,
)
from utils.helper import (
    calculate_ispu,
    now_wib,
    parse_firestore_timestamp,
    WIB,
)
from utils.logger import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# MAPPING HELPER
# ═══════════════════════════════════════════════════════════════════════════

def _map_esp_reading(data: Dict[str, Any], device_id: str) -> Dict[str, Any]:
    """
    Map ESP8266 Indonesian Firestore fields to the dashboard's standard fields.
    ESP8266 Fields:
      - suhu -> temperature
      - kelembaban -> humidity
      - debu -> pm10
      - gas_co_mq7 -> co
      - waktu -> timestamp (parsed string)
    """
    temperature = float(data.get("suhu", 0.0))
    humidity = float(data.get("kelembaban", 0.0))
    pm10 = float(data.get("debu", 0.0))
    co = float(data.get("gas_co_mq7", 0.0))

    waktu_str = data.get("waktu", "")
    try:
        ts = datetime.strptime(waktu_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=WIB)
    except Exception:
        # Fallback to document ID as unix timestamp or now
        doc_id = data.get("id", "")
        if doc_id.isdigit():
            ts = datetime.fromtimestamp(int(doc_id), tz=timezone.utc).astimezone(WIB)
        else:
            ts = now_wib()

    # Calculate ISPU
    ispu_result = calculate_ispu(pm10, co)

    return {
        "id": data.get("id"),
        "device_id": device_id,
        "timestamp": ts,
        "temperature": temperature,
        "humidity": humidity,
        "pm10": pm10,
        "co": co,
        **ispu_result,
    }


# ═══════════════════════════════════════════════════════════════════════════
# MOCK DATA GENERATION
# ═══════════════════════════════════════════════════════════════════════════

def _sinusoidal_value(
    base: float,
    amplitude: float,
    period_minutes: float,
    minute_offset: float,
    noise_pct: float = 0.05,
) -> float:
    """Generate a sinusoidal value with optional Gaussian noise."""
    angle = 2 * math.pi * minute_offset / period_minutes
    noise = random.gauss(0, amplitude * noise_pct)
    return base + amplitude * math.sin(angle) + noise


def _generate_mock_reading(device_id: str, timestamp: datetime) -> Dict[str, Any]:
    """Generate a single realistic mock sensor reading."""
    minutes_since_midnight = timestamp.hour * 60 + timestamp.minute

    # Temperature: peaks around 14:00 (840 min), period = 1440 min (24 h)
    temp_min, temp_max = MOCK_RANGES["temperature"]
    temp_base = (temp_min + temp_max) / 2
    temp_amp = (temp_max - temp_min) / 2
    temperature = _sinusoidal_value(
        temp_base, temp_amp * 0.6, 1440, minutes_since_midnight - 360, noise_pct=0.08
    )
    temperature = max(temp_min, min(temp_max, round(temperature, 1)))

    # Humidity: inverse of temperature
    hum_min, hum_max = MOCK_RANGES["humidity"]
    hum_base = (hum_min + hum_max) / 2
    hum_amp = (hum_max - hum_min) / 2
    humidity = _sinusoidal_value(
        hum_base, hum_amp * 0.6, 1440, minutes_since_midnight + 360, noise_pct=0.08
    )
    humidity = max(hum_min, min(hum_max, round(humidity, 1)))

    # PM10: 12-hour cycle (two peaks per day — rush hours)
    pm_min, pm_max = MOCK_RANGES["pm10"]
    pm_base = (pm_min + pm_max) / 2 * 0.4
    pm_amp = (pm_max - pm_min) / 2 * 0.35
    pm10 = _sinusoidal_value(
        pm_base, pm_amp, 720, minutes_since_midnight, noise_pct=0.15
    )
    pm10 = max(pm_min, min(pm_max, round(pm10, 1)))

    # CO: same rhythm as PM10, scaled to ppm
    co_min, co_max = MOCK_RANGES["co"]
    co_base = (co_min + co_max) / 2 * 0.35
    co_amp = (co_max - co_min) / 2 * 0.3
    co = _sinusoidal_value(
        co_base, co_amp, 720, minutes_since_midnight + 30, noise_pct=0.15
    )
    co = max(co_min, min(co_max, round(co, 2)))

    # ISPU
    ispu_result = calculate_ispu(pm10, co)

    return {
        "device_id": device_id,
        "timestamp": timestamp,
        "temperature": temperature,
        "humidity": humidity,
        "pm10": pm10,
        "co": co,
        **ispu_result,
    }


def _generate_mock_history(
    device_id: str,
    count: int = MOCK_HISTORY_COUNT,
    end_time: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Generate a list of mock readings going backwards from end_time."""
    if end_time is None:
        end_time = now_wib()

    readings = []
    for i in range(count):
        ts = end_time - timedelta(minutes=i)
        readings.append(_generate_mock_reading(device_id, ts))
    return readings


# ═══════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════

def get_latest_reading(device_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve the latest sensor reading for a device from kualitas_udara/{device_id}/logs."""
    if is_offline_mode():
        reading = _generate_mock_reading(device_id, now_wib())
        logger.debug("[MOCK] Generated latest reading for '%s'.", device_id)
        return reading

    try:
        # Fetch the latest log document by sorting by 'waktu' descending
        docs = query_collection(
            f"kualitas_udara/{device_id}/logs",
            field="waktu",
            operator=">=",
            value="",
            order_by="waktu",
            order_direction="DESCENDING",
            limit=1
        )

        if docs:
            return _map_esp_reading(docs[0], device_id)

        logger.warning("No readings found for device '%s' in Firestore subcollection.", device_id)
        return None

    except Exception as e:
        logger.error("Error fetching latest reading for '%s': %s", device_id, e)
        return None


def get_readings(
    device_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Retrieve sensor readings for a device within an optional date range."""
    current_time = now_wib()
    
    import datetime as dt

    if end_date is None:
        end_date = current_time
    elif not isinstance(end_date, datetime):
        # Convert date to aware datetime (end of day)
        end_date = datetime.combine(end_date, dt.time.max).replace(tzinfo=WIB)

    if start_date is None:
        start_date = current_time - timedelta(hours=24)
    elif not isinstance(start_date, datetime):
        # Convert date to aware datetime (start of day)
        start_date = datetime.combine(start_date, dt.time.min).replace(tzinfo=WIB)

    if is_offline_mode():
        total_minutes = int((end_date - start_date).total_seconds() / 60)
        count = min(total_minutes, MOCK_HISTORY_COUNT)
        all_readings = _generate_mock_history(device_id, count, end_time=end_date)
        filtered = [
            r for r in all_readings
            if start_date <= r["timestamp"] <= end_date
        ]
        logger.debug("[MOCK] Returning %d readings for '%s'.", len(filtered[:limit]), device_id)
        return filtered[:limit]

    try:
        # Fetch the latest documents for this device subcollection, then filter by date in Python
        query_limit = max(limit, 500)
        docs = query_collection(
            f"kualitas_udara/{device_id}/logs",
            field="waktu",
            operator=">=",
            value="",
            order_by="waktu",
            order_direction="DESCENDING",
            limit=query_limit
        )

        results = []
        for raw_data in docs:
            data = _map_esp_reading(raw_data, device_id)
            ts = data["timestamp"]

            if ts and start_date <= ts <= end_date:
                results.append(data)
                if len(results) >= limit:
                    break

        return results

    except Exception as e:
        logger.error("Error fetching readings for '%s': %s", device_id, e)
        return []


def get_readings_dataframe(
    device_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> pd.DataFrame:
    """Retrieve sensor readings as a pandas DataFrame."""
    try:
        readings = get_readings(
            device_id,
            start_date=start_date,
            end_date=end_date,
            limit=MOCK_HISTORY_COUNT,
        )

        if not readings:
            return pd.DataFrame()

        df = pd.DataFrame(readings)

        if "category" in df.columns:
            df["category_label"] = df["category"].apply(
                lambda c: c.get("label", "") if isinstance(c, dict) else ""
            )

        if "timestamp" in df.columns:
            df = df.sort_values("timestamp").reset_index(drop=True)

        return df

    except Exception as e:
        logger.error("Error building DataFrame for '%s': %s", device_id, e)
        return pd.DataFrame()


def get_all_device_ids() -> List[str]:
    """Retrieve a list of all registered device IDs."""
    if is_offline_mode():
        logger.debug("[MOCK] Returning default device IDs: %s", DEFAULT_DEVICE_IDS)
        return list(DEFAULT_DEVICE_IDS)

    try:
        docs = get_collection(COLLECTION_DEVICES)
        device_ids = []
        for data in docs:
            did = data.get("device_id", data.get("id"))
            if did:
                device_ids.append(did)

        if not device_ids:
            logger.warning("No devices found in Firestore — using defaults.")
            return list(DEFAULT_DEVICE_IDS)

        return device_ids

    except Exception as e:
        logger.error("Error fetching device IDs: %s", e)
        return list(DEFAULT_DEVICE_IDS)
