---
title: "Python Automation: VictoriaMetrics & VictoriaLogs"
category: "python"
date: "2026-04-11T14:15:00.000Z"
author: "Admin"
---

VictoriaMetrics and VictoriaLogs are high-performance, cost-effective alternatives to standard PromQL/Elasticsearch observability backends. Because their architecture relies heavily on highly efficient, stateless HTTP APIs for ingestion and querying, Python serves as an incredible automation wrapper for scraping, verifying, and reporting across these endpoints.

In this tutorial, we will execute 6 common Python tasks specifically tailored for managing and maintaining a Victoria observability suite. Every step follows our strict standard: explaining the technical rationale, displaying data payloads, dissecting the script line-by-line, and rendering the simulated standard output.

---

### Task 1: Push/query time-series or log data through HTTP APIs

**Why use this logic?** VictoriaMetrics allows for extremely rapid data backfilling over HTTP. If a legacy pipeline generates historical CSV performance data, Python's `requests` can instantly dump thousands of historical time-series datapoints straight into the database via the `/api/v1/import` native API, securely bridging old and new architectures.

**Example Log (VictoriaMetrics JSONLine Ingestion):**
`{"metric": {"__name__": "legacy_cpu"}, "values": [45], "timestamps": [1680000000]}`

**Python Script:**
```python
import json

def push_victoria_metrics_payload(target_api_url, historical_data_list):
    # 1. Structure the endpoint for VictoriaMetrics JSON-Line bulk ingestion
    bulk_ingest_path = f"{target_api_url}/api/v1/import"
    
    # 2. Iterate through Python dictionary entries to generate Victoria-friendly JSON payloads
    payload_lines = []
    for entry in historical_data_list:
        vm_dict = {
            "metric": {"__name__": entry["metric_name"], "source": "python_import"},
            "values": [entry["value"]],
            "timestamps": [entry["epoch"]]  # Unix timestamp required
        }
        # JSON line formatting dictates raw JSON dicts separated by \n, not a JSON array
        payload_lines.append(json.dumps(vm_dict))
        
    payload_string = "\n".join(payload_lines)
    
    # 3. Simulate HTTP POST operation
    # In reality: requests.post(bulk_ingest_path, data=payload_string)
    
    return f"Prepared bulk HTTP POST to [{bulk_ingest_path}]\nData structure injected:\n{payload_string[:150]}..."

legacy_csv = [
    {"metric_name": "app_latency", "value": 450, "epoch": 1680000000},
    {"metric_name": "app_latency", "value": 120, "epoch": 1680000010}
]

print(push_victoria_metrics_payload("http://victoria.cluster.local:8428", legacy_csv))
```

**Output of the script:**
```text
Prepared bulk HTTP POST to [http://victoria.cluster.local:8428/api/v1/import]
Data structure injected:
{"metric": {"__name__": "app_latency", "source": "python_import"}, "values": [450], "timestamps": [1680000000]}
{"metric": {"__name__": "app_latency...
```

---

### Task 2: Run scheduled health checks for ingestion endpoints

**Why use this logic?** VictoriaMetrics/Logs rely unconditionally on target ports (`8428` for metrics, `9428` for logs). If networking firewall rules change dynamically, ingest stops silently. Automating a script to execute a quick query-ping or `/health` check guarantees rapid cluster viability tracking.

**Example Log (Network URLs):**
`["http://vm-insert:8428", "http://vl-insert:9428"]`

**Python Script:**
```python
def check_victoria_liveness(endpoints):
    report = []
    
    # 1. Iterate over cluster storage nodes
    for endpoint in endpoints:
        health_path = f"{endpoint}/health"
        
        # 2. Emulate an HTTP GET validation
        is_reachable = "offline" not in endpoint
        
        # 3. Handle status return logic structurally
        if is_reachable:
            report.append(f"🟢 [UP] Victoria backend responsive at {health_path}")
        else:
            report.append(f"🔴 [DOWN] Connection timed out connecting to {health_path}")
            
    return "\n".join(report)

victoria_nodes = [
    "http://victoria-insert-01.data.svc:8428",
    "http://victoria-insert-02.data.svc_offline:8428", # Simulated dead node
    "http://victoria-logs-01.logs.svc:9428"
]

print(check_victoria_liveness(victoria_nodes))
```

