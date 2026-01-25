import numpy as np
import pandas as pd

# -------------------------------
# Configuration
# -------------------------------
NUM_SAMPLES = 1000
OUTPUT_PATH = "../data/raw/system_metrics.csv"

# -------------------------------
# Generate normal system behavior
# -------------------------------
np.random.seed(42)

cpu_usage = np.random.normal(loc=50, scale=10, size=NUM_SAMPLES)
memory_usage = np.random.normal(loc=60, scale=15, size=NUM_SAMPLES)
disk_usage = np.random.normal(loc=70, scale=5, size=NUM_SAMPLES)

# -------------------------------
# Inject anomalies
# -------------------------------
anomaly_indices = np.random.choice(NUM_SAMPLES, size=50, replace=False)

cpu_usage[anomaly_indices] = cpu_usage[anomaly_indices] + np.random.normal(40, 10, 50)
memory_usage[anomaly_indices] = memory_usage[anomaly_indices] + np.random.normal(30, 10, 50)
disk_usage[anomaly_indices] = disk_usage[anomaly_indices] + np.random.normal(20, 5, 50)

# -------------------------------
# Create DataFrame
# -------------------------------
data = pd.DataFrame({
    "cpu_usage": cpu_usage,
    "memory_usage": memory_usage,
    "disk_usage": disk_usage,
    "anomaly": 0
})

data.loc[anomaly_indices, "anomaly"] = 1

# -------------------------------
# Save to CSV
# -------------------------------
data.to_csv(OUTPUT_PATH, index=False)

print("System metrics data generated and saved successfully.")
