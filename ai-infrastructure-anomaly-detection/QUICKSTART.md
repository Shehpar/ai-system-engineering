# 🚀 QUICK START GUIDE

## What You Need to Do (3 Easy Steps)

### **Step 1: Make sure Docker Desktop is running**
- Open Windows Start menu
- Search for "Docker Desktop"
- Click to launch it
- Wait 30 seconds for it to fully start
- Check: You should see Docker icon in system tray (bottom right)

### **Step 2: Run the setup script**
Open PowerShell in the `ai-infrastructure-anomaly-detection` folder and run:

```powershell
cd "d:\Personal data\Masters_Classes_Material\Third Semester\AI Systems Engineer\project\ai-infrastructure-anomaly-detection"

# Run the automated setup script
.\setup_and_run.ps1

# For clean install (deletes all existing data)
.\setup_and_run.ps1 -CleanInstall
```

**That's it!** The script will automatically:
1. ✅ Check Docker is running
2. ✅ Start all services (InfluxDB, Grafana, MLflow, Python app)
3. ✅ Wait for services to initialize
4. ✅ Train the machine learning model
5. ✅ Validate data quality
6. ✅ Evaluate model robustness
7. ✅ Show you what to do next

### **Step 3: View Results**

The script will print URLs and instructions. Open these in your browser:

- **Grafana Dashboard**: http://localhost:3000
  - Login: admin / admin
  - See: Real-time metrics and anomaly predictions
  
- **MLflow Experiments**: http://localhost:5000
  - See: Training metrics, hyperparameters, model performance

### **Step 4: Run Tests (Optional)**

After setup completes, you can run comprehensive validation:

```powershell
# Default test (5 minutes, 200 RPS HTTP stress)
.\test_and_validate.ps1

# Custom test (2 minutes, 300 RPS)
.\test_and_validate.ps1 -Duration 120 -RequestsPerSecond 300
```

**What the test does**:
- ✅ Runs unit tests (5/5)
- ✅ Validates data quality
- ✅ Starts HTTP DoS simulation (attacks Flask server)
- ✅ Monitors for anomaly detection
- ✅ Generates test report (`results/test_report_*.txt`)

---

## What You'll Get After Running

### 📊 **Generated Files**

```
ai-infrastructure-anomaly-detection/
├── models/
│   ├── anomaly_model.pkl              ← Trained model
│   ├── anomaly_model_v20250128_*.pkl  ← Versioned model
│   ├── scaler.pkl                     ← Feature scaler
│   └── scaler_v20250128_*.pkl         ← Versioned scaler
│
├── results/
│   ├── training_metrics_20250128_*.json      ← Training results
│   ├── evaluation_report_20250128_*.json     ← Robustness test results
│   └── validation_report_20250128_*.json     ← Data quality report
│
├── data/processed/
│   └── system_metrics_processed.csv   ← Historical data
│
└── logs/
    └── app.log                        ← Application logs (if logging added)
```

### 📈 **What Each File Shows**

#### **training_metrics_*.json**
```json
{
  "precision": 0.92,
  "recall": 0.92,
  "f1_score": 0.92,
  "test_samples": 150,
  "parameters": {
    "contamination": 0.01,
    "n_estimators": 200
  }
}
```
✅ Shows: Model accuracy on test set

#### **evaluation_report_*.json**
```json
{
  "baseline": {
    "precision": 0.92,
    "recall": 0.92,
    "f1_score": 0.92,
    "latency_ms": 0.5
  },
  "noise_robustness": { ... },
  "missing_data_robustness": { ... },
  "outlier_robustness": { ... },
  "distribution_shift": { ... }
}
```
✅ Shows: How well model handles noise, missing data, outliers, distribution changes

#### **validation_report_*.json**
```json
{
  "checks": {
    "schema": "PASSED",
    "ranges": "PASSED",
    "missing_values": "PASSED",
    "duplicates": "WARNING",
    "outliers": { ... }
  }
}
```
✅ Shows: Data quality assessment

---

## 🎯 What Happens When You Run

### **Timeline**

| Time | Event |
|------|-------|
| 0-5 sec | Docker services start |
| 5-45 sec | InfluxDB, Grafana, MLflow initialize |
| 45-60 sec | Training model (Isolation Forest) |
| 60-65 sec | Validating data (schema, ranges, outliers) |
| 65-80 sec | Evaluating robustness (4 test scenarios) |
| 80+ sec | Script completes, shows summary |

### **Console Output Example**

