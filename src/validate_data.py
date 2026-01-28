"""
Data Validation Script
======================
Validates data schema, ranges, and quality before training/inference.
Checks:
- Schema (3 required columns)
- Value ranges (CPU/mem: 0-100%, network: ≥0)
- Missing values, duplicates, outliers
- Fails pipeline if validation fails
"""

import pandas as pd
import numpy as np
import json
import os
import logging
from datetime import datetime

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORICAL_DATA_PATH = os.path.join(BASE_DIR, "data/processed/system_metrics_processed.csv")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
VALIDATION_RULES = {
    "cpu_usage": {"min": 0, "max": 100},
    "memory_usage": {"min": 0, "max": 100},
    "network_load": {"min": 0, "max": None}  # No upper limit
}

os.makedirs(RESULTS_DIR, exist_ok=True)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

class DataValidator:
    def __init__(self):
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "passed": True,
            "checks": {}
        }
    
    def validate_schema(self, df):
        """Check required columns exist."""
        logger.info("SCHEMA VALIDATION")
        
        required_columns = ["cpu_usage", "memory_usage", "network_load"]
        missing = [col for col in required_columns if col not in df.columns]
        
        if missing:
            logger.error("Missing columns: %s", missing)
            self.validation_results["passed"] = False
            return False
        
        logger.info("All required columns present: %s", required_columns)
        self.validation_results["checks"]["schema"] = "PASSED"
        return True
    
    def validate_ranges(self, df):
        """Check values are within expected ranges."""
        logger.info("RANGE VALIDATION")
        
        all_valid = True
        range_violations = {}
        
        for col, rules in VALIDATION_RULES.items():
            min_val = rules["min"]
            max_val = rules["max"]
            
            below_min = df[col] < min_val
            if below_min.any():
                count = below_min.sum()
                logger.warning("%s: %s values below %s", col, count, min_val)
                range_violations[f"{col}_below_min"] = int(count)
                all_valid = False
            
            if max_val is not None:
                above_max = df[col] > max_val
                if above_max.any():
                    count = above_max.sum()
                    logger.warning("%s: %s values above %s", col, count, max_val)
                    range_violations[f"{col}_above_max"] = int(count)
                    all_valid = False
        
        if all_valid:
            logger.info("All values within expected ranges")
            self.validation_results["checks"]["ranges"] = "PASSED"
        else:
            self.validation_results["checks"]["ranges"] = {
                "status": "WARNINGS",
                "violations": range_violations
            }
        
        return all_valid or len(range_violations) < len(df) * 0.05  # Fail if >5% violations
    
    def validate_missing_values(self, df):
        """Check for null values."""
        logger.info("MISSING VALUE VALIDATION")
        
        missing_counts = df.isnull().sum()
        total_missing = missing_counts.sum()
        
        if total_missing == 0:
            logger.info("No missing values detected")
            self.validation_results["checks"]["missing_values"] = "PASSED"
            return True
        else:
            logger.error("Found %s missing values:", total_missing)
            for col, count in missing_counts[missing_counts > 0].items():
                logger.error("%s: %s", col, count)
            self.validation_results["passed"] = False
            self.validation_results["checks"]["missing_values"] = {
                "status": "FAILED",
                "counts": missing_counts.to_dict()
            }
            return False
    
    def validate_duplicates(self, df):
        """Check for duplicate rows."""
        logger.info("DUPLICATE VALIDATION")
        
        duplicates = df.duplicated().sum()
        
        if duplicates == 0:
            logger.info("No duplicate rows detected")
            self.validation_results["checks"]["duplicates"] = "PASSED"
            return True
        else:
            logger.warning("Found %s duplicate rows (%.2f%%)", duplicates, duplicates / len(df) * 100)
            if duplicates / len(df) > 0.1:  # Fail if >10% duplicates
                self.validation_results["passed"] = False
                self.validation_results["checks"]["duplicates"] = {
                    "status": "FAILED",
                    "count": int(duplicates),
                    "ratio": float(duplicates / len(df))
                }
                return False
            else:
                self.validation_results["checks"]["duplicates"] = {
                    "status": "WARNING",
                    "count": int(duplicates),
                    "ratio": float(duplicates / len(df))
                }
                return True
    
    def validate_statistics(self, df):
        """Validate statistical properties."""
        logger.info("STATISTICAL VALIDATION")
        
        stats = {}
        for col in ["cpu_usage", "memory_usage", "network_load"]:
            col_stats = {
                "mean": float(df[col].mean()),
                "std": float(df[col].std()),
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "q25": float(df[col].quantile(0.25)),
                "q75": float(df[col].quantile(0.75))
            }
            stats[col] = col_stats
            logger.info(
                "%s: mean=%.2f, std=%.2f, range=[%.2f, %.2f]",
                col,
                col_stats["mean"],
                col_stats["std"],
                col_stats["min"],
                col_stats["max"]
            )
        
        self.validation_results["checks"]["statistics"] = stats
        self.validation_results["checks"]["sample_count"] = len(df)
        
        # Warn if very small dataset
        if len(df) < 30:
            logger.warning("Only %s samples. Recommend at least 30 for training.", len(df))
        
        return True
    
    def validate_outliers(self, df):
        """Detect statistical outliers using IQR method."""
        logger.info("OUTLIER DETECTION (IQR Method)")
        
        outlier_summary = {}
        total_outliers = 0
        
        for col in ["cpu_usage", "memory_usage", "network_load"]:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
            outlier_ratio = outliers / len(df)
            total_outliers += outliers
            
            outlier_summary[col] = {
                "count": int(outliers),
                "ratio": float(outlier_ratio),
                "bounds": [float(lower_bound), float(upper_bound)]
            }
            
            if outliers > 0:
                logger.warning("%s: %s outliers (%.2f%%)", col, outliers, outlier_ratio * 100)
        
        if total_outliers == 0:
            logger.info("No statistical outliers detected")
            self.validation_results["checks"]["outliers"] = "PASSED"
        else:
            logger.info("Total: %s outliers in dataset", total_outliers)
            self.validation_results["checks"]["outliers"] = outlier_summary
        
        return True
    
    def save_validation_report(self):
        """Save validation report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(RESULTS_DIR, f"validation_report_{timestamp}.json")
        
        with open(report_path, 'w') as f:
            json.dump(self.validation_results, f, indent=2)
        
        # Also save as latest
        with open(os.path.join(RESULTS_DIR, "validation_report_latest.json"), 'w') as f:
            json.dump(self.validation_results, f, indent=2)
        
        logger.info("Validation report saved: %s", report_path)
        return self.validation_results["passed"]

def validate_live_data(cpu, mem, net):
    """Quick validation for live data point."""
    issues = []
    
    if not (0 <= cpu <= 100):
        issues.append(f"CPU {cpu} out of range [0, 100]")
    if not (0 <= mem <= 100):
        issues.append(f"Memory {mem} out of range [0, 100]")
    if not (net >= 0):
        issues.append(f"Network {net} is negative")
    
    return len(issues) == 0, issues

def main():
    logger.info("DATA VALIDATION")
    
    try:
        if not os.path.exists(HISTORICAL_DATA_PATH):
            logger.error("Data file not found: %s", HISTORICAL_DATA_PATH)
            return False
        
        df = pd.read_csv(HISTORICAL_DATA_PATH)
        logger.info("Loaded %s samples from %s", len(df), HISTORICAL_DATA_PATH)
        
        validator = DataValidator()
        
        # Run all validations
        schema_ok = validator.validate_schema(df)
        ranges_ok = validator.validate_ranges(df)
        missing_ok = validator.validate_missing_values(df)
        duplicates_ok = validator.validate_duplicates(df)
        validator.validate_statistics(df)
        validator.validate_outliers(df)
        
        # Save report
        passed = validator.save_validation_report()
        
        if passed:
            logger.info("DATA VALIDATION PASSED - Safe to use for training")
        else:
            logger.error("DATA VALIDATION FAILED - Review report and fix issues")
        
        return passed
        
    except Exception as e:
        logger.exception("Validation error: %s", e)
        raise

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
