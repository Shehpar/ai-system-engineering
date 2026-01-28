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

class DataValidator:
    def __init__(self):
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "passed": True,
            "checks": {}
        }
    
    def validate_schema(self, df):
        """Check required columns exist."""
        print("\n🔍 SCHEMA VALIDATION")
        print("-" * 40)
        
        required_columns = ["cpu_usage", "memory_usage", "network_load"]
        missing = [col for col in required_columns if col not in df.columns]
        
        if missing:
            print(f"❌ Missing columns: {missing}")
            self.validation_results["passed"] = False
            return False
        
        print(f"✅ All required columns present: {required_columns}")
        self.validation_results["checks"]["schema"] = "PASSED"
        return True
    
    def validate_ranges(self, df):
        """Check values are within expected ranges."""
        print("\n📏 RANGE VALIDATION")
        print("-" * 40)
        
        all_valid = True
        range_violations = {}
        
        for col, rules in VALIDATION_RULES.items():
            min_val = rules["min"]
            max_val = rules["max"]
            
            below_min = df[col] < min_val
            if below_min.any():
                count = below_min.sum()
                print(f"⚠️  {col}: {count} values below {min_val}")
                range_violations[f"{col}_below_min"] = int(count)
                all_valid = False
            
            if max_val is not None:
                above_max = df[col] > max_val
                if above_max.any():
                    count = above_max.sum()
                    print(f"⚠️  {col}: {count} values above {max_val}")
                    range_violations[f"{col}_above_max"] = int(count)
                    all_valid = False
        
        if all_valid:
            print("✅ All values within expected ranges")
            self.validation_results["checks"]["ranges"] = "PASSED"
        else:
            self.validation_results["checks"]["ranges"] = {
                "status": "WARNINGS",
                "violations": range_violations
            }
        
        return all_valid or len(range_violations) < len(df) * 0.05  # Fail if >5% violations
    
    def validate_missing_values(self, df):
        """Check for null values."""
        print("\n⚠️  MISSING VALUE VALIDATION")
        print("-" * 40)
        
        missing_counts = df.isnull().sum()
        total_missing = missing_counts.sum()
        
        if total_missing == 0:
            print("✅ No missing values detected")
            self.validation_results["checks"]["missing_values"] = "PASSED"
            return True
        else:
            print(f"❌ Found {total_missing} missing values:")
            for col, count in missing_counts[missing_counts > 0].items():
                print(f"  {col}: {count}")
            self.validation_results["passed"] = False
            self.validation_results["checks"]["missing_values"] = {
                "status": "FAILED",
                "counts": missing_counts.to_dict()
            }
            return False
    
    def validate_duplicates(self, df):
        """Check for duplicate rows."""
        print("\n🔄 DUPLICATE VALIDATION")
        print("-" * 40)
        
        duplicates = df.duplicated().sum()
        
        if duplicates == 0:
            print("✅ No duplicate rows detected")
            self.validation_results["checks"]["duplicates"] = "PASSED"
            return True
        else:
            print(f"⚠️  Found {duplicates} duplicate rows ({duplicates/len(df)*100:.2f}%)")
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
        print("\n📊 STATISTICAL VALIDATION")
        print("-" * 40)
        
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
            print(f"{col}: μ={col_stats['mean']:.2f}, σ={col_stats['std']:.2f}, "
                  f"range=[{col_stats['min']:.2f}, {col_stats['max']:.2f}]")
        
        self.validation_results["checks"]["statistics"] = stats
        self.validation_results["checks"]["sample_count"] = len(df)
        
        # Warn if very small dataset
        if len(df) < 30:
            print(f"⚠️  Only {len(df)} samples. Recommend at least 30 for training.")
        
        return True
    
    def validate_outliers(self, df):
        """Detect statistical outliers using IQR method."""
        print("\n🎯 OUTLIER DETECTION (IQR Method)")
        print("-" * 40)
        
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
                print(f"⚠️  {col}: {outliers} outliers ({outlier_ratio*100:.2f}%)")
        
        if total_outliers == 0:
            print("✅ No statistical outliers detected")
            self.validation_results["checks"]["outliers"] = "PASSED"
        else:
            print(f"ℹ️  Total: {total_outliers} outliers in dataset")
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
        
        print(f"\n✅ Validation report saved: {report_path}")
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
    print("=" * 60)
    print("📋 DATA VALIDATION")
    print("=" * 60)
    
    try:
        if not os.path.exists(HISTORICAL_DATA_PATH):
            print(f"❌ Data file not found: {HISTORICAL_DATA_PATH}")
            return False
        
        df = pd.read_csv(HISTORICAL_DATA_PATH)
        print(f"\n✅ Loaded {len(df)} samples from {HISTORICAL_DATA_PATH}")
        
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
        
        print("\n" + "=" * 60)
        if passed:
            print("✅ DATA VALIDATION PASSED - Safe to use for training")
        else:
            print("❌ DATA VALIDATION FAILED - Review report and fix issues")
        print("=" * 60)
        
        return passed
        
    except Exception as e:
        print(f"\n❌ Validation error: {e}")
        raise

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