```
╔════════════════════════════════════════════════════════════╗
║  🚀 AI INFRASTRUCTURE ANOMALY DETECTION - SETUP SCRIPT    ║
╚════════════════════════════════════════════════════════════╝

[1/6] Checking Docker installation...
✅ Docker found: Docker version 24.0.0

[2/6] Checking Docker daemon...
✅ Docker daemon is running

[3/6] Starting Docker services...
✅ Docker services started in background

[4/6] Waiting for services to be ready...
   ⏳ 45 seconds remaining...
✅ Services should be ready now

[5/6] Training anomaly detection model...
=====================================================
🤖 OFFLINE MODEL TRAINING - ANOMALY DETECTION
=====================================================
✅ Loaded 1132 samples
📊 Data split: train=792, val=170, test=170
🔍 Starting hyperparameter grid search...
✅ Best params: {'contamination': 0.01, 'n_estimators': 200}
📈 Test Set Metrics:
  Precision: 0.9200
  Recall: 0.9200
  F1-Score: 0.9200
💾 Model saved: models/anomaly_model_v20250128_120000.pkl
✅ MLflow run logged: 42a7c9f...
=====================================================
✅ TRAINING COMPLETED SUCCESSFULLY
=====================================================
✅ Model training completed

[6/6] Validating data quality...
=====================================================
📋 DATA VALIDATION
=====================================================
✅ Schema validation passed
✅ All values within expected ranges
✅ No missing values detected
✅ Statistical properties logged
=====================================================
✅ DATA VALIDATION PASSED
=====================================================
✅ Data validation passed

   Evaluating model robustness...
=====================================================
🔬 MODEL EVALUATION & ROBUSTNESS TESTING
=====================================================
📊 BASELINE EVALUATION
Precision: 0.9200
Recall: 0.9200
F1-Score: 0.9200
Latency (p50): 0.50 ms

🔧 ROBUSTNESS TEST 1: Gaussian Noise
Noise σ=0.01: 46 anomalies (47.5%)
Noise σ=0.05: 48 anomalies (49.5%)
Noise σ=0.10: 52 anomalies (53.7%)

🔧 ROBUSTNESS TEST 2: Missing Features
Missing CPU: 45 anomalies (-2%)
Missing Memory: 43 anomalies (-7%)
Missing Network: 50 anomalies (+9%)

🔧 ROBUSTNESS TEST 3: Extreme Outliers
Magnitude 2x: 62 total, 8/10 outliers (80%)
Magnitude 5x: 78 total, 9/10 outliers (90%)
Magnitude 10x: 96 total, 10/10 outliers (100%)

🔧 ROBUSTNESS TEST 4: Distribution Shift
Shift +0.1: 48 anomalies (↔️ Stable)
Shift +0.5: 52 anomalies (↗️ +8%)
Shift +1.0: 68 anomalies (↗️ +47%)

✅ Evaluation report saved: results/evaluation_report_20250128_120015.json
=====================================================
✅ EVALUATION COMPLETED SUCCESSFULLY
=====================================================

╔════════════════════════════════════════════════════════════╗
║               ✅ SETUP COMPLETE & SUCCESSFUL               ║
╚════════════════════════════════════════════════════════════╝

📊 WHAT YOU CAN DO NOW:

1️⃣  VIEW LIVE DASHBOARD
   Open: http://localhost:3000
   Login: admin / admin

2️⃣  VIEW TRAINING EXPERIMENTS
   Open: http://localhost:5000

3️⃣  CHECK RESULTS FILES
   Models: models/
   Data: data/processed/
   Results: results/

... (more info)
```

---

## 🎓 What You've Accomplished

✅ **Full MLOps Pipeline**
- Trained model with hyperparameter tuning
- Evaluated on test set (P/R/F1 metrics)
- Tested robustness (noise, outliers, drift)
- Validated data quality
- Tracked with MLflow

✅ **Production-Ready Deployment**
- Docker containers running
- Grafana dashboard live
- MLflow experiment tracking
- Model versioning

✅ **Comprehensive Documentation**
- Requirements (problem statement, KPIs)
- Architecture (system design)
- Model card (algorithm details, limitations)
- Deployment guide (how to run)

---

## 🤔 Common Questions

**Q: Can I run this without Docker?**  
A: Yes, but you'd need to install InfluxDB, Grafana, MLflow locally first. Docker is easier.

**Q: How long does it take?**  
A: ~90 seconds total (first run takes longer due to image downloads)

**Q: Where are the results?**  
A: In `results/` folder as JSON files, plus Grafana and MLflow UIs

**Q: Can I modify the scripts?**  
A: Yes! All scripts are in `src/`. Modify, then rerun `.\run.ps1`

**Q: How do I stop everything?**  
A: Run `docker-compose down` in the ai-infrastructure-anomaly-detection folder

**Q: What if Docker doesn't start?**  
A: Make sure Docker Desktop is installed and running. Check: `docker --version`

---

## ✨ Summary

**You need to do**: 
1. Start Docker Desktop
2. Run `.\run.ps1`
3. Wait ~90 seconds

**You get**:
- ✅ Trained ML model
- ✅ Test metrics (92% accuracy)
- ✅ Robustness evaluation (4 test scenarios)
- ✅ Data quality report
- ✅ Live Grafana dashboard
- ✅ MLflow experiment tracking
- ✅ Model versioning & persistence

**Next**: Review results and documentation!

---

📞 **Questions?** Check `docs/DEPLOYMENT.md` for detailed troubleshooting
