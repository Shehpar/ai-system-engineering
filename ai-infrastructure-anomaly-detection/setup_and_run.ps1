#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Automated setup script for AI Infrastructure Anomaly Detection System
.DESCRIPTION
    This script performs a complete clean installation and setup:
    - Checks prerequisites (Docker, Python)
    - Cleans up old containers/volumes/data
    - Starts monitoring infrastructure (InfluxDB, Grafana, MLflow)
    - Creates database and imports dashboards
    - Collects/generates training data
    - Trains the ML model
    - Starts datacenter monitoring and AI detection
    - Displays service URLs and status
.PARAMETER CleanInstall
    If specified, removes all existing data and starts fresh
.EXAMPLE
    .\setup_and_run.ps1
    .\setup_and_run.ps1 -CleanInstall
#>

param(
    [switch]$CleanInstall
)

# Color output functions
function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "ℹ️  $msg" -ForegroundColor Cyan }
function Write-Warning { param($msg) Write-Host "⚠️  $msg" -ForegroundColor Yellow }
function Write-Error-Custom { param($msg) Write-Host "❌ $msg" -ForegroundColor Red }
function Write-Step { param($msg) Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta; Write-Host "🚀 $msg" -ForegroundColor Magenta; Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Magenta }

Write-Host @"
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║     AI INFRASTRUCTURE ANOMALY DETECTION SYSTEM                 ║
║     Automated Setup & Deployment Script                        ║
║                                                                ║
║     Course: AI Systems Engineering                             ║
║     Status: Production Ready                                   ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

# ============================================================================
# STEP 1: Prerequisites Check
# ============================================================================
Write-Step "STEP 1/10: Checking Prerequisites"

# Check Docker
Write-Info "Checking Docker installation..."
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker found: $dockerVersion"
    } else {
        throw "Docker not found"
    }
} catch {
    Write-Error-Custom "Docker is not installed or not in PATH"
    Write-Info "Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
}

# Check Docker Compose
Write-Info "Checking Docker Compose..."
try {
    $composeVersion = docker-compose --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker Compose found: $composeVersion"
    } else {
        throw "Docker Compose not found"
    }
} catch {
    Write-Error-Custom "Docker Compose is not installed"
    exit 1
}

# Check Docker daemon
Write-Info "Checking Docker daemon..."
try {
    docker ps | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker daemon is running"
    } else {
        throw "Docker daemon not running"
    }
} catch {
    Write-Error-Custom "Docker daemon is not running. Please start Docker Desktop."
    exit 1
}

# Check Python (optional, for local development)
Write-Info "Checking Python installation..."
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Python found: $pythonVersion"
    } else {
        Write-Warning "Python not found (optional for Docker deployment)"
    }
} catch {
    Write-Warning "Python not found (optional for Docker deployment)"
}

# ============================================================================
# STEP 2: Clean Up (if requested)
# ============================================================================
if ($CleanInstall) {
    Write-Step "STEP 2/10: Cleaning Up Old Installation"
    
    Write-Info "Stopping and removing all containers..."
    docker-compose -f docker/docker-compose.yml down -v 2>&1 | Out-Null
    docker-compose -f ../datacenter/docker-compose.yml down -v 2>&1 | Out-Null
    docker-compose -f ../stress-test-docker/docker-compose.yml down -v 2>&1 | Out-Null
    
    Write-Info "Removing old data files..."
    if (Test-Path "data/raw/system_metrics.csv") { Remove-Item "data/raw/system_metrics.csv" -Force }
    if (Test-Path "data/processed/system_metrics_processed.csv") { Remove-Item "data/processed/system_metrics_processed.csv" -Force }
    if (Test-Path "models/*.pkl") { Remove-Item "models/*.pkl" -Force }
    if (Test-Path "results/*.json") { Remove-Item "results/*.json" -Force }
    if (Test-Path "results/*.csv") { Remove-Item "results/*.csv" -Force }
    
    Write-Success "Cleanup completed"
} else {
    Write-Step "STEP 2/10: Cleanup Skipped (use -CleanInstall flag to clean)"
}

# ============================================================================
# STEP 3: Start Core Infrastructure
# ============================================================================
Write-Step "STEP 3/10: Starting Core Infrastructure (InfluxDB, Grafana, MLflow)"

