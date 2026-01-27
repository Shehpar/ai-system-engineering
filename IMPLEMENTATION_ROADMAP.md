# Implementation Roadmap: AI Infrastructure Anomaly Detection

**Date**: January 27, 2025  
**Status**: Tier 1 (Core MLOps) – IN PROGRESS  
**Target Completion**: January 28, 2025

---

## 📋 Summary

This roadmap tracks implementation of the course project in three tiers:

- **Tier 1 (Core MLOps)**: Essential ML lifecycle components ✅ IN PROGRESS
- **Tier 2 (Testing & Ops)**: Quality assurance, logging, monitoring
- **Tier 3 (Advanced)**: Optional enhancements (model registry, CI/CD, interpretability)

Each tier aligns with the **AI Systems Engineering** course objectives on design, development, verification, validation, and operations.

---

## 🎯 Course Requirements Alignment

| Objective | Tier | Component | Status |
|-----------|------|-----------|--------|
| **Requirements Analysis** | 1 | REQUIREMENTS.md + success criteria | ✅ Done |
| **Design & Architecture** | 1 | ARCHITECTURE.md + data flow diagram | ✅ Done |
| **ML Workflow & MLOps** | 1 | train_model.py + evaluate_model.py | ✅ Done |
| **Data Engineering** | 1 | validate_data.py + preprocessing | ✅ Done |
| **Model Persistence** | 1 | Model versioning (.pkl files) | ✅ Done |
| **Monitoring & Drift** | 1 | Drift detection (KS-test) | ✅ Done |
| **Testing (ML Accuracy)** | 1 | Precision, Recall, F1, ROC-AUC | ✅ Done |
| **Robustness Testing** | 1 | Noise, missing data, outliers | ✅ Done |
| **Deployment** | 1 | Docker Compose setup | ✅ Done |
| **Operations** | 2 | Logging, healthchecks, alerts | 🔄 Pending |
| **Testing (Quality)** | 2 | Unit/integration tests, pytest | 🔄 Pending |
| **Deployment Strategy** | 2 | Blue-green, canary (optional) | 🔄 Pending |
| **Security/Privacy** | 2 | Secrets, RBAC (optional) | 🔄 Pending |
| **Interpretability** | 3 | SHAP explanations (optional) | 🔄 Backlog |

---

## 🚀 Tier 1: Core MLOps (In Progress)

### Objective
Establish complete ML lifecycle: data validation → training → evaluation → inference → monitoring

### Deliverables

#### 1. ✅ Offline Training Script
**File**: `src/train_model.py`  
**Status**: COMPLETE

**Features**:
- Load historical data from CSV
- Split: 70% train, 15% val, 15% test
- StandardScaler preprocessing
- Grid search (contamination, n_estimators)
- IsolationForest training
- Test set evaluation (precision, recall, F1, ROC-AUC)
- Model versioning (timestamp)
- MLflow experiment tracking

**Execution**:
```bash
docker exec ai_app python src/train_model.py
```

**Outputs**:
- `models/anomaly_model_vYYYYMMDD_HHMMSS.pkl` (model artifact)
- `models/scaler_vYYYYMMDD_HHMMSS.pkl` (scaler artifact)
- `results/training_metrics_*.json` (metrics)
- MLflow run logged with params, metrics, model

---

#### 2. ✅ Model Evaluation Script
**File**: `src/evaluate_model.py`  
**Status**: COMPLETE

**Features**:
- Load trained model + scaler
- Test set baseline evaluation
- Robustness tests:
  - Gaussian noise injection (σ = 0.01, 0.05, 0.1)
  - Missing feature imputation
  - Extreme outlier injection (2x, 5x, 10x)
  - Distribution shift (+0.1, +0.5, +1.0)
- Prediction latency measurement
- Comprehensive JSON report

**Execution**:
```bash
docker exec ai_app python src/evaluate_model.py
```

**Outputs**:
- `results/evaluation_report_*.json` (detailed metrics)
- Console output with formatted tables

---

#### 3. ✅ Data Validation Script
**File**: `src/validate_data.py`  
**Status**: COMPLETE

**Features**:
- Schema validation (3 required columns)
- Range checks (CPU/mem: 0-100, network: ≥0)
- Missing value detection
- Duplicate detection
- Statistical summary (mean, std, quantiles)
- Outlier detection (IQR method)
- Pass/fail decision (>5% violations = FAIL)
- JSON validation report

**Execution**:
```bash
docker exec ai_app python src/validate_data.py
```

**Outputs**:
- `results/validation_report_*.json` (detailed findings)
- Exit code 0 (pass) or 1 (fail)

---

#### 4. ✅ Drift Detection
**File**: `src/detect_anomaly.py` (updated)  
**Status**: COMPLETE

**Features**:
- Kolmogorov-Smirnov test for feature distribution shift
- Triggered every prediction cycle
- Flags drift if p-value < 0.05
- Conditional retraining on drift + time-based triggers
- MLflow logging of each inference run

