# Automation Guide

## Overview

This guide explains the automated setup and testing infrastructure for the AI Infrastructure Anomaly Detection System. Two PowerShell scripts provide complete automation for deployment and validation.

---

## 🎯 Purpose

**Problem**: Manual setup requires 15-20 steps across multiple terminals, making it error-prone and time-consuming for demonstrations.

**Solution**: Automated scripts that handle:
- ✅ Clean installation from scratch
- ✅ Prerequisite validation
- ✅ Service orchestration
- ✅ Data preparation (real or synthetic)
- ✅ Model training and validation
- ✅ Testing and stress simulation
- ✅ Report generation

---

## 📁 Automation Files

### 1. `setup_and_run.ps1` - Complete System Setup

**Purpose**: One-command deployment of the entire system from scratch.

**What it does**:
```
1. Prerequisites Check     → Verifies Docker, Docker Compose, Python
2. Clean Up (optional)     → Removes old containers, volumes, data
3. Start Infrastructure    → Launches InfluxDB, Grafana, MLflow, AI service
4. Wait for Services       → Health checks until all services ready
5. Create Database         → Initializes InfluxDB 'system_metrics' database
6. Import Dashboard        → Auto-provisions Grafana datasource & dashboard
7. Prepare Training Data   → Collects real data OR generates synthetic data
8. Validate Data Quality   → Runs 6 validation checks (schema, ranges, nulls)
9. Train ML Model          → Grid search + hyperparameter optimization
10. Start Monitoring       → Launches datacenter (Flask + Telegraf) + AI detection
```

**Usage**:
```powershell
# Standard setup (preserves existing data)
.\setup_and_run.ps1

# Clean install (deletes all data and starts fresh)
.\setup_and_run.ps1 -CleanInstall
```

**Parameters**:
- `-CleanInstall` (switch): Remove all existing data, containers, volumes

**Duration**: 3-5 minutes (depending on data collection)

**Output**:
- Service URLs (Grafana, MLflow, InfluxDB, Flask)
- Container status table
- Training metrics summary
- Next steps guide

---

### 2. `test_and_validate.ps1` - Automated Testing

**Purpose**: Comprehensive testing with stress simulation and anomaly validation.

**What it does**:
```
1. Check Service Status    → Verifies all 6 services are running
2. Run Unit Tests          → Executes pytest suite (5 tests)
3. Validate Data Quality   → Re-checks data integrity
4. Record Baseline         → Captures normal system state
5. Start Stress Test       → HTTP DoS simulation against Flask server
6. Monitor for Anomalies   → Checks every 30s for AI detection
7. Generate Report         → Creates test report with metrics
```

**Usage**:
```powershell
# Default test (5 minutes, 200 RPS)
.\test_and_validate.ps1

# Custom duration and load
.\test_and_validate.ps1 -Duration 120 -RequestsPerSecond 300
```

**Parameters**:
- `-Duration <int>`: Stress test duration in seconds (default: 300)
- `-RequestsPerSecond <int>`: HTTP load target (default: 200)

**Duration**: Matches stress test duration (default 5 minutes)

**Output**:
- Unit test results (PASSED/FAILED)
- Anomaly detection status (YES/NO)
- Flask container metrics (CPU, Memory, Network)
- Test report saved to `results/test_report_*.txt`

---

## 🏗️ Architecture

### Automation Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    setup_and_run.ps1                        │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │ Validate    │───►│ Start       │───►│ Initialize  │    │
│  │ Environment │    │ Services    │    │ Database    │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│         │                   │                   │          │
│         ▼                   ▼                   ▼          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │ Collect/    │───►│ Train       │───►│ Start       │    │
│  │ Generate    │    │ Model       │    │ Monitoring  │    │
│  │ Data        │    │             │    │ & AI        │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ System Ready
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   test_and_validate.ps1                     │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │ Run Unit    │───►│ Start HTTP  │───►│ Monitor     │    │
│  │ Tests       │    │ Stress Test │    │ Anomalies   │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│         │                   │                   │          │
│         ▼                   ▼                   ▼          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │ Validate    │───►│ Stop Stress │───►│ Generate    │    │
│  │ Data        │    │ Test        │    │ Report      │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Key Components

### Service Orchestration

**Managed Services**:
1. **InfluxDB** (Port 8086) - Time-series database
2. **Grafana** (Port 3000) - Dashboard and visualization
3. **MLflow** (Port 5000) - Experiment tracking
4. **AI Service** (docker-ai_app-1) - Anomaly detection
5. **Flask App** (Port 5005) - Simulated workload
6. **Telegraf** (telegraf_site_b) - Metrics collector

