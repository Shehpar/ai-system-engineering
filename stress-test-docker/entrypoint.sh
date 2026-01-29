#!/bin/bash

echo "=== LIGHT STRESS TEST STARTING ==="
echo "CPU Threads: 1 (10% target)"
echo "Memory Stress: 128MB"
echo "Duration: Infinite (press Ctrl+C to stop)"
echo ""

# Run stress-ng for LIGHT CPU/memory stress
# --cpu 1: 1 CPU worker
# --cpu-load 10: target ~10% CPU
# --vm 1: 1 memory worker
# --vm-bytes 128M: 128MB allocation
# --timeout 0: infinite
# --verbose: show output
stress-ng \
  --cpu 1 \
  --cpu-load 10 \
  --vm 1 \
  --vm-bytes 128M \
  --timeout 0 \
  --verbose \
  --metrics