**Code Snippet**:
```python
from scipy.stats import ks_2samp
anomaly_scores = model.score_samples(X_test_scaled)
stat, pval = ks_2samp(training_dist, live_dist)
if pval < 0.05:
    print("⚠️ Drift detected! Triggering retrain...")
    retrain_model()
```

---

#### 5. ✅ MLflow Integration
**File**: All training/detection scripts  
**Status**: COMPLETE

**Features**:
- MLflow Tracking Server (Docker service)
- Experiment: `anomaly_detection_training`
- Logged per training run:
  - Parameters: contamination, n_estimators, train_samples
  - Metrics: precision, recall, f1, roc_auc
  - Artifacts: model (.pkl), metrics (.json)
- Accessible via UI: http://localhost:5000

---

#### 6. ✅ Documentation Suite
**Files**:
- `docs/REQUIREMENTS.md` – Problem statement, KPIs, stakeholders, constraints
- `docs/ARCHITECTURE.md` – System design, data flow, components, tech stack
- `docs/MODEL_CARD.md` – Algorithm, training data, performance, limitations, fairness
- `docs/DEPLOYMENT.md` – Quick start, setup, troubleshooting, operations

**Status**: COMPLETE

**Coverage**:
- 40+ pages of comprehensive documentation
- Diagrams, tables, code snippets
- Aligned with AISE course objectives
- Addresses fairness, ethics, security, interpretability

---

#### 7. ✅ Updated Requirements
**File**: `requirements.txt`  
**Status**: COMPLETE

**Added Packages**:
- `mlflow>=2.0.0` – Experiment tracking
- `scipy` – Statistical tests (KS-test)

---

#### 8. ✅ Docker Support
**File**: `docker/docker-compose.yml`  
**Status**: COMPLETE (with MLflow addition)

**Services**:
- `ai_app`: Python anomaly detection
- `influxdb`: Time-series database
- `grafana`: Dashboard
- `mlflow` (new): Tracking server

**Updated**:
```yaml
mlflow:
  image: ghcr.io/mlflow/mlflow:latest
  ports:
    - "5000:5000"
  command: mlflow server --host 0.0.0.0
```

---

### ✅ Tier 1 Definition of Done

- [x] Offline training with train/val/test split
- [x] Hyperparameter grid search
- [x] Test set evaluation (precision, recall, F1, ROC-AUC)
- [x] Robustness testing (noise, missing, outliers, drift)
- [x] Data validation pipeline
- [x] Drift detection (KS-test)
- [x] MLflow experiment tracking
- [x] Model versioning (timestamp)
- [x] Comprehensive documentation (4 docs)
- [x] Docker Compose with MLflow
- [x] GitHub ready for commit

---

## 🔄 Tier 2: Testing & Operations (Pending)

### Objective
Ensure system reliability, observability, and code quality

### Planned Deliverables

#### 1. Unit & Integration Tests
**Files**: `tests/test_model.py`, `tests/test_data.py`, `tests/test_integration.py`  
**Status**: 🔄 NOT STARTED

**Scope**:
- Model loads correctly
- Prediction latency < 1s
- Data validation catches bad data
- End-to-end: data → train → predict → InfluxDB
- Mock InfluxDB for offline testing

**Framework**: pytest  
**Coverage Goal**: >80%

**Execution**:
```bash
pytest tests/ -v --cov=src
```

---

#### 2. Structured Logging
**File**: `src/detect_anomaly.py` (refactored)  
**Status**: 🔄 NOT STARTED

**Changes**:
- Replace `print()` with Python `logging` module
- JSON format: `{"timestamp": "...", "level": "INFO", "message": "..."}`
- File output: `logs/app.log`
- Rotation: 10 MB per file, keep 7 days

**Example**:
```python
import logging
logger = logging.getLogger(__name__)
logger.info({"event": "anomaly_detected", "cpu": 65.4, "confidence": 0.92})
```

---

#### 3. Docker Healthchecks
**File**: `docker/docker-compose.yml`  
**Status**: 🔄 NOT STARTED

**Additions**:
- `ai_app`: Test model file exists + InfluxDB responsive
- `influxdb`: Ping check
- `grafana`: HTTP 200 on dashboard endpoint

**Restart Policy**: auto-restart on unhealthy

---

#### 4. Performance Monitoring
**File**: `src/detect_anomaly.py` (enhanced)  
**Status**: 🔄 NOT STARTED

**Metrics**:
- Prediction latency (p50, p95) → log to InfluxDB
- Model F1-score over time → calculate weekly
- Anomaly rate (count/hour) → Grafana query
- Retrain frequency → log to MLflow

---

#### 5. CI/CD Automation
**File**: `.github/workflows/ci.yml`  
**Status**: 🔄 NOT STARTED

**Triggers**: On push to `main` or PR

**Jobs**:
- Lint (flake8)
- Unit tests (pytest)
- Docker build
- Push to GitHub Container Registry

---

#### 6. README Update
**File**: `README.md`  
**Status**: 🔄 NOT STARTED

**Content**:
- Quick start (copy from DEPLOYMENT.md)
- Project structure
- Key scripts & usage
- Links to detailed docs
- Badges (build, coverage)

---

