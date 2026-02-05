import pandas as pd
import joblib
import time
from influxdb import InfluxDBClient
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, precision_score, recall_score, accuracy_score
import numpy as np
import os
import logging
from datetime import datetime

try:
    import mlflow
    mlflow.set_tracking_uri("http://mlflow:5000")
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

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

MLFLOW_EXPERIMENT_NAME = "anomaly_detection_retraining"

# InfluxDB connection
try:
    client = InfluxDBClient(host='influxdb', port=8086, database='system_metrics')
    client.ping()
except:
    client = InfluxDBClient(host='localhost', port=8086, database='system_metrics')

# 🔧 CRITICAL FIX: Store previous network value for derivative calculation
previous_network = {"bytes": None, "time": None}

# 🔧 NEW: Track consecutive anomalies for temporal filtering (2 min = 12 predictions)
anomaly_counter = 0
ANOMALY_THRESHOLD = 12  # 12 * 10sec = 2 minutes (for demo/testing)

# 🔧 NEW: Surge thresholds (absolute %). Alert only if sustained + >= threshold
CPU_SURGE_THRESHOLD = 10.0
MEM_SURGE_THRESHOLD = 30.0
NET_SURGE_THRESHOLD = 15000.0

# 🔧 NEW: Anomaly collection for model evaluation
DETECTED_ANOMALIES_PATH = os.path.join(BASE_DIR, "results/detected_anomalies_for_testing.csv")
os.makedirs(os.path.join(BASE_DIR, "results"), exist_ok=True)

def save_detected_anomaly(cpu_val, mem_val, net_val):
    """Save detected anomaly to file for later evaluation."""
    try:
        anomaly_record = pd.DataFrame([{
            "cpu_usage": float(cpu_val),
            "memory_usage": float(mem_val),
            "network_load": float(net_val),
            "timestamp": datetime.utcnow().isoformat()
        }])
        
        if os.path.exists(DETECTED_ANOMALIES_PATH):
            existing = pd.read_csv(DETECTED_ANOMALIES_PATH)
            anomaly_record = pd.concat([existing, anomaly_record], ignore_index=True).tail(1000)  # Keep last 1000
        
        anomaly_record.to_csv(DETECTED_ANOMALIES_PATH, index=False)
    except Exception as e:
        logger.warning("Failed to save anomaly: %s", e)

