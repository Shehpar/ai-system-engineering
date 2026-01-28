import pandas as pd
import joblib
import time
from influxdb import InfluxDBClient
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler 
import os
import logging
from datetime import datetime

# --- 1. CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models/anomaly_model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "models/scaler.pkl")
HISTORICAL_DATA_PATH = os.path.join(BASE_DIR, "data/processed/system_metrics_processed.csv")

# Ensure directories exist
os.makedirs(os.path.join(BASE_DIR, "models"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "data/processed"), exist_ok=True)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# InfluxDB connection
try:
    client = InfluxDBClient(host='influxdb', port=8086, database='system_metrics')
    client.ping()
except:
    client = InfluxDBClient(host='localhost', port=8086, database='system_metrics')

# 🔧 CRITICAL FIX: Store previous network value for derivative calculation
previous_network = {"bytes": None, "time": None}

def load_core_memory():
    """Reads the 'Long-term Memory' from the Hard Drive."""
    if not os.path.exists(HISTORICAL_DATA_PATH):
        return pd.DataFrame(columns=["cpu_usage", "memory_usage", "network_load"])
    return pd.read_csv(HISTORICAL_DATA_PATH)

def fetch_live_logs():
    """Queries InfluxDB for the most recent system heartbeat."""
    global previous_network
    
    # Query each measurement SEPARATELY (like Grafana does)
    cpu_query = '''
    SELECT "usage_idle"
    FROM "cpu"
    WHERE time > now() - 5m
    ORDER BY time DESC LIMIT 1
    '''
    
    mem_query = '''
    SELECT "used_percent"
    FROM "mem"
    WHERE time > now() - 5m
    ORDER BY time DESC LIMIT 1
    '''
    
    net_query = '''
    SELECT "bytes_recv"
    FROM "net"
    WHERE time > now() - 5m
    ORDER BY time DESC LIMIT 1
    '''
    
    try:
        # Execute each query separately
        cpu_result = list(client.query(cpu_query).get_points())
        mem_result = list(client.query(mem_query).get_points())
        net_result = list(client.query(net_query).get_points())
        
        # Extract and calculate values
        cpu_val = None
        mem_val = None
        net_val = None
        
        if cpu_result and "usage_idle" in cpu_result[0]:
            usage_idle = cpu_result[0]["usage_idle"]
            if usage_idle is not None:
                cpu_val = 100 - usage_idle
        
        if mem_result and "used_percent" in mem_result[0]:
            mem_val = mem_result[0]["used_percent"]
        
        # 🔧 CRITICAL FIX: Calculate network RATE (bytes per second) like Grafana does
        if net_result and "bytes_recv" in net_result[0]:
            current_bytes = net_result[0]["bytes_recv"]
            current_time = net_result[0]["time"]
            
            if previous_network["bytes"] is not None and previous_network["time"] is not None:
                # Calculate time difference in seconds
                time_diff = (datetime.fromisoformat(current_time.replace('Z', '+00:00')) - 
                           datetime.fromisoformat(previous_network["time"].replace('Z', '+00:00'))).total_seconds()
                
                if time_diff > 0:
                    bytes_diff = current_bytes - previous_network["bytes"]
                    # Network rate in bytes per second (non-negative)
                    net_val = max(0, bytes_diff / time_diff)
            
            # Update previous values for next iteration
            previous_network["bytes"] = current_bytes
            previous_network["time"] = current_time
        
        # Only return data if ALL three metrics are available
        if cpu_val is not None and mem_val is not None and net_val is not None:
            data = {
                "cpu_usage": cpu_val,
                "memory_usage": mem_val,
                "network_load": net_val
            }
            return pd.DataFrame([data])
        else:
            return pd.DataFrame()
            
    except Exception as e:
        logger.warning("Database error: %s", e)
        return pd.DataFrame()

# --- 2. THE MAIN SYNC PIPELINE ---
def run_pipeline():
    logger.info("Initializing non-stop monitoring...")
    features = ["cpu_usage", "memory_usage", "network_load"]
    
    # STEP 1: PRE-LOAD BRAIN (The "Detector")
    try:
        model = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        logger.info("Pre-trained model found. Starting detection immediately.")
        ai_is_ready = True
    except:
        logger.warning("No model found. Detection will start after initial training.")
        ai_is_ready = False

    last_retrain_time = time.time()

    while True:
        historical_df = load_core_memory()
        live_df = fetch_live_logs()

        if not live_df.empty:
            current_metrics = live_df[features]

            # STEP 3: IMMEDIATE DETECTION
            ai_status = 0
            if ai_is_ready:
                latest_scaled = scaler.transform(current_metrics)
                prediction = model.predict(latest_scaled)
                ai_status = 1 if prediction[0] == -1 else 0

            # STEP 4: SYNC WITH GRAFANA
            json_body = [{
                "measurement": "ai_predictions",
                "fields": {
                    "is_anomaly": ai_status,
                    "cpu_val": float(current_metrics["cpu_usage"].values[0]),
                    "mem_val": float(current_metrics["memory_usage"].values[0]),
                    "net_val": float(current_metrics["network_load"].values[0])
                }
            }]
            client.write_points(json_body)

            # 🔧 CHANGED: Learn ONLY from NORMAL behavior
            if ai_status == 0:
                updated_memory = pd.concat(
                    [historical_df[features], current_metrics],
                    ignore_index=True
                ).tail(2000)
                updated_memory.to_csv(HISTORICAL_DATA_PATH, index=False)
            else:
                updated_memory = historical_df[features]

            # 🔧 CHANGED: Retrain model every 5 minutes instead of every loop
            if len(updated_memory) >= 30 and (time.time() - last_retrain_time) > 300:
                scaler = StandardScaler()
                scaled_features = scaler.fit_transform(updated_memory)

                model = IsolationForest(
                    contamination=0.01,
                    random_state=42
                ).fit(scaled_features)

                joblib.dump(model, MODEL_PATH)
                joblib.dump(scaler, SCALER_PATH)

                ai_is_ready = True
                last_retrain_time = time.time()
                logger.info("Model retrained with %s samples", len(updated_memory))

            status_txt = "ANOMALY!!" if ai_status else "Normal"
            logger.info("Monitoring synced. Status: %s", status_txt)

        else:
            logger.info("Waiting for Site B metrics...")

        time.sleep(10)

if __name__ == "__main__":
    run_pipeline()