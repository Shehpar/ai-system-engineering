# Quick Reference Guide - AI Anomaly Detection System

**For**: Professor Demonstrations & Testing  
**Date**: February 3, 2026  
**Status**: ✅ Production Ready

---

## 🚀 Quick Start Commands

### **Complete Setup (Clean Install)**
```powershell
# Delete everything and start fresh (3-5 minutes)
.\ai-infrastructure-anomaly-detection\setup_and_run.ps1 -CleanInstall
```

### **Run Validation Tests**
```powershell
# Comprehensive testing (5 minutes)
.\ai-infrastructure-anomaly-detection\test_and_validate.ps1
```

---

## 🌐 Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:3000 | admin / admin |
| **MLflow** | http://localhost:5000 | No auth |
| **InfluxDB** | http://localhost:8086 | No auth |
| **Flask App** | http://localhost:5005 | No auth |

---

## 📊 What to Show Professor

### **1. Automated Setup** (3 minutes)
```powershell
.\ai-infrastructure-anomaly-detection\setup_and_run.ps1 -CleanInstall
```
**What happens**:
- ✅ 6 services start automatically
- ✅ Database created
- ✅ Model trained
- ✅ Monitoring begins

### **2. Grafana Dashboard** (1 minute)
1. Open http://localhost:3000
2. Login: admin / admin
3. Navigate to "AI Anomaly Detection" dashboard
4. Show: Real-time metrics (CPU, Memory, Network)

### **3. Stress Test & Anomaly Detection** (5 minutes)
```powershell
.\ai-infrastructure-anomaly-detection\test_and_validate.ps1 -Duration 300
```
**What happens**:
- ✅ HTTP attack starts (200 RPS → Flask)
- ✅ Flask container CPU/Memory spike
- ✅ AI detects anomalies in 2-3 minutes
- ✅ Test report generated

### **4. MLflow Experiments** (1 minute)
1. Open http://localhost:5000
2. Click "anomaly_detection_training"
3. Show: Training metrics (F1-score, precision, recall)
4. Compare runs

---

## 🧪 Testing Scenarios

### **Scenario 1: Normal Operation**
```powershell
# Just setup, no stress
.\setup_and_run.ps1 -CleanInstall
```
**Expected**: Status = "Normal", no anomalies

### **Scenario 2: Light Load**
```powershell
.\setup_and_run.ps1 -CleanInstall
.\test_and_validate.ps1 -Duration 120 -RequestsPerSecond 150
```
**Expected**: Status = "Normal" or occasional anomalies

### **Scenario 3: Heavy Load (DoS Attack)**
```powershell
.\setup_and_run.ps1 -CleanInstall
.\test_and_validate.ps1 -Duration 300 -RequestsPerSecond 500
```
**Expected**: Status = "ANOMALY!!", sustained detection

---

## 🔍 Monitoring Points

### **In Grafana Dashboard**:
1. **Real-time Metrics**: CPU, Memory, Network (last 24h)
2. **Anomaly Status**: 0 = Normal, 1 = Anomaly
3. **Container Metrics**: Per-container CPU, Memory, Network
4. **Alert List**: Recent anomalies with timestamps

### **In MLflow**:
1. **Experiment Runs**: Training history
2. **Metrics**: F1-score, precision, recall, ROC-AUC
3. **Parameters**: contamination, n_estimators
4. **Artifacts**: Trained models, scalers

### **In InfluxDB** (via CLI):
```bash
docker exec docker-influxdb-1 influx -database system_metrics -execute "SELECT * FROM ai_predictions ORDER BY time DESC LIMIT 10"
```

---

## 🐛 Troubleshooting Quick Fixes

### **Services Not Starting**
```powershell
# Check Docker
docker ps

# Restart everything
docker-compose -f ai-infrastructure-anomaly-detection/docker/docker-compose.yml down -v
.\ai-infrastructure-anomaly-detection\setup_and_run.ps1 -CleanInstall
```

### **No Anomalies Detected**
```powershell
# Increase load
.\ai-infrastructure-anomaly-detection\test_and_validate.ps1 -Duration 180 -RequestsPerSecond 500

# OR lower thresholds in src/detect_anomaly.py
# CPU_THRESHOLD = 5.0 (instead of 10.0)
# MEMORY_THRESHOLD = 20.0 (instead of 30.0)
```

### **Grafana Dashboard Empty**
```bash
# Re-import dashboard
docker exec docker-ai_app-1 python import_dashboard.py

# Restart Grafana
docker restart docker-grafana-1
```

### **Data Collection Failed**
```bash
# Use synthetic data (works immediately)
docker exec docker-ai_app-1 python src/data_generation.py
docker exec docker-ai_app-1 python src/preprocessing.py
docker exec docker-ai_app-1 python src/train_model.py
```

---

## 📋 Validation Checklist

### **Pre-Demo Checklist**:
- [ ] Docker Desktop running
- [ ] 8GB RAM available
- [ ] 5GB disk space free
- [ ] No other services on ports 3000, 5000, 8086, 5005

