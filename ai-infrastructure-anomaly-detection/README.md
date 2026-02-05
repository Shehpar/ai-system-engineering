# AI Infrastructure Anomaly Detection System

**Status**: ✅ Production Ready

---

## 🎯 Overview

A production-grade AI system for **real-time infrastructure anomaly detection** using Isolation Forest machine learning. Detects anomalies in system metrics (CPU, Memory, Network) with sub-10ms latency.

### Key Capabilities

- **ML Pipeline**: Offline training with grid search optimization, real-time inference
- **Explainability**: SHAP values for per-feature anomaly contributions
- **Monitoring**: Grafana dashboards + InfluxDB time-series database
- **Experiment Tracking**: MLflow for reproducibility and model management
- **Data Ingestion**: Multiple sources (Flask simulation, Telegraf real metrics)
- **Stress Testing**: HTTP load generation for system validation
- **Containerization**: Docker Compose orchestration for all services
- **Testing**: Unit tests with pytest, CI/CD via GitHub Actions

---

## 🏗️ System Architecture

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│  Grafana Dashboard (Port 3000)                                  │
│  ├─ Real-time anomaly visualization                            │
│  ├─ System metrics charts                                       │
│  └─ SHAP feature contribution panels                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────────┐
│                  EXPERIMENT & ANALYTICS LAYER                  │
├─────────────────────────────────────────────────────────────────┤
│  MLflow UI (Port 5000)                                          │
│  ├─ Experiment tracking                                         │
│  ├─ Model artifacts storage                                     │
│  └─ Run history & parameters                                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────────┐
│                   INFERENCE & ML LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  Python ML Pipeline                                             │
│  ├─ detect_anomaly.py → Real-time predictions + SHAP values   │
│  ├─ train_model.py → Offline model training (grid search)      │
│  ├─ validate_data.py → Data quality checks (6 validations)     │
│  └─ evaluate_model.py → Robustness testing (4 scenarios)       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────────┐
│                 DATA STORAGE & TIME-SERIES LAYER                │
├─────────────────────────────────────────────────────────────────┤
│  InfluxDB (Port 8086)                                           │
│  ├─ Measurement: system_metrics (CPU, Memory, Network)          │
│  ├─ Measurement: ai_predictions (anomaly scores, SHAP values)   │
│  └─ Retention: Time-series data for trend analysis              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────────┐
│                 DATA COLLECTION & INGESTION LAYER               │
├─────────────────────────────────────────────────────────────────┤
│  Source 1: Flask App (Simulated Metrics)                        │
│  ├─ generate_metrics() → CPU, Memory, Network                   │
│  └─ HTTP stress testing endpoint                                │
│                                                                 │
│  Source 2: Telegraf (Real Metrics - via datacenter/)            │
│  ├─ System resource collection                                  │
│  └─ Pushes to InfluxDB                                          │
│                                                                 │
│  Source 3: Real Data Collector                                  │
│  └─ collect_real_data.py → Extracts 24h historical data        │
└─────────────────────────────────────────────────────────────────┘
```

### Component Interactions

```
Setup Phase:
1. Docker Compose starts: ai_app → influxdb, grafana, mlflow
2. ai_app container:
   - Installs Python deps from requirements.txt
   - Prepares /app directory
   - Awaits container health checks

Training Phase:
3. train_model.py:
   - Loads data/processed/system_metrics_processed.csv
   - Grid search: contamination ∈ {0.01, 0.05, 0.1}
   - Selects best Isolation Forest model
   - Saves to models/anomaly_model_*.pkl
   - Logs metrics to MLflow

Inference Phase:
4. detect_anomaly.py (runs continuously):
   - Reads latest metrics from InfluxDB
   - Predicts anomalies using trained model
   - Computes SHAP values per prediction
   - Writes predictions + SHAP to InfluxDB (ai_predictions)
   - Grafana consumes and visualizes in real-time