**Health Check Logic**:
```powershell
# InfluxDB readiness check
Invoke-WebRequest -Uri "http://localhost:8086/ping"
# Expected: 204 No Content

# Grafana readiness check
Invoke-WebRequest -Uri "http://localhost:3000/api/health"
# Expected: 200 OK with {"database": "ok"}

# MLflow readiness check
Invoke-WebRequest -Uri "http://localhost:5000"
# Expected: 200 OK
```

**Retry Logic**: 30 attempts with 2-second intervals (60 seconds max wait)

---

### Data Collection Strategy

The automation intelligently decides between real and synthetic data:

```powershell
# Decision tree
if (data/raw/system_metrics.csv exists) {
    Use existing data
} else if (InfluxDB has historical data) {
    Run collect_real_data.py (extracts 24h of metrics)
} else {
    Run data_generation.py (creates 1000 synthetic samples)
}
```

**Real Data Collection**:
- Queries: `cpu.usage_idle`, `mem.used_percent`, `net.bytes_recv/bytes_sent`
- Window: Last 24 hours
- Output: ~144 samples (1 per 10 minutes)
- File: `data/raw/system_metrics.csv`

**Synthetic Data Generation**:
- Distributions: Normal (CPU, Memory), Poisson (Network)
- Anomalies: 5% outliers with 3× magnitude
- Samples: 1000 total
- Advantage: Works immediately without historical data

---

### Stress Test Architecture

**HTTP Load Generator** (`stress-test-docker/http_load_generator.py`):

```python
class HTTPLoadGenerator:
    def __init__(self, target_url, requests_per_second, duration, num_threads):
        self.target_url = target_url              # Flask server URL
        self.rps = requests_per_second            # Load intensity
        self.duration = duration                  # Test duration (seconds)
        self.num_threads = num_threads            # Concurrent workers
        
    def send_request(self):
        """Single HTTP GET request with 5s timeout"""
        requests.get(self.target_url, timeout=5)
        
    def worker(self, worker_id):
        """Continuous request loop with rate limiting"""
        while time.time() < self.end_time:
            self.send_request()
            time.sleep(delay)  # Rate control
            
    def run(self):
        """ThreadPoolExecutor manages worker pool"""
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = [executor.submit(self.worker, i) 
                      for i in range(self.num_threads)]
```

**Attack Simulation**:
- Target: `http://host.docker.internal:5005` (Flask server)
- Method: GET requests to root endpoint
- Default Load: 200 RPS (adjustable)
- Concurrency: 50 threads (configurable)
- Duration: 300 seconds (5 minutes)

**Why DoS Simulation?**:
- Tests container-level monitoring (Flask metrics)
- Creates realistic network/CPU/memory load
- Validates anomaly detection under attack
- Demonstrates IP-level traceability (stress container → Flask container)

---

### Monitoring & Detection

**Anomaly Detection Loop** (`src/detect_anomaly.py`):

```python
while True:
    # 1. Query latest metrics from InfluxDB (5-minute window)
    metrics = query_influxdb("SELECT * FROM cpu, mem, net WHERE time > now() - 5m")
    
    # 2. Load trained model
    model = joblib.load("models/anomaly_model.pkl")
    scaler = joblib.load("models/scaler.pkl")
    
    # 3. Scale features
    scaled = scaler.transform(metrics)
    
    # 4. Predict (-1 = anomaly, 1 = normal)
    predictions = model.predict(scaled)
    
    # 5. Write to InfluxDB
    write_influxdb("ai_predictions", {
        "is_anomaly": 1 if prediction == -1 else 0,
        "cpu_val": metrics[0],
        "mem_val": metrics[1],
        "net_val": metrics[2]
    })
    
    # 6. Sleep 30 seconds
    time.sleep(30)
```

**Threshold Configuration**:
```python
ANOMALY_THRESHOLD = 12  # 12 detections = 6 minutes sustained
CPU_THRESHOLD = 10.0    # 10% usage
MEMORY_THRESHOLD = 30.0 # 30% usage
NETWORK_THRESHOLD = 15000  # 15k bytes/sec
```

---

## 🚀 Usage Scenarios

### Scenario 1: Professor Demo (Clean Start)

**Situation**: Professor wants to see system from scratch.

