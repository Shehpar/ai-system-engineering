import pandas as pd
from sklearn.preprocessing import StandardScaler

# -------------------------------
# Paths
# -------------------------------
INPUT_PATH = "../data/raw/system_metrics.csv"
OUTPUT_PATH = "../data/processed/system_metrics_processed.csv"

# -------------------------------
# Load data
# -------------------------------
data = pd.read_csv(INPUT_PATH)

# -------------------------------
# Select features
# -------------------------------
features = ["cpu_usage", "memory_usage", "disk_usage"]
X = data[features]

# -------------------------------
# Normalize features
# -------------------------------
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# -------------------------------
# Save processed data
# -------------------------------
processed_data = pd.DataFrame(X_scaled, columns=features)
processed_data["anomaly"] = data["anomaly"]

processed_data.to_csv(OUTPUT_PATH, index=False)

print("Data preprocessing completed successfully.")
