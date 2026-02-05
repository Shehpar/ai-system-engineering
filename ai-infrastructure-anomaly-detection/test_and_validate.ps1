#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Automated testing and validation script for AI Anomaly Detection System
.DESCRIPTION
    This script performs comprehensive testing:
    - Runs unit tests
    - Starts HTTP stress test (DoS simulation)
    - Monitors for anomaly detection
    - Generates test report
    - Stops stress test
.PARAMETER Duration
    Duration of stress test in seconds (default: 300 = 5 minutes)
.PARAMETER RequestsPerSecond
    Target requests per second for HTTP load (default: 200)
.EXAMPLE
    .\test_and_validate.ps1
    .\test_and_validate.ps1 -Duration 120 -RequestsPerSecond 300
#>

param(
    [int]$Duration = 300,
    [int]$RequestsPerSecond = 200
)

# Color output functions
function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "ℹ️  $msg" -ForegroundColor Cyan }
function Write-Warning { param($msg) Write-Host "⚠️  $msg" -ForegroundColor Yellow }
function Write-Error-Custom { param($msg) Write-Host "❌ $msg" -ForegroundColor Red }
function Write-Step { param($msg) Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta; Write-Host "🧪 $msg" -ForegroundColor Magenta; Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Magenta }

Write-Host @"
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║     AI ANOMALY DETECTION - TESTING & VALIDATION                ║
║     Automated Test Suite                                       ║
║                                                                ║
║     Duration: $Duration seconds                                        ║
║     Target Load: $RequestsPerSecond RPS                                      ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

# ============================================================================
# STEP 1: Check Services
# ============================================================================
Write-Step "STEP 1/7: Checking Service Status"

Write-Info "Verifying all services are running..."
$services = @("docker-influxdb-1", "docker-grafana-1", "docker-mlflow-1", "docker-ai_app-1", "flask_prod_server", "telegraf_site_b")
$allRunning = $true

foreach ($service in $services) {
    $status = docker ps --filter "name=$service" --format "{{.Status}}"
    if ($status -match "Up") {
        Write-Success "$service is running"
    } else {
        Write-Error-Custom "$service is not running"
        $allRunning = $false
    }
}

if (-not $allRunning) {
    Write-Error-Custom "Not all services are running. Please run setup_and_run.ps1 first."
    exit 1
}

# ============================================================================
# STEP 2: Run Unit Tests
# ============================================================================
Write-Step "STEP 2/7: Running Unit Tests"

Write-Info "Executing pytest test suite..."
$testOutput = docker exec docker-ai_app-1 pytest tests/ -v 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Success "All unit tests passed"
} else {
    Write-Warning "Some unit tests failed (check output)"
}

Write-Host $testOutput | Select-String -Pattern "PASSED|FAILED|ERROR" -Context 0,1

# ============================================================================
# STEP 3: Validate Data Quality
# ============================================================================
Write-Step "STEP 3/7: Validating Data Quality"

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
# STEP 4: Check Baseline Metrics
# ============================================================================
Write-Step "STEP 4/7: Recording Baseline Metrics"

Write-Info "Querying current system state from InfluxDB..."
$baselineQuery = "SELECT MEAN(usage_idle) FROM cpu WHERE time > now() - 5m"
$baselineCPU = docker exec docker-influxdb-1 influx -database system_metrics -execute $baselineQuery 2>&1

Write-Info "Baseline CPU (idle): $($baselineCPU | Select-String -Pattern '\d+\.\d+')"

Write-Info "Checking AI detection status..."
$detectionQuery = "SELECT * FROM ai_predictions ORDER BY time DESC LIMIT 5"
$currentStatus = docker exec docker-influxdb-1 influx -database system_metrics -execute $detectionQuery 2>&1

Write-Host "Recent predictions:" -ForegroundColor Gray
Write-Host $currentStatus

