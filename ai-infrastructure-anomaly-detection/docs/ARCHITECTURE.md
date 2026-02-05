# System Architecture

## High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                       MONITORING SYSTEM (Site A)                    │
│                                                                      │
│  ┌──────────────┐        ┌──────────────┐      ┌──────────────┐    │
│  │ InfluxDB     │◄──┬────┤ Python       │      │ Grafana      │    │
│  │              │   │    │ Anomaly      │─────►│ Dashboard    │    │
│  │ Measurements:│   │    │ Detection    │      │              │    │
│  │  - cpu       │   │    │ Script       │      │ Shows:       │    │
│  │  - mem       │   │    │              │      │  - Metrics   │    │
│  │  - net       │   │    │ Functions:   │      │  - Anomalies │    │
│  │              │   │    │  - Load data │      │  - Alerts    │    │
│  │  - predictions    │    │  - Train     │      │              │    │
│  │  - anomalies│   │    │  - Predict   │      └──────────────┘    │
│  └──────────────┘   │    │  - Drift     │                         │
│         ▲           │    │    detect    │                         │
│         │           │    │              │                         │
│         └───────────┼────┤              │                         │
│                     │    └──────────────┘                         │
│                     │                                              │
│                     │    ┌──────────────┐                         │
│                     │    │ MLflow       │                         │
│                     └───►│ Tracking     │                         │
│                          │ Server       │                         │
│                          │ (Experiment) │                         │
│                          └──────────────┘                         │
│                                                                      │
│                      Docker Container                              │
└─────────────────────────────────────────────────────────────────────┘
         ▲
         │ Telegraf sends metrics
         │ (TCP/UDP)
         │
┌─────────────────────────────────────────────────────────────────────┐
│                    MONITORED INFRASTRUCTURE (Site B)               │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Linux Docker Container (Flask Web App)                       │ │
│  │                                                               │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │ │
│  │  │ CPU      │  │ Memory   │  │ Network  │  │ Disk     │   │ │
│  │  │ Metrics  │  │ Metrics  │  │ Metrics  │  │ Metrics  │   │ │
│  │  └────▲─────┘  └────▲─────┘  └────▲─────┘  └────▲─────┘   │ │
│  │       │             │             │             │           │ │
│  │  ┌────┴─────────────┴─────────────┴─────────────┴────┐     │ │
│  │  │ Telegraf Agent (Metrics Collector)               │     │ │
│  │  │  - Polls system metrics every 10s                │     │ │
│  │  │  - Converts to InfluxDB format                   │     │ │
│  │  └──────────────────┬───────────────────────────────┘     │ │
│  └─────────────────────┼──────────────────────────────────────┘ │
│                        │                                        │
│                  Docker Container                              │
└────────────────────────┼──────────────────────────────────────────┘
                         │
                    Data Network
```

## Component Description

### Site A: Monitoring System

#### 1. **InfluxDB** (Time-Series Database)
- **Purpose**: Store system metrics and predictions
- **Tables (Measurements)**:
  - `cpu`, `mem`, `net`: Raw metrics from Telegraf
  - `ai_predictions`: Model outputs (is_anomaly, cpu_val, mem_val, net_val)
- **Retention**: 30 days
- **Port**: 8086

#### 2. **Python Anomaly Detection Script**
- **Main Script**: `src/detect_anomaly.py`
- **Flow**:
  1. Load pre-trained model & scaler from disk
  2. Query InfluxDB for latest metrics (5-minute window)
  3. Scale features using StandardScaler
  4. Run Isolation Forest prediction
  5. Write prediction to InfluxDB (`ai_predictions` table)
  6. On normal samples: append to training CSV
  7. Every 5 minutes: retrain if new samples + drift detected
  8. Log run to MLflow

- **Supporting Scripts**:
  - `src/train_model.py`: Offline training with train/val/test split
  - `src/evaluate_model.py`: Test set evaluation + robustness tests
  - `src/validate_data.py`: Data schema & quality checks
  - `src/collect_real_data.py`: Extract actual metrics from InfluxDB (24h window)
  - `src/data_generation.py`: Generate synthetic training data (fallback)

#### 3. **MLflow Tracking Server**
- **Purpose**: Track training experiments, hyperparameters, metrics
- **UI**: `http://localhost:5000` (inside Docker)
- **Logged Artifacts**:
  - Model parameters (contamination, n_estimators)
  - Test metrics (precision, recall, F1, ROC-AUC)
  - Training data size, anomaly count
  - Model artifact (.pkl)