**Output of the script:**
```text
🟢 [UP] Victoria backend responsive at http://victoria-insert-01.data.svc:8428/health
🔴 [DOWN] Connection timed out connecting to http://victoria-insert-02.data.svc_offline:8428/health
🟢 [UP] Victoria backend responsive at http://victoria-logs-01.logs.svc:9428/health
```

---

### Task 3: Detect missing series or missing log streams

**Why use this logic?** High-performance storage is useless if clients stop writing to it. Creating a Python query sequence that specifically retrieves a list of explicitly required metric series (`auth_service_cpu`) and raises an alert if VictoriaMetrics returns `0` series guards against silent application telemetry failure.

**Example Log (Query result list):**
`["payments_revenue", "db_pool"]` vs Schema `["payments_revenue", "db_pool", "auth_cpu"]`

**Python Script:**
```python
def detect_missing_storage_series(active_series_array, required_series_schema):
    missing_streams = []
    
    # 1. Cross-reference expected application series against database reality
    for required_name in required_series_schema:
        if required_name not in active_series_array:
            missing_streams.append(required_name)
            
    # 2. Logic gate checking for dropped streams
    if missing_streams:
        # 3. Create an actionable remediation alert
        return f"CRITICAL: VictoriaMetrics dropped data streams! The following series are silent: {missing_streams}"
        
    return "All critical data streams are actively being ingested into VictoriaMetrics."

# The database indicates these are the only streams it received today
stored_data_streams = ["frontend_latency_ms", "database_connections"]

# The Enterprise architecture requires all 3 logic gates present
mandatory_requirements = ["frontend_latency_ms", "database_connections", "billing_gateway_errors"]

print(detect_missing_storage_series(stored_data_streams, mandatory_requirements))
```

**Output of the script:**
```text
CRITICAL: VictoriaMetrics dropped data streams! The following series are silent: ['billing_gateway_errors']
```

---

### Task 4: Summarize top error streams and metric spikes

**Why use this logic?** If an outage hits, you don't have time to write complex MetricsQL queries manually. Python scripts can pre-compile these queries and format the REST API output into a human-readable top-N fault list for immediate rapid-incident response.

**Example Log (Spike representation object):**
`[{ "stream": "api-gateway", "error_count": 850 }]`

**Python Script:**
```python
def summarize_victoria_faults(victoria_query_results):
    # 1. Assume parameter format: Sorted list of dicts based upon PromQL output analysis
    # For VictoriaLogs format, filtering uses standard pipeline pipes (|)
    
    # 2. Iterate to sum massive occurrences mapped to services securely
    total_spikes = 0
    top_culprit = ""
    max_errors = 0
    
    for row in victoria_query_results:
        service = row.get("stream")
        err_count = row.get("error_count", 0)
        
        total_spikes += err_count
        
        if err_count > max_errors:
            max_errors = err_count
            top_culprit = service
            
    # 3. Generate summary presentation natively
    if total_spikes > 100:
        return f"🚨 CRITICAL INCIDENT SUMMARY\nTotal Fleet Errors: {total_spikes}\nHighest Spike: {top_culprit} ({max_errors} events)"
    else:
        return "Fleet stable."

vm_latest_query_output = [
    {"stream": "user-auth", "error_count": 15},
    {"stream": "api-gateway", "error_count": 870}, # Massive localized anomaly
    {"stream": "cache-node", "error_count": 2}
]

print(summarize_victoria_faults(vm_latest_query_output))
```

**Output of the script:**
```text
🚨 CRITICAL INCIDENT SUMMARY
Total Fleet Errors: 887
Highest Spike: api-gateway (870 events)
```

