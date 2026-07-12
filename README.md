# 🌿 AirSense — IoT Air Quality Monitoring Dashboard

AirSense is a premium, modern, and high-performance Web Dashboard built with **Streamlit** to visualize real-time and historical air quality data. The platform communicates directly with **Google Firebase Firestore** via REST APIs, allowing remote IoT sensor nodes (e.g., ESP8266) to stream telemetry data seamlessly.

---

## ✨ Features

- **📊 Modern Glassmorphic UI**: Vibrant, responsive, and state-of-the-art dark theme UI inspired by premium glassmorphism principles.
- **🌡️ ISPU Index Calculation**: Real-time ISPU (Indeks Standar Pencemar Udara) category computation with interactive meter bars and action recommendations.
- **🔌 Online/Offline Status Indicator**: Automatically checks if a device is active. Shows a status warning if no data has been received within 10 minutes.
- **🔧 Device Management**: Complete CRUD interface to add, edit, status-check, or remove registered IoT device nodes.
- **🔮 Time-Series ML Forecasting**: Real-time 1-hour air quality predictions using a trained LSTM (Long Short-Term Memory) neural network, complete with premium glassmorphism trend analysis and custom health mitigation recommendation cards.

---

## 🛠️ Tech Stack

- **Frontend/App Framework**: [Streamlit](https://streamlit.io/) (v1.35.0+)
- **Charts & Data Visualization**: [Plotly](https://plotly.com/) (v5.18.0+)
- **Data Engineering**: [Pandas](https://pandas.pydata.org/) & [NumPy](https://numpy.org/)
- **Backend Database**: [Firebase Firestore REST API](https://firebase.google.com/)
- **Machine Learning**: [TensorFlow](https://www.tensorflow.org/) (v2.16.0+) & [Scikit-Learn](https://scikit-learn.org/) (MinMaxScaler)
- **Styling**: Vanilla CSS with modern font styling ('Inter' via Google Fonts).

---

## 📁 Project Structure

```text
air_quality_monitoring/
│
├── app.py                     # Main application entry point (navigation & sidebar config)
├── requirements.txt           # Python dependency specifications
├── .env.example               # Template file for environment variables
│
├── components/                # Modular reusable UI components
│   ├── cards.py               # Glassmorphic KPI cards, ISPU card, and forecast analysis renders
│   ├── charts.py              # Interactive Plotly line & forecast charts
│   ├── sidebar.py             # Shared device selector and sidebar content
│   └── tables.py              # Premium tables for raw data visualization
│
├── config/                    # Configuration modules
│   ├── settings.py            # Constant strings, Collection Names, and UI thresholds
│   └── firebase_config.py     # REST API credentials loader & mock mode checker
│
├── models/                    # Trained Machine Learning models
│   ├── model_lstm_kualitas_udara.keras # Trained LSTM model for time-series forecasting
│   └── scaler.pkl             # MinMaxScaler object for feature scaling
│
├── pages/                     # Individual page dashboards
│   ├── dashboard.py           # Main KPI & status summary page
│   ├── forecasting.py         # LSTM air quality forecasting dashboard page
│   ├── alerts.py              # System notifications & air quality warnings
│   ├── devices.py             # CRUD management for IoT devices
│   └── about.py               # Documentation and project info
│
├── services/                  # Business logic & APIs
│   ├── firebase_service.py    # Direct Firestore REST requests & mock implementations
│   ├── sensor_service.py      # Calculations, sorting logic, and data mappings
│   ├── alert_service.py       # Exceeded-threshold checking algorithms
│   └── prediction_service.py  # Autoregressive multi-step prediction using LSTM
│
└── utils/                     # Utility and helper functions
    ├── helper.py              # Date/time formatting, ISPU category lookup, and conversion functions
    ├── constants.py           # ISPU breakpoints and category thresholds
    └── logger.py              # Customized logger configuration
```

---

## 🔌 Database Architecture (Firestore)

The system parses readings in Indonesian and maps them dynamically. Telemetry is stored in Firestore subcollections:

```text
kualitas_udara/                     [Collection]
  └── {device_id}/                  [Document]
        └── logs/                   [Subcollection]
              └── {document_id}/    [Document]
                    ├── suhu        : 34.4 (Double)
                    ├── kelembaban  : 62.9 (Double)
                    ├── mq7         : 1.2 (Double)
                    ├── mq135       : 1.0 (Double)
                    ├── pm10        : 14.5 (Double)
                    └── waktu       : "2026-07-07 14:51:26" (String)
```

---

## 🚀 Getting Started

### 1. Prerequisites
Make sure you have Python 3.9 or higher installed on your system.

### 2. Installation
Clone this repository, navigate to the `air_quality_monitoring` directory, and initialize a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Configuration
Copy the `.env.example` file to `.env` and fill in your Firebase API details:

```ini
# Firebase Configuration
FIREBASE_API_KEY=AIzaSyB7...YourAPIKey
FIREBASE_PROJECT_ID=sistem-kualitas-udara-849d3

# App Configuration
APP_NAME=AirSense
REFRESH_INTERVAL_SECONDS=60
MOCK_MODE=false
```

*Note: If `MOCK_MODE=true` is set, the application will run in offline mode using mock data, bypassing Firebase connections.*

### 4. Running the Dashboard
Run the Streamlit application using the command:

```bash
streamlit run app.py
```

The web dashboard will automatically open in your default browser at `http://localhost:8501`.

---

## 📄 License
This project is for educational/academic research purposes (Metode Penelitian). All rights reserved.
