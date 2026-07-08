"""
Firebase Configuration Module
Provides helper functions for identifying offline mock mode.
No longer requires the service account key for Firestore CRUD.
"""
import os
from utils.logger import get_logger

logger = get_logger(__name__)

_is_offline = True
_project_id = ""
_api_key = ""


def initialize_firebase():
    """
    Checks if a valid Firebase Project ID is configured in the environment.
    Sets is_offline = False if a valid ID is provided, else True.
    """
    global _is_offline, _project_id, _api_key

    _project_id = os.getenv("FIREBASE_PROJECT_ID", "").strip()
    _api_key = os.getenv("FIREBASE_API_KEY", "").strip()

    if not _project_id or _project_id == "your-project-id":
        logger.warning(
            "FIREBASE_PROJECT_ID is empty or default. "
            "Running in OFFLINE MOCK MODE."
        )
        _is_offline = True
    else:
        logger.info(f"Firebase REST configuration initialized for Project ID: {_project_id}")
        _is_offline = False


def get_project_id():
    """Return the configured Firebase Project ID."""
    return _project_id


def get_api_key():
    """Return the configured Firebase API Key."""
    return _api_key


def is_offline_mode():
    """Return True if the app is running in offline mock mode."""
    return _is_offline
