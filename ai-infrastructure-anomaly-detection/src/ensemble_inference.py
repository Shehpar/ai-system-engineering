"""
Ensemble Inference - Combine Multiple Anomaly Detection Models
==============================================================
Implements ensemble methods for combining predictions from multiple models.

Ensemble Strategies:
1. Hard Voting: Anomaly if ≥2/3 models agree
2. Soft Voting: Average anomaly scores from all models
3. Weighted Voting: Weight models by their ROC-AUC performance

Usage:
    from ensemble_inference import EnsembleDetector
    
    detector = EnsembleDetector(
        models_dir="models/",
        strategy="soft"  # 'hard', 'soft', or 'weighted'
    )
    
    anomaly_score, is_anomaly, model_votes = detector.predict(
        cpu=45.2,
        memory=62.1,
        network=1250.5
    )
"""

import joblib
import numpy as np
import os
import logging
from typing import Tuple, Dict, List
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnsembleDetector:
    """Ensemble anomaly detector combining multiple models."""
    
    # Model weights (based on typical ROC-AUC performance)
    MODEL_WEIGHTS = {
        "isolation_forest_model.pkl": 0.40,      # Best balanced
        "elliptic_envelope_model.pkl": 0.35,     # Fast + accurate
        "lof_model_model.pkl": 0.25               # Catches local anomalies
    }
    
    ENSEMBLE_STRATEGIES = {
        "hard": "Majority voting (anomaly if ≥2/3 models agree)",
        "soft": "Average anomaly scores across all models",
        "weighted": "Weighted average by ROC-AUC performance"
    }
    
    def __init__(self, models_dir: str, scaler_path: str = None, 
                 strategy: str = "soft", threshold: float = 0.5):
        """
        Initialize ensemble detector.
        
        Args:
            models_dir: Directory containing trained model .pkl files
            scaler_path: Path to StandardScaler pickle file
            strategy: 'hard', 'soft', or 'weighted'
            threshold: Anomaly score threshold for classification
        """
        self.models_dir = models_dir
        self.strategy = strategy.lower()
        self.threshold = threshold
        self.models = {}
        self.scaler = None
        
        if self.strategy not in self.ENSEMBLE_STRATEGIES:
            raise ValueError(f"Strategy must be one of: {list(self.ENSEMBLE_STRATEGIES.keys())}")
        
        # Load scaler
        if scaler_path and os.path.exists(scaler_path):
            self.scaler = joblib.load(scaler_path)
            logger.info("✅ Loaded scaler from: %s", scaler_path)
        else:
            # Try to find scaler in models_dir
            default_scaler = os.path.join(models_dir, "scaler.pkl")
            if os.path.exists(default_scaler):
                self.scaler = joblib.load(default_scaler)
                logger.info("✅ Loaded scaler from: %s", default_scaler)
        
        # Load all models
        self._load_models()
        
        logger.info("✅ Initialized ensemble detector (strategy: %s)", self.strategy)
    
    def _load_models(self):
        """Load all trained models from directory."""
        if not os.path.exists(self.models_dir):
            raise FileNotFoundError(f"Models directory not found: {self.models_dir}")
        
        model_files = [f for f in os.listdir(self.models_dir) 
                      if f.endswith("_model.pkl")]
        
        if not model_files:
            raise FileNotFoundError(f"No models found in: {self.models_dir}")
        
        for model_file in model_files:
            model_path = os.path.join(self.models_dir, model_file)
            try:
                model = joblib.load(model_path)
                self.models[model_file] = model
                logger.info("✅ Loaded model: %s", model_file)
            except Exception as e:
                logger.error("❌ Failed to load model %s: %s", model_file, str(e))
        
        if not self.models:
            raise RuntimeError("No models loaded successfully")
    
    def predict(self, features: np.ndarray) -> Tuple[float, int, Dict]:
        """
        Predict anomaly using ensemble.
        
        Args:
            features: Array of shape (3,) [cpu, memory, network]
        
        Returns:
            (anomaly_score, is_anomaly, votes_dict)
            - anomaly_score: 0.0-1.0, higher = more anomalous
            - is_anomaly: 0 (normal) or 1 (anomaly)
            - votes_dict: Details from each model
        """
        if len(features) != 3:
            raise ValueError(f"Expected 3 features, got {len(features)}")
        
        # Scale features
        if self.scaler:
            features_scaled = self.scaler.transform([features])[0]
        else:
            features_scaled = features
        
        # Get predictions from all models
        model_votes = {}
        anomaly_scores = []
        
        for model_name, model in self.models.items():
            try:
                # Predict
                prediction = model.predict([features_scaled])[0]
                
                # Get anomaly score
                if hasattr(model, 'score_samples'):
                    score = model.score_samples([features_scaled])[0]
                else:
                    score = model.decision_function([features_scaled])[0]
                
                # Convert prediction to binary (1=anomaly, 0=normal)
                is_anomaly = 1 if prediction == -1 else 0
                anomaly_scores.append(score)
                
                model_votes[model_name] = {
                    "prediction": int(is_anomaly),
                    "score": float(score)
                }
                
            except Exception as e:
                logger.warning("Model %s failed: %s", model_name, str(e))
                model_votes[model_name] = {"error": str(e)}
        
        # Combine predictions using ensemble strategy
        if self.strategy == "hard":
            ensemble_score, final_prediction = self._hard_voting(model_votes)
        elif self.strategy == "soft":
            ensemble_score, final_prediction = self._soft_voting(model_votes)
        elif self.strategy == "weighted":
            ensemble_score, final_prediction = self._weighted_voting(model_votes)
        
        return ensemble_score, final_prediction, model_votes
    
    def _hard_voting(self, model_votes: Dict) -> Tuple[float, int]:
        """Majority voting: anomaly if ≥2/3 models agree."""
        predictions = [v["prediction"] for v in model_votes.values() 
                      if "prediction" in v]
        
        if not predictions:
            return 0.0, 0
        
        anomaly_count = sum(predictions)
        total_models = len(predictions)
        
        # Score = ratio of models detecting anomaly
        score = anomaly_count / total_models
        
        # Anomaly if ≥2/3 models agree
        final_prediction = 1 if anomaly_count >= (total_models * 2 / 3) else 0
        
        return score, final_prediction
    
    def _soft_voting(self, model_votes: Dict) -> Tuple[float, int]:
        """Average anomaly scores."""
        scores = [abs(v["score"]) for v in model_votes.values() 
                 if "score" in v]
        
        if not scores:
            return 0.0, 0
        
        # Normalize scores to 0-1 range
        max_score = max(scores) if scores else 1.0
        if max_score == 0:
            max_score = 1.0
        
        normalized_scores = [s / max_score for s in scores]
        ensemble_score = np.mean(normalized_scores)
        
        # Classify based on threshold
        final_prediction = 1 if ensemble_score >= self.threshold else 0
        
        return ensemble_score, final_prediction
    
    def _weighted_voting(self, model_votes: Dict) -> Tuple[float, int]:
        """Weighted average by model performance."""
        weighted_sum = 0.0
        weight_sum = 0.0
        
        for model_name, vote in model_votes.items():
            if "score" in vote:
                weight = self.MODEL_WEIGHTS.get(model_name, 1.0 / len(self.models))
                score = abs(vote["score"])
                weighted_sum += score * weight
                weight_sum += weight
        
        if weight_sum == 0:
            return 0.0, 0
        
        # Normalize to 0-1
        ensemble_score = weighted_sum / weight_sum if weight_sum > 0 else 0.0
        max_score = max([abs(v["score"]) for v in model_votes.values() 
                        if "score" in v], default=1.0)
        if max_score > 0:
            ensemble_score = ensemble_score / max_score
        
        # Classify based on threshold
        final_prediction = 1 if ensemble_score >= self.threshold else 0
        
        return ensemble_score, final_prediction
    
    def get_strategy_info(self) -> str:
        """Get information about ensemble strategy."""
        return self.ENSEMBLE_STRATEGIES.get(self.strategy, "Unknown")
    
    def set_threshold(self, threshold: float):
        """Update anomaly threshold."""
        if not 0 <= threshold <= 1:
            raise ValueError("Threshold must be between 0 and 1")
        self.threshold = threshold
        logger.info("Updated threshold to: %.2f", threshold)