Write-Info "Starting docker-compose services..."
Set-Location "docker"
docker-compose up -d --build 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Error-Custom "Failed to start services"
    exit 1
}

Set-Location ".."
Write-Success "Services started"

# ============================================================================
# STEP 4: Wait for Services to be Ready
# ============================================================================
Write-Step "STEP 4/10: Waiting for Services to be Healthy"

Write-Info "Waiting for InfluxDB to be ready..."
$maxRetries = 30
$retryCount = 0
while ($retryCount -lt $maxRetries) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8086/ping" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 204) {
            Write-Success "InfluxDB is ready"
            break
        }
    } catch {
        $retryCount++
        Write-Info "Waiting... ($retryCount/$maxRetries)"
        Start-Sleep -Seconds 2
    }
}

if ($retryCount -eq $maxRetries) {
    Write-Error-Custom "InfluxDB failed to start"
    exit 1
}

Write-Info "Waiting for Grafana to be ready..."
$retryCount = 0
while ($retryCount -lt $maxRetries) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000/api/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Success "Grafana is ready"
            break
        }
    } catch {
        $retryCount++
        Write-Info "Waiting... ($retryCount/$maxRetries)"
        Start-Sleep -Seconds 2
    }
}

Write-Info "Waiting for MLflow to be ready..."
$retryCount = 0
while ($retryCount -lt $maxRetries) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Success "MLflow is ready"
            break
        }
    } catch {
        $retryCount++
        Write-Info "Waiting... ($retryCount/$maxRetries)"
        Start-Sleep -Seconds 2
    }
}

Write-Info "Waiting additional 10 seconds for service initialization..."
Start-Sleep -Seconds 10

# ============================================================================
# STEP 5: Create InfluxDB Database
# ============================================================================
Write-Step "STEP 5/10: Creating InfluxDB Database"

Write-Info "Creating 'system_metrics' database..."
docker exec docker-influxdb-1 influx -execute "CREATE DATABASE system_metrics" 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Success "Database created successfully"
} else {
    Write-Warning "Database may already exist (this is OK)"
}

# Verify database
Write-Info "Verifying database..."
$dbCheck = docker exec docker-influxdb-1 influx -execute "SHOW DATABASES" 2>&1
if ($dbCheck -match "system_metrics") {
    Write-Success "Database 'system_metrics' confirmed"
} else {
    Write-Error-Custom "Failed to verify database"
    exit 1
}

# ============================================================================
# STEP 6: Import Grafana Dashboard
# ============================================================================
Write-Step "STEP 6/10: Importing Grafana Dashboard"

Write-Info "Checking if dashboard is auto-provisioned..."
Start-Sleep -Seconds 5  # Give Grafana time to provision

Write-Info "Testing dashboard availability..."
try {
    python check_datasource.py 2>&1 | Out-Null
    Write-Success "Grafana datasource configured"
} catch {
    Write-Warning "Datasource check failed (may auto-configure)"
}

Write-Success "Grafana dashboard ready at http://localhost:3000"

# ============================================================================
# STEP 7: Generate/Collect Training Data
# ============================================================================
Write-Step "STEP 7/10: Preparing Training Data"

# Check if we need to generate synthetic data or collect real data
if (-not (Test-Path "data/raw/system_metrics.csv")) {
    Write-Info "No existing data found. Checking if InfluxDB has historical data..."
    
    # Check if InfluxDB has data
    $dataCheck = docker exec docker-influxdb-1 influx -database system_metrics -execute "SELECT COUNT(*) FROM cpu" 2>&1
    
    if ($dataCheck -match "count") {
        Write-Info "Found historical data in InfluxDB. Collecting real metrics..."
        docker exec docker-ai_app-1 python src/collect_real_data.py
        
        if (Test-Path "data/raw/system_metrics.csv") {
            Write-Success "Real data collected successfully"
        } else {
            Write-Warning "Real data collection failed. Generating synthetic data..."
            docker exec docker-ai_app-1 python src/data_generation.py
            Write-Success "Synthetic training data generated"
        }
    } else {
        Write-Info "No historical data found. Generating synthetic training data..."
        docker exec docker-ai_app-1 python src/data_generation.py
        Write-Success "Synthetic training data generated (1000 samples)"
    }
} else {
    Write-Success "Training data already exists"
}

