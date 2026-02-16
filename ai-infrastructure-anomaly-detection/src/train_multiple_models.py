"""
Multi-Model Training Script - Train Multiple Anomaly Detection Models
=====================================================================
Trains and persists multiple anomaly detection models for ensemble inference.

This script trains:
1. Isolation Forest (current baseline)
2. Elliptic Envelope (fast alternative)
3. Local Outlier Factor (local anomalies)

Usage:
    python src/train_multiple_models.py

Output:
    - models/isolation_forest_model.pkl
    - models/elliptic_envelope_model.pkl
    - models/lof_model.pkl
    - models/scaler.pkl (shared scaler)
    - results/multi_model_training_metrics.json
"""

import pandas as pd
import numpy as np
import joblib
import json
import os
import logging
from datetime import datetime
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.covariance import EllipticEnvelope
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix
)

import warnings
warnings.filterwarnings('ignore')

try:
    import mlflow
    from mlflow.models.signature import infer_signature
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORICAL_DATA_PATH = os.path.join(BASE_DIR, "data/processed/system_metrics_processed.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
MLFLOW_EXPERIMENT_NAME = "multi_model_anomaly_detection"

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# MLflow configuration
if MLFLOW_AVAILABLE:
    try:
        mlflow.set_tracking_uri("http://mlflow:5000")
    except:
        mlflow.set_tracking_uri(os.path.join(BASE_DIR, ".mlflow"))


class MultiModelTrainer:
    """Train and manage multiple anomaly detection models."""
    
    def __init__(self, contamination=0.05, random_state=42):
        self.contamination = contamination
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.models = {}
        self.results = {}
    
    def load_data(self):
        """Load and prepare data."""
        logger.info("Loading historical data from %s", HISTORICAL_DATA_PATH)
        
        if not os.path.exists(HISTORICAL_DATA_PATH):
            raise FileNotFoundError(f"Data not found: {HISTORICAL_DATA_PATH}")
        
        df = pd.read_csv(HISTORICAL_DATA_PATH)
        features = ["cpu_usage", "memory_usage", "network_load"]
        
        for feat in features:
            if feat not in df.columns:
                raise ValueError(f"Missing feature: {feat}")
        
        X = df[features].values
        logger.info("Loaded %d samples with %d features", X.shape[0], X.shape[1])
        
        return X
    
    def split_data(self, X, test_size=0.15, val_size=0.15):
        """Split data into train/val/test."""
        X_train, X_temp = train_test_split(
            X, test_size=(test_size + val_size),
            random_state=self.random_state
        )
        
        X_val, X_test = train_test_split(
            X_temp, test_size=0.5,
            random_state=self.random_state
        )
        
        logger.info("Data split - Train: %d, Val: %d, Test: %d",
                   len(X_train), len(X_val), len(X_test))
        
        return X_train, X_val, X_test
    
    def train_models(self, X_train, X_val, X_test):
        """Train all models."""
        # Scale data
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Create ground truth using Isolation Forest (reference model)
        logger.info("Creating pseudo-labels using Isolation Forest as reference...")
        iso_ref = IsolationForest(contamination=self.contamination, random_state=self.random_state)
        y_true = iso_ref.fit_predict(X_train_scaled)
        y_true = (y_true == -1).astype(int)  # Convert to binary (1=anomaly)
        
        # Define models
        models_config = {
            "isolation_forest": {
                "model": IsolationForest(
                    contamination=self.contamination,
                    n_estimators=100,
                    random_state=self.random_state,
                    max_samples='auto'
                ),
                "description": "Isolation Forest - Unsupervised ensemble method"
            },
            "elliptic_envelope": {
                "model": EllipticEnvelope(
                    contamination=self.contamination,
                    random_state=self.random_state,
                    support_fraction=0.95
                ),
                "description": "Elliptic Envelope - Robust covariance estimation"
            },
            "lof": {
                "model": LocalOutlierFactor(
                    n_neighbors=20,
                    contamination=self.contamination,
                    novelty=False
                ),
                "description": "Local Outlier Factor - Density-based detection"
            }
        }
        
        # Train each model
        for model_name, model_config in models_config.items():
            logger.info("-" * 60)
            logger.info("Training: %s", model_config["description"])
            logger.info("-" * 60)
            
            try:
                model = model_config["model"]
                
                # Train
                model.fit(X_train_scaled)
                self.models[model_name] = model
                
                # Predict on test set
                y_pred = model.predict(X_test_scaled)
                y_pred_binary = (y_pred == -1).astype(int)
                
                # Get anomaly scores
                if hasattr(model, 'score_samples'):
                    y_scores = model.score_samples(X_test_scaled)
                else:
                    y_scores = model.decision_function(X_test_scaled)
                
                # Calculate metrics
                precision = precision_score(y_true[:len(y_pred)], y_pred_binary, zero_division=0)
                recall = recall_score(y_true[:len(y_pred)], y_pred_binary, zero_division=0)
                f1 = f1_score(y_true[:len(y_pred)], y_pred_binary, zero_division=0)
                
                try:
                    roc_auc = roc_auc_score(y_true[:len(y_pred)], y_scores)
                except:
                    roc_auc = 0.0
                
                tn, fp, fn, tp = confusion_matrix(y_true[:len(y_pred)], y_pred_binary).ravel()
                
                # Store results
                self.results[model_name] = {
                    "description": model_config["description"],
                    "precision": round(float(precision), 4),
                    "recall": round(float(recall), 4),
                    "f1_score": round(float(f1), 4),
                    "roc_auc": round(float(roc_auc), 4),
                    "true_positives": int(tp),
                    "false_positives": int(fp),
                    "true_negatives": int(tn),
                    "false_negatives": int(fn),
                    "contamination": self.contamination,
                    "trained_at": datetime.now().isoformat(),
                    "status": "✅ Success"
                }
                
                logger.info("✅ %s - F1: %.4f | Precision: %.4f | Recall: %.4f | ROC-AUC: %.4f",
                           model_name, f1, precision, recall, roc_auc)
                
            except Exception as e:
                logger.error("❌ %s - Error: %s", model_name, str(e))
                self.results[model_name] = {
                    "status": f"❌ Error: {str(e)}"
                }
    
    def save_models(self):
        """Save trained models and scaler."""
        logger.info("-" * 60)
        logger.info("Saving trained models...")
        logger.info("-" * 60)
        
        # Save scaler
        scaler_path = os.path.join(MODEL_DIR, "scaler.pkl")
        joblib.dump(self.scaler, scaler_path)
        logger.info("✅ Saved scaler to: %s", scaler_path)
        
        # Save each model
        for model_name, model in self.models.items():
            model_path = os.path.join(MODEL_DIR, f"{model_name}_model.pkl")
            joblib.dump(model, model_path)
            logger.info("✅ Saved %s to: %s", model_name, model_path)
    
    def save_results(self):
        """Save training results."""
        # JSON report
        json_path = os.path.join(RESULTS_DIR, "multi_model_training_metrics.json")
        with open(json_path, "w") as f:
            json.dump(self.results, f, indent=2)
        logger.info("✅ Saved metrics to: %s", json_path)
        
        # Markdown report
        md_path = os.path.join(RESULTS_DIR, "multi_model_training_report.md")
        with open(md_path, "w") as f:
            f.write("# Multi-Model Training Report\n\n")
            f.write(f"**Generated**: {datetime.now().isoformat()}\n\n")
            
            f.write("## Summary\n\n")
            f.write("| Model | F1-Score | Precision | Recall | ROC-AUC | Status |\n")
            f.write("|-------|----------|-----------|--------|---------|--------|\n")
            
            for model_name, metrics in self.results.items():
                if "f1_score" in metrics:
                    f.write(f"| {model_name} | {metrics['f1_score']} | {metrics['precision']} | {metrics['recall']} | {metrics['roc_auc']} | {metrics.get('status', '✅')} |\n")
                else:
                    f.write(f"| {model_name} | — | — | — | — | {metrics.get('status', 'Failed')} |\n")
            
            f.write("\n## Model Descriptions\n\n")
            for model_name, metrics in self.results.items():
                if "description" in metrics:
                    f.write(f"### {model_name}\n")
                    f.write(f"{metrics['description']}\n\n")
        
        logger.info("✅ Saved report to: %s", md_path)
    
    def log_to_mlflow(self):
        """Log results to MLflow."""
        if not MLFLOW_AVAILABLE:
            logger.warning("MLflow not available. Skipping logging.")
            return
        
        try:
            mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
            
            with mlflow.start_run():
                # Log parameters
                mlflow.log_param("contamination", self.contamination)
                mlflow.log_param("models_trained", list(self.models.keys()))
                
                # Log metrics for each model
                for model_name, metrics in self.results.items():
                    if "f1_score" in metrics:
                        mlflow.log_metrics({
                            f"{model_name}_f1": metrics["f1_score"],
                            f"{model_name}_precision": metrics["precision"],
                            f"{model_name}_recall": metrics["recall"],
                            f"{model_name}_roc_auc": metrics["roc_auc"]
                        })
                
                logger.info("✅ Logged to MLflow run")
        except Exception as e:
            logger.warning("Failed to log to MLflow: %s", str(e))
    
    def print_summary(self):
        """Print training summary."""
        logger.info("\n" + "=" * 70)
        logger.info("MULTI-MODEL TRAINING SUMMARY")
        logger.info("=" * 70)
        
        for model_name, metrics in self.results.items():
            if "f1_score" in metrics:
                logger.info("\n%s:", model_name)
                logger.info("  F1-Score:  %.4f", metrics["f1_score"])
                logger.info("  Precision: %.4f", metrics["precision"])
                logger.info("  Recall:    %.4f", metrics["recall"])
                logger.info("  ROC-AUC:   %.4f", metrics["roc_auc"])
                logger.info("  TP/FP/FN/TN: %d/%d/%d/%d",
                           metrics["true_positives"],
                           metrics["false_positives"],
                           metrics["false_negatives"],
                           metrics["true_negatives"])
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ All models trained and saved!")
        logger.info("=" * 70)


def main():
    """Main execution."""
    try:
        trainer = MultiModelTrainer(contamination=0.05, random_state=42)
        
        # Load data
        X = trainer.load_data()
        
        # Split data
        X_train, X_val, X_test = trainer.split_data(X)
        
        # Train all models
        trainer.train_models(X_train, X_val, X_test)
        
        # Save models
        trainer.save_models()
        
        # Save results
        trainer.save_results()
        
        # Log to MLflow
        trainer.log_to_mlflow()
        
        # Print summary
        trainer.print_summary()
        
    except Exception as e:
        logger.error("Fatal error: %s", str(e), exc_info=True)
        raise


if __name__ == "__main__":
    main()
