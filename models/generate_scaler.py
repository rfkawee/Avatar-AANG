"""
Generate Scaler Script
Reads the training CSV and fits a MinMaxScaler on the same features
used during LSTM model training. Saves the scaler as a .pkl file
so the dashboard can inverse_transform predictions at runtime.

Usage:
    python generate_scaler.py
"""
import os
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import joblib

# ── Paths ────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(SCRIPT_DIR, "script", "data_kualitas_udara.csv")
SCALER_PATH = os.path.join(SCRIPT_DIR, "scaler.pkl")

# ── Features (must match training notebook exactly) ──────────────────────
FEATURES = ["suhu", "kelembaban", "debu", "gas_mq7", "gas_mq135"]

def main():
    print(f"Reading CSV from: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)

    # Filter same as notebook: keep only year > 2000
    df["waktu"] = pd.to_datetime(df["waktu"])
    df = df.sort_values("waktu")
    df = df[df["waktu"].dt.year > 2000]
    df.reset_index(drop=True, inplace=True)

    print(f"Rows after filtering: {len(df)}")
    print(f"Features: {FEATURES}")
    print(f"Sample data:\n{df[FEATURES].head()}\n")

    scaler = MinMaxScaler()
    scaler.fit(df[FEATURES])

    joblib.dump(scaler, SCALER_PATH)
    print(f"[OK] Scaler saved to: {SCALER_PATH}")
    print(f"   data_min_: {scaler.data_min_}")
    print(f"   data_max_: {scaler.data_max_}")

if __name__ == "__main__":
    main()