#### 4. **Grafana Dashboard**
- **Purpose**: Real-time visualization
- **Panels**:
  - Time-series: CPU, Memory, Network (last 24 hours)
  - Anomaly flag: Boolean (0=normal, 1=anomaly)
  - Alert list: Recent anomalies + timestamps
- **Data Source**: InfluxDB
- **Port**: 3000

---

### Site B: Monitored Infrastructure

#### 1. **Flask Web App** (Simulated Workload)
- **Purpose**: Generate system load to create realistic metrics
- **Docker Image**: Custom (debian + Python + Flask)
- **Endpoints**:
  - `GET /`: Simple health check
  - `POST /stress`: Trigger CPU/memory load for stress testing

#### 2. **Telegraf Agent** (Metrics Collector)
- **Purpose**: Poll system metrics, convert to InfluxDB format
- **Metrics Collected**:
  - **Host Metrics**: `cpu.usage_idle`, `mem.used_percent`, `net.bytes_recv/bytes_sent`
  - **Container Metrics**: `docker_container_cpu.usage_percent`, `docker_container_mem.usage`, `docker_container_net.rx_bytes/tx_bytes`
  - **Container Status**: `docker_container_status.exitcode`, `oomkilled`, `pid`, `uptime_ns`
- **Poll Interval**: 10 seconds (configurable)
- **Output**: Sends to InfluxDB via TCP/UDP
- **Config**: `../datacenter/telegraf.conf`

#### 3. **HTTP Stress Test Container** (DoS Simulator)
- **Purpose**: Simulate web traffic attacks to test anomaly detection
- **Implementation**: Python ThreadPoolExecutor with `requests` library
- **Configuration**:
  - Target: `http://host.docker.internal:5005` (Flask server)
  - Default Load: 200 RPS (configurable)
  - Threads: 50 concurrent workers
  - Duration: 300 seconds (5 minutes)
- **Attack Type**: HTTP GET flood to simulate DoS
- **Directory**: `../stress-test-docker/`

---

## Data Flow

### Training Phase (Offline)

```
Historical Data (CSV)
       ▼
┌─────────────────────┐
│ train_model.py      │
│ - Load CSV          │
│ - Split 70/15/15    │
│ - Grid search       │
│ - Train on training │
│ - Evaluate on test  │
│ - MLflow logging    │
└──────┬──────────────┘
       ▼
Models/ (saved versions)
- anomaly_model_vYYYYMMDD_HHMMSS.pkl
- scaler_vYYYYMMDD_HHMMSS.pkl
- anomaly_model.pkl (latest symlink)

Results/ (metrics)
- training_metrics_YYYYMMDD_HHMMSS.json
- evaluation_report_YYYYMMDD_HHMMSS.json
```

### Inference Phase (Real-Time)

```
InfluxDB (metrics)
       ▼
┌─────────────────────────────────────────┐
│ detect_anomaly.py (continuous loop)     │
│ 1. Query InfluxDB (last 5 min)          │
│ 2. Load model + scaler                  │
│ 3. Scale features                       │
│ 4. Predict (normal=0, anomaly=-1)       │
│ 5. Write ai_predictions to InfluxDB     │
│ 6. Log to MLflow                        │
│ 7. Append normal samples to CSV         │
│ 8. Every 5 min: drift check + retrain   │
└────────────────┬────────────────────────┘
                 ▼
┌─────────────────────────────────────────┐
│ InfluxDB (ai_predictions measurement)   │
│ - is_anomaly (0 or 1)                   │
│ - cpu_val, mem_val, net_val             │
│ - timestamp                             │
└────────────────┬────────────────────────┘
                 ▼
          Grafana Dashboard
          (real-time alerts)
```

---

## Model Pipeline (MLOps)

```
Data Validation
    ▼
Feature Scaling (StandardScaler)
    ▼
Isolation Forest Training
    ▼
Hyperparameter Grid Search
    ▼
Test Set Evaluation
    ▼
Robustness Testing
(noise, missing, outliers, drift)
    ▼
Model Versioning (timestamp)
    ▼
MLflow Tracking
    ▼
Deployment (Docker)
    ▼
Online Prediction + Monitoring
    ▼
Drift Detection (KS-test)
    ▼
Conditional Retraining
```

---

## Technology Stack

| Component | Technology | Version | Role |
|-----------|-----------|---------|------|
| **Database** | InfluxDB | 1.8 | Time-series storage |
| **Language** | Python | 3.9+ | ML script |
| **ML Library** | scikit-learn | 1.8.0 | Model training |
| **Data Processing** | pandas, numpy | Latest | Data manipulation |
| **Experiment Tracking** | MLflow | 2.0+ | Run logging & registry |
| **Visualization** | Grafana | Latest | Dashboard & alerts |
| **Orchestration** | Docker Compose | 3.8 | Container management |
| **Metrics Collector** | Telegraf | Latest | Agent-based polling |