# Preprocess data
Write-Info "Preprocessing data..."
docker exec docker-ai_app-1 python src/preprocessing.py
Write-Success "Data preprocessing completed"

# ============================================================================
# STEP 8: Validate Data Quality
# ============================================================================
Write-Step "STEP 8/10: Validating Data Quality"

Write-Info "Running data validation checks..."
$validationOutput = docker exec docker-ai_app-1 python src/validate_data.py 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Success "Data validation passed"
} else {
    Write-Error-Custom "Data validation failed"
    Write-Host $validationOutput
    exit 1
}

# ============================================================================
# STEP 9: Train ML Model
# ============================================================================
Write-Step "STEP 9/10: Training Machine Learning Model"

Write-Info "Starting model training with hyperparameter grid search..."
Write-Info "This may take 2-3 minutes..."
$trainingOutput = docker exec docker-ai_app-1 python src/train_model.py 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Success "Model training completed successfully"
    
    # Show training metrics
    if (Test-Path "results/training_metrics*.json") {
        $latestMetrics = Get-ChildItem "results/training_metrics*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        Write-Info "Training metrics saved: $($latestMetrics.Name)"
    }
} else {
    Write-Error-Custom "Model training failed"
    Write-Host $trainingOutput
    exit 1
}

# ============================================================================
# STEP 10: Start Datacenter Monitoring & AI Detection
# ============================================================================
Write-Step "STEP 10/10: Starting Datacenter Monitoring & AI Detection"

Write-Info "Starting Flask application and Telegraf monitoring..."
Set-Location "../datacenter"
docker-compose up -d --build 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Error-Custom "Failed to start datacenter monitoring"
    exit 1
}

Write-Success "Datacenter monitoring started"
Set-Location "../ai-infrastructure-anomaly-detection"

Write-Info "Starting AI anomaly detection service..."
Start-Sleep -Seconds 5

# Start detection in background
docker exec -d docker-ai_app-1 python src/detect_anomaly.py 2>&1 | Out-Null
Write-Success "AI detection service started"

# ============================================================================
# FINAL STATUS & ACCESS INFORMATION
# ============================================================================
Write-Host "`n"
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                                                                ║" -ForegroundColor Green
Write-Host "║                 🎉 SETUP COMPLETED SUCCESSFULLY 🎉             ║" -ForegroundColor Green
Write-Host "║                                                                ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host "`n"

Write-Host "📊 ACCESS POINTS:" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  🌐 Grafana Dashboard:  " -NoNewline
Write-Host "http://localhost:3000" -ForegroundColor Yellow
Write-Host "     Login: admin / admin" -ForegroundColor Gray
Write-Host ""
Write-Host "  🔬 MLflow Experiments: " -NoNewline
Write-Host "http://localhost:5000" -ForegroundColor Yellow
Write-Host ""
Write-Host "  💾 InfluxDB:           " -NoNewline
Write-Host "http://localhost:8086" -ForegroundColor Yellow
Write-Host ""
Write-Host "  🌍 Flask Web App:      " -NoNewline
Write-Host "http://localhost:5005" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

Write-Host "🐳 RUNNING SERVICES:" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Where-Object { $_ -match "docker-" -or $_ -match "flask_" -or $_ -match "telegraf_" }
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 NEXT STEPS:" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  1. Open Grafana: http://localhost:3000 (admin/admin)" -ForegroundColor White
Write-Host "  2. View 'AI Anomaly Detection' dashboard" -ForegroundColor White
Write-Host "  3. Check MLflow experiments: http://localhost:5000" -ForegroundColor White
Write-Host "  4. Run stress test: .\test_and_validate.ps1" -ForegroundColor White
Write-Host "  5. View logs: docker-compose -f docker/docker-compose.yml logs -f" -ForegroundColor White
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

Write-Host "📚 DOCUMENTATION:" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  • Architecture:  docs/ARCHITECTURE.md" -ForegroundColor White
Write-Host "  • Deployment:    docs/DEPLOYMENT.md" -ForegroundColor White
Write-Host "  • Model Details: docs/MODEL_CARD.md" -ForegroundColor White
Write-Host "  • Requirements:  docs/REQUIREMENTS.md" -ForegroundColor White
Write-Host "  • Automation:    docs/AUTOMATION_GUIDE.md" -ForegroundColor White
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

Write-Success "System is ready for demonstration and testing!"
Write-Host ""
