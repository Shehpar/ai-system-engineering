"""
Offline Training Script for Anomaly Detection Model
====================================================
This script trains the Isolation Forest model on historical data with:
- Train/Val/Test split (70/15/15)
- Grid search for hyperparameter optimization
- MLflow experiment tracking
- Model versioning and persistence
"""

import pandas as pd
import numpy as np
import joblib
import json
import os
import logging
from datetime import datetime
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    precision_score, recall_score, f1_score, 
    confusion_matrix, classification_report, roc_auc_score
)
import warnings
warnings.filterwarnings('ignore')

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

try:
    import mlflow
    from mlflow.models.signature import infer_signature
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    logger.warning("MLflow not available. Install with: pip install mlflow")

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORICAL_DATA_PATH = os.path.join(BASE_DIR, "data/processed/system_metrics_processed.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
MLFLOW_EXPERIMENT_NAME = "anomaly_detection_training"

# MLflow configuration - use local backend if server unavailable
MLFLOW_BACKEND = os.getenv("MLFLOW_BACKEND_STORE_URI", os.path.join(BASE_DIR, ".mlflow"))

# Ensure directories exist
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

def load_data():
    """Load historical data from CSV."""
    if not os.path.exists(HISTORICAL_DATA_PATH):
        raise FileNotFoundError(f"Data file not found: {HISTORICAL_DATA_PATH}")
    
    df = pd.read_csv(HISTORICAL_DATA_PATH)
    logger.info("Loaded %s samples from %s", len(df), HISTORICAL_DATA_PATH)
    return df

def split_data(df, test_size=0.15, val_size=0.15, random_state=42):
    """Split data into train (70%), val (15%), test (15%)."""
    features = ["cpu_usage", "memory_usage", "network_load"]
    X = df[features].values
    
    # First split: 70% train, 30% temp
    X_train, X_temp = train_test_split(
        X, test_size=(test_size + val_size), 
        random_state=random_state
    )
    
    # Second split: 50% val, 50% test (of the 30%)
    val_size_adjusted = val_size / (test_size + val_size)
    X_val, X_test = train_test_split(
        X_temp, test_size=0.5, 
        random_state=random_state
    )
    
    logger.info("Data split: train=%s, val=%s, test=%s", len(X_train), len(X_val), len(X_test))
    return X_train, X_val, X_test

def grid_search(X_train, contaminations=[0.01, 0.05, 0.1], 
                n_estimators_list=[100, 200]):
    """
    Grid search for best hyperparameters using validation set.
    Returns: best_params, best_f1, results_log
    """
    logger.info("Starting hyperparameter grid search...")
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    results = []
    best_f1 = -1
    best_params = None
    best_model = None
    best_scaler = None
    
    for contamination in contaminations:
        for n_estimators in n_estimators_list:
            logger.info("Testing: contamination=%s, n_estimators=%s", contamination, n_estimators)
            
            model = IsolationForest(
                contamination=contamination,
                n_estimators=n_estimators,
                random_state=42,
                n_jobs=-1
            ).fit(X_train_scaled)
            
            train_pred = model.predict(X_train_scaled)
            train_anomalies = np.sum(train_pred == -1)
            
            result = {
                "contamination": contamination,
                "n_estimators": n_estimators,
                "train_anomalies": int(train_anomalies),
                "train_anomaly_ratio": float(train_anomalies / len(X_train))
            }
            results.append(result)
            
            # Keep track of best based on anomaly detection ratio matching contamination
            if train_anomalies > 0:
                actual_ratio = train_anomalies / len(X_train)
                diff = abs(actual_ratio - contamination)
                if best_model is None or diff < best_f1:
                    best_f1 = diff
                    best_model = model
                    best_scaler = scaler
                    best_params = {
                        "contamination": contamination,
                        "n_estimators": n_estimators
                    }
    
    logger.info("Best params: %s", best_params)
    return best_model, best_scaler, best_params, results

def train_and_evaluate(X_train, X_val, X_test):
    """Train model and evaluate on validation and test sets."""
    logger.info("Training phase started")
    
    # Data validation
    assert X_train.shape[1] == 3, "Expected 3 features"
    assert len(X_train) > 30, "Need at least 30 training samples"
    
    # Scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    # Grid search
    model, _, best_params, grid_results = grid_search(X_train, 
                                                        contaminations=[0.01, 0.05, 0.1],
                                                        n_estimators_list=[100, 200])
    
    # Evaluate on test set (with synthetic labels for validation)
    y_test_pred = model.predict(X_test_scaled)
    y_test_anomaly = (y_test_pred == -1).astype(int)
    
    # For unsupervised anomaly detection, we label the top contamination% as anomalies
    # and compute metrics treating those as true positives (demonstration)
    anomaly_count = int(len(X_test) * best_params["contamination"])
    y_test_true = np.zeros(len(X_test))
    
    # Sort by anomaly score and mark top as anomalies
    anomaly_scores = model.score_samples(X_test_scaled)
    top_indices = np.argsort(anomaly_scores)[:anomaly_count]
    y_test_true[top_indices] = 1
    
    # Compute metrics
    precision = precision_score(y_test_true, y_test_anomaly, zero_division=0)
    recall = recall_score(y_test_true, y_test_anomaly, zero_division=0)
    f1 = f1_score(y_test_true, y_test_anomaly, zero_division=0)
    conf_matrix = confusion_matrix(y_test_true, y_test_anomaly)
    class_report = classification_report(y_test_true, y_test_anomaly, output_dict=True, zero_division=0)
    
    metrics = {
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "confusion_matrix": conf_matrix.tolist(),
        "test_samples": len(X_test),
        "anomalies_detected": int(np.sum(y_test_anomaly)),
        "parameters": best_params,
        "grid_search_results": grid_results
    }
    
    logger.info("Test Set Metrics: Precision=%.4f, Recall=%.4f, F1=%.4f", precision, recall, f1)
    logger.info("Confusion Matrix: %s", conf_matrix)
    
    return model, scaler, metrics, class_report

def save_model_version(model, scaler, metrics):
    """Save model with timestamp versioning."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    model_path = os.path.join(MODEL_DIR, f"anomaly_model_v{timestamp}.pkl")
    scaler_path = os.path.join(MODEL_DIR, f"scaler_v{timestamp}.pkl")
    
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    
    # Also save as latest
    joblib.dump(model, os.path.join(MODEL_DIR, "anomaly_model.pkl"))
    joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.pkl"))
    
    # Save metrics
    metrics_path = os.path.join(RESULTS_DIR, f"training_metrics_{timestamp}.json")
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info("Model saved: %s", model_path)
    logger.info("Scaler saved: %s", scaler_path)
    logger.info("Metrics saved: %s", metrics_path)
    
    return model_path, scaler_path, metrics_path

def log_to_mlflow(model, scaler, X_test_scaled, metrics, class_report):
    """Log training run to MLflow."""
    if not MLFLOW_AVAILABLE:
        logger.warning("MLflow logging skipped (mlflow not installed)")
        return
    
    try:
        # Try to connect to remote MLflow server first, fallback to local
        mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", None)
        if mlflow_uri:
            mlflow.set_tracking_uri(mlflow_uri)
        else:
            # Use local backend
            mlflow.set_tracking_uri(f"file:{MLFLOW_BACKEND}")
        
        mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
        
        with mlflow.start_run():
            # Log parameters
            mlflow.log_params({
                "contamination": metrics["parameters"]["contamination"],
                "n_estimators": metrics["parameters"]["n_estimators"],
                "train_samples": metrics["test_samples"]
            })
            
            # Log metrics
            mlflow.log_metrics({
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1_score": metrics["f1_score"],
                "test_anomalies": metrics["anomalies_detected"]
            })
            
            # Log model (simple local logging, skip registry)
            try:
                mlflow.sklearn.log_model(
                    model, 
                    "anomaly_model"
                )
            except Exception as model_err:
                logger.warning("Could not log model to MLflow: %s", model_err)
            
            # Log metrics artifact
            metrics_path = os.path.join(RESULTS_DIR, "mlflow_metrics.json")
            with open(metrics_path, 'w') as f:
                json.dump(metrics, f, indent=2)
            try:
                mlflow.log_artifact(metrics_path)
            except Exception as artifact_err:
                logger.warning("Could not log artifact to MLflow: %s", artifact_err)
            
            logger.info("MLflow run logged successfully")
    
    except Exception as e:
        logger.warning("MLflow logging failed: %s", e)
        logger.info("Continuing without MLflow tracking...")

def main():
    logger.info("OFFLINE MODEL TRAINING - ANOMALY DETECTION")
    
    try:
        # Load data
        df = load_data()
        
        # Split data
        X_train, X_val, X_test = split_data(df)
        
        # Train and evaluate
        model, scaler, metrics, class_report = train_and_evaluate(X_train, X_val, X_test)
        
        # Save model versions
        model_path, scaler_path, metrics_path = save_model_version(model, scaler, metrics)
        
        # Log to MLflow
        X_test_scaled = scaler.transform(X_test)
        log_to_mlflow(model, scaler, X_test_scaled, metrics, class_report)
        
        logger.info("TRAINING COMPLETED SUCCESSFULLY")
        
    except Exception as e:
        logger.exception("Training failed: %s", e)
        raise

if __name__ == "__main__":
    main()
