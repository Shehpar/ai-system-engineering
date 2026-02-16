"""
Model Comparison Script - Anomaly Detection Benchmarking
=========================================================
Compares 5 different anomaly detection models on your infrastructure data.

Usage:
    python src/compare_models.py

Output:
    - Detailed metrics comparison (precision, recall, F1, ROC-AUC)
    - Latency benchmarking for each model
    - Results saved to results/model_comparison_report.json
    - Visualizations in results/model_comparison.txt
"""

import pandas as pd
import numpy as np
import joblib
import json
import time
import os
import logging
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)

# All models already available in scikit-learn!
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM
from sklearn.covariance import EllipticEnvelope
from sklearn.mixture import GaussianMixture

import warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORICAL_DATA_PATH = os.path.join(BASE_DIR, "data/processed/system_metrics_processed.csv")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# Model configurations
CONTAMINATION = 0.05  # 5% of data assumed to be anomalies
RANDOM_STATE = 42
TEST_SIZE = 0.2

class ModelComparison:
    """Trains and compares multiple anomaly detection models."""
    
    def __init__(self, data_path, contamination=0.05):
        self.data_path = data_path
        self.contamination = contamination
        self.results = {}
        self.scaler = StandardScaler()
        
    def load_data(self):
        """Load and prepare data."""
        logger.info("Loading data from %s", self.data_path)
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Data not found: {self.data_path}")
        
        df = pd.read_csv(self.data_path)
        features = ["cpu_usage", "memory_usage", "network_load"]
        
        # Check if features exist
        for feat in features:
            if feat not in df.columns:
                raise ValueError(f"Missing feature: {feat}")
        
        X = df[features].values
        logger.info("Loaded %d samples with %d features", X.shape[0], X.shape[1])
        
        return X
    
    def prepare_splits(self, X):
        """Create train/test splits."""
        X_train, X_test = train_test_split(
            X, test_size=TEST_SIZE, random_state=RANDOM_STATE
        )
        
        # Scale training data
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        logger.info("Train size: %d, Test size: %d", len(X_train), len(X_test))
        
        # Create pseudo labels (assuming Isolation Forest as reference)
        iso_forest = IsolationForest(contamination=self.contamination, random_state=RANDOM_STATE)
        y_test = iso_forest.fit_predict(X_train_scaled)
        y_test = (y_test == -1).astype(int)  # -1 = anomaly, 1 = normal
        
        return X_train_scaled, X_test_scaled, y_test
    
    def create_models(self):
        """Create all model instances."""
        models = {
            "Isolation Forest": {
                "model": IsolationForest(
                    contamination=self.contamination,
                    random_state=RANDOM_STATE,
                    n_estimators=100
                ),
                "requires_fit": True,
                "negative_label": -1
            },
            "Local Outlier Factor (LOF)": {
                "model": LocalOutlierFactor(
                    n_neighbors=20,
                    contamination=self.contamination,
                    novelty=False  # Use original data for evaluation
                ),
                "requires_fit": True,
                "negative_label": -1
            },
            "One-Class SVM": {
                "model": OneClassSVM(
                    nu=self.contamination,
                    kernel='rbf',
                    gamma='auto'
                ),
                "requires_fit": True,
                "negative_label": -1
            },
            "Elliptic Envelope": {
                "model": EllipticEnvelope(
                    contamination=self.contamination,
                    random_state=RANDOM_STATE
                ),
                "requires_fit": True,
                "negative_label": -1
            },
            "Gaussian Mixture Model": {
                "model": GaussianMixture(
                    n_components=3,
                    random_state=RANDOM_STATE,
                    n_init=10
                ),
                "requires_fit": True,
                "negative_label": None  # Uses probability
            }
        }
        return models
    
    def train_and_evaluate(self, X_train, X_test, y_test):
        """Train all models and evaluate on test set."""
        models = self.create_models()
        
        for model_name, model_dict in models.items():
            logger.info("=" * 60)
            logger.info("Training: %s", model_name)
            logger.info("=" * 60)
            
            try:
                model = model_dict["model"]
                
                # Training time
                train_start = time.time()
                
                if model_name == "Gaussian Mixture Model":
                    # Special handling for GMM
                    model.fit(X_train)
                    # Predict using log probability
                    y_scores_test = model.score_samples(X_test)
                    # Lower probability = anomaly
                    threshold = np.percentile(model.score_samples(X_train), 100 * self.contamination)
                    y_pred = (y_scores_test < threshold).astype(int)
                else:
                    # Standard fit/predict
                    model.fit(X_train)
                    y_pred = model.predict(X_test)
                    y_scores_test = model.score_samples(X_test) if hasattr(model, 'score_samples') else model.decision_function(X_test)
                
                train_time = time.time() - train_start
                
                # Convert predictions (-1 = anomaly, 1 = normal)
                y_pred_binary = (y_pred == -1).astype(int)
                
                # Inference time (measure over 100 predictions)
                inference_times = []
                for _ in range(100):
                    start = time.time()
                    if model_name == "Gaussian Mixture Model":
                        _ = model.score_samples(X_test[:1])
                    else:
                        _ = model.predict(X_test[:1])
                    inference_times.append(time.time() - start)
                
                avg_latency = np.mean(inference_times) * 1000  # Convert to ms
                
                # Calculate metrics
                try:
                    roc_auc = roc_auc_score(y_test, y_scores_test)
                except:
                    roc_auc = 0.0  # If all predictions same class
                
                precision = precision_score(y_test, y_pred_binary, zero_division=0)
                recall = recall_score(y_test, y_pred_binary, zero_division=0)
                f1 = f1_score(y_test, y_pred_binary, zero_division=0)
                
                tn, fp, fn, tp = confusion_matrix(y_test, y_pred_binary).ravel()
                specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
                
                # Store results
                self.results[model_name] = {
                    "training_time_sec": round(train_time, 4),
                    "avg_latency_ms": round(avg_latency, 4),
                    "precision": round(precision, 4),
                    "recall": round(recall, 4),
                    "f1_score": round(f1, 4),
                    "roc_auc": round(roc_auc, 4),
                    "specificity": round(specificity, 4),
                    "true_positives": int(tp),
                    "false_positives": int(fp),
                    "true_negatives": int(tn),
                    "false_negatives": int(fn),
                    "status": "✅ Success"
                }
                
                logger.info("✅ %s - F1: %.4f | Latency: %.2fms | ROC-AUC: %.4f",
                           model_name, f1, avg_latency, roc_auc)
                
            except Exception as e:
                logger.error("❌ %s - Error: %s", model_name, str(e))
                self.results[model_name] = {
                    "status": f"❌ Error: {str(e)}"
                }
    
    def generate_report(self):
        """Generate comparison report."""
        logger.info("\n" + "=" * 80)
        logger.info("MODEL COMPARISON REPORT")
        logger.info("=" * 80)
        
        # Create summary table
        summary_data = []
        for model_name, metrics in self.results.items():
            if "status" in metrics and "Error" not in metrics.get("status", ""):
                summary_data.append({
                    "Model": model_name,
                    "F1-Score": metrics.get("f1_score", "N/A"),
                    "Precision": metrics.get("precision", "N/A"),
                    "Recall": metrics.get("recall", "N/A"),
                    "ROC-AUC": metrics.get("roc_auc", "N/A"),
                    "Latency (ms)": metrics.get("avg_latency_ms", "N/A"),
                    "Training (s)": metrics.get("training_time_sec", "N/A")
                })
        
        summary_df = pd.DataFrame(summary_data)
        logger.info("\n%s", summary_df.to_string(index=False))
        
        # Find best models
        logger.info("\n" + "=" * 80)
        logger.info("TOP MODELS")
        logger.info("=" * 80)
        
        valid_results = {k: v for k, v in self.results.items() if "f1_score" in v}
        
        if valid_results:
            # Best F1-Score
            best_f1_model = max(valid_results.items(), key=lambda x: x[1]["f1_score"])
            logger.info("🏆 Best F1-Score: %s (%.4f)", best_f1_model[0], best_f1_model[1]["f1_score"])
            
            # Best ROC-AUC
            best_auc_model = max(valid_results.items(), key=lambda x: x[1]["roc_auc"])
            logger.info("🎯 Best ROC-AUC: %s (%.4f)", best_auc_model[0], best_auc_model[1]["roc_auc"])
            
            # Fastest
            best_speed_model = min(valid_results.items(), key=lambda x: x[1]["avg_latency_ms"])
            logger.info("⚡ Fastest: %s (%.2fms)", best_speed_model[0], best_speed_model[1]["avg_latency_ms"])
            
            # Best balanced (F1 + Speed)
            balanced_scores = {
                k: (v["f1_score"] * 0.7 + (100 - min(v["avg_latency_ms"], 100)) / 100 * 0.3)
                for k, v in valid_results.items()
            }
            best_balanced = max(balanced_scores.items(), key=lambda x: x[1])
            logger.info("⚖️  Best Balanced (70% F1 + 30% Speed): %s (%.4f)", best_balanced[0], best_balanced[1])
        
        logger.info("\n" + "=" * 80)
    
    def save_results(self):
        """Save results to JSON."""
        output_path = os.path.join(RESULTS_DIR, "model_comparison_report.json")
        with open(output_path, "w") as f:
            json.dump(self.results, f, indent=2)
        logger.info("Results saved to: %s", output_path)
        
        # Also save as markdown
        md_path = os.path.join(RESULTS_DIR, "model_comparison_report.md")
        with open(md_path, "w") as f:
            f.write("# Anomaly Detection Model Comparison Report\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            
            f.write("## Summary\n\n")
            f.write("| Model | F1-Score | Precision | Recall | ROC-AUC | Latency (ms) | Training (s) | Status |\n")
            f.write("|-------|----------|-----------|--------|---------|--------------|--------------|--------|\n")
            
            for model_name, metrics in self.results.items():
                if "f1_score" in metrics:
                    f.write(f"| {model_name} | {metrics['f1_score']} | {metrics['precision']} | {metrics['recall']} | {metrics['roc_auc']} | {metrics['avg_latency_ms']} | {metrics['training_time_sec']} | {metrics.get('status', '✅')} |\n")
                else:
                    f.write(f"| {model_name} | — | — | — | — | — | — | {metrics.get('status', 'Unknown')} |\n")
            
            f.write("\n## Detailed Results\n\n")
            f.write("```json\n")
            f.write(json.dumps(self.results, indent=2))
            f.write("\n```\n")
        
        logger.info("Markdown report saved to: %s", md_path)


def main():
    """Main execution."""
    try:
        comparison = ModelComparison(HISTORICAL_DATA_PATH, contamination=CONTAMINATION)
        
        # Load data
        X = comparison.load_data()
        
        # Prepare splits
        X_train, X_test, y_test = comparison.prepare_splits(X)
        
        # Train and evaluate all models
        comparison.train_and_evaluate(X_train, X_test, y_test)
        
        # Generate report
        comparison.generate_report()
        
        # Save results
        comparison.save_results()
        
        logger.info("\n✅ Model comparison complete!")
        logger.info("Results saved to: %s", RESULTS_DIR)
        
    except Exception as e:
        logger.error("Fatal error: %s", str(e), exc_info=True)
        raise


if __name__ == "__main__":
    main()
