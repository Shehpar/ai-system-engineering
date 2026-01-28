# ============================================================
# AI Infrastructure Anomaly Detection - Automated Setup Script
# ============================================================
# This script:
# 1. Starts Docker services (InfluxDB, Grafana, MLflow, Python app)
# 2. Waits for services to be ready
# 3. Trains the anomaly detection model
# 4. Validates data quality
# 5. Evaluates model performance
# 6. Shows URLs for monitoring dashboards
# ============================================================

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🚀 AI INFRASTRUCTURE ANOMALY DETECTION - SETUP SCRIPT    ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

# Colors for output
$Success = "Green"
$Warning = "Yellow"
$Info = "Cyan"
$Error = "Red"

# Check if Docker is installed
Write-Host "`n[1/6] Checking Docker installation..." -ForegroundColor $Info
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker found: $dockerVersion" -ForegroundColor $Success
} catch {
    Write-Host "❌ Docker not found. Please install Docker Desktop first." -ForegroundColor $Error
    Write-Host "   Download: https://www.docker.com/products/docker-desktop" -ForegroundColor $Warning
    exit 1
}

# Check if Docker daemon is running
Write-Host "`n[2/6] Checking Docker daemon..." -ForegroundColor $Info
try {
    docker ps | Out-Null
    Write-Host "✅ Docker daemon is running" -ForegroundColor $Success
} catch {
    Write-Host "❌ Docker daemon not running!" -ForegroundColor $Error
    Write-Host "   Please start Docker Desktop and wait 30 seconds, then try again." -ForegroundColor $Warning
    exit 1
}

# Start Docker Compose services
Write-Host "`n[3/6] Starting Docker services (InfluxDB, Grafana, MLflow, Python)..." -ForegroundColor $Info
Write-Host "   This may take 1-2 minutes on first run..." -ForegroundColor $Warning
docker-compose -f docker/docker-compose.yml up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start Docker services" -ForegroundColor $Error
    exit 1
}

Write-Host "✅ Docker services started in background" -ForegroundColor $Success

# Wait for services to be ready
Write-Host "`n[4/6] Waiting for services to be ready..." -ForegroundColor $Info
Write-Host "   ⏳ Waiting 45 seconds for InfluxDB, Grafana, and MLflow to initialize..." -ForegroundColor $Warning

for ($i = 45; $i -gt 0; $i--) {
    Write-Host -NoNewline "`r   ⏳ $i seconds remaining...  "
    Start-Sleep -Seconds 1
}
Write-Host "`n✅ Services should be ready now" -ForegroundColor $Success

# List running containers
Write-Host "`n   Running containers:" -ForegroundColor $Info
docker-compose -f docker/docker-compose.yml ps

# Train Model
Write-Host "`n[5/6] Training anomaly detection model..." -ForegroundColor $Info
Write-Host "   This will:" -ForegroundColor $Warning
Write-Host "   - Load historical data from CSV" -ForegroundColor $Warning
Write-Host "   - Split into train/val/test (70/15/15)" -ForegroundColor $Warning
Write-Host "   - Grid search for best hyperparameters" -ForegroundColor $Warning
Write-Host "   - Evaluate on test set (P/R/F1/ROC-AUC)" -ForegroundColor $Warning
Write-Host "   - Log results to MLflow" -ForegroundColor $Warning
Write-Host "`n   Running train_model.py..." -ForegroundColor $Info

docker exec ai_app python src/train_model.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Training failed" -ForegroundColor $Error
    Write-Host "   Check logs: docker logs ai_app" -ForegroundColor $Warning
    exit 1
}

Write-Host "✅ Model training completed" -ForegroundColor $Success

# Validate Data
Write-Host "`n[6/6] Validating data quality..." -ForegroundColor $Info
Write-Host "   This will:" -ForegroundColor $Warning
Write-Host "   - Check schema (3 required columns)" -ForegroundColor $Warning
Write-Host "   - Verify ranges (CPU/mem: 0-100%, network: ≥0)" -ForegroundColor $Warning
Write-Host "   - Detect missing values and duplicates" -ForegroundColor $Warning
Write-Host "   - Identify statistical outliers (IQR)" -ForegroundColor $Warning
Write-Host "`n   Running validate_data.py..." -ForegroundColor $Info

docker exec ai_app python src/validate_data.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Data validation found issues (see above)" -ForegroundColor $Warning
} else {
    Write-Host "✅ Data validation passed" -ForegroundColor $Success
}

# Evaluate Model
Write-Host "`n   Evaluating model robustness..." -ForegroundColor $Info
Write-Host "   This will:" -ForegroundColor $Warning
Write-Host "   - Test on clean test data (baseline)" -ForegroundColor $Warning
Write-Host "   - Inject Gaussian noise (σ = 0.01, 0.05, 0.1)" -ForegroundColor $Warning
Write-Host "   - Test missing feature handling" -ForegroundColor $Warning
Write-Host "   - Inject extreme outliers (2x, 5x, 10x)" -ForegroundColor $Warning
Write-Host "   - Test distribution shifts (+0.1, +0.5, +1.0)" -ForegroundColor $Warning
Write-Host "`n   Running evaluate_model.py..." -ForegroundColor $Info

