"""
Collect Real System Data from InfluxDB
=======================================
This script extracts actual system metrics from InfluxDB to use for model training
instead of synthetic data. This ensures the model learns from real baseline behavior.
"""

import pandas as pd
import os
from influxdb import InfluxDBClient
from datetime import datetime

# Configuration
INFLUXDB_HOST = os.getenv("INFLUXDB_HOST", "influxdb")
INFLUXDB_PORT = int(os.getenv("INFLUXDB_PORT", "8086"))
INFLUXDB_DATABASE = "system_metrics"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_DIR, "data/raw/system_metrics.csv")

# Ensure directory exists
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

# Connect to InfluxDB
client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT, database=INFLUXDB_DATABASE)

print("Collecting real system data from InfluxDB...")

# Query for CPU data
cpu_query = '''
SELECT mean("usage_idle") as cpu_idle
FROM "cpu"
WHERE time > now() - 24h
GROUP BY time(30s)
fill(null)
'''

# Query for Memory data
mem_query = '''
SELECT mean("used_percent") as mem_used
FROM "mem"
WHERE time > now() - 24h
GROUP BY time(30s)
fill(null)
'''

# Query for Network data
net_query = '''
SELECT mean("bytes_recv") as bytes_in
FROM "net"
WHERE time > now() - 24h
GROUP BY time(30s)
fill(null)
'''

# Execute queries
cpu_result = list(client.query(cpu_query).get_points())
mem_result = list(client.query(mem_query).get_points())
net_result = list(client.query(net_query).get_points())

print(f"Retrieved {len(cpu_result)} CPU samples")
print(f"Retrieved {len(mem_result)} memory samples")
print(f"Retrieved {len(net_result)} network samples")

# Convert to DataFrames
cpu_df = pd.DataFrame(cpu_result)
mem_df = pd.DataFrame(mem_result)
net_df = pd.DataFrame(net_result)

# Calculate CPU usage from idle
if not cpu_df.empty and 'cpu_idle' in cpu_df.columns:
    cpu_df['cpu_usage'] = 100 - cpu_df['cpu_idle']
    cpu_df['time'] = pd.to_datetime(cpu_df['time'])
else:
    print("ERROR: No CPU data found")
    exit(1)

# Rename memory column
if not mem_df.empty and 'mem_used' in mem_df.columns:
    mem_df['memory_usage'] = mem_df['mem_used']
    mem_df['time'] = pd.to_datetime(mem_df['time'])
else:
    print("ERROR: No memory data found")
    exit(1)

# Calculate network rate
if not net_df.empty and 'bytes_in' in net_df.columns:
    net_df['time'] = pd.to_datetime(net_df['time'])
    net_df = net_df.sort_values('time')
    
    # Calculate rate as bytes per second (difference between consecutive samples)
    net_df['network_load'] = net_df['bytes_in'].diff() / 30.0  # 30 second intervals
    net_df['network_load'] = net_df['network_load'].fillna(0)
    net_df['network_load'] = net_df['network_load'].clip(lower=0)  # Remove negative values
else:
    print("ERROR: No network data found")
    exit(1)

# Merge all three DataFrames on time
merged_df = cpu_df[['time', 'cpu_usage']].merge(
    mem_df[['time', 'memory_usage']], 
    on='time', 
    how='inner'
).merge(
    net_df[['time', 'network_load']], 
    on='time', 
    how='inner'
)

# Remove any rows with NaN values
merged_df = merged_df.dropna()

# Add anomaly column (all zeros for normal baseline data)
merged_df['anomaly'] = 0

# Select only the required columns
final_df = merged_df[['cpu_usage', 'memory_usage', 'network_load', 'anomaly']]

# Save to CSV
final_df.to_csv(OUTPUT_PATH, index=False)

print(f"\n✅ Successfully saved {len(final_df)} real system samples to {OUTPUT_PATH}")
print(f"\nData statistics:")
print(f"  CPU usage: {final_df['cpu_usage'].mean():.2f}% (±{final_df['cpu_usage'].std():.2f}%)")
print(f"  Memory usage: {final_df['memory_usage'].mean():.2f}% (±{final_df['memory_usage'].std():.2f}%)")
print(f"  Network load: {final_df['network_load'].mean():.2f} bytes/s (±{final_df['network_load'].std():.2f} bytes/s)")
print(f"\nNext step: Run preprocessing.py and train_model.py to retrain with real data")