**Commands**:
```powershell
# Terminal 1: Complete setup
.\setup_and_run.ps1 -CleanInstall

# Wait 3-5 minutes for setup to complete
# Access Grafana: http://localhost:3000 (admin/admin)
# Access MLflow: http://localhost:5000

# Terminal 2: Run validation test
.\test_and_validate.ps1 -Duration 180 -RequestsPerSecond 250

# Observe:
# - Grafana dashboard shows real-time metrics
# - Flask container CPU/Memory spikes during stress
# - AI detection flags anomalies in 2-3 minutes
# - Test report generated automatically
```

**Timeline**:
- 0:00 - Start setup
- 3:00 - System ready
- 3:30 - Start stress test (3 minutes)
- 6:30 - Test complete, report generated
- **Total: ~7 minutes**

---

### Scenario 2: Development Workflow

**Situation**: Making changes and testing iteratively.

**Commands**:
```powershell
# Initial setup (once)
.\setup_and_run.ps1

# Make code changes to src/train_model.py
# ...

# Re-train model manually
docker exec docker-ai_app-1 python src/train_model.py

# Quick validation test (2 minutes)
.\test_and_validate.ps1 -Duration 120 -RequestsPerSecond 150

# Review results in Grafana/MLflow
```

---

### Scenario 3: Troubleshooting

**Situation**: Something isn't working correctly.

**Commands**:
```powershell
# Full clean install
.\setup_and_run.ps1 -CleanInstall

# If services fail, check logs
docker-compose -f docker/docker-compose.yml logs -f

# If database issues
docker exec docker-influxdb-1 influx -execute "SHOW DATABASES"

# If model issues
docker exec docker-ai_app-1 python src/validate_data.py
docker exec docker-ai_app-1 python src/train_model.py
```

---

## 📊 Validation Criteria

### Setup Success Indicators

✅ **All services healthy**:
```powershell
docker ps --format "table {{.Names}}\t{{.Status}}"
# Expected: All show "(healthy)"
```

✅ **Database created**:
```powershell
docker exec docker-influxdb-1 influx -execute "SHOW DATABASES"
# Expected: system_metrics in list
```

✅ **Model trained**:
```powershell
ls models/*.pkl
# Expected: anomaly_model.pkl, scaler.pkl
```

✅ **Grafana accessible**:
- Open http://localhost:3000
- Login with admin/admin
- See "AI Anomaly Detection" dashboard

---

### Test Success Indicators

✅ **Unit tests passing**:
```
tests/test_train_model.py::test_split_data_shapes PASSED
tests/test_validate_data.py::test_validate_schema_pass PASSED
...
5 passed in 2.34s
```

✅ **Stress test active**:
```
Worker 0 started
Worker 1 started
...
13s: 1717 requests | 129.4 RPS | 0 errors
```

✅ **Anomaly detection working**:
```sql
SELECT * FROM ai_predictions WHERE is_anomaly = 1 AND time > now() - 5m
# Expected: Rows with is_anomaly=1 during stress
```

✅ **Flask metrics spiking**:
```
flask_prod_server   10.25%   45MB / 512MB   NetIO: 1.2MB / 850kB
# Expected: CPU > 5%, Network > 500kB during stress
```

---

## 🔍 Troubleshooting Guide

### Problem: Services Not Starting

**Symptoms**:
- `docker ps` shows containers as "unhealthy" or "restarting"
- Setup script fails at "Waiting for Services"

**Solutions**:
```powershell
# Check Docker resources
# Docker Desktop → Settings → Resources
# Increase Memory to 8GB, CPU to 4 cores

# Check logs
docker-compose -f docker/docker-compose.yml logs

# Nuclear option: full cleanup
docker-compose -f docker/docker-compose.yml down -v
docker system prune -a
.\setup_and_run.ps1 -CleanInstall
```

---

### Problem: No Anomalies Detected

**Symptoms**:
- Stress test runs but `is_anomaly` always 0
- Flask metrics spike but AI doesn't flag

**Solutions**:
```powershell
# 1. Check model was trained with correct data
docker exec docker-ai_app-1 cat data/raw/system_metrics.csv | head -10

# 2. Verify thresholds match system baseline
docker exec docker-ai_app-1 python -c "
import pandas as pd
df = pd.read_csv('data/raw/system_metrics.csv')
print('Baseline:', df[['cpu_usage_percent', 'memory_usage_percent']].mean())
"

# 3. Adjust thresholds in detect_anomaly.py
# Edit: CPU_THRESHOLD, MEMORY_THRESHOLD, NETWORK_THRESHOLD

# 4. Re-train model
docker exec docker-ai_app-1 python src/train_model.py

# 5. Re-run test with higher load
.\test_and_validate.ps1 -Duration 180 -RequestsPerSecond 500
```