docker exec ai_app python src/evaluate_model.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Evaluation failed" -ForegroundColor $Error
    exit 1
}

Write-Host "✅ Model evaluation completed" -ForegroundColor $Success

# Summary
Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor $Success
Write-Host "║               ✅ SETUP COMPLETE & SUCCESSFUL               ║" -ForegroundColor $Success
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor $Success

Write-Host "`n📊 WHAT YOU CAN DO NOW:" -ForegroundColor $Info
Write-Host "`n1️⃣  VIEW LIVE DASHBOARD" -ForegroundColor $Info
Write-Host "   Open in browser: http://localhost:3000" -ForegroundColor $Success
Write-Host "   Login: admin / admin" -ForegroundColor $Warning
Write-Host "   Watch real-time metrics and anomaly predictions" -ForegroundColor $Warning

Write-Host "`n2️⃣  VIEW TRAINING EXPERIMENTS" -ForegroundColor $Info
Write-Host "   Open in browser: http://localhost:5000" -ForegroundColor $Success
Write-Host "   See hyperparameters, metrics, model artifacts" -ForegroundColor $Warning

Write-Host "`n3️⃣  CHECK RESULTS FILES" -ForegroundColor $Info
Write-Host "   Models saved to: models/" -ForegroundColor $Success
Write-Host "   Data saved to: data/processed/" -ForegroundColor $Success
Write-Host "   Results saved to: results/" -ForegroundColor $Success

Write-Host "`n4️⃣  VIEW LOGS" -ForegroundColor $Info
Write-Host "   docker logs -f ai_app          (follow logs)" -ForegroundColor $Success
Write-Host "   docker logs ai_app             (view all logs)" -ForegroundColor $Success

Write-Host "`n5️⃣  STOP SERVICES" -ForegroundColor $Info
Write-Host "   docker-compose down            (stop all services)" -ForegroundColor $Success
Write-Host "   docker-compose down -v         (stop and delete data)" -ForegroundColor $Warning

Write-Host "`n📁 GENERATED FILES:" -ForegroundColor $Info
Write-Host "   ✅ models/anomaly_model.pkl           (trained model)" -ForegroundColor $Success
Write-Host "   ✅ models/scaler.pkl                  (feature scaler)" -ForegroundColor $Success
Write-Host "   ✅ results/training_metrics_*.json    (training results)" -ForegroundColor $Success
Write-Host "   ✅ results/evaluation_report_*.json   (robustness test results)" -ForegroundColor $Success
Write-Host "   ✅ results/validation_report_*.json   (data quality report)" -ForegroundColor $Success
Write-Host "   ✅ data/processed/system_metrics_processed.csv  (processed data)" -ForegroundColor $Success

Write-Host "`n📚 DOCUMENTATION:" -ForegroundColor $Info
Write-Host "   📖 docs/REQUIREMENTS.md    (problem statement & KPIs)" -ForegroundColor $Success
Write-Host "   📖 docs/ARCHITECTURE.md    (system design & data flow)" -ForegroundColor $Success
Write-Host "   📖 docs/MODEL_CARD.md      (model details & robustness results)" -ForegroundColor $Success
Write-Host "   📖 docs/DEPLOYMENT.md      (setup & operations guide)" -ForegroundColor $Success

Write-Host "`n🎯 NEXT STEPS:" -ForegroundColor $Info
Write-Host "   1. Open Grafana dashboard (http://localhost:3000)" -ForegroundColor $Success
Write-Host "   2. Review training metrics in MLflow (http://localhost:5000)" -ForegroundColor $Success
Write-Host "   3. Check JSON reports in results/ folder" -ForegroundColor $Success
Write-Host "   4. Read documentation (especially REQUIREMENTS.md & ARCHITECTURE.md)" -ForegroundColor $Success
Write-Host "   5. Leave services running to monitor live predictions" -ForegroundColor $Success

Write-Host "`n⚠️  IMPORTANT:" -ForegroundColor $Warning
Write-Host "   - Keep Docker running to view live dashboards" -ForegroundColor $Warning
Write-Host "   - Default Grafana credentials: admin / admin" -ForegroundColor $Warning
Write-Host "   - MLflow is read-only; metrics already logged" -ForegroundColor $Warning
Write-Host "   - To view logs: docker logs -f ai_app" -ForegroundColor $Warning
Write-Host "   - To stop everything: docker-compose down" -ForegroundColor $Warning

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $Info
Write-Host "✨ All systems running. Happy exploring! ✨" -ForegroundColor $Success
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $Info
