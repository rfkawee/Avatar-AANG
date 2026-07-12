"""
Prediction Service Module
Integrates the trained LSTM model for air quality forecasting.
Supports autoregressive multi-step prediction using historical
sensor data from Firebase Firestore.
"""
import os
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from utils.helper import calculate_ispu_pm10, now_wib, WIB, convert_debu_adc_to_ugm3
from utils.logger import get_logger

logger = get_logger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# MODEL & SCALER PATHS
# ═══════════════════════════════════════════════════════════════════════════

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MODEL_PATH = os.path.join(_BASE_DIR, "models", "model_lstm_kualitas_udara.keras")
_SCALER_PATH = os.path.join(_BASE_DIR, "models", "scaler.pkl")

# Feature order MUST match the training notebook exactly
FEATURES = ["suhu", "kelembaban", "debu", "gas_mq7", "gas_mq135"]
WINDOW_SIZE = 60  # Number of past timesteps required by the LSTM


# ═══════════════════════════════════════════════════════════════════════════
# LAZY LOADING (loaded once, cached in module globals)
# ═══════════════════════════════════════════════════════════════════════════

_model = None
_scaler = None


def _load_model():
    """Lazy-load the Keras model."""
    global _model
    if _model is None:
        try:
            import tensorflow as tf
            _model = tf.keras.models.load_model(_MODEL_PATH)
            logger.info("LSTM model loaded from: %s", _MODEL_PATH)
        except Exception as e:
            logger.error("Failed to load LSTM model: %s", e)
            _model = None
    return _model


def _load_scaler():
    """Lazy-load the MinMaxScaler."""
    global _scaler
    if _scaler is None:
        try:
            import joblib
            _scaler = joblib.load(_SCALER_PATH)
            logger.info("Scaler loaded from: %s", _SCALER_PATH)
        except Exception as e:
            logger.error("Failed to load scaler: %s", e)
            _scaler = None
    return _scaler


# ═══════════════════════════════════════════════════════════════════════════
# RAW DATA FETCHER (bypasses sensor_service mapping)
# ═══════════════════════════════════════════════════════════════════════════

def _fetch_raw_readings(device_id: str, limit: int) -> List[Dict[str, Any]]:
    """
    Fetch raw sensor data directly from Firebase without ADC→µg/m³ conversion.
    This is necessary because the LSTM model was trained on RAW ADC values
    for the 'debu' column (e.g. 277, 285), not converted µg/m³ values.
    """
    from config.firebase_config import is_offline_mode
    from services.firebase_service import query_collection

    if is_offline_mode():
        # In offline/mock mode, generate synthetic raw readings
        import math
        import random
        current = now_wib()
        readings = []
        for i in range(limit):
            ts = current - timedelta(minutes=(limit - 1 - i))
            mins = ts.hour * 60 + ts.minute
            readings.append({
                "suhu": round(30 + 3 * math.sin(2 * math.pi * mins / 1440) + random.gauss(0, 0.3), 1),
                "kelembaban": round(65 - 5 * math.sin(2 * math.pi * mins / 1440) + random.gauss(0, 0.5), 1),
                "debu": round(280 + 10 * math.sin(2 * math.pi * mins / 720) + random.gauss(0, 2), 1),
                "gas_mq7": float(random.choice([0, 1])),
                "gas_mq135": float(random.choice([0, 1])),
                "waktu": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp": ts,
            })
        return readings

    try:
        docs = query_collection(
            f"kualitas_udara/{device_id}/logs",
            field="waktu",
            operator=">=",
            value="",
            order_by="waktu",
            order_direction="DESCENDING",
            limit=limit,
        )

        results = []
        for raw in docs:
            waktu_str = raw.get("waktu", "")
            try:
                ts = datetime.strptime(waktu_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=WIB)
            except Exception:
                doc_id = raw.get("id", "")
                if isinstance(doc_id, str) and doc_id.isdigit():
                    ts = datetime.fromtimestamp(int(doc_id), tz=timezone.utc).astimezone(WIB)
                else:
                    ts = now_wib()

            results.append({
                "suhu": float(raw.get("suhu", 0.0)),
                "kelembaban": float(raw.get("kelembaban", 0.0)),
                "debu": float(raw.get("debu", 0.0)),
                "gas_mq7": float(raw.get("gas_mq7", raw.get("gas_co_mq7", 0.0))),
                "gas_mq135": float(raw.get("gas_mq135", raw.get("mq135", 0.0))),
                "waktu": waktu_str,
                "timestamp": ts,
            })

        return results

    except Exception as e:
        logger.error("Error fetching raw readings for '%s': %s", device_id, e)
        return []


# ═══════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════

def is_model_available() -> bool:
    """
    Check whether both the trained model and scaler files exist on disk.
    """
    return os.path.isfile(_MODEL_PATH) and os.path.isfile(_SCALER_PATH)