Validation Phase:
5. validate_data.py:
   - Schema checks (required columns)
   - Range validations (0-100 for CPU/mem, ≥0 for network)
   - Missing data, duplicates, outliers
   - IQR-based anomaly detection

Evaluation Phase:
6. evaluate_model.py:
   - Robustness scenarios: noise, missing data, outliers, shifts
   - Produces results/evaluation_report_*.json
```

### Technology Stack

| Layer | Technology | Version | Port | Purpose |
|-------|-----------|---------|------|---------|
| **Runtime** | Python | 3.11, 3.12 | — | ML model execution |
| **Container** | Docker | 29.1.3+ | — | Service isolation |
| **Orchestration** | Docker Compose | 2.0+ | — | Multi-service coordination |
| **Database** | InfluxDB | 1.8.10 | 8086 | Time-series metrics storage |
| **Visualization** | Grafana | latest | 3000 | Dashboard & alerting |
| **ML Experiment** | MLflow | 2.0+ | 5000 | Tracking & model registry |
| **ML Framework** | scikit-learn | 1.8.0 | — | Isolation Forest algorithm |
| **Explainability** | SHAP | 0.42.0+ | — | Feature contribution analysis |

---

## 📋 Installation

### Docker Deployment (Recommended)

```bash
# Clone and enter directory
git clone https://github.com/Shehpar/ai-system-engineering.git
cd ai-infrastructure-anomaly-detection

# Start all services
docker-compose -f docker/docker-compose.yml up -d

# Verify healthy status
docker-compose -f docker/docker-compose.yml ps

# View logs
docker-compose -f docker/docker-compose.yml logs -f ai_app

# Stop services
docker-compose -f docker/docker-compose.yml down
```

### Local Python Setup

```bash
# Requires Python 3.11+ (CI runs on 3.11 and 3.12)
# Install dependencies
pip install -r requirements.txt

# Train model
python src/train_model.py

# Validate data
python src/validate_data.py

# Evaluate robustness
python src/evaluate_model.py

# Run tests
pytest tests/ -v
```

---

## 🧪 Testing

### Run Unit Tests
```bash
# Via Docker
docker-compose -f docker/docker-compose.yml exec -T ai_app pytest tests/ -v

