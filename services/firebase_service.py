"""
Firebase Service Module
Wrapper around Firestore operations using the Firebase REST API.
No private key file or service account is needed, only FIREBASE_PROJECT_ID.
Falls back to an in-memory dict store when running in offline mock mode.
"""
import uuid
import requests
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config.firebase_config import get_project_id, get_api_key, is_offline_mode
from config.settings import (
    COLLECTION_DEVICES,
    COLLECTION_SENSOR_DATA,
    COLLECTION_ALERTS,
    COLLECTION_THRESHOLDS,
)
from utils.logger import get_logger

logger = get_logger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# IN-MEMORY STORE (used in offline / mock mode)
# ═══════════════════════════════════════════════════════════════════════════

_mock_store: Dict[str, Dict[str, Dict[str, Any]]] = {
    COLLECTION_DEVICES: {},
    COLLECTION_SENSOR_DATA: {},
    COLLECTION_ALERTS: {},
    COLLECTION_THRESHOLDS: {},
}


def _get_mock_collection(collection_name: str) -> Dict[str, Dict[str, Any]]:
    """Return (and lazily create) the in-memory collection dict."""
    if collection_name not in _mock_store:
        _mock_store[collection_name] = {}
    return _mock_store[collection_name]


# ═══════════════════════════════════════════════════════════════════════════
# REST API PARSERS
# ═══════════════════════════════════════════════════════════════════════════

def _parse_firestore_value(value_dict: dict) -> Any:
    """Parse a single Firestore REST value dict to its Python type."""
    if not value_dict or not isinstance(value_dict, dict):
        return None

    key = list(value_dict.keys())[0]
    val = value_dict[key]

    if key == "stringValue":
        return str(val)
    elif key == "integerValue":
        return int(val)
    elif key == "doubleValue":
        return float(val)
    elif key == "booleanValue":
        return bool(val)
    elif key == "timestampValue":
        from utils.helper import parse_firestore_timestamp
        return parse_firestore_timestamp(val)
    elif key == "nullValue":
        return None
    elif key == "arrayValue":
        values = val.get("values", [])
        return [_parse_firestore_value(v) for v in values]
    elif key == "mapValue":
        fields = val.get("fields", {})
        return {k: _parse_firestore_value(v) for k, v in fields.items()}

    return val