---

### Task 5: Create migration scripts between backends

**Why use this logic?** Migrating 100 million logs from traditional Elasticsearch over to VictoriaLogs natively is impossible without custom bridges. Python is perfect for acting as the "Extract, Transform, Load" (ETL) broker—sucking JSON from Elastic and spitting it into Victoria’s ingest format structurally. 

**Example Log (Elasticsearch output -> VictoriaLogs Input):**
`{"index": "logs", "msg": "hello"} -> {"_msg": "hello", "stream": "logs"}`

**Python Script:**
```python
import json

def elastisearch_to_victorialogs_migration(elastic_document_list):
    victoria_compatible_queue = []
    
    # 1. Iterate through traditional ES JSON formatted objects
    for document in elastic_document_list:
        # 2. Perform transformation into VictoriaLogs implicit schema formatting
        vl_entry = {
            "_msg": document.get("message", "No message provided"),
            "_stream": document.get("_index", "default_stream"),
            "original_timestamp": document.get("@timestamp")
        }
        
        victoria_compatible_queue.append(json.dumps(vl_entry))
        
    # 3. Simulate transmitting payload
    payload_dump = "\n".join(victoria_compatible_queue)
    return f"Transformed {len(elastic_document_list)} Elastic docs to Victoria JSONStream.\nPreview:\n{payload_dump[:150]}..."

es_dump = [
    {"_index": "web-prod-2026", "message": "Nginx restarted successfully", "@timestamp": "2026-04-10T12:00:00Z"},
    {"_index": "web-prod-2026", "message": "SSL Handshake Failed", "@timestamp": "2026-04-10T12:00:01Z"}
]

print(elastisearch_to_victorialogs_migration(es_dump))
```

**Output of the script:**
```text
Transformed 2 Elastic docs to Victoria JSONStream.
Preview:
{"_msg": "Nginx restarted successfully", "_stream": "web-prod-2026", "original_timestamp": "2026-04-10T12:00:00Z"}
{"_msg": "SSL Handshake Failed",...
```

---

### Task 6: Generate retention and volume usage reports

**Why use this logic?** VictoriaMetrics utilizes highly efficient block compression. To verify these efficiency gains, FinOps teams require scripts that periodically query `/api/v1/status/tsdb` to retrieve cardinality and block structure statistics to plot cost savings.

**Example Log (API TSDB JSON Response):**
`{"data": {"seriesCountByMetricName": [{"name": "http_req", "value": 50000}]}}`

**Python Script:**
```python
class VictoriaMetricsDiskUtilization:
    @staticmethod
    def calculate_retention_efficiency(total_series, disk_usage_mb):
        # 1. Execute logic measuring metric series density
        series_per_mb = total_series / disk_usage_mb if disk_usage_mb > 0 else 0
        
        # 2. Assess block efficiency structurally
        efficiency_status = "Excellent" if series_per_mb > 500 else "Sub-optimal"
        
        # 3. Formulate report block
        report = f"""
## VictoriaMetrics Storage Analysis
**Total Indexed Series:** {total_series} Series
**Actual Disk Cost:** {disk_usage_mb} MB
**Compression Density:** {series_per_mb:.1f} Series per MB
**Health Grade:** {efficiency_status}
"""
        return report.strip()

# Simulating data pulled from 'vm_data_size_bytes' & '/api/v1/status/tsdb'
print(VictoriaMetricsDiskUtilization.calculate_retention_efficiency(total_series=1250000, disk_usage_mb=450))
```

**Output of the script:**
```markdown
## VictoriaMetrics Storage Analysis
**Total Indexed Series:** 1250000 Series
**Actual Disk Cost:** 450 MB
**Compression Density:** 2777.8 Series per MB
**Health Grade:** Excellent
```

---

Using Python to script against VictoriaMetrics and VictoriaLogs enables you to quickly audit, scale, and manipulate vast pools of telemetry data securely while maintaining highly effective cost controls. 
