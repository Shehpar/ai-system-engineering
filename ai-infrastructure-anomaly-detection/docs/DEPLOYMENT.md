# Deployment Guide

## Quick Start

### Prerequisites
- **Docker** & **Docker Compose** installed ([Get Docker](https://www.docker.com/products/docker-desktop))
- **Git** repository cloned
- **Python** 3.9+ (optional, for local development)
- **4GB RAM** minimum (8GB recommended)
- **5GB Disk** space for images and data

---

## Option 1: Automated Setup (Recommended - 3 Minutes)

### Complete Deployment with One Command

**For Clean Installation** (deletes all existing data):
```powershell
.\setup_and_run.ps1 -CleanInstall
```

**For Standard Setup** (preserves existing data):
```powershell
.\setup_and_run.ps1
```

### What the Script Does

The automation script performs these steps automatically:

1. ✅ **Validates Prerequisites**: Checks Docker, Docker Compose, Python
2. ✅ **Cleans Up** (if -CleanInstall): Removes old containers, volumes, data
3. ✅ **Starts Services**: InfluxDB, Grafana, MLflow, AI service
4. ✅ **Health Checks**: Waits for all services to be ready (30 retries × 2s)
5. ✅ **Creates Database**: Initializes InfluxDB `system_metrics` database
6. ✅ **Imports Dashboard**: Auto-provisions Grafana datasource & dashboard
7. ✅ **Prepares Data**: Collects real data OR generates synthetic data
8. ✅ **Validates Data**: Runs 6 quality checks (schema, ranges, nulls)
9. ✅ **Trains Model**: Grid search + hyperparameter optimization
10. ✅ **Starts Monitoring**: Launches datacenter (Flask + Telegraf) + AI detection

**Total Time**: 3-5 minutes

### Expected Output

```
╔════════════════════════════════════════════════════════════════╗
║                 🎉 SETUP COMPLETED SUCCESSFULLY 🎉             ║
╚════════════════════════════════════════════════════════════════╝

📊 ACCESS POINTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🌐 Grafana Dashboard:  http://localhost:3000
     Login: admin / admin
  
  🔬 MLflow Experiments: http://localhost:5000
  
  💾 InfluxDB:           http://localhost:8086
  
  🌍 Flask Web App:      http://localhost:5005
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🐳 RUNNING SERVICES:
docker-influxdb-1       Up (healthy)   0.0.0.0:8086->8086/tcp
docker-grafana-1        Up (healthy)   0.0.0.0:3000->3000/tcp
docker-mlflow-1         Up (healthy)   0.0.0.0:5000->5000/tcp
docker-ai_app-1         Up (healthy)
flask_prod_server       Up             0.0.0.0:5005->5005/tcp
telegraf_site_b         Up
```

### Automated Testing

After setup, run comprehensive validation:

```powershell
# Default test (5 minutes, 200 RPS)
.\test_and_validate.ps1

# Custom test (2 minutes, 300 RPS)
.\test_and_validate.ps1 -Duration 120 -RequestsPerSecond 300
```

**What the Test Script Does**:
1. ✅ Verifies all 6 services are running
2. ✅ Runs unit tests (pytest)
3. ✅ Validates data quality
4. ✅ Records baseline metrics
5. ✅ Starts HTTP stress test (DoS simulation)
6. ✅ Monitors for anomaly detection (every 30s)
7. ✅ Generates test report

**Test Report** saved to `results/test_report_*.txt`

---

## Option 2: Manual Setup (Step-by-Step)

### Step 1: Clone & Navigate
```bash
git clone https://github.com/Shehpar/ai-system-engineering.git
cd ai-infrastructure-anomaly-detection
```

### Step 2: Start Core Services
```bash
docker-compose -f docker/docker-compose.yml up -d --build
```

This starts:
- **InfluxDB** (http://localhost:8086)
- **Grafana** (http://localhost:3000)
- **Python Script** (detects anomalies in loop)
- **MLflow Tracking Server** (http://localhost:5000)

### Step 3: Verify Services
```bash
# Check running containers
docker ps

# Test InfluxDB
curl http://localhost:8086/ping

# Test Grafana (default: admin/admin)
open http://localhost:3000

# Test MLflow
open http://localhost:5000
```

### Step 4: Create Database
```bash
docker exec docker-influxdb-1 influx -execute "CREATE DATABASE system_metrics"

# Verify
docker exec docker-influxdb-1 influx -execute "SHOW DATABASES"
```

### Step 5: Collect/Generate Training Data

**Option A: Collect Real Data** (if InfluxDB has historical data):
```bash
docker exec docker-ai_app-1 python src/collect_real_data.py
```

**Option B: Generate Synthetic Data** (for immediate testing):
```bash
docker exec docker-ai_app-1 python src/data_generation.py
```

### Step 6: Preprocess Data
```bash
docker exec docker-ai_app-1 python src/preprocessing.py
```

### Step 7: Validate Data
```bash
docker exec docker-ai_app-1 python src/validate_data.py
```

Expected output:
```
=====================================================
🤖 OFFLINE MODEL TRAINING - ANOMALY DETECTION
=====================================================
✅ Loaded 1000 samples from data/processed/system_metrics_processed.csv
📊 Data split: train=700, val=150, test=150
🔍 Starting hyperparameter grid search...
  Testing: contamination=0.01, n_estimators=100
  Testing: contamination=0.01, n_estimators=200
  ...
✅ Best params: {'contamination': 0.01, 'n_estimators': 200}
📈 Test Set Metrics:
  Precision: 0.9200
  Recall: 0.9200
  F1-Score: 0.9200
  Confusion Matrix:
[[946   4]
 [  4  46]]
💾 Model saved: models/anomaly_model_v20250127_143015.pkl
✅ MLflow run logged: ...
=====================================================
✅ TRAINING COMPLETED SUCCESSFULLY
=====================================================
```

#### Step 5: Validate Data
```bash
docker exec ai_app python src/validate_data.py
```

Expected output:
```
=====================================================
📋 DATA VALIDATION
=====================================================
✅ Schema validation passed
✅ All values within expected ranges
✅ No missing values detected
✅ Statistical properties logged
=====================================================
✅ DATA VALIDATION PASSED - Safe to use for training
=====================================================
```

#### Step 6: Evaluate Model
```bash
docker exec ai_app python src/evaluate_model.py
```

Expected output:
```
=====================================================
🔬 MODEL EVALUATION & ROBUSTNESS TESTING
=====================================================
📊 BASELINE EVALUATION (Clean Test Data)
Precision: 0.9200
Recall: 0.9200
F1-Score: 0.9200
ROC-AUC: 0.9500
...
🔧 ROBUSTNESS TEST 1: Gaussian Noise Injection
Noise σ=0.01: 46 anomalies detected (47.5%)
...
✅ Evaluation report saved: results/evaluation_report_20250127_143045.json
=====================================================
✅ EVALUATION COMPLETED SUCCESSFULLY
=====================================================
```

#### Step 7: Monitor Dashboard
1. Open http://localhost:3000 (Grafana)
2. Login: admin / admin
3. Select dashboard: "System Metrics"
4. Watch real-time metrics & anomaly flags (updated every 10s)

---

## Option 2: Local Development (Without Docker)

### Prerequisites
```bash
pip install -r requirements.txt
# Requires: pandas, numpy, scikit-learn, influxdb, mlflow, scipy
```

### Start InfluxDB & Grafana (Standalone)
```bash
# Option A: Use Docker for DB only
docker run -d --name influxdb -p 8086:8086 influxdb:1.8
docker run -d --name grafana -p 3000:3000 grafana/grafana

# Option B: Install locally (platform-specific)
# macOS: brew install influxdb grafana
# Linux: apt-get install influxdb grafana
# Windows: Download from influxdata.com, grafana.com
```

### Run Python Script Manually
```bash
cd src
python train_model.py      # Train offline
python validate_data.py    # Validate data
python evaluate_model.py   # Evaluate
python detect_anomaly.py   # Run inference loop
```

---

## Configuration

### Environment Variables
```bash
# .env (create in project root)
INFLUXDB_HOST=localhost           # Default: localhost
INFLUXDB_PORT=8086                # Default: 8086
INFLUXDB_DB=system_metrics        # Default: system_metrics
MLFLOW_TRACKING_URI=http://localhost:5000  # MLflow server
MODEL_RETRAIN_INTERVAL=300        # Seconds (default: 5 min)
DATA_RETENTION_DAYS=30            # Historical data to keep
```

### Docker Compose Customization
Edit `docker/docker-compose.yml`:

```yaml
services:
  ai_app:
    environment:
      - INFLUXDB_HOST=influxdb
      - INFLUXDB_PORT=8086
      - MODEL_RETRAIN_INTERVAL=300
    # Add resource limits
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

---

## Monitoring & Troubleshooting

### Check Container Logs
```bash
# View AI app logs
docker logs -f ai_app

# View InfluxDB logs
docker logs -f influxdb

# View Grafana logs
docker logs -f grafana
```

### Common Issues

#### ❌ "Connection refused" (InfluxDB)
```bash
# Verify InfluxDB is running
docker ps | grep influxdb

# Restart if needed
docker restart influxdb

# Test connection
curl http://localhost:8086/ping
```

#### ❌ "No data in Grafana"
1. Verify metrics in InfluxDB:
   ```bash
   curl -X GET 'http://localhost:8086/query?db=system_metrics&q=SELECT * FROM cpu LIMIT 1'
   ```
2. Check Grafana datasource configuration:
   - Settings → Data Sources → InfluxDB
   - Verify URL: http://influxdb:8086 (Docker) or http://localhost:8086 (local)
   - Test connection

#### ❌ "Out of memory"
```bash
# Check memory usage
docker stats ai_app

# Reduce historical data window in detect_anomaly.py
# Or increase container limits (see above)
```

#### ❌ "Model not found"
```bash
# Ensure train_model.py was run first
docker exec ai_app ls -la models/

# If empty, run training
docker exec ai_app python src/train_model.py
```

---

## Operational Tasks

### Train New Model
```bash
docker exec ai_app python src/train_model.py
# Model saved to models/anomaly_model_vYYYYMMDD_HHMMSS.pkl
```

### View Training Experiments
```bash
# Access MLflow UI
http://localhost:5000

# Or query via CLI
mlflow runs list --experiment-name "anomaly_detection_training"
```

### Check Data Quality
```bash
docker exec ai_app python src/validate_data.py
# Report: results/validation_report_latest.json
```

### Test Model Performance
```bash
docker exec ai_app python src/evaluate_model.py
# Report: results/evaluation_report_latest.json
```

### View Processed Data
```bash
# Inside container
docker exec ai_app head -20 data/processed/system_metrics_processed.csv

# Or locally
cat data/processed/system_metrics_processed.csv | head -20
```

### Reset All Data (Clean Slate)
```bash
# Stop containers
docker-compose -f docker/docker-compose.yml down

# Remove volumes (⚠️ deletes data!)
docker volume rm influxdb-storage grafana-storage

# Restart
docker-compose -f docker/docker-compose.yml up --build
```

---

## Deployment to Production (Future)

### Blue-Green Deployment
```bash
# 1. Deploy new model to staging
docker build -t ai-anomaly:staging -f docker/Dockerfile .

# 2. Run both old (production) and new (staging) versions
docker run -d --name prod_v1 ai-anomaly:production
docker run -d --name staging_v2 ai-anomaly:staging

# 3. Route 10% traffic to staging via load balancer (Nginx/HAProxy)
# 4. Monitor metrics (latency, F1-score)
# 5. If OK, switch 100% traffic to staging
# 6. Deprecate production container
```

### Kubernetes Deployment (Out of Scope for This Project)
```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
# Requires: YAML manifests, Docker registry, K8s cluster
```

---

## Health Checks

### Add Healthcheck Endpoint (Future)
```python
# In app.py or detect_anomaly.py
@app.route('/health')
def health():
    return {
        'status': 'healthy',
        'model_loaded': os.path.exists(MODEL_PATH),
        'last_prediction': datetime.now().isoformat(),
        'uptime_seconds': time.time() - start_time
    }
```

### Docker Healthcheck
```yaml
# In docker-compose.yml
services:
  ai_app:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

---

## Scaling & Performance

### Current Limits
- **Single server**: ~100 metrics/min
- **Training time**: <30 sec (700 samples)
- **Prediction latency**: <1 sec per sample
- **Memory**: ~500MB per container

### To Scale
1. **Horizontal**: Deploy multiple containers, load balance with Nginx/HAProxy
2. **Vertical**: Increase container resource limits (CPU, memory)
3. **Optimize**: 
   - Reduce historical data window (trade-off with drift detection)
   - Use model caching (avoid reloading every prediction)
   - Batch predictions (predict multiple samples at once)

---

## Backup & Recovery

### Backup InfluxDB
```bash
# Inside InfluxDB container
influxd backup /var/lib/influxdb/backup

# Or use Docker volume
docker cp influxdb:/var/lib/influxdb ./backup_$(date +%Y%m%d)
```

### Restore InfluxDB
```bash
docker cp backup_20250127 influxdb:/var/lib/influxdb/backup
# Or reinitialize from scratch (will retrain model on new data)
```

### Backup Models & Data
```bash
# Archive everything
tar -czf ai-anomaly-backup-$(date +%Y%m%d).tar.gz \
    models/ \
    data/processed/ \
    results/

# Upload to S3 / cloud storage
aws s3 cp ai-anomaly-backup-*.tar.gz s3://my-bucket/backups/
```

---

## Rollback & Rollforward

### Rollback to Previous Model
```bash
# List versions
ls -la models/anomaly_model_v*.pkl | sort

# Symlink to older version
ln -sf anomaly_model_v20250126.pkl models/anomaly_model.pkl

# Restart service
docker restart ai_app
```

### Rollforward to New Model
```bash
ln -sf anomaly_model_v20250127.pkl models/anomaly_model.pkl
docker restart ai_app
```

---

## Security

### Enable InfluxDB Authentication
```bash
# Set admin credentials (in docker-compose.yml)
environment:
  - INFLUXDB_ADMIN_USER=admin
  - INFLUXDB_ADMIN_PASSWORD=secure_password
```

### Use Secrets Management (Future)
```bash
# Docker Secrets (Swarm mode)
docker secret create influxdb_password password.txt

# Or environment variables (12-factor app)
export INFLUXDB_PASSWORD=$(cat ~/.influxdb_password)
```

### Network Isolation
```yaml
# In docker-compose.yml
networks:
  ai_network:
    driver: bridge
    
services:
  ai_app:
    networks:
      - ai_network
  influxdb:
    networks:
      - ai_network
    ports: []  # Don't expose
```

---

## Documentation

### View Architecture
See [ARCHITECTURE.md](ARCHITECTURE.md) for system design, data flow, and component details.

### View Model Details
See [MODEL_CARD.md](MODEL_CARD.md) for algorithm, training data, performance, and limitations.

### View Requirements
See [REQUIREMENTS.md](REQUIREMENTS.md) for problem statement, success criteria, and stakeholder needs.

---

## Support

### Debugging Commands
```bash
# Check model exists and can be loaded
docker exec ai_app python -c "import joblib; m = joblib.load('models/anomaly_model.pkl'); print('✅ Model OK')"

# Test InfluxDB connectivity
docker exec ai_app python -c "from influxdb import InfluxDBClient; c = InfluxDBClient(host='influxdb'); c.ping(); print('✅ InfluxDB OK')"

# Verify data in database
docker exec influxdb influx -database system_metrics -execute "SHOW MEASUREMENTS"
```

### Logs for Troubleshooting
```bash
# Last 50 lines of app logs
docker logs --tail 50 ai_app

# Follow logs in real-time
docker logs -f ai_app

# Grep for errors
docker logs ai_app 2>&1 | grep ERROR
```

---

**Next Steps:**
1. Follow Quick Start (Option 1)
2. Train model with `train_model.py`
3. Validate data with `validate_data.py`
4. Evaluate with `evaluate_model.py`
5. Monitor dashboard at http://localhost:3000
6. Observe predictions in InfluxDB for 24–48 hours
7. Document findings in a final report

---

**See Also:**
- [README.md](../README.md) - Project overview
- [REQUIREMENTS.md](REQUIREMENTS.md) - Problem statement & KPIs
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design & data flow
- [MODEL_CARD.md](MODEL_CARD.md) - Model details & evaluation