def _to_firestore_value(val: Any) -> dict:
    """Convert a Python value to Firestore REST value format."""
    if val is None:
        return {"nullValue": None}
    elif isinstance(val, bool):
        return {"booleanValue": val}
    elif isinstance(val, int):
        return {"integerValue": str(val)}
    elif isinstance(val, float):
        return {"doubleValue": val}
    elif isinstance(val, str):
        return {"stringValue": val}
    elif isinstance(val, datetime):
        if val.tzinfo is None:
            return {"timestampValue": val.strftime("%Y-%m-%dT%H:%M:%SZ")}
        return {"timestampValue": val.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    elif isinstance(val, list):
        return {"arrayValue": {"values": [_to_firestore_value(v) for v in val]}}
    elif isinstance(val, dict):
        return {"mapValue": {"fields": {k: _to_firestore_value(v) for k, v in val.items()}}}

    return {"stringValue": str(val)}


def _parse_firestore_doc(doc_dict: dict) -> dict:
    """Convert a Firestore REST document to a flat Python dict."""
    doc_id = doc_dict.get("name", "").split("/")[-1]
    fields = doc_dict.get("fields", {})
    parsed_fields = {k: _parse_firestore_value(v) for k, v in fields.items()}
    parsed_fields["id"] = doc_id
    return parsed_fields


# ═══════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════

def get_collection(collection_name: str) -> List[Dict[str, Any]]:
    """
    Retrieve all documents from a Firestore collection using REST API.
    Supports nested subcollection paths (e.g. "kualitas_udara/ruang1/logs").
    """
    if is_offline_mode():
        collection = _get_mock_collection(collection_name)
        return [{"id": doc_id, **doc} for doc_id, doc in collection.items()]

    try:
        project_id = get_project_id()
        api_key = get_api_key()
        url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/{collection_name}?key={api_key}"
        res = requests.get(url)
        if res.status_code == 404:
            return []
        res.raise_for_status()

        data = res.json()
        docs = data.get("documents", [])
        return [_parse_firestore_doc(doc) for doc in docs]

    except Exception as e:
        logger.error("Error fetching collection '%s' via REST: %s", collection_name, e)
        return []


def get_document(collection_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a single document by its ID using REST API.
    """
    if is_offline_mode():
        collection = _get_mock_collection(collection_name)
        doc = collection.get(doc_id)
        if doc is not None:
            return {"id": doc_id, **doc}
        return None

    try:
        project_id = get_project_id()
        api_key = get_api_key()
        url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/{collection_name}/{doc_id}?key={api_key}"
        res = requests.get(url)
        if res.status_code == 404:
            return None
        res.raise_for_status()

        return _parse_firestore_doc(res.json())

    except Exception as e:
        logger.error("Error fetching document '%s/%s' via REST: %s", collection_name, doc_id, e)
        return None


def add_document(
    collection_name: str, data: Dict[str, Any], doc_id: Optional[str] = None
) -> Optional[str]:
    """
    Add a new document to a Firestore collection using REST API.
    """
    if is_offline_mode():
        generated_id = doc_id or str(uuid.uuid4())
        collection = _get_mock_collection(collection_name)
        collection[generated_id] = dict(data)
        logger.debug("[MOCK] Added document '%s' to '%s'.", generated_id, collection_name)
        return generated_id

    try:
        project_id = get_project_id()
        url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/{collection_name}"

        params = {"key": get_api_key()}
        if doc_id:
            params["documentId"] = doc_id

        payload = {
            "fields": {k: _to_firestore_value(v) for k, v in data.items()}
        }

        res = requests.post(url, json=payload, params=params)
        res.raise_for_status()

        res_data = res.json()
        new_id = res_data.get("name", "").split("/")[-1]
        return new_id

    except Exception as e:
        logger.error("Error adding document to '%s' via REST: %s", collection_name, e)
        return None


def update_document(
    collection_name: str, doc_id: str, data: Dict[str, Any]
) -> bool:
    """
    Update an existing document's fields using REST API PATCH with field masks.
    """
    if is_offline_mode():
        collection = _get_mock_collection(collection_name)
        if doc_id in collection:
            collection[doc_id].update(data)
        else:
            collection[doc_id] = dict(data)
        logger.debug("[MOCK] Updated document '%s' in '%s'.", doc_id, collection_name)
        return True

    try:
        project_id = get_project_id()
        api_key = get_api_key()
        mask_params = [f"updateMask.fieldPaths={k}" for k in data.keys()]
        mask_qs = "&".join(mask_params)

        url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/{collection_name}/{doc_id}?key={api_key}&{mask_qs}"

        payload = {
            "fields": {k: _to_firestore_value(v) for k, v in data.items()}
        }

        res = requests.patch(url, json=payload)
        res.raise_for_status()
        return True

    except Exception as e:
        logger.error("Error updating document '%s/%s' via REST: %s", collection_name, doc_id, e)
        return False


def delete_document(collection_name: str, doc_id: str) -> bool:
    """
    Delete a document from a Firestore collection using REST API.
    """
    if is_offline_mode():
        collection = _get_mock_collection(collection_name)
        collection.pop(doc_id, None)
        logger.debug("[MOCK] Deleted document '%s' from '%s'.", doc_id, collection_name)
        return True

    try:
        project_id = get_project_id()
        api_key = get_api_key()
        url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/{collection_name}/{doc_id}?key={api_key}"
        res = requests.delete(url)
        res.raise_for_status()
        return True

    except Exception as e:
        logger.error("Error deleting document '%s/%s' via REST: %s", collection_name, doc_id, e)
        return False


# ═══════════════════════════════════════════════════════════════════════════
# QUERY COLLECTION & REST OPERATOR MAPPINGS
# ═══════════════════════════════════════════════════════════════════════════

REST_OP_MAP = {
    "==": "EQUAL",
    "!=": "NOT_EQUAL",
    "<": "LESS_THAN",
    "<=": "LESS_THAN_OR_EQUAL",
    ">": "GREATER_THAN",
    ">=": "GREATER_THAN_OR_EQUAL",
    "in": "IN"
}


def query_collection(
    collection_name: str,
    field: str,
    operator: str,
    value: Any,
    order_by: Optional[str] = None,
    order_direction: str = "ASCENDING",
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Query a Firestore collection. Handles nested subcollection paths like "kualitas_udara/ruang1/logs"
    by finding the correct parent path for the runQuery POST request.
    """
    if is_offline_mode():
        return _mock_query(collection_name, field, operator, value, order_by, order_direction, limit)

    try:
        project_id = get_project_id()

        # Parse parent path and target collection ID for runQuery endpoint
        if "/" in collection_name:
            parts = collection_name.rsplit("/", 1)
            parent_path = parts[0]
            collection_id = parts[1]
            url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/{parent_path}:runQuery"
        else:
            collection_id = collection_name
            url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents:runQuery"

        rest_op = REST_OP_MAP.get(operator, "EQUAL")

        structured_query = {
            "from": [{"collectionId": collection_id}],
            "where": {
                "fieldFilter": {
                    "field": {"fieldPath": field},
                    "op": rest_op,
                    "value": _to_firestore_value(value)
                }
            }
        }

        if order_by:
            structured_query["orderBy"] = [
                {
                    "field": {"fieldPath": order_by},
                    "direction": order_direction
                }
            ]

        if limit:
            structured_query["limit"] = limit

        payload = {
            "structuredQuery": structured_query
        }

        params = {"key": get_api_key()}
        res = requests.post(url, json=payload, params=params)
        res.raise_for_status()

        query_res = res.json()
        results = []

        # runQuery can return a list containing an empty dict if there are no matches
        for item in query_res:
            doc = item.get("document")
            if doc:
                results.append(_parse_firestore_doc(doc))

        return results

    except Exception as e:
        logger.error(
            "Error querying '%s' (where %s %s %s) via REST: %s",
            collection_name, field, operator, value, e,
        )
        return []


# ═══════════════════════════════════════════════════════════════════════════
# MOCK QUERY HELPERS
# ═══════════════════════════════════════════════════════════════════════════

_OPERATOR_MAP = {
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    "<":  lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">":  lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "in": lambda a, b: a in b,
}


def _mock_query(
    collection_name: str,
    field: str,
    operator: str,
    value: Any,
    order_by: Optional[str],
    order_direction: str,
    limit: Optional[int],
) -> List[Dict[str, Any]]:
    """Execute a filter on the in-memory mock store."""
    collection = _get_mock_collection(collection_name)
    op_fn = _OPERATOR_MAP.get(operator)

    if op_fn is None:
        logger.warning("[MOCK] Unsupported operator '%s' — returning all docs.", operator)
        results = [{"id": doc_id, **doc} for doc_id, doc in collection.items()]
    else:
        results = []
        for doc_id, doc in collection.items():
            doc_value = doc.get(field)
            if doc_value is not None and op_fn(doc_value, value):
                results.append({"id": doc_id, **doc})

    # Sort if requested
    if order_by:
        reverse = (order_direction == "DESCENDING")
        results.sort(key=lambda d: d.get(order_by, ""), reverse=reverse)

    # Apply limit
    if limit:
        results = results[:limit]

    return results
