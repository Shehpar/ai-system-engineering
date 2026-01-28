# AI Infrastructure Anomaly Detection - Setup Script
# Simple and clean version that works on Windows PowerShell

Write-Host "`n===== AI Anomaly Detection Setup =====" -ForegroundColor Cyan

# Check Docker
Write-Host "`n[1/4] Checking Docker..." -ForegroundColor Yellow
docker --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker not found!" -ForegroundColor Red
    exit 1
}
Write-Host "OK: Docker is available" -ForegroundColor Green

# Start services
Write-Host "`n[2/4] Starting Docker services..." -ForegroundColor Yellow
docker-compose -f docker/docker-compose.yml up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to start services" -ForegroundColor Red
    exit 1
}
Write-Host "OK: Services started" -ForegroundColor Green

# Wait
Write-Host "`n[3/4] Waiting 45 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 45
Write-Host "OK: Services ready" -ForegroundColor Green

# Train
Write-Host "`n[4/4] Training model..." -ForegroundColor Yellow
docker-compose -f docker/docker-compose.yml exec -T ai_app python src/train_model.py
Write-Host "OK: Training complete" -ForegroundColor Green

# Validate
Write-Host "`nValidating data..." -ForegroundColor Yellow
docker-compose -f docker/docker-compose.yml exec -T ai_app python src/validate_data.py
Write-Host "OK: Validation complete" -ForegroundColor Green

# Evaluate
Write-Host "`nEvaluating robustness..." -ForegroundColor Yellow
docker-compose -f docker/docker-compose.yml exec -T ai_app python src/evaluate_model.py
Write-Host "OK: Evaluation complete" -ForegroundColor Green

# Done
Write-Host "`n===== SUCCESS =====" -ForegroundColor Green

Write-Host "`nDashboards:" -ForegroundColor Cyan
Write-Host "  Grafana:  http://localhost:3000 (admin/admin)" -ForegroundColor White
Write-Host "  MLflow:   http://localhost:5000" -ForegroundColor White

Write-Host "`nResults:" -ForegroundColor Cyan
Write-Host "  results/training_metrics_*.json" -ForegroundColor White
Write-Host "  results/evaluation_report_*.json" -ForegroundColor White
Write-Host "  results/validation_report_*.json" -ForegroundColor White

Write-Host "`nDone!" -ForegroundColor Green
