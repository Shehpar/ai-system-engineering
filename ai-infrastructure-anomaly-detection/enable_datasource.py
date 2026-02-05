#!/usr/bin/env python
import requests
import json

# Get current datasource
print("Fetching datasource configuration...")
response = requests.get(
    'http://localhost:3000/api/datasources/uid/influxdb',
    auth=('admin', 'admin')
)

ds = response.json()
print(f'Current enabled state: {ds.get("enabled", "unknown")}')

# Update datasource to enable it
ds['enabled'] = True
print("Enabling datasource...")
response = requests.put(
    'http://localhost:3000/api/datasources/uid/influxdb',
    json=ds,
    auth=('admin', 'admin'),
    headers={'Content-Type': 'application/json'}
)

if response.status_code == 200:
    result = response.json()
    print('✅ Datasource enabled successfully!')
    print(f'Message: {result.get("message", "OK")}')
    
    # Verify it's enabled
    response = requests.get(
        'http://localhost:3000/api/datasources/uid/influxdb',
        auth=('admin', 'admin')
    )
    ds = response.json()
    print(f'New enabled state: {ds.get("enabled")}')
else:
    print(f'❌ Error: {response.status_code}')
    print(response.text)