---

## Deployment Architecture

```
┌──────────────────────────────────────────────────────────┐
│ Docker Compose (Local Environment)                       │
│                                                          │
│ ┌────────────┐  ┌────────────┐  ┌────────────┐         │
│ │ ai_app     │  │ influxdb   │  │ grafana    │         │
│ │ Service    │  │ Service    │  │ Service    │         │
│ │            │  │            │  │            │         │
│ │ Port: N/A  │  │ Port: 8086 │  │ Port: 3000 │         │
│ │ Volumes:   │  │ Volumes:   │  │ Volumes:   │         │
│ │ - /app/data│  │ - influx-db│  │ - grafana- │         │
│ │ - /app/logs│  │   -storage │  │   storage  │         │
│ │            │  │            │  │            │         │
│ └────────────┘  └────────────┘  └────────────┘         │
│       │                │                 │              │
│       └────────────────┼─────────────────┘              │
│                    Network: bridge                      │
└──────────────────────────────────────────────────────────┘

Host (Windows/Linux/Mac):
- Port 8086: InfluxDB API
- Port 3000: Grafana UI
- Port 5000: MLflow UI (optional)
- Volumes: Local data persistence
```

---

## Batch vs Stream Processing

### Current Implementation: **Stream Processing**
- **Paradigm**: Event-driven (metric arrives → immediate prediction)
- **Latency**: ~10 sec (Telegraf interval) + <1 sec (prediction)
- **Window**: Last 5 minutes of data
- **Advantages**: Real-time alerting, responsive to recent changes
- **Disadvantages**: Cannot buffer for cost optimization

### Future: Batch Processing (Out of Scope)
- Would aggregate metrics hourly, retrain once/day
- Lower compute cost, but slower alerting

---

## API & Integration Points

### InfluxDB Query API
```bash
# Query latest CPU metric
SELECT "usage_idle" FROM "cpu" WHERE time > now() - 5m LIMIT 1

# Write anomaly prediction
POST /write?db=system_metrics
{
  "measurement": "ai_predictions",
  "fields": {"is_anomaly": 1, "cpu_val": 45.2, ...},
  "timestamp": 1234567890
}
```

### MLflow Experiment Tracking API
```python
mlflow.start_run()
mlflow.log_params({"contamination": 0.01})
mlflow.log_metrics({"f1_score": 0.92})
mlflow.sklearn.log_model(model, "anomaly_model")
mlflow.end_run()
```

### Grafana Dashboard API
- Pulls from InfluxDB datasource
- Renders time-series + alerts

---

## Monitoring & Observability

### Logs
- **Location**: `logs/app.log` (inside container)
- **Format**: JSON (timestamp, level, message, context)
- **Retention**: 7 days (rotate)

### Metrics Exposed
- Prediction latency (MLflow)
- Model F1-score over time (InfluxDB)
- Anomaly count/hour (Grafana query)
- Retrain frequency (MLflow run count)

### Alerts
- **High anomaly rate**: >100 anomalies/hour
- **Latency spike**: Prediction >10 sec
- **Model drift**: KS-test p-value < 0.05
- **System downtime**: InfluxDB query fails

---

## Automation Architecture

### Setup & Deployment (`setup_and_run.ps1`)