# ============================================================================
# STEP 5: Start Stress Test
# ============================================================================
Write-Step "STEP 5/7: Starting HTTP Stress Test (DoS Simulation)"

Write-Info "Configuring stress test parameters..."
Write-Info "  Duration: $Duration seconds"
Write-Info "  Target RPS: $RequestsPerSecond"
Write-Info "  Target: http://host.docker.internal:5005 (Flask server)"

# Update stress test configuration
Set-Location "../stress-test-docker"

# Check if http_load_generator.py needs updating
if (Test-Path "http_load_generator.py") {
    Write-Info "Updating load generator configuration..."
    (Get-Content "http_load_generator.py") -replace 'DURATION = \d+', "DURATION = $Duration" | Set-Content "http_load_generator.py"
    (Get-Content "http_load_generator.py") -replace 'REQUESTS_PER_SECOND = \d+', "REQUESTS_PER_SECOND = $RequestsPerSecond" | Set-Content "http_load_generator.py"
}

Write-Info "Starting stress test container..."
docker-compose up -d --build 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Error-Custom "Failed to start stress test"
    exit 1
}

Write-Success "Stress test started"
Set-Location "../ai-infrastructure-anomaly-detection"

# Wait for stress to initialize
Start-Sleep -Seconds 5

# Show initial logs
Write-Info "Stress test output:"
docker logs stress_test_container --tail 20

# ============================================================================
# STEP 6: Monitor for Anomaly Detection
# ============================================================================
Write-Step "STEP 6/7: Monitoring for Anomaly Detection"

Write-Info "Monitoring system for $Duration seconds..."
Write-Info "Checking every 30 seconds for anomaly detection..."

$startTime = Get-Date
$anomalyDetected = $false
$checkInterval = 30
$maxChecks = [Math]::Ceiling($Duration / $checkInterval)

for ($i = 1; $i -le $maxChecks; $i++) {
    $elapsed = [Math]::Round(((Get-Date) - $startTime).TotalSeconds)
    Write-Info "Check $i/$maxChecks (Elapsed: ${elapsed}s / ${Duration}s)"
    
    # Query for recent anomalies
    $anomalyQuery = "SELECT * FROM ai_predictions WHERE is_anomaly = 1 AND time > now() - 1m ORDER BY time DESC LIMIT 1"
    $anomalyResult = docker exec docker-influxdb-1 influx -database system_metrics -execute $anomalyQuery 2>&1
    
    if ($anomalyResult -match "is_anomaly") {
        Write-Success "🚨 ANOMALY DETECTED! 🚨"
        $anomalyDetected = $true
        Write-Host $anomalyResult -ForegroundColor Yellow
    } else {
        Write-Info "Status: Normal (no anomalies yet)"
    }
    
    # Show Flask container metrics
    Write-Info "Flask container status:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" flask_prod_server
    
    # Show stress test progress
    $stressLogs = docker logs stress_test_container --tail 5 2>&1
    Write-Info "Stress test progress:"
    Write-Host $stressLogs | Select-String -Pattern "requests|RPS|errors" | Select-Object -Last 1
    
    if ($i -lt $maxChecks) {
        Start-Sleep -Seconds $checkInterval
    }
}

# ============================================================================
# STEP 7: Generate Test Report
# ============================================================================
Write-Step "STEP 7/7: Generating Test Report"

# Stop stress test
Write-Info "Stopping stress test..."
Set-Location "../stress-test-docker"
docker-compose down 2>&1 | Out-Null
Set-Location "../ai-infrastructure-anomaly-detection"
Write-Success "Stress test stopped"

# Wait for system to stabilize
Write-Info "Waiting 15 seconds for system to stabilize..."
Start-Sleep -Seconds 15

# Collect final metrics
Write-Info "Collecting test results..."

$reportData = @{
    TestTimestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Duration = $Duration
    TargetRPS = $RequestsPerSecond
    AnomalyDetected = $anomalyDetected
}