# Locally
pytest tests/ -v
```

**Test Results**:
- test_split_data_shapes: ✅ PASSED
- test_validate_schema_pass: ✅ PASSED
- test_validate_schema_fail: ✅ PASSED
- test_validate_ranges_fail_when_outside_bounds: ✅ PASSED
- test_validate_live_data: ✅ PASSED

**Total**: 5/5 tests passing (100%)

---

## 📊 Model Performance (Jan 28, 2026)

### Baseline Metrics
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Precision** | 100.0% | ≥90% | ✅ EXCEEDS |
| **Recall** | 72.73% | ≥90% | ⚠️ ACCEPTABLE |
| **F1-Score** | 84.21% | ≥85% | ⚠️ NEAR |
| **ROC-AUC** | 100.0% | ≥95% | ✅ EXCEEDS |
| **Latency** | 6.94ms | <5s | ✅ EXCEEDS |

### Robustness Results
- ✅ **Noise**: Stable under σ=0.01-0.1 Gaussian noise
- ✅ **Missing Data**: Handles feature imputation gracefully
- ✅ **Outliers**: 100% detection rate for 10x magnitude anomalies
- ✅ **SHAP**: Explains per-feature contributions to anomalies

See [docs/MODEL_CARD.md](docs/MODEL_CARD.md) for detailed results.

---

## 📁 Project Structure & Directory Architecture

### Core Directory Layout

```
ai-infrastructure-anomaly-detection/                         ← Root project folder
│
├── 🐍 src/                                                   ← ML Pipeline (Python scripts)
│   ├── train_model.py                                        # Offline model training
│   │   ├─ Loads: data/processed/system_metrics_processed.csv
│   │   ├─ Algorithm: Isolation Forest with grid search
│   │   ├─ Grid: contamination ∈ {0.01, 0.05, 0.1}
│   │   ├─ Output: models/anomaly_model_*.pkl
│   │   └─ Tracking: Logs to MLflow (metrics, params, artifacts)
│   │
│   ├── validate_data.py                                      # Data Quality Checks
│   │   ├─ Validates: Required columns, types, ranges
│   │   ├─ Anomaly Detection: IQR-based outlier detection
│   │   ├─ Missing Data: Identifies gaps & duplicates
│   │   └─ Output: Validation reports + cleaned data
│   │
│   ├── evaluate_model.py                                     # Robustness Testing
│   │   ├─ Scenario 1: Gaussian noise injection (σ=0.01-0.1)
│   │   ├─ Scenario 2: Missing value imputation
│   │   ├─ Scenario 3: Extreme outlier detection (10x magnitude)
│   │   ├─ Scenario 4: Data shift simulation
│   │   └─ Output: results/evaluation_report_*.json
│   │
│   ├── detect_anomaly.py                                     # Real-time Inference [SHAP]
│   │   ├─ Loads: Trained model from models/
│   │   ├─ Input: Real-time metrics from InfluxDB (system_metrics)
│   │   ├─ Process: Prediction + SHAP explainability analysis
│   │   ├─ Output: Writes to InfluxDB (ai_predictions measurement)
│   │   │   ├─ Fields: anomaly_score, is_anomaly, latency_ms
│   │   │   └─ SHAP fields: shap_cpu, shap_memory, shap_network
│   │   └─ Feature: Per-feature contribution explanation
│   │
│   ├── preprocessing.py                                      # Data Transformations
│   │   ├─ Standardization: Mean=0, Std=1
│   │   ├─ Handling: Missing values, outliers
│   │   └─ Pipeline: Preparation for training/inference
│   │
│   ├── data_generation.py                                    # Synthetic Data Creation
│   │   ├─ Generates: Normal distribution metrics
│   │   ├─ Injects: Anomalies (spikes, trends)
│   │   └─ Output: CSV files for testing
│   │
│   └── collect_real_data.py                                  # Real Data Extraction
│       ├─ Pulls: 24-hour historical data from InfluxDB
│       ├─ Aggregation: Time-bucket averaging
│       └─ Output: data/raw/system_metrics.csv
│
├── 🧪 tests/                                                 ← Unit Tests (pytest)
│   ├── conftest.py                                           # pytest configuration & fixtures
│   ├── test_train_model.py                                   # Training pipeline tests
│   │   ├─ Model creation & hyperparameter sensitivity
│   │   ├─ Grid search correctness
│   │   └─ Artifact generation validation
│   │
│   └── test_validate_data.py                                 # Data validation tests
│       ├─ Schema & type validation
│       ├─ Range constraints
│       └─ Anomaly detection accuracy
│
├── 🐳 docker/                                                ← Containerization
│   ├── Dockerfile                                            # Python 3.11-slim base
│   │   ├─ Base: python:3.11-slim (minimal, ~170MB)
│   │   ├─ Dependencies: Installs from requirements.txt
│   │   ├─ Entrypoint: Runs Python scripts via docker-compose
│   │   └─ Health Check: Container health status monitoring
│   │
│   └── docker-compose.yml                                    # Service Orchestration (4 services)
│       ├─ Service 1: ai_app (Custom Python container)
│       │   ├─ Container: anomaly-detection-app
│       │   ├─ Volumes: Maps src/, data/, models/, results/
│       │   ├─ Env: Python ML pipeline environment
│       │   └─ Dependencies: Depends on influxdb health
│       │
│       ├─ Service 2: influxdb:1.8.10
│       │   ├─ Database: system_metrics (raw) + ai_predictions (inferences)
│       │   ├─ Port: 8086 (HTTP API)
│       │   ├─ Volumes: influxdb-storage (persists data)
│       │   └─ Health Check: Queries /_health endpoint
│       │
│       ├─ Service 3: grafana:latest
│       │   ├─ UI: http://localhost:3000 (admin/admin)
│       │   ├─ Provisioning: Auto-configures InfluxDB datasource
│       │   ├─ Dashboards: Auto-loads from grafana/dashboards/
│       │   └─ Features: Anomaly viz, SHAP panels, alerting
│       │
│       └─ Service 4: mlflow (Optional, for experiment tracking)
│           ├─ UI: http://localhost:5000
│           ├─ Backend: SQLite (mlflow/mlflow.db)
│           └─ Storage: Artifacts in mlflow/artifacts/
│
├── 📊 grafana/                                               ← Dashboard Configuration
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── influxdb.yml                                  # Auto-provisioned InfluxDB connector
│   │   │       ├─ Host: influxdb:8086
│   │   │       ├─ Database: anomaly_detection
│   │   │       └─ Is default: true
│   │   │
│   │   └── dashboards/
│   │       ├── dashboard.yml                                 # Dashboard provider config
│   │       └── AI Anomaly Detection - Advanced...json        # Pre-built dashboard JSON
│   │           ├─ Panels: Metrics time series, anomaly heatmap
│   │           ├─ SHAP: Feature contribution bar charts
│   │           ├─ Stats: Real-time KPIs & alerts
│   │           └─ Refresh: 10s update interval
│   │
│   └── [Images auto-generated at runtime]
│
├── 🧬 mlflow/                                                ← Experiment Tracking Storage
│   ├── mlflow.db                                             # SQLite database (created at runtime)
│   │   ├─ Stores: Experiment metadata, run info, parameters
│   │   ├─ Models: Registered model versions
│   │   └─ Metrics: Training & validation metrics timeseries
│   │
│   └── artifacts/                                            # Model artifact storage
│       └── [Experiment folders created per run]
│           ├─ Models: Trained .pkl files
│           ├─ Metrics: JSON performance reports
│           └─ Params: Hyperparameter logs
│
├── 📂 data/                                                  ← Data Storage (CSV files)
│   ├── raw/
│   │   └── system_metrics.csv                                # Original unprocessed metrics
│   │       ├─ Columns: timestamp, cpu, memory, network
│   │       ├─ Source: collect_real_data.py or data_generation.py
│   │       └─ Format: Time-indexed CSV (rows = 24h samples)
│   │
│   └── processed/
│       └── system_metrics_processed.csv                      # Cleaned & standardized data
│           ├─ Standardization: (x - mean) / std applied
│           ├─ Missing values: Imputed or removed
│           ├─ Duplicates: Removed
│           └─ Train/test split: 80/20 by default
│
├── 🤖 models/                                                ← Trained Model Storage
│   ├── anomaly_model_*.pkl                                   # Serialized Isolation Forest
│   │   ├─ Input: Features = [cpu, memory, network]
│   │   ├─ Output: anomaly_score ∈ [0, 1], is_anomaly ∈ {0, 1}
│   │   ├─ Loaded by: detect_anomaly.py (inference)
│   │   └─ Versioning: Timestamped filenames
│   │
│   └── [Optional: Additional model variants]
│
├── 📈 results/                                               ← Outputs & Reports
│   ├── training_metrics_*.json                               # Per-run training metrics
│   │   ├─ Metrics: precision, recall, f1, roc_auc, latency
│   │   ├─ Params: contamination, n_estimators, random_state
│   │   └─ Timestamp: Run ID in filename
│   │
│   ├── mlflow_metrics.json                                   # Consolidated MLflow metrics
│   │   ├─ Best model: Top hyperparameter configuration
│   │   ├─ Performance: Aggregated scores across grid search
│   │   └─ Reproducibility: Git commit hash, Python version
│   │
│   ├── evaluation_report_*.json                              # Robustness test results
│   │   ├─ Scenarios: Noise, missing data, outliers, shifts
│   │   ├─ Results: Per-scenario accuracy & latency
│   │   └─ Recommendations: Model stability insights
│   │
│   └── detected_anomalies_for_testing.csv                    # Sample inference output
│       ├─ Columns: timestamp, anomaly_score, is_anomaly, SHAP_*
│       └─ Example: Real predictions with feature contributions
│
├── 📜 requirements.txt                                        ← Python Dependencies
│   ├─ Core ML: scikit-learn==1.8.0 (requires Python 3.11+)
│   ├─ Explainability: SHAP>=0.42.0
│   ├─ Databases: influxdb>=1.18.0, influxdb-client>=1.19.0
│   ├─ Monitoring: MLflow>=2.0.0
│   ├─ Data: pandas>=2.0.0, numpy>=1.23.0
│   ├─ Testing: pytest>=7.0.0, pytest-cov>=4.0.0
│   └─ Others: python-dotenv, requests (for API calls)
│
├── 🔧 setup_and_run.ps1                                      ← Automated Setup Script
│   ├─ Checks: Docker installation & version
│   ├─ Builds: Services if needed
│   ├─ Starts: docker-compose up -d
│   ├─ Waits: Service health checks (30s timeout per service)
│   ├─ Initializes: Database, credentials, seeds data
│   └─ Launches: Browser tabs for Grafana, MLflow
│
├── 🧪 test_and_validate.ps1                                  ← Testing Orchestration
│   ├─ Runs: pytest with coverage
│   ├─ Stress tests: HTTP load generation (configurable RPS)
│   ├─ Anomaly injection: Triggers synthetic anomalies
│   ├─ Reports: Coverage, latency, detection accuracy
│   └─ Output: Saves to results/ folder
│
├── ▶️  run.ps1                                                ← Quick Start Script
│   └─ Executes: docker-compose up -d (simplified)
│
├── 📖 README.md                                              ← This file
├── 🐳 docker command.txt                                     ← Manual docker-compose commands
│   ├─ Alternative: If scripts fail, run commands directly
│   └─ Format: Copy-paste ready commands
│
├── ✅ check_datasource.py                                    ← InfluxDB Connectivity Check
│   ├─ Verifies: InfluxDB connection & database
│   ├─ Lists: Available measurements
│   └─ Debug: Helps troubleshoot connection issues
│
└── 🔐 enable_datasource.py                                   ← Grafana Datasource Setup
    ├─ Creates: InfluxDB datasource in Grafana
    ├─ Auth: API calls to Grafana admin endpoint
    └─ Idempotent: Safe to run multiple times
