"""
Application Settings Module
Loads configuration from environment variables and provides global constants.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── App ──────────────────────────────────────────────────────────────────
APP_NAME = os.getenv("APP_NAME", "AirSense")
REFRESH_INTERVAL_SECONDS = int(os.getenv("REFRESH_INTERVAL_SECONDS", "60"))
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"

# ── Firebase ─────────────────────────────────────────────────────────────
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "")
FIREBASE_SERVICE_ACCOUNT_KEY = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY", "")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")

# ── Firestore Collection Names ───────────────────────────────────────────
COLLECTION_DEVICES = "devices"
COLLECTION_SENSOR_DATA = "sensor_data"
COLLECTION_ALERTS = "alerts"
COLLECTION_THRESHOLDS = "thresholds"
