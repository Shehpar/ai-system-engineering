#!/usr/bin/env python
import requests
import json

# Get datasource details
response = requests.get(
    'http://localhost:3000/api/datasources/uid/influxdb',
    auth=('admin', 'admin')
)

ds = response.json()
print('Datasource Configuration:')
print(f'  Name: {ds.get("name")}')
print(f'  Type: {ds.get("type")}')
print(f'  URL: {ds.get("url")}')
print(f'  Database: {ds.get("database")}')
print(f'  Enabled: {ds.get("enabled")}')
print(f'  Access: {ds.get("access")}')
print(f'  HTTP Method: {ds.get("jsonData", {}).get("httpMethod", "GET")}')
print(f'  UID: {ds.get("uid")}')
print(f'  Is Default: {ds.get("isDefault")}')

# Now test a query through Grafana's query endpoint
print('\n=== Testing Query through Grafana ===')
payload = {
    "datasourceUid": "influxdb",
    "maxDataPoints": 43200,
    "intervalMs": 1000,
    "queries": [
        {
            "refId": "A",
            "queryType": "",
            "model": {
                "datasource": {
                    "uid": "influxdb",
                    "type": "influxdb"
                },
                "params": [
                    "system_metrics",
                    "SELECT mean(\"usage_idle\") FROM \"cpu\" WHERE $timeFilter GROUP BY time($__interval) fill(null)"
                ],
                "targets": [
                    {
                        "datasource": {
                            "uid": "influxdb",
                            "type": "influxdb"
                        },
                        "refId": "A",
                        "query": "SELECT mean(\"usage_idle\") FROM \"cpu\" WHERE \"time\" > now() - 6h GROUP BY time(30s) fill(null)"
                    }
                ]
            }
        }
    ],
    "range": {
        "from": "now-6h",
        "to": "now"
    }
}

response = requests.post(
    'http://localhost:3000/api/ds/query',
    json=payload,
    auth=('admin', 'admin'),
    headers={'Content-Type': 'application/json'}
)

print(f'Query Response Status: {response.status_code}')
if response.status_code == 200:
    result = response.json()
    print('Results:')
    print(json.dumps(result, indent=2)[:500])
else:
    print(f'Error: {response.text[:500]}')