# Example usage
if __name__ == "__main__":
    import sys
    
    # Initialize ensemble
    try:
        ensemble = EnsembleDetector(
            models_dir="models/",
            strategy="soft"
        )
        
        # Example predictions
        test_cases = [
            ("Normal", np.array([30.0, 45.0, 500.0])),
            ("CPU Spike", np.array([85.0, 50.0, 600.0])),
            ("Memory High", np.array([35.0, 90.0, 700.0])),
            ("Network Burst", np.array([40.0, 55.0, 8000.0])),
        ]
        
        print("\n" + "=" * 80)
        print("ENSEMBLE PREDICTION EXAMPLES")
        print("=" * 80)
        print(f"Strategy: {ensemble.get_strategy_info()}\n")
        
        for test_name, features in test_cases:
            score, pred, votes = ensemble.predict(features)
            print(f"{test_name}:")
            print(f"  Features: CPU={features[0]:.1f}%, MEM={features[1]:.1f}%, NET={features[2]:.1f}bps")
            print(f"  Ensemble Score: {score:.4f}")
            print(f"  Prediction: {'🔴 ANOMALY' if pred == 1 else '🟢 NORMAL'}")
            print(f"  Model Votes: {votes}")
            print()
        
    except Exception as e:
        logger.error("Error: %s", str(e))
        sys.exit(1)
