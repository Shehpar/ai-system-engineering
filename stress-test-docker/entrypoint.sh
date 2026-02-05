#!/bin/bash

echo "=== HTTP LOAD GENERATOR - DoS SIMULATION ==="
echo "Target: Flask Server (http://host.docker.internal:5005)"
echo "Mode: High traffic simulation"
echo ""
echo "This will send many HTTP requests to Flask to simulate:"
echo "  - High user traffic"
echo "  - DoS attack scenario"
echo "  - Network stress"
echo ""
echo "Watch Grafana to see Flask container metrics spike!"
echo "Press Ctrl+C to stop"
echo ""

# Run HTTP load generator to attack Flask server
python3 /app/http_load_generator.py
  --timeout 0 \
  --verbose \
  --metrics