def log_retrain_to_mlflow(model, sample_count, metrics=None):
    """Log retraining event to MLflow."""
    if not MLFLOW_AVAILABLE:
        logger.debug("MLflow not available; retraining log skipped.")
        return

    try:
        mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
        with mlflow.start_run():
            mlflow.log_params({
                "model_type": "IsolationForest",
                "contamination": getattr(model, "contamination", None),
                "n_estimators": getattr(model, "n_estimators", None),
                "retrain_samples": sample_count
            })
            
            # Log evaluation metrics if available
            if metrics:
                mlflow.log_metrics({
                    "f1_score": metrics.get("f1_score", 0),
                    "precision": metrics.get("precision", 0),
                    "recall": metrics.get("recall", 0),
                    "accuracy": metrics.get("accuracy", 0),
                    "test_anomalies": metrics.get("test_anomalies", 0)
                })
                logger.info(
                    "MLflow retrain logged - F1: %.3f, Precision: %.3f, Recall: %.3f",
                    metrics.get("f1_score", 0),
                    metrics.get("precision", 0),
                    metrics.get("recall", 0)
                )
            else:
                logger.info("MLflow retrain run logged")
    except Exception as e:
        logger.warning("MLflow logging failed: %s", e)

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

            cpu_val = float(current_metrics["cpu_usage"].values[0])
            mem_val = float(current_metrics["memory_usage"].values[0])
            net_val = float(current_metrics["network_load"].values[0])

            # STEP 3: IMMEDIATE DETECTION (Raw model output)
            model_prediction = 0
            if ai_is_ready:
                latest_scaled = scaler.transform(current_metrics)
                prediction = model.predict(latest_scaled)
                model_prediction = 1 if prediction[0] == -1 else 0

            # STEP 3.5: TEMPORAL BUFFERING + SURGE GATING
            # Only alert if anomaly is sustained AND CPU/MEM/NET is >= threshold
            surge_condition = (
                (cpu_val >= CPU_SURGE_THRESHOLD) or
                (mem_val >= MEM_SURGE_THRESHOLD) or
                (net_val >= NET_SURGE_THRESHOLD)
            )

            global anomaly_counter
            if model_prediction == 1 and surge_condition:
                anomaly_counter += 1
                # Only report anomaly if we have 12+ consecutive detections (2 min)
                ai_status = 1 if anomaly_counter >= ANOMALY_THRESHOLD else 0
            else:
                # Reset counter when normal or below surge threshold
                anomaly_counter = 0
                ai_status = 0

            # STEP 4: SYNC WITH GRAFANA
            json_body = [{
                "measurement": "ai_predictions",
                "fields": {
                    "is_anomaly": ai_status,
                    "cpu_val": cpu_val,
                    "mem_val": mem_val,
                    "net_val": net_val
                }
            }]
            client.write_points(json_body)

            # 🔧 CHANGED: Learn ONLY from NORMAL behavior
            # 🔧 CRITICAL: Use model_prediction (raw) not ai_status (buffered) for training
            # This ensures anomalous data NEVER enters training, even during buffering period
            if model_prediction == 0:
                updated_memory = pd.concat(
                    [historical_df[features], current_metrics],
                    ignore_index=True
                ).tail(2000)
                updated_memory.to_csv(HISTORICAL_DATA_PATH, index=False)
            else:
                # 🔧 NEW: Save detected anomaly for later testing
                save_detected_anomaly(cpu_val, mem_val, net_val)
                updated_memory = historical_df[features]

            # 🔧 CHANGED: Retrain model every 5 minutes instead of every loop
            if len(updated_memory) >= 30 and (time.time() - last_retrain_time) > 300:
                scaler = StandardScaler()
                scaled_features = scaler.fit_transform(updated_memory)

                model = IsolationForest(
                    contamination=0.05,
                    random_state=42
                ).fit(scaled_features)

                joblib.dump(model, MODEL_PATH)
                joblib.dump(scaler, SCALER_PATH)

                ai_is_ready = True
                last_retrain_time = time.time()
                logger.info("Model retrained with %s samples", len(updated_memory))
                
                # 🔧 NEW: Evaluate model on COLLECTED ANOMALIES for real metrics
                if os.path.exists(DETECTED_ANOMALIES_PATH) and os.path.getsize(DETECTED_ANOMALIES_PATH) > 0:
                    try:
                        # Load collected anomalies
                        anomaly_data = pd.read_csv(DETECTED_ANOMALIES_PATH)
                        if len(anomaly_data) > 0:
                            anomaly_features = anomaly_data[features]
                            
                            # Scale anomalies with trained scaler
                            anomaly_scaled = scaler.transform(anomaly_features)
                            
                            # Predict on real collected anomalies
                            anomaly_predictions = model.predict(anomaly_scaled)
                            detected_count = (anomaly_predictions == -1).sum()
                            
                            # Calculate metrics
                            # True labels: all are anomalies (1)
                            true_labels = np.ones(len(anomaly_data))
                            pred_labels = (anomaly_predictions == -1).astype(int)
                            
                            metrics = {
                                "f1_score": float(f1_score(true_labels, pred_labels, zero_division=0)),
                                "precision": float(precision_score(true_labels, pred_labels, zero_division=0)),
                                "recall": float(recall_score(true_labels, pred_labels, zero_division=0)),
                                "test_anomalies": int(detected_count),
                                "total_test_samples": len(anomaly_data)
                            }
                            
                            logger.info(
                                "Model evaluated on %d collected anomalies - F1: %.3f, Precision: %.3f, Recall: %.3f, Detected: %d",
                                len(anomaly_data), metrics["f1_score"], metrics["precision"], metrics["recall"], detected_count
                            )
                            log_retrain_to_mlflow(model, len(updated_memory), metrics)
                        else:
                            log_retrain_to_mlflow(model, len(updated_memory))
                    except Exception as e:
                        logger.warning("Error evaluating on anomalies: %s", e)
                        log_retrain_to_mlflow(model, len(updated_memory))
                else:
                    # No anomalies collected yet
                    log_retrain_to_mlflow(model, len(updated_memory))

            status_txt = "ANOMALY!!" if ai_status else "Normal"
            logger.info("Monitoring synced. Status: %s", status_txt)

        else:
            logger.info("Waiting for Site B metrics...")

        time.sleep(10)

if __name__ == "__main__":
    run_pipeline()