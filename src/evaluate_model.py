import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
import os

# -------------------------------
# Paths
# -------------------------------
RESULTS_PATH = "../results/detected_anomalies.csv"
METRICS_OUT = "../results/evaluation_metrics.txt"

# Ensure results directory exists
os.makedirs("../results", exist_ok=True)

# -------------------------------
# Load Results
# -------------------------------
data = pd.read_csv(RESULTS_PATH)

# 'anomaly' is what we injected (Ground Truth)
# 'ai_prediction' is what the Isolation Forest found
y_true = data['anomaly']
y_pred = data['ai_prediction']

# -------------------------------
# Calculate Metrics
# -------------------------------
report = classification_report(y_true, y_pred)
conf_matrix = confusion_matrix(y_true, y_pred)

# -------------------------------
# Save and Print Report
# -------------------------------
with open(METRICS_OUT, "w") as f:
    f.write("AI SYSTEMS ENGINEERING - PROJECT EVALUATION\n")
    f.write("===========================================\n")
    f.write(f"Model: Isolation Forest (Anomaly Detection)\n\n")
    f.write("Classification Report:\n")
    f.write(report)
    f.write("\nConfusion Matrix:\n")
    f.write(str(conf_matrix))

print("Quality Assessment Completed.")
print(f"Metrics saved to {METRICS_OUT}")
print("\n--- Model Performance ---")
print(report)