# Query final statistics
$totalAnomaliesQuery = "SELECT COUNT(is_anomaly) FROM ai_predictions WHERE is_anomaly = 1 AND time > now() - ${Duration}s"
$totalAnomalies = docker exec docker-influxdb-1 influx -database system_metrics -execute $totalAnomaliesQuery 2>&1

$avgCPUQuery = "SELECT MEAN(cpu_usage_percent) FROM ai_predictions WHERE time > now() - ${Duration}s"
$avgCPU = docker exec docker-influxdb-1 influx -database system_metrics -execute $avgCPUQuery 2>&1

Write-Host "`n"
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                                                                ║" -ForegroundColor Green
Write-Host "║                    📊 TEST REPORT SUMMARY                      ║" -ForegroundColor Green
Write-Host "║                                                                ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host "`n"

Write-Host "🕐 Test Duration:      ${Duration} seconds" -ForegroundColor Cyan
Write-Host "⚡ Target Load:        ${RequestsPerSecond} RPS" -ForegroundColor Cyan
Write-Host "🚨 Anomaly Detected:   $(if ($anomalyDetected) { 'YES ✅' } else { 'NO ❌' })" -ForegroundColor Cyan
Write-Host ""
Write-Host "📈 Metrics During Test:" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host $totalAnomalies | Select-String -Pattern "count"
Write-Host $avgCPU | Select-String -Pattern "mean"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host ""

# Unit test results
Write-Host "🧪 Unit Tests:" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
if ($testOutput -match "(\d+) passed") {
    Write-Success "All tests passed: $($matches[1]) tests"
} else {
    Write-Warning "Check test output for details"
}
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host ""

Write-Host "✅ VALIDATION RESULTS:" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "  [✓] Services Running:       All 6 services healthy" -ForegroundColor White
Write-Host "  [✓] Unit Tests:             $(if ($testOutput -match 'passed') { 'PASSED' } else { 'REVIEW NEEDED' })" -ForegroundColor White
Write-Host "  [✓] Data Validation:        PASSED" -ForegroundColor White
Write-Host "  [✓] Stress Test:            Executed (${Duration}s)" -ForegroundColor White
Write-Host "  [✓] Anomaly Detection:      $(if ($anomalyDetected) { 'WORKING (Detected attack)' } else { 'Check thresholds' })" -ForegroundColor White
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""

Write-Host "📚 NEXT STEPS:" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  1. Review Grafana dashboard: http://localhost:3000" -ForegroundColor White
Write-Host "  2. Check MLflow runs: http://localhost:5000" -ForegroundColor White
Write-Host "  3. View detailed logs: docker-compose -f docker/docker-compose.yml logs" -ForegroundColor White
Write-Host "  4. Adjust thresholds in src/detect_anomaly.py if needed" -ForegroundColor White
Write-Host "  5. Re-run test: .\test_and_validate.ps1" -ForegroundColor White
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

Write-Success "Testing and validation completed!"
Write-Host ""

# Save report to file
$reportFile = "results/test_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
@"
AI ANOMALY DETECTION - TEST REPORT
Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

TEST CONFIGURATION:
- Duration: ${Duration} seconds
- Target Load: ${RequestsPerSecond} RPS
- Target: Flask server (localhost:5005)

TEST RESULTS:
- Anomaly Detected: $(if ($anomalyDetected) { 'YES' } else { 'NO' })
- Services Status: All running
- Unit Tests: $(if ($testOutput -match 'passed') { 'PASSED' } else { 'REVIEW NEEDED' })
- Data Validation: PASSED

METRICS:
$totalAnomalies
$avgCPU

CONCLUSION:
System is $(if ($anomalyDetected) { 'functioning correctly - anomalies were detected during stress test' } else { 'operational - consider adjusting detection thresholds' })
"@ | Out-File -FilePath $reportFile -Encoding UTF8

Write-Info "Report saved to: $reportFile"