### **Post-Setup Checklist**:
- [ ] 6 containers running (`docker ps`)
- [ ] Grafana accessible (http://localhost:3000)
- [ ] MLflow accessible (http://localhost:5000)
- [ ] Dashboard shows metrics
- [ ] AI status: "Normal"

### **Post-Test Checklist**:
- [ ] Anomalies detected (is_anomaly = 1)
- [ ] Flask CPU spiked (>10%)
- [ ] Test report generated (`results/test_report_*.txt`)
- [ ] Unit tests passed (5/5)

---

## 🎯 Success Metrics

| Metric | Target | How to Verify |
|--------|--------|---------------|
| **Setup Time** | <5 min | Watch script output |
| **Services Healthy** | 6/6 | `docker ps` |
| **Model F1-Score** | >80% | Check MLflow UI |
| **Detection Latency** | <10ms | Check logs |
| **Anomaly Detection** | <5 min | Watch Grafana during stress |
| **Test Pass Rate** | 100% | pytest output |

---

## 📞 Quick Commands Reference

### **View Logs**:
```powershell
# All services
docker-compose -f ai-infrastructure-anomaly-detection/docker/docker-compose.yml logs -f

# Specific service
docker logs docker-ai_app-1 -f
docker logs flask_prod_server -f
```

### **Check Service Status**:
```powershell
# List all containers
docker ps

# Check health
docker inspect docker-influxdb-1 | Select-String -Pattern "Health"
```

### **Manual Operations**:
```bash
# Train model
docker exec docker-ai_app-1 python src/train_model.py

# Collect real data
docker exec docker-ai_app-1 python src/collect_real_data.py

# Validate data
docker exec docker-ai_app-1 python src/validate_data.py

# Run tests
docker exec docker-ai_app-1 pytest tests/ -v
```

### **Cleanup**:
```powershell
# Stop all
docker-compose -f ai-infrastructure-anomaly-detection/docker/docker-compose.yml down
docker-compose -f datacenter/docker-compose.yml down
docker-compose -f stress-test-docker/docker-compose.yml down

# Remove volumes
docker-compose -f ai-infrastructure-anomaly-detection/docker/docker-compose.yml down -v

# Full cleanup
docker system prune -a
```

---

## 🎓 Key Talking Points for Professor

### **1. Innovation Highlights**:
- ✅ **Container-Level Monitoring**: Not just host - per-container CPU, Memory, Network
- ✅ **IP Traceability**: Can identify which container caused anomaly (stress → Flask)
- ✅ **Real Data Preference**: Uses actual system metrics when available
- ✅ **One-Command Deployment**: Complete setup in <5 minutes

### **2. MLOps Best Practices**:
- ✅ **Experiment Tracking**: MLflow for reproducibility
- ✅ **Model Versioning**: Timestamp-based model files
- ✅ **Data Validation**: 6 quality checks before training
- ✅ **Automated Testing**: Unit tests + integration tests

### **3. Production Readiness**:
- ✅ **Health Checks**: All services monitored
- ✅ **Error Handling**: Graceful degradation
- ✅ **Logging**: Structured JSON logs
- ✅ **Documentation**: 70+ pages

### **4. Scalability**:
- ✅ **Docker Compose**: Easy local deployment
- ✅ **Kubernetes Ready**: k8s/ directory with manifests
- ✅ **Horizontal Scaling**: Can add more workers
- ✅ **Cloud Compatible**: Works on AWS, Azure, GCP

---

## 📚 Documentation Quick Links

- **Automation Guide**: `docs/AUTOMATION_GUIDE.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **Deployment**: `docs/DEPLOYMENT.md`
- **Model Card**: `docs/MODEL_CARD.md`
- **Requirements**: `docs/REQUIREMENTS.md`
- **Session Summary**: `SESSION_SUMMARY_AUTOMATION.md`

---

## ⏱️ 10-Minute Demo Flow

| Time | Action | Command |
|------|--------|---------|
| 0:00 | Start setup | `.\setup_and_run.ps1 -CleanInstall` |
| 0:30 | Explain architecture | Show diagram in docs/ |
| 3:00 | Setup complete | Show service URLs |
| 3:30 | Open Grafana | http://localhost:3000 |
| 4:00 | Show baseline metrics | Point to dashboard |
| 4:30 | Start stress test | `.\test_and_validate.ps1` |
| 5:00 | Explain stress test | HTTP DoS simulation |
| 6:00 | Show Flask metrics spike | CPU/Memory graphs |
| 7:00 | Wait for anomaly detection | Status changes to "ANOMALY!!" |
| 8:00 | Show MLflow runs | http://localhost:5000 |
| 9:00 | Show test report | `results/test_report_*.txt` |
| 10:00 | Q&A | Answer questions |

---

**Last Updated**: February 3, 2026  
**Version**: 1.0  
**Status**: ✅ Ready for Professor Demo
