# Stress Test Docker

Quick stress testing container to generate CPU/memory load for anomaly detection testing.

## Quick Start

### Option 1: Docker Desktop GUI
1. Open Docker Desktop
2. Navigate to `stress-test-docker` folder
3. Click "Build" to create the image
4. Click "Run" to start the stress test
5. Watch the logs in Docker Desktop
6. Check Grafana dashboard for anomaly detection

### Option 2: Command Line

```bash
cd stress-test-docker

# Build the image
docker-compose build stress-test

# Run the stress test
docker-compose up

# To stop (Ctrl+C or in another terminal):
docker-compose down
```

## What It Does

- **CPU Stress**: 4 threads computing intensive calculations
- **Memory Stress**: Allocates ~500MB and holds it
- **Logs**: Real-time CPU%, memory% to Docker Desktop

## Monitor Anomalies

While stress is running:
1. Open Grafana: http://localhost:3000
2. Watch the CPU/Memory panels spike
3. Watch the "Anomaly Predictions" panel for anomaly detection (after 2 minutes)
4. Watch "Anomaly Throughput" counter increase

## Customize Stress

Edit `stress.py` to change:
- `cpu_percent=80` - Target CPU usage
- `memory_mb=500` - Memory allocation size
- `duration=None` - Run time in seconds (None = infinite)
- `cpu_threads=4` - Number of CPU stress threads

## Stop Stress

- Press `Ctrl+C` in terminal, or
- Click "Stop" in Docker Desktop, or
- Run: `docker-compose down`