```
User runs: .\setup_and_run.ps1 -CleanInstall
       ▼
┌──────────────────────────────────────────┐
│ 1. Prerequisites Check                   │
│    - Docker / Docker Compose             │
│    - Python (optional)                   │
└──────────┬───────────────────────────────┘
           ▼
┌──────────────────────────────────────────┐
│ 2. Clean Up (if -CleanInstall)          │
│    - Stop all containers                 │
│    - Remove volumes & data files         │
└──────────┬───────────────────────────────┘
           ▼
┌──────────────────────────────────────────┐
│ 3. Start Infrastructure                  │
│    docker-compose up -d --build          │
│    (InfluxDB, Grafana, MLflow, AI)       │
└──────────┬───────────────────────────────┘
           ▼
┌──────────────────────────────────────────┐
│ 4. Health Checks (30 retries × 2s)      │
│    - InfluxDB: /ping → 204              │
│    - Grafana: /api/health → 200         │
│    - MLflow: / → 200                    │
└──────────┬───────────────────────────────┘
           ▼
┌──────────────────────────────────────────┐
│ 5. Initialize Database                   │
│    influx -execute "CREATE DATABASE..."  │
└──────────┬───────────────────────────────┘
           ▼
┌──────────────────────────────────────────┐
│ 6. Data Preparation (Intelligent)        │
│    IF system_metrics.csv exists:         │
│       Use existing data                  │
│    ELIF InfluxDB has historical data:    │
│       collect_real_data.py (24h)         │
│    ELSE:                                 │
│       data_generation.py (synthetic)     │
└──────────┬───────────────────────────────┘
           ▼
┌──────────────────────────────────────────┐
│ 7. Validate Data Quality                 │
│    validate_data.py (6 checks)           │
└──────────┬───────────────────────────────┘
           ▼
┌──────────────────────────────────────────┐
│ 8. Train ML Model                        │
│    train_model.py (grid search)          │
│    → models/anomaly_model.pkl            │
│    → Log to MLflow                       │
└──────────┬───────────────────────────────┘
           ▼
┌──────────────────────────────────────────┐
│ 9. Start Datacenter Monitoring           │
│    cd ../datacenter                      │
│    docker-compose up -d                  │
│    (Flask + Telegraf)                    │
└──────────┬───────────────────────────────┘
           ▼
┌──────────────────────────────────────────┐
│ 10. Start AI Detection Service           │
│     docker exec -d ai_app \              │
│       python src/detect_anomaly.py       │
└──────────┬───────────────────────────────┘
           ▼
     System Ready!
     - Grafana: localhost:3000
     - MLflow: localhost:5000
     - Flask: localhost:5005
```

### Testing & Validation (`test_and_validate.ps1`)

```
User runs: .\test_and_validate.ps1 -Duration 300 -RequestsPerSecond 200
       ▼
┌──────────────────────────────────────────┐
│ 1. Verify Services Running               │
│    docker ps → Check 6 containers        │
└──────────┬───────────────────────────────┘
           ▼
┌──────────────────────────────────────────┐
│ 2. Run Unit Tests                        │
│    pytest tests/ -v                      │
└──────────┬───────────────────────────────┘
           ▼
┌──────────────────────────────────────────┐
│ 3. Validate Data Quality                 │
│    validate_data.py                      │
└──────────┬───────────────────────────────┘
           ▼
┌──────────────────────────────────────────┐
│ 4. Record Baseline Metrics               │
│    Query InfluxDB for normal state       │
└──────────┬───────────────────────────────┘
           ▼
┌──────────────────────────────────────────┐
│ 5. Start HTTP Stress Test                │
│    cd ../stress-test-docker              │
│    docker-compose up -d                  │
│    → http_load_generator.py              │
│    → 50 threads × 200 RPS → Flask        │
└──────────┬───────────────────────────────┘
           ▼
┌──────────────────────────────────────────┐
│ 6. Monitor Loop (every 30s)              │
│    - Query ai_predictions.is_anomaly     │
│    - Check Flask container metrics       │
│    - Display stress test progress        │
│    Loop for Duration seconds             │
└──────────┬───────────────────────────────┘
           ▼
┌──────────────────────────────────────────┐
│ 7. Stop Stress Test                      │
│    docker-compose down                   │
└──────────┬───────────────────────────────┘
           ▼
┌──────────────────────────────────────────┐
│ 8. Generate Test Report                  │
│    - Anomaly detection: YES/NO           │
│    - Unit test results                   │
│    - Metrics summary                     │
│    → results/test_report_*.txt           │
└──────────────────────────────────────────┘
```

### Key Automation Features

1. **Intelligent Data Handling**:
   - Prefers real data from InfluxDB if available
   - Falls back to synthetic data for immediate testing
   - Validates data quality before training

2. **Robust Error Handling**:
   - Health checks with retry logic (30 attempts)
   - Graceful degradation (warns instead of fails)
   - Comprehensive logging at each step

3. **One-Command Deployment**:
   - Single script orchestrates 10 complex steps
   - 3-5 minute total setup time
   - Color-coded output for easy monitoring

4. **Container Monitoring**:
   - Per-container metrics (CPU, Memory, Network)
   - Container status (OOM killed, exit codes)
   - Grafana queries with dropdown selector

5. **Stress Test Integration**:
   - HTTP DoS simulation (not internal stress)
   - Configurable load (RPS, duration, threads)
   - Real-time progress monitoring
   - Automated report generation

---

**See Also:**
- [AUTOMATION_GUIDE.md](AUTOMATION_GUIDE.md) - Detailed automation documentation
- [DEPLOYMENT.md](DEPLOYMENT.md) - Manual deployment procedures
- [MODEL_CARD.md](MODEL_CARD.md) - Model details & limitations
- [README.md](../README.md) - Project overview
