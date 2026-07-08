"""
Alert Service Module
Manages air quality alerts based on ISPU thresholds.
Uses firebase_service REST operations rather than direct firebase_admin calls.
Falls back to mock alerts when running in offline mode.
"""
import random
import uuid
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from config.firebase_config import is_offline_mode
from config.settings import COLLECTION_ALERTS
from services.firebase_service import add_document, get_collection, update_document, query_collection
from utils.constants import (
    ALERT_ISPU_THRESHOLD,
    DEFAULT_DEVICE_IDS,
    ISPU_CATEGORIES,
    MOCK_RANGES,
)
from utils.helper import (
    calculate_ispu,
    get_ispu_category,
    now_wib,
    parse_firestore_timestamp,
    WIB,
)
from utils.logger import get_logger

logger = get_logger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# MOCK ALERT GENERATION
# ═══════════════════════════════════════════════════════════════════════════

_mock_alerts: List[Dict[str, Any]] = []
_mock_alerts_generated = False


def _ensure_mock_alerts() -> None:
    """Lazily generate sample mock alerts (once)."""
    global _mock_alerts, _mock_alerts_generated
    if _mock_alerts_generated:
        return
    _mock_alerts_generated = True

    current = now_wib()
    # Generate ~15 sample alerts spread over the last 48 hours
    for i in range(15):
        device_id = random.choice(DEFAULT_DEVICE_IDS)
        ts = current - timedelta(hours=random.uniform(1, 48))

        pm10 = random.uniform(160, 350)
        co = random.uniform(10.0, 25.0)
        ispu_result = calculate_ispu(pm10, co)
        ispu_value = ispu_result["ispu_final"]
        category = ispu_result["category"]

        _mock_alerts.append({
            "id": str(uuid.uuid4()),
            "device_id": device_id,
            "timestamp": ts,
            "category": category.get("label", "Tidak Sehat"),
            "ispu_value": round(ispu_value, 1),
            "pm10": round(pm10, 1),
            "co": round(co, 2),
            "message": (
                f"ISPU {round(ispu_value, 1)} ({category.get('label', '')}) "
                f"terdeteksi pada perangkat {device_id}."
            ),
            "acknowledged": random.choice([True, False, False]),
        })

    # Sort newest first
    _mock_alerts.sort(key=lambda a: a["timestamp"], reverse=True)
    logger.debug("[MOCK] Generated %d sample alerts.", len(_mock_alerts))


# ═══════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════

def check_and_create_alert(
    device_id: str, reading: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Evaluate a sensor reading and create an alert if the ISPU is unhealthy.
    """
    ispu_value = reading.get("ispu_final", 0)

    if ispu_value < ALERT_ISPU_THRESHOLD:
        return None

    category = reading.get("category", {})
    category_label = (
        category.get("label", "Tidak Sehat") if isinstance(category, dict) else str(category)
    )

    alert_data = {
        "device_id": device_id,
        "timestamp": reading.get("timestamp", now_wib()),
        "category": category_label,
        "ispu_value": round(ispu_value, 1),
        "pm10": round(reading.get("pm10", 0), 1),
        "co": round(reading.get("co", 0), 2),
        "message": (
            f"ISPU {round(ispu_value, 1)} ({category_label}) "
            f"terdeteksi pada perangkat {device_id}."
        ),
        "acknowledged": False,
    }

    if is_offline_mode():
        alert_id = str(uuid.uuid4())
        alert_data["id"] = alert_id
        _ensure_mock_alerts()
        _mock_alerts.insert(0, alert_data)
        logger.debug("[MOCK] Created alert '%s' for device '%s'.", alert_id, device_id)
        return alert_data

    try:
        new_id = add_document(COLLECTION_ALERTS, alert_data)
        if new_id:
            alert_data["id"] = new_id
            logger.info("Alert created: %s (ISPU %.1f) for device '%s'.", new_id, ispu_value, device_id)
            return alert_data
        return None

    except Exception as e:
        logger.error("Error creating alert for device '%s': %s", device_id, e)
        return None


def get_alerts(
    device_id: Optional[str] = None, limit: int = 50
) -> List[Dict[str, Any]]:
    """Retrieve alert documents, optionally filtered by device."""
    if is_offline_mode():
        _ensure_mock_alerts()
        alerts = list(_mock_alerts)
        if device_id:
            alerts = [a for a in alerts if a.get("device_id") == device_id]
        return alerts[:limit]

    try:
        if device_id:
            results = query_collection(
                COLLECTION_ALERTS,
                field="device_id",
                operator="==",
                value=device_id,
                order_by="timestamp",
                limit=limit
            )
        else:
            results = get_collection(COLLECTION_ALERTS)

        # Parse timestamps and sort newest first
        for data in results:
            data["timestamp"] = parse_firestore_timestamp(data.get("timestamp"))

        results.sort(key=lambda x: x.get("timestamp") or datetime.min.replace(tzinfo=WIB), reverse=True)
        return results[:limit]

    except Exception as e:
        logger.error("Error fetching alerts: %s", e)
        return []


def acknowledge_alert(alert_id: str) -> bool:
    """Mark an alert as acknowledged."""
    if is_offline_mode():
        _ensure_mock_alerts()
        for alert in _mock_alerts:
            if alert.get("id") == alert_id:
                alert["acknowledged"] = True
                logger.debug("[MOCK] Acknowledged alert '%s'.", alert_id)
                return True
        logger.warning("[MOCK] Alert '%s' not found.", alert_id)
        return False

    try:
        success = update_document(COLLECTION_ALERTS, alert_id, {"acknowledged": True})
        if success:
            logger.info("Alert '%s' acknowledged.", alert_id)
        return success

    except Exception as e:
        logger.error("Error acknowledging alert '%s': %s", alert_id, e)
        return False


def get_alert_summary() -> Dict[str, Any]:
    """Return a summary of alerts grouped by ISPU category."""
    alerts = get_alerts(limit=200)

    total = len(alerts)
    unacknowledged = sum(1 for a in alerts if not a.get("acknowledged", False))

    by_category = dict(Counter(a.get("category", "Unknown") for a in alerts))
    by_device = dict(Counter(a.get("device_id", "Unknown") for a in alerts))

    return {
        "total": total,
        "unacknowledged": unacknowledged,
        "by_category": by_category,
        "by_device": by_device,
    }