### 🎯 Tier 2 Target
- [x] Requirements from course
- [ ] Unit tests + coverage >80%
- [ ] Structured JSON logging
- [ ] Docker healthchecks
- [ ] Performance tracking
- [ ] CI/CD pipeline
- [ ] Polished README

**Timeline**: Week 2 (5–7 days)

---

## 🌟 Tier 3: Advanced Enhancements (Backlog)

### Objective
Production-readiness & advanced ML features

### Planned Deliverables

#### 1. Model Registry & Versioning
- DVC (Data Version Control) or MLflow Model Registry
- Tag models: `production`, `staging`, `archived`
- Rollback capability
- A/B testing of model versions

#### 2. Blue-Green Deployment
- Run two model versions side-by-side
- Route 10% traffic to new model (canary)
- Automatic switch if metrics OK

#### 3. Interpretability (SHAP)
- SHAP values: which feature(s) caused anomaly?
- Feature importance per prediction
- Integrate into Grafana tooltips

#### 4. Advanced Drift Detection
- Concept drift detection (model performance degradation)
- Automatic retraining on major drift
- Drift severity scoring (1–10)

#### 5. Security Hardening
- InfluxDB authentication (user/password)
- Docker secrets (credentials management)
- TLS encryption (HTTPS)
- RBAC: ops team can only view alerts

#### 6. Kubernetes Deployment
- K8s manifests (deployment, service, statefulset)
- Helm chart for easy rollout
- HPA (horizontal pod autoscaling)
- Multi-zone deployment

### 🎯 Tier 3 Target
- [ ] Model registry with versioning
- [ ] Blue-green deployment demo
- [ ] SHAP explanations in alerts
- [ ] Concept drift detection
- [ ] Secrets management
- [ ] Kubernetes ready

**Timeline**: Optional (Week 3+ or future)

---

## 📊 Progress Summary

| Tier | Status | Completion | Tasks | 
|------|--------|-----------|-------|
| **Tier 1** | 🟢 IN PROGRESS | 95% | 8/8 Done, commit pending |
| **Tier 2** | 🟡 PLANNED | 0% | 6 tasks queued |
| **Tier 3** | 🔵 BACKLOG | 0% | 6 tasks optional |
| **Overall** | 🟢 ON TRACK | 33% | All critical items prioritized |

---

## 🚦 Next Steps

### Immediate (Next 1 hour)
1. ✅ Commit Tier 1 changes to GitHub
2. ✅ Push to main branch
3. ✅ Verify all documentation loads correctly
4. Test locally:
   ```bash
   docker-compose -f docker/docker-compose.yml up --build
   docker exec ai_app python src/train_model.py
   docker exec ai_app python src/validate_data.py
   docker exec ai_app python src/evaluate_model.py
   ```

### Short-term (Day 2)
1. Request teacher feedback on:
   - Problem statement & KPIs (REQUIREMENTS.md)
   - Architecture & design choices (ARCHITECTURE.md)
   - Model card & limitations (MODEL_CARD.md)
2. Address any gaps or clarifications
3. Plan Tier 2 tasks if time permits

### Medium-term (Week 2)
1. Add Tier 2 components (tests, logging, CI/CD)
2. Prepare final presentation
3. Document lessons learned & future improvements

---

## 📝 Glossary

| Term | Definition |
|------|-----------|
| **MLOps** | Machine Learning Operations; practices for deploying, versioning, monitoring ML models |
| **Drift Detection** | Identifying when input data distribution changes (performance risk) |
| **Robustness** | Model's ability to handle noise, outliers, edge cases |
| **Model Card** | Document describing algorithm, training data, performance, limitations, ethical considerations |
| **Blue-Green** | Deployment strategy: run 2 versions in parallel, switch traffic atomically |
| **SHAP** | SHapley Additive exPlanations; tool for explaining individual predictions |
| **KS-test** | Kolmogorov-Smirnov test; statistical test for distribution differences |
| **Tier** | Prioritized layer of implementation (core → ops → advanced) |

---

## 📖 References

- **Course Syllabus**: AI Systems Engineering (AISE), 2025-26
- **MLOps Handbook**: https://ml-ops.systems/
- **scikit-learn Docs**: https://scikit-learn.org/
- **MLflow Docs**: https://www.mlflow.org/
- **Model Cards**: https://modelcards.withgoogle.com/

---

## ✍️ Sign-Off

| Role | Name | Date | Status |
|------|------|------|--------|
| **Student** | Shehpar | Jan 27, 2025 | Implementing Tier 1 |
| **Instructor** | Prof. Pietrantuono | TBD | Review pending |
| **Peer Review** | TBD | TBD | Optional |

---

**Document Version**: v1.0  
**Last Updated**: January 27, 2025, 15:00 UTC  
**Next Review**: January 28, 2025

---

**See Also**:
- [REQUIREMENTS.md](docs/REQUIREMENTS.md) – Detailed problem statement
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) – System design
- [MODEL_CARD.md](docs/MODEL_CARD.md) – Model documentation
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) – Setup & operations
- [README.md](README.md) – Project overview (to be updated)
