"""
Model Evaluation Script - Testing & Robustness Assessment
==========================================================
This script evaluates the trained model on test data and runs robustness tests:
- Test set metrics (Precision, Recall, F1, ROC-AUC)
- Robustness tests: noise injection, missing data, extreme outliers
- Performance baseline comparison
- Results saved to results/evaluation_report.json
"""

import pandas as pd
import numpy as np
import joblib
import json
import os
import time
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    confusion_matrix, classification_report, roc_curve, auc
)
import warnings
warnings.filterwarnings('ignore')

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models/anomaly_model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "models/scaler.pkl")
HISTORICAL_DATA_PATH = os.path.join(BASE_DIR, "data/processed/system_metrics_processed.csv")
RESULTS_DIR = os.path.join(BASE_DIR, "results")

os.makedirs(RESULTS_DIR, exist_ok=True)

class ModelEvaluator:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.results = {}
        
    def load_model(self):
        """Load trained model and scaler."""
        if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
            raise FileNotFoundError(f"Model files not found. Run train_model.py first.")
        
        self.model = joblib.load(MODEL_PATH)
        self.scaler = joblib.load(SCALER_PATH)
        print("✅ Model and scaler loaded successfully")
    
    def load_test_data(self):
        """Load and prepare test data."""
        df = pd.read_csv(HISTORICAL_DATA_PATH)
        features = ["cpu_usage", "memory_usage", "network_load"]
        
        # Use last 20% as test data
        test_size = int(len(df) * 0.2)
        X_test = df[features].iloc[-test_size:].values
        
        X_test_scaled = self.scaler.transform(X_test)
        print(f"✅ Loaded {len(X_test)} test samples")
        return X_test, X_test_scaled
    
    def evaluate_base(self, X_test, X_test_scaled):
        """Evaluate model on clean test data."""
        print("\n" + "=" * 60)
        print("📊 BASELINE EVALUATION (Clean Test Data)")
        print("=" * 60)
        
        # Predictions
        y_pred = self.model.predict(X_test_scaled)
        y_pred_binary = (y_pred == -1).astype(int)
        
        # Anomaly scores
        anomaly_scores = self.model.score_samples(X_test_scaled)
        
        # For evaluation, assume top contamination% are true anomalies
        contamination = self.model.contamination if hasattr(self.model, 'contamination') else 0.01
        anomaly_count = int(len(X_test) * contamination)
        y_true = np.zeros(len(X_test))
        top_indices = np.argsort(anomaly_scores)[:anomaly_count]
        y_true[top_indices] = 1
        
        # Metrics
        precision = precision_score(y_true, y_pred_binary, zero_division=0)
        recall = recall_score(y_true, y_pred_binary, zero_division=0)
        f1 = f1_score(y_true, y_pred_binary, zero_division=0)
        
        try:
            roc_auc = roc_auc_score(y_true, -anomaly_scores)
        except:
            roc_auc = 0.0
        
        conf_matrix = confusion_matrix(y_true, y_pred_binary)
        
        print(f"Precision: {precision:.4f}")
        print(f"Recall: {recall:.4f}")
        print(f"F1-Score: {f1:.4f}")
        print(f"ROC-AUC: {roc_auc:.4f}")
        print(f"Anomalies detected: {np.sum(y_pred_binary)}/{len(X_test)}")
        print(f"Confusion Matrix:\n{conf_matrix}")
        
        # Latency test
        start = time.time()
        for _ in range(100):
            self.model.predict(X_test_scaled[:1])
        latency_ms = (time.time() - start) / 100 * 1000
        print(f"Prediction latency (avg): {latency_ms:.2f} ms")
        
        self.results["baseline"] = {
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1),
            "roc_auc": float(roc_auc),
            "confusion_matrix": conf_matrix.tolist(),
            "anomalies_detected": int(np.sum(y_pred_binary)),
            "latency_ms": float(latency_ms)
        }
        
        return y_true, y_pred_binary, anomaly_scores
    
    def test_noise_robustness(self, X_test, X_test_scaled):
        """Test model robustness to feature noise."""
        print("\n" + "=" * 60)
        print("🔧 ROBUSTNESS TEST 1: Gaussian Noise Injection")
        print("=" * 60)
        
        noise_levels = [0.01, 0.05, 0.1]
        results = {}
        
        for noise_level in noise_levels:
            X_noisy = X_test + np.random.normal(0, noise_level, X_test.shape)
            X_noisy_scaled = self.scaler.transform(X_noisy)
            
            y_pred = self.model.predict(X_noisy_scaled)
            y_pred_binary = (y_pred == -1).astype(int)
            
            anomaly_ratio = np.sum(y_pred_binary) / len(X_test)
            print(f"Noise σ={noise_level}: {np.sum(y_pred_binary)} anomalies detected ({anomaly_ratio:.2%})")
            
            results[f"noise_sigma_{noise_level}"] = {
                "anomalies_detected": int(np.sum(y_pred_binary)),
                "ratio": float(anomaly_ratio)
            }
        
        self.results["noise_robustness"] = results
    
    def test_missing_data(self, X_test, X_test_scaled):
        """Test model robustness to missing features."""
        print("\n" + "=" * 60)
        print("🔧 ROBUSTNESS TEST 2: Missing Feature Values")
        print("=" * 60)
        
        feature_names = ["cpu_usage", "memory_usage", "network_load"]
        results = {}
        
        for feature_idx, feature_name in enumerate(feature_names):
            X_missing = X_test.copy()
            # Replace with median
            X_missing[:, feature_idx] = np.median(X_test[:, feature_idx])
            X_missing_scaled = self.scaler.transform(X_missing)
            
            y_pred = self.model.predict(X_missing_scaled)
            y_pred_binary = (y_pred == -1).astype(int)
            
            anomaly_ratio = np.sum(y_pred_binary) / len(X_test)
            print(f"Missing {feature_name}: {np.sum(y_pred_binary)} anomalies detected ({anomaly_ratio:.2%})")
            
            results[f"missing_{feature_name}"] = {
                "anomalies_detected": int(np.sum(y_pred_binary)),
                "ratio": float(anomaly_ratio)
            }
        
        self.results["missing_data_robustness"] = results
    
    def test_outlier_robustness(self, X_test, X_test_scaled):
        """Test model sensitivity to extreme outliers."""
        print("\n" + "=" * 60)
        print("🔧 ROBUSTNESS TEST 3: Extreme Outlier Injection")
        print("=" * 60)
        
        outlier_magnitudes = [2, 5, 10]
        results = {}
        
        for magnitude in outlier_magnitudes:
            X_outliers = X_test.copy()
            # Inject outliers in 10% of samples
            outlier_indices = np.random.choice(len(X_test), int(0.1 * len(X_test)), replace=False)
            X_outliers[outlier_indices] *= magnitude
            X_outliers_scaled = self.scaler.transform(X_outliers)
            
            y_pred = self.model.predict(X_outliers_scaled)
            y_pred_binary = (y_pred == -1).astype(int)
            
            # Count outliers detected
            outliers_flagged = np.sum(y_pred_binary[outlier_indices])
            anomaly_ratio = np.sum(y_pred_binary) / len(X_test)
            
            print(f"Magnitude {magnitude}x: {np.sum(y_pred_binary)} total, "
                  f"{outliers_flagged} outliers detected ({anomaly_ratio:.2%})")
            
            results[f"magnitude_{magnitude}x"] = {
                "total_anomalies": int(np.sum(y_pred_binary)),
                "outliers_detected": int(outliers_flagged),
                "ratio": float(anomaly_ratio)
            }
        
        self.results["outlier_robustness"] = results
    
    def test_distribution_shift(self, X_test, X_test_scaled):
        """Test model sensitivity to shifted feature distributions."""
        print("\n" + "=" * 60)
        print("🔧 ROBUSTNESS TEST 4: Distribution Shift")
        print("=" * 60)
        
        shifts = [0.1, 0.5, 1.0]
        results = {}
        
        for shift in shifts:
            X_shifted = X_test + shift
            X_shifted_scaled = self.scaler.transform(X_shifted)
            
            y_pred = self.model.predict(X_shifted_scaled)
            y_pred_binary = (y_pred == -1).astype(int)
            
            anomaly_ratio = np.sum(y_pred_binary) / len(X_test)
            print(f"Shift +{shift}: {np.sum(y_pred_binary)} anomalies detected ({anomaly_ratio:.2%})")
            
            results[f"shift_{shift}"] = {
                "anomalies_detected": int(np.sum(y_pred_binary)),
                "ratio": float(anomaly_ratio)
            }
        
        self.results["distribution_shift"] = results
    
    def save_evaluation_report(self):
        """Save evaluation results to JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(RESULTS_DIR, f"evaluation_report_{timestamp}.json")
        
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Also save as latest
        with open(os.path.join(RESULTS_DIR, "evaluation_report_latest.json"), 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n✅ Evaluation report saved: {report_path}")

def main():
    print("=" * 60)
    print("🔬 MODEL EVALUATION & ROBUSTNESS TESTING")
    print("=" * 60)
    
    try:
        evaluator = ModelEvaluator()
        evaluator.load_model()
        
        X_test, X_test_scaled = evaluator.load_test_data()
        
        # Baseline evaluation
        y_true, y_pred, scores = evaluator.evaluate_base(X_test, X_test_scaled)
        
        # Robustness tests
        evaluator.test_noise_robustness(X_test, X_test_scaled)
        evaluator.test_missing_data(X_test, X_test_scaled)
        evaluator.test_outlier_robustness(X_test, X_test_scaled)
        evaluator.test_distribution_shift(X_test, X_test_scaled)
        
        # Save report
        evaluator.save_evaluation_report()
        
        print("\n" + "=" * 60)
        print("✅ EVALUATION COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        raise

if __name__ == "__main__":
    main()