---

### Problem: Data Collection Fails

**Symptoms**:
- Setup script says "Real data collection failed"
- Falls back to synthetic data

**Root Cause**: InfluxDB has no historical data (fresh install)

**Solution**:
```powershell
# Option 1: Let system collect data for 1 hour
Start-Sleep -Seconds 3600
docker exec docker-ai_app-1 python src/collect_real_data.py

# Option 2: Use synthetic data (works immediately)
docker exec docker-ai_app-1 python src/data_generation.py
docker exec docker-ai_app-1 python src/preprocessing.py
docker exec docker-ai_app-1 python src/train_model.py
```

---

### Problem: Grafana Dashboard Not Loading

**Symptoms**:
- http://localhost:3000 works but no dashboard visible
- "No dashboards found" message

**Solutions**:
```powershell
# 1. Check provisioning files
docker exec docker-grafana-1 ls /etc/grafana/provisioning/dashboards/

# 2. Re-import dashboard manually
docker exec docker-ai_app-1 python import_dashboard.py

# 3. Restart Grafana
docker restart docker-grafana-1
Start-Sleep -Seconds 10
# Open http://localhost:3000
```

---

## 🎓 Educational Value

### What Students Learn

1. **DevOps Automation**:
   - PowerShell scripting for orchestration
   - Docker Compose service management
   - Health check patterns
   - Error handling and retry logic

2. **MLOps Practices**:
   - Automated model training pipelines
   - Data validation before training
   - Experiment tracking with MLflow
   - Model versioning with timestamps

3. **Testing Strategies**:
   - Unit testing (pytest)
   - Integration testing (service health)
   - Load testing (HTTP stress)
   - Validation reporting

4. **Production Readiness**:
   - One-command deployment
   - Automated rollback (CleanInstall)
   - Comprehensive logging
   - Documentation-driven development

---

## 🔐 Security Considerations

### Credentials

**Default Credentials** (for demo only):
```
Grafana: admin / admin (change on first login)
InfluxDB: No auth (for development)
MLflow: No auth (for development)
```

**Production Recommendations**:
- Enable InfluxDB authentication
- Use environment variables for secrets
- Add HTTPS with Let's Encrypt
- Implement RBAC in Grafana

### Network Isolation

**Current Setup**:
- All services on Docker bridge network
- Ports exposed only on localhost
- No external access by default

**Production Hardening**:
- Use Docker networks for isolation
- Add reverse proxy (nginx)
- Implement firewall rules
- Enable audit logging

---

## 📈 Performance Metrics

### Setup Performance

| Phase | Duration | CPU | Memory |
|-------|----------|-----|--------|
| Service Start | 30-60s | 50% | 2GB |
| Data Collection | 10-30s | 10% | 500MB |
| Model Training | 60-120s | 80% | 1GB |
| **Total** | **3-5 min** | **Avg 40%** | **Peak 3GB** |

### Test Performance

| Metric | Value | Notes |
|--------|-------|-------|
| HTTP RPS | 150-200 | Actual (200 target) |
| Flask CPU | 10-20% | During stress |
| Detection Latency | 6.94ms | Per prediction |
| Anomaly Detection Time | 2-6 min | 12 sustained detections |

---

## 📚 Related Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System design and data flow
- [DEPLOYMENT.md](DEPLOYMENT.md) - Manual deployment steps
- [MODEL_CARD.md](MODEL_CARD.md) - ML model details
- [REQUIREMENTS.md](REQUIREMENTS.md) - Functional requirements
- [README.md](../README.md) - Project overview

---

## 🎯 Summary

**Automation Benefits**:
- ✅ **Time Savings**: 15-20 manual steps → 1 command (3 minutes)
- ✅ **Repeatability**: Same results every time
- ✅ **Error Reduction**: Automated validation at each step
- ✅ **Demo Ready**: Perfect for professor presentations
- ✅ **Educational**: Clear code with extensive comments

**Key Scripts**:
```powershell
.\setup_and_run.ps1 -CleanInstall    # Full setup from scratch
.\test_and_validate.ps1              # Comprehensive testing
```

**For Questions**: See [DEPLOYMENT.md](DEPLOYMENT.md) for manual procedures or check inline script comments.

---

**Last Updated**: February 3, 2026  
**Script Version**: 1.0  
**Status**: ✅ Production Ready