def get_live_prediction(
    device_id: str,
    steps: int = 60,
) -> Optional[Dict[str, Any]]:
    """
    Generate a multi-step autoregressive forecast using the trained LSTM model.

    Workflow:
        1. Fetch the last WINDOW_SIZE (60) RAW readings from Firebase.
        2. Scale the feature columns using the saved MinMaxScaler.
        3. Predict 1 step ahead, append result, slide window, repeat for N steps.
        4. Inverse-transform the predictions back to real-world units.
        5. Calculate ISPU from predicted debu (raw ADC → µg/m³ conversion).

    Args:
        device_id: The device identifier to pull historical data from.
        steps: Number of future timesteps to forecast (default 60).

    Returns:
        A dict with timestamps, predicted values per feature, and ISPU.
        None if model/scaler are unavailable or data is insufficient.
    """
    model = _load_model()
    scaler = _load_scaler()

    if model is None or scaler is None:
        logger.warning("Model or scaler not available — cannot generate prediction.")
        return None

    # ── 1. Fetch RAW historical data ─────────────────────────────────
    raw_readings = _fetch_raw_readings(device_id, limit=WINDOW_SIZE + 10)

    if not raw_readings or len(raw_readings) < WINDOW_SIZE:
        logger.warning(
            "Insufficient data for device '%s': got %d, need %d.",
            device_id, len(raw_readings) if raw_readings else 0, WINDOW_SIZE,
        )
        return None

    # Sort by timestamp ascending (oldest first)
    raw_readings.sort(key=lambda r: r["timestamp"])

    # Take the last WINDOW_SIZE readings
    recent = raw_readings[-WINDOW_SIZE:]

    # ── 2. Build feature matrix & scale ──────────────────────────────
    raw_matrix = []
    timestamps_history = []
    history_debu_raw = []

    for r in recent:
        row = [
            r["suhu"],
            r["kelembaban"],
            r["debu"],           # RAW ADC value (as used in training)
            r["gas_mq7"],
            r["gas_mq135"],
        ]
        raw_matrix.append(row)
        timestamps_history.append(r["timestamp"])
        history_debu_raw.append(r["debu"])

    raw_arr = np.array(raw_matrix, dtype=np.float64)
    scaled_arr = scaler.transform(raw_arr)

    # ── 3. Autoregressive prediction loop ────────────────────────────
    window = scaled_arr.copy()  # shape: (WINDOW_SIZE, 5)
    predictions_scaled = []

    for _ in range(steps):
        input_seq = window.reshape(1, WINDOW_SIZE, len(FEATURES))
        pred = model.predict(input_seq, verbose=0)[0]  # shape: (5,)
        predictions_scaled.append(pred)
        # Slide window: drop oldest, append prediction
        window = np.vstack([window[1:], pred.reshape(1, -1)])

    predictions_scaled = np.array(predictions_scaled)  # shape: (steps, 5)

    # ── 4. Inverse transform ─────────────────────────────────────────
    predictions_real = scaler.inverse_transform(predictions_scaled)

    # ── 5. Build output ──────────────────────────────────────────────
    last_ts = timestamps_history[-1]
    # Estimate interval between readings
    if len(timestamps_history) >= 2:
        avg_delta = (timestamps_history[-1] - timestamps_history[0]).total_seconds() / (len(timestamps_history) - 1)
        interval = timedelta(seconds=max(avg_delta, 30))  # at least 30s
    else:
        interval = timedelta(minutes=1)

    forecast_timestamps = []
    suhu_pred = []
    kelembaban_pred = []
    debu_pred = []
    ispu_predicted = []

    for i in range(steps):
        ts = last_ts + interval * (i + 1)
        forecast_timestamps.append(ts)

        suhu_val = round(float(predictions_real[i, 0]), 1)
        kelembaban_val = round(float(predictions_real[i, 1]), 1)
        debu_val = round(float(predictions_real[i, 2]), 1)

        # Convert raw ADC debu → µg/m³ for ISPU calculation
        pm10_ugm3 = convert_debu_adc_to_ugm3(debu_val)

        ispu_val = round(calculate_ispu_pm10(pm10_ugm3), 1)

        suhu_pred.append(suhu_val)
        kelembaban_pred.append(kelembaban_val)
        debu_pred.append(debu_val)
        ispu_predicted.append(ispu_val)

    logger.info(
        "Generated %d-step forecast for device '%s'.", steps, device_id
    )

    return {
        "device_id": device_id,
        "generated_at": now_wib(),
        "timestamps": forecast_timestamps,
        "suhu_predicted": suhu_pred,
        "kelembaban_predicted": kelembaban_pred,
        "debu_predicted": debu_pred,
        "ispu_predicted": ispu_predicted,
        "history_timestamps": timestamps_history,
        "history_debu": history_debu_raw,
    }
