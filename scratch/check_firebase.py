import os
import sys
from dotenv import load_dotenv

# Ensure the root folder is in Python path so we can import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.firebase_config import initialize_firebase
from services.firebase_service import get_collection, query_collection
from utils.constants import DEFAULT_DEVICE_IDS

load_dotenv()
initialize_firebase()

print("--- CHECKING DEVICES COLLECTION ---")
try:
    devices = get_collection("devices")
    print(f"Found {len(devices)} devices in 'devices' collection:")
    for d in devices:
        print(d)
except Exception as e:
    print("Error getting devices:", e)

print("\n--- CHECKING LATEST LOGS FROM KUALITAS_UDARA/RUANG1/LOGS ---")
try:
    # ruangs or device IDs
    # Let's try "ruang1" first since it was in the ESP8266 code
    logs = query_collection(
        "kualitas_udara/ruang1/logs",
        field="waktu",
        operator=">=",
        value="",
        order_by="waktu",
        order_direction="DESCENDING",
        limit=5
    )
    print(f"Found {len(logs)} logs in 'kualitas_udara/ruang1/logs':")
    for l in logs:
        print(l)
except Exception as e:
    print("Error getting logs for ruang1:", e)

# Let's also check other potential collections
print("\n--- CHECKING LATEST LOGS FROM KUALITAS_UDARA/AQM-001/LOGS ---")
try:
    logs = query_collection(
        "kualitas_udara/AQM-001/logs",
        field="waktu",
        operator=">=",
        value="",
        order_by="waktu",
        order_direction="DESCENDING",
        limit=5
    )
    print(f"Found {len(logs)} logs in 'kualitas_udara/AQM-001/logs':")
    for l in logs:
        print(l)
except Exception as e:
    print("Error getting logs for AQM-001:", e)