```

### Related Project Folders (Ecosystem)

These folders exist at the project root level and work with the core system:

#### 📦 `../datacenter/` (Data Generation & Collection)
```
datacenter/
├── flask_app/                       ← Metrics simulation server
│   ├── app.py                       # Flask HTTP server (Port 5005)
│   │   ├─ Endpoint 1: /metrics → Returns simulated system metrics
│   │   ├─ Endpoint 2: /stress → Accepts stress test requests
│   │   └─ Metrics: CPU%, Memory%, Network I/O
│   │
│   ├── stress_test.py               # Stress testing helper
│   ├── telegraf_flask.conf          # Telegraf input plugin for Flask
│   ├── Dockerfile                   # Flask container definition
│   └── entrypoint.sh                # Startup script
│
├── docker-compose.yml               ← Datacenter service orchestration
│   ├─ Service: Flask app (Port 5005)
│   └─ Service: Telegraf collector (pushes to InfluxDB)
│
├── telegraf.conf                    ← Telegraf system metrics collector
│   ├─ CPU, Memory, Disk, Network collection
│   └─ Output: Pushes to InfluxDB (http://localhost:8086)
│
└── requirements.txt                 ← Flask dependencies

Purpose: Generates simulated & real infrastructure metrics
Data Flow: Flask/Telegraf → InfluxDB (system_metrics) → AI Pipeline
```

#### ⚡ `../stress-test-docker/` (Load Testing)
```
stress-test-docker/
├── http_load_generator.py           ← HTTP request generator
│   ├─ Threads: Configurable concurrent requests
│   ├─ RPS: Adjustable requests-per-second
│   ├─ Targets: Flask /metrics endpoint
│   └─ Metrics: Latency, throughput, success rate
│
├── stress.py                        ← Orchestration script
│   ├─ Runs: Load generation with specified duration
│   ├─ Reports: Latency percentiles (p50, p95, p99)
│   └─ Output: Stress test results JSON
│
├── docker-compose.yml               ← Stress test environment
│   ├─ Service: HTTP load generator container
│   └─ Network: Links to Flask app
│
├── Dockerfile                       ← Load generator container
├── entrypoint.sh                    ← Container startup
└── requirements.txt                 ← Dependencies (requests, locust)

Purpose: Generates artificial system load for testing
Data Flow: Stress → Flask → InfluxDB → AI Pipeline detects anomalies
```

### Architecture Data Flow Summary

```
┌─────────────────────────────────────────────────────────────────┐
│ Data Collection Phase                                           │
├─────────────────────────────────────────────────────────────────┤
│ Telegraf/Flask → InfluxDB (system_metrics measurement)         │
│                 └─ Stores: cpu, memory, network metrics         │
│                    Retention: Real-time + historical            │
└──────────────────┬──────────────────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────────────────┐
│ Model Training Phase                                            │
├─────────────────────────────────────────────────────────────────┤
│ train_model.py:                                                 │
│   data/processed/system_metrics_processed.csv                  │
│     → Isolation Forest (grid search)                            │
│     → models/anomaly_model_*.pkl                                │
│     → MLflow (experiment tracking)                              │
└──────────────────┬──────────────────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────────────────┐
│ Data Validation Phase (Continuous)                              │
├─────────────────────────────────────────────────────────────────┤
│ validate_data.py:                                               │
│   InfluxDB system_metrics → 6 validation checks → Pass/Fail     │
└──────────────────┬──────────────────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────────────────┐
│ Real-Time Inference Phase                                       │
├─────────────────────────────────────────────────────────────────┤
│ detect_anomaly.py (runs continuously):                          │
│   1. Read latest metrics from InfluxDB (system_metrics)        │
│   2. Load models/anomaly_model_*.pkl                           │
│   3. Predict: anomaly_score + is_anomaly                       │
│   4. Explain: SHAP feature contributions                       │
│   5. Write: InfluxDB ai_predictions measurement                │
└──────────────────┬──────────────────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────────────────┐
│ Visualization & Monitoring Phase                                │
├─────────────────────────────────────────────────────────────────┤
│ Grafana Dashboard (localhost:3000):                             │
│   - Real-time anomaly heatmap & alerts                         │
│   - SHAP feature contribution panels                           │
│   - System metrics time series                                 │
│                                                                 │
│ MLflow UI (localhost:5000):                                     │
│   - Experiment history & metrics                               │
│   - Model artifacts & parameters                               │
│   - Run comparison & best model tracking                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Service Dependencies

```
docker-compose.yml orchestration:
┌──────────────────────────────────────────┐
│         ai_app (Python 3.11)             │  ← Main ML service
│  depends_on: influxdb (healthy)          │
└──────────────────────────────────────────┘
            ↓ reads/writes
┌──────────────────────────────────────────┐
│      influxdb:1.8.10 (Port 8086)         │  ← Time-series storage
│  health_check: /_health endpoint         │
└──────────────────────────────────────────┘
            ↓ reads data
┌──────────────────────────────────────────┐
│        grafana:latest (Port 3000)        │  ← Visualization
│  auto_provisioned: InfluxDB datasource   │
└──────────────────────────────────────────┘

Optional:
┌──────────────────────────────────────────┐
│       mlflow (Port 5000)                 │  ← Experiment tracking
│  backend: mlflow/mlflow.db (SQLite)      │
└──────────────────────────────────────────┘
```
├── models/                          # Trained models with versioning
│   └── anomaly_model_v20260128_145609.pkl
├── results/                         # Training/evaluation reports
│   ├── training_metrics_*.json
│   ├── validation_report_*.json
│   └── evaluation_report_*.json
├── docs/                            # Comprehensive documentation
│   ├── REQUIREMENTS.md              # Problem statement & KPIs
│   ├── ARCHITECTURE.md              # System design & data flow
│   ├── MODEL_CARD.md                # Algorithm & robustness
│   └── DEPLOYMENT.md                # Operations guide
├── .github/workflows/tests.yml      # CI/CD pipeline
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

### Related Folders in the Workspace

- [../datacenter](../datacenter) — Flask-based metric generator + Telegraf config used for realistic data ingestion.
    - docker-compose.yml, telegraf.conf
    - flask_app/ (app.py, stress_test.py, Dockerfile, entrypoint.sh)
    - flask_logs/ (runtime logs)
- [../stress-test-docker](../stress-test-docker) — Standalone HTTP load generator for stress testing.
    - docker-compose.yml, Dockerfile, entrypoint.sh
    - http_load_generator.py, stress.py, requirements.txt

---

## 🔧 Configuration

### Environment Variables

```bash
# Log level (INFO, DEBUG, WARNING, ERROR)
export LOG_LEVEL=INFO

# MLflow tracking URI
export MLFLOW_TRACKING_URI=http://mlflow:5000

# InfluxDB connection
export INFLUXDB_HOST=influxdb
export INFLUXDB_PORT=8086
export INFLUXDB_DATABASE=system_metrics
```

### Docker Customization

Edit `docker/docker-compose.yml` to adjust:
- Port numbers (3000, 5000, 8086)
- Resource limits (CPU, RAM)
- Healthcheck intervals
- Environment variables

---

## 📊 Dashboard Access

### Grafana (http://localhost:3000)
- **Login**: admin / admin
- **Dashboard**: "AI Anomaly Detection" (auto-loads)
- **Features**: Real-time anomalies, trends, alerts, custom panels

### MLflow (http://localhost:5000)
- **Experiments**: anomaly_detection_training
- **Metrics**: Precision, Recall, F1, ROC-AUC
- **Artifacts**: Models, scalers, reports
- **Comparison**: A/B test runs

---

## 🔍 Monitoring & Logging

### View Logs

```bash
# All services with timestamps
docker-compose -f docker/docker-compose.yml logs -f --timestamps

# Specific service
docker-compose -f docker/docker-compose.yml logs -f ai_app

# Real-time with filtering
docker-compose -f docker/docker-compose.yml logs -f ai_app | grep "ERROR"
```

### Structured Logging

All scripts use Python `logging` module:

```bash
# View with different verbosity
export LOG_LEVEL=DEBUG  # Verbose
export LOG_LEVEL=INFO   # Normal
export LOG_LEVEL=ERROR  # Production
```

### Health Checks

```bash
# View service health status
docker-compose -f docker/docker-compose.yml ps

# Detailed health info
docker inspect docker-ai_app-1 | grep -A 5 Health
```

---

## 🚀 Common Tasks

### Automated Workflows

```powershell
# Complete setup from scratch
.\setup_and_run.ps1 -CleanInstall

# Run validation tests
.\test_and_validate.ps1

# Custom stress test (5 min, 500 RPS)
.\test_and_validate.ps1 -Duration 300 -RequestsPerSecond 500
```

### Manual Operations

```bash
# Train a new model
docker-compose -f docker/docker-compose.yml exec -T ai_app python src/train_model.py

# Collect real data from InfluxDB
docker-compose -f docker/docker-compose.yml exec -T ai_app python src/collect_real_data.py

# Validate data quality
docker-compose -f docker/docker-compose.yml exec -T ai_app python src/validate_data.py

# Test model robustness
docker-compose -f docker/docker-compose.yml exec -T ai_app python src/evaluate_model.py

# Run unit tests
docker-compose -f docker/docker-compose.yml exec -T ai_app pytest tests/ -v
```

---

## 📚 Documentation

Full documentation in `/docs`:

| Document | Content |
|----------|---------|
| [AUTOMATION_GUIDE.md](docs/AUTOMATION_GUIDE.md) | Automated setup & testing scripts (NEW) |
- [TIER_1_SUMMARY.md](../TIER_1_SUMMARY.md) - MLOps core (8 components)
- [TIER_2_SUMMARY.md](../TIER_2_SUMMARY.md) - QA & operations (6 components)
- [IMPLEMENTATION_ROADMAP.md](../IMPLEMENTATION_ROADMAP.md) - Course alignment

---

## 🔄 MLOps Pipeline

### Training Workflow
1. Load historical metrics (CSV)
2. Validate data quality (6 checks)
3. Split 70/15/15 (train/val/test)
4. Grid search hyperparameters
5. Train Isolation Forest
6. Evaluate metrics
7. Version model with timestamp
8. Log to MLflow

### Inference Workflow
1. Query live metrics from InfluxDB
2. Apply fitted scaler
3. Get predictions + anomaly scores
4. Write results to InfluxDB
5. View SHAP feature contributions
6. Trigger retraining if needed

---

## 🐛 Troubleshooting

### Services Not Starting
```bash
# Check Docker daemon
docker --version

# View detailed logs
docker-compose -f docker/docker-compose.yml logs

# Rebuild fresh
docker-compose -f docker/docker-compose.yml down -v
docker-compose -f docker/docker-compose.yml up -d --build
```

### Grafana Dashboard Not Loading
```bash
# Wait 30 seconds for startup
# Refresh browser
# Check provisioning:
docker exec docker-grafana-1 ls /etc/grafana/provisioning/dashboards/
```

### Tests Failing
```bash
# Verbose output
docker-compose -f docker/docker-compose.yml exec -T ai_app pytest tests/ -vv

# Verify data exists
docker-compose -f docker/docker-compose.yml exec -T ai_app ls -la data/processed/
```

---

## 🎓 Course Information

**Course**: AI Systems Engineering  
**Semester**: Fall 2025  
**Project Type**: Innovation-driven (INN)  

**Requirements Coverage**:
- ✅ Part I: Design (REQUIREMENTS.md, ARCHITECTURE.md)
- ✅ Part II: Development (train_model.py, validate_data.py)
- ✅ Part III: Verification (evaluate_model.py, tests/)
- ✅ Part IV: Operations (docker-compose.yml, grafana/, mlflow/)

---

## 📊 Project Statistics

- **Python Code**: 1000+ lines
- **Tests**: 5 unit tests (100% passing)
- **Documentation**: 65+ pages
- **Docker Services**: 4 (with health checks)
- **CI/CD**: GitHub Actions workflow
- **Git Commits**: 15+ with detailed history

---

## 🔐 Security & License

- **License**: MIT
- **Security**: Dependency scanning via GitHub Actions
- **Code Quality**: Linting and vulnerability checks

---

## 🎯 Implemented Tier 3 Features

**Explainability & Monitoring** (Fully Implemented):
- ✅ **SHAP Values Integration**: Per-feature anomaly contribution analysis (detect_anomaly.py)
- ✅ **Grafana Dashboards**: Real-time visualization + SHAP panels
- ✅ **Secrets Management**: Environment variables for secure credential handling
- ✅ **Complete Monitoring Stack**: InfluxDB + Grafana + MLflow

**Not Implemented** (Out of Scope):
- ❌ MLflow Model Registry (versioning)
- ❌ Blue-green deployment strategy
- ❌ Kubernetes deployment manifests
- ❌ Advanced drift detection (5 statistical tests)

---

**Repository**: https://github.com/Shehpar/ai-system-engineering  
**Last Updated**: January 28, 2026  
**Status**: ✅ Production Ready
