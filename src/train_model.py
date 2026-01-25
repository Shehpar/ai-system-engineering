import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib

# -------------------------------
# Paths
# -------------------------------
DATA_PATH = "../data/processed/system_metrics_processed.csv"
MODEL_PATH = "../models/anomaly_model.pkl"

# -------------------------------
# Load processed data
# -------------------------------
data = pd.read_csv(DATA_PATH)

features = ["cpu_usage", "memory_usage", "disk_usage"]
X = data[features]

# -------------------------------
# Train Isolation Forest model
# -------------------------------
model = IsolationForest(
    n_estimators=100,
    contamination=0.05,
    random_state=42
)

model.fit(X)

# -------------------------------
# Save trained model
# -------------------------------
joblib.dump(model, MODEL_PATH)

print("Anomaly detection model trained and saved successfully.")
