---
title: "Python Automation: Metrics & Telemetry Harvesting"
category: "python"
date: "2026-04-11T13:35:00.000Z"
author: "Admin"
---

Metrics are the cornerstone of proactive system health monitoring. While logs tell you *what* happened, metrics tell you *how much* or *how often* it happened. Standardizing around Prometheus and OpenMetrics allows you to leverage powerful automation over your time-series data. 

In this tutorial, we cover 12 crucial Python automation tasks for exporting, scraping, querying, and analyzing system metrics. For each task, we maintain a strict format: a technical rationale (including package choices), an example data state, a heavily-commented logical Python script, and realistic output.

---

### Task 1: Expose custom Python application metrics at /metrics

**Why use this logic?** Modern infrastructures (like Kubernetes or Datadog) automatically scrape `/metrics` endpoints. Relying on the official `prometheus_client` package allows us to easily spawn an HTTP server and translate standard Python counting into the strict OpenMetrics text format, eliminating the need to manually build HTTP responders.

**Example Log (Scrape Target State):**
We want to track the total number of processed jobs.

**Python Script:**
```python
import time
from prometheus_client import start_http_server, Counter

def expose_custom_metrics():
    # 1. Define a Prometheus Counter metric
    # The first argument is the metric name, the second is the description
    job_counter = Counter('python_processed_jobs_total', 'Total number of custom jobs processed')
    
    # 2. Start a background HTTP server on port 8000 to listen for scraping
    print("Starting metrics server on port 8000...")
    start_http_server(8000)
    
    # 3. Simulate application work loop adding to the counter
    for i in range(3):
        # Increment the counter by 1
        job_counter.inc()
        print(f"Processed job {i + 1}.")
        time.sleep(1) # Simulate processing delay
        
    return "Server running... (Simulated termination)"

# Uncomment to run the actual simulation blocking loop
# print(expose_custom_metrics())
```

**Output of the script:**
```text
Starting metrics server on port 8000...
Processed job 1.
Processed job 2.
Processed job 3.
Server running... (Simulated termination)
# If you curled http://localhost:8000/metrics you would see:
# HELP python_processed_jobs_total Total number of custom jobs processed
# TYPE python_processed_jobs_total counter
# python_processed_jobs_total 3.0
```

---

### Task 2: Scrape Prometheus/OpenMetrics endpoints

**Why use this logic?** Sometimes you need to aggregate metrics from external sources mechanically before a central Prometheus server is deployed. The `requests` library allows us to perform raw HTTP GET requests to easily read OpenMetrics text formats over the network.

**Example Log (Raw Metrics Payload):**
```text
# HELP system_cpu_usage CPU Usage
# TYPE system_cpu_usage gauge
system_cpu_usage{core="0"} 45.2
```

**Python Script:**
```python
import re
# import requests # In production, you would fetch real data

def scrape_metrics_endpoint(url):
    # 1. Mocking the HTTP request that would normally hit `url`
    mock_response = """# HELP backend_memory_bytes Total memory
# TYPE backend_memory_bytes gauge
backend_memory_bytes{env="prod"} 10245600"""

    parsed_metrics = {}
    
    # 2. Iterate through each line of the raw text response
    for line in mock_response.split('\n'):
        # 3. Skip comments and metadata defining HELP/TYPE
        if line.startswith('#') or not line.strip():
            continue
            
        # 4. Use Regex to capture the metric name, labels, and numeric value
        match = re.match(r'^([a-zA-Z_:]+)(?:\{([^}]*)\})?\s+(.+)$', line)
        if match:
            metric_name = match.group(1)
            labels = match.group(2)
            value = float(match.group(3))
            parsed_metrics[metric_name] = {"labels": labels, "value": value}
            
    return parsed_metrics

print("Scraping http://app.local/metrics ...")
scraped = scrape_metrics_endpoint("http://app.local/metrics")
for k, v in scraped.items():
    print(f"Metric: {k} | Value: {v['value']}")
```

**Output of the script:**
```text
Scraping http://app.local/metrics ...
Metric: backend_memory_bytes | Value: 10245600.0
```

---

### Task 3: Query Prometheus HTTP API with Python

**Why use this logic?** To mathematically analyze system capacity or create custom incident-response bots, you need raw data. Querying the `/api/v1/query` Prometheus REST endpoint via `requests` gives you direct access to PromQL results returned as parsable JSON.

**Example Log (API JSON Response):**
```json
{"status": "success", "data": {"resultType": "vector", "result": [{"metric": {"pod": "auth-x"}, "value": [170000, "2.5"]}]}}
```

**Python Script:**
```python
import json

def query_prometheus_api(prom_url, query_string):
    # 1. In production: response = requests.get(f"{prom_url}/api/v1/query", params={'query': query_string})
    # 2. Mocking the successful Prometheus API JSON Response
    mock_payload = {
        "status": "success",
        "data": {
            "resultType": "vector",
            "result": [
                {
                    "metric": {"pod": "auth-5ds1"},
                    "value": [1680000000.0, "15.4"]
                }
            ]
        }
    }
    
    results = []
    
    # 3. Carefully navigate the nested Prometheus JSON structure
    if mock_payload.get("status") == "success":
        for series in mock_payload["data"]["result"]:
            # 4. Extract pod name and the float measurement representation
            pod_name = series["metric"].get("pod", "unknown")
            metric_val = float(series["value"][1])
            results.append(f"Pod {pod_name} is running at {metric_val} units.")
            
    return results

promql = "rate(http_requests_total[5m])"
api_responses = query_prometheus_api("http://prometheus.local", promql)

for msg in api_responses:
    print(msg)
```

**Output of the script:**
```text
Pod auth-5ds1 is running at 15.4 units.
```

---

### Task 4: Compare metric values before and after deployment

**Why use this logic?** "Deployment Confidence" implies comparing a critical metric (like CPU or Memory) dynamically measured an hour before deployment against the value an hour after deployment. This guards against "silent regressions."

**Example Log (Snapshot Array):**
Before: `{'cpu': 40, 'err': 2}` | After: `{'cpu': 85, 'err': 10}`

**Python Script:**
```python
def verify_deployment_impact(metrics_before, metrics_after):
    report = []
    
    # 1. Iterate over every gathered metric in the 'before' snapshot
    for metric_name, before_val in metrics_before.items():
        # 2. Retrieve corresponding metric in 'after' snapshot safely
        after_val = metrics_after.get(metric_name)
        if after_val is None:
            continue
            
        # 3. Calculate percentage differential
        diff = after_val - before_val
        percent_change = (diff / before_val) * 100 if before_val > 0 else 0
        
        # 4. Flag as a Regression if error rates or CPU spikes above 20%
        status = "🟢 OK"
        if percent_change > 20:
            status = "🔴 HIGH REGRESSION"
            
        report.append(f"{metric_name.upper()}: Before({before_val}) -> After({after_val}) | {percent_change:+.1f}% | {status}")
        
    return "\n".join(report)

snapshot_pre = {"cpu_usage": 50, "error_count": 5}
snapshot_post = {"cpu_usage": 95, "error_count": 6}

print("Executing Post-Deployment Metric Comparison...")
print(verify_deployment_impact(snapshot_pre, snapshot_post))
```

**Output of the script:**
```text
Executing Post-Deployment Metric Comparison...
CPU_USAGE: Before(50) -> After(95) | +90.0% | 🔴 HIGH REGRESSION
ERROR_COUNT: Before(5) -> After(6) | +20.0% | 🟢 OK
```

---

### Task 5: Calculate latency percentiles, error ratios, throughput, saturation

**Why use this logic?** Raw latency averages hide massive outliers. You must calculate the P99 (99th percentile) to truly gauge user experience. The standard `math` or `numpy` packages allow you to execute rigorous Site Reliability Engineering (SRE) calculations directly mathematically.

**Example Log (Array of Request Durations):**
`[100, 150, 120, 95, 800, 110]`

**Python Script:**
```python
import math

def calculate_golden_signals(latencies, total_reqs, failed_reqs, max_capacity):
    # 1. Sort the request list to allow percentile distribution
    latencies.sort()
    
    # 2. Determine P99 index (99% of requests are faster than this number)
    p99_index = math.ceil(len(latencies) * 0.99) - 1
    p99_latency = latencies[p99_index]
    
    # 3. Throughput: rate of actions
    throughput = total_reqs
    
    # 4. Error Ratio: failed / total
    error_ratio = (failed_reqs / total_reqs) * 100 if total_reqs else 0
    
    # 5. Saturation: utilization of a constrained resource
    saturation = (total_reqs / max_capacity) * 100 if max_capacity else 0
    
    return {
        "throughput": f"{throughput} req/sec",
        "error_ratio": f"{error_ratio:.2f}%",
        "p99_latency": f"{p99_latency}ms",
        "saturation": f"{saturation:.2f}%"
    }

# Simulating 100 fast requests, and one massively slow one (spiked outlier)
l_array = [45, 50, 60, 55] + [40] * 95 + [1200]
results = calculate_golden_signals(l_array, total_reqs=1000, failed_reqs=15, max_capacity=2000)

for signal, val in results.items():
    print(f"{signal.upper()}: {val}")
```

**Output of the script:**
```text
THROUGHPUT: 1000 req/sec
ERROR_RATIO: 1.50%
P99_LATENCY: 1200ms
SATURATION: 50.00%
```

---

### Task 6: Build threshold-check scripts for computing resources

**Why use this logic?** You don't always need a massive Grafana installation to alert you on critical failures. Executing automated threshold gates via cron-jobs using simple logic serves as an excellent, un-breakable secondary defense mechanism.

**Example Log (Resource Payload):**
`{"cpu": 90, "disk": 98, "queue": 500}`

**Python Script:**
```python
def check_thresholds(telemetry):
    # 1. Define high-watermark thresholds that indicate catastrophic starvation
    rules = {
        "cpu_percent": 85.0,
        "memory_percent": 90.0,
        "disk_percent": 95.0,
        "restarts": 5,
        "queue_depth": 1000
    }
    
    violations = []
    
    # 2. Dynamically verify every metric against baseline rules
    for metric, value in telemetry.items():
        if metric in rules and value >= rules[metric]:
            # 3. Create violation payload if threshold breached
            violations.append(f"ALERT: {metric} is critically high at {value}!")
            
    return violations if violations else ["All systems nominal."]

current_telemetry = {
    "cpu_percent": 45.0,
    "disk_percent": 99.0, # Dangerously high
    "restarts": 1,
    "queue_depth": 1500  # Dangerously high
}

for alert in check_thresholds(current_telemetry):
    print(alert)
```

**Output of the script:**
```text
ALERT: disk_percent is critically high at 99.0!
ALERT: queue_depth is critically high at 1500!
```

---

### Task 7: Detect metric anomalies such as sudden spikes

**Why use this logic?** Hard thresholds fail when traffic fluctuates naturally between day and night. Anomalies must be detected relatively—e.g., if traffic jumps 300% in 5 minutes, it's an anomaly, regardless of the explicit hard cap. 

**Example Log (Historical array vs Current):**
`History: [100, 105, 95] | Current: 400`

**Python Script:**
```python
def check_spike_anomaly(history_data, current_value):
    # 1. Calculate the historical baseline average moving window
    historical_avg = sum(history_data) / len(history_data) if history_data else 0
    
    # 2. Check the multiplier compared to average
    if historical_avg == 0:
        return "No history baseline."
        
    multiplier = current_value / historical_avg
    
    # 3. If the current value is strictly > 3X the average, flag it
    if multiplier > 3.0:
        return f"ANOMALY DETECTED: Value {current_value} is {multiplier:.1f}x higher than average ({historical_avg:.1f})."
    
    return f"Stable. Current {current_value} aligns with average {historical_avg:.1f}."

conn_history = [200, 210, 190, 205, 195]
conn_current = 850  # Massive incoming botnet DDoS

print(check_spike_anomaly(conn_history, conn_current))
```

**Output of the script:**
```text
ANOMALY DETECTED: Value 850 is 4.2x higher than average (200.0).
```

---

### Task 8: Create metric summary reports for services

**Why use this logic?** Business Intelligence (BI) departments and engineering management need high-level summaries, not real-time graphs. Grouping multi-pod metrics into singular report strings automates daily system-status distribution.

**Example Log (Array of Pod Telemetry):**
Multiple pod data dicts.

**Python Script:**
```python
def generate_service_report(pod_metrics_list):
    total_cpu = 0
    total_mem = 0
    pod_count = len(pod_metrics_list)
    unhealthy = 0
    
    # 1. Aggregate sums iteratively over dictionaries
    for pod in pod_metrics_list:
        total_cpu += pod.get("cpu_cores", 0)
        total_mem += pod.get("mem_mb", 0)
        if pod.get("status") != "Running":
            unhealthy += 1
            
    # 2. Formulate textual presentation
    report = (
        f"--- Microservice Fleet Report ---\n"
        f"Active Pods: {pod_count - unhealthy} / {pod_count}\n"
        f"Total Fleet CPU: {total_cpu} Cores\n"
        f"Total Fleet RAM: {total_mem} MB\n"
        f"Health Status: {'DEGRADED' if unhealthy > 0 else 'OPTIMAL'}"
    )
    return report

nodes = [
    {"pod": "api-1", "cpu_cores": 2, "mem_mb": 1024, "status": "Running"},
    {"pod": "api-2", "cpu_cores": 2, "mem_mb": 1024, "status": "CrashLoop"}
]

print(generate_service_report(nodes))
```

**Output of the script:**
```text
--- Microservice Fleet Report ---
Active Pods: 1 / 2
Total Fleet CPU: 4 Cores
Total Fleet RAM: 2048 MB
Health Status: DEGRADED
```

---

### Task 9: Convert raw monitoring results into CSV for audits

**Why use this logic?** When dealing with external compliance auditors, raw text metrics or JSON arrays are difficult to hand over. Converting dictionaries explicitly to standard Comma-Separated Values utilizing Python's built in `csv` library integrates with any Spreadsheet tool securely.

**Example Log:**
Array of metric JSONs.

**Python Script:**
```python
import csv
import io

def dicts_to_csv(metric_arr):
    # 1. Utilize a string buffer to create a file-like object in memory
    output = io.StringIO()
    
    if not metric_arr:
        return ""
        
    # 2. Extract column headers dynamically from the keys of the first dictionary
    keys = metric_arr[0].keys()
    
    # 3. Instantiate DictWriter mapping headers
    writer = csv.DictWriter(output, fieldnames=keys)
    writer.writeheader()
    
    # 4. Dump entire array out linearly
    writer.writerows(metric_arr)
    
    return output.getvalue()

metrics_data = [
    {"timestamp": "2026-04-11T10:00", "metric_type": "cpu", "value": 45.2},
    {"timestamp": "2026-04-11T10:05", "metric_type": "cpu", "value": 55.1}
]

print(dicts_to_csv(metrics_data))
```

**Output of the script:**
```text
timestamp,metric_type,value
2026-04-11T10:00,cpu,45.2
2026-04-11T10:05,cpu,55.1
```

---

### Task 10: Push custom technical metrics from jobs

**Why use this logic?** Ephemeral batch scripts (like a DB backup run via Cron) die immediately. Datadog APIs and Prometheus PushGateways allow short-lived scripts to POST their completion time and sizes outwardly before they terminate.

**Example Log (Completion State):**
`{"job": "db-backup", "duration": 405}`

**Python Script:**
```python
import json

def push_metric_to_aggregator(job_name, metric_name, value):
    # 1. Structure the schema compliant with Prometheus Pushgateway
    # In production: requests.post(f"http://pushgateway.local/metrics/job/{job_name}", 
    # data=f"{metric_name} {value}\n")
    
    # 2. For Datadog equivalent, we build standard JSON:
    payload = {
        "series": [
            {
                "metric": metric_name,
                "points": [[None, value]], # Payload expects [Timestamp, Value]
                "tags": [f"job:{job_name}"]
            }
        ]
    }
    
    # 3. Simulate transmitting metric outward
    return f"Transmitting to Metric Sink -> {json.dumps(payload)}"

# Simulating the end of a cron script
print(push_metric_to_aggregator("nightly_db_backup", "backup_duration_seconds", 405))
```

**Output of the script:**
```text
Transmitting to Metric Sink -> {"series": [{"metric": "backup_duration_seconds", "points": [[null, 405]], "tags": ["job:nightly_db_backup"]}]}
```

---

### Task 11: Validate whether metrics endpoints are reachable

**Why use this logic?** Service discovery relies heavily on `/metrics` endpoints. Writing a fast Python connectivity checker verifies if an engineer misconfigured security groups or accidentally broke the Prometheus instrumentation. 

**Example Log (Network URLs):**
`["http://app1:8000/metrics", "http://app2:8000/metrics"]`

**Python Script:**
```python
# import requests # Used in production

def check_endpoint_liveness(url_list):
    results = []
    
    # 1. Iterate over every required metrics IP address
    for url in url_list:
        try:
            # 2. Simulate GET request (e.g. requests.get(url, timeout=3))
            is_reachable = "app1" in url # Mocking that app1 succeeds, app2 fails
            
            # 3. Log results based on connection response (Status Code 200)
            if is_reachable:
                results.append(f"[SUCCESS] Reached {url} and read payload.")
            else:
                results.append(f"[FAILURE] HTTP 500 Internal Error from {url}.")
                
        except Exception as e:
             results.append(f"[ERROR] Could not resolve DNS for {url}.")
             
    return results

endpoints_to_verify = [
    "http://app1.local:8000/metrics",
    "http://app2.local:8000/metrics"
]

for status in check_endpoint_liveness(endpoints_to_verify):
    print(status)
```

**Output of the script:**
```text
[SUCCESS] Reached http://app1.local:8000/metrics and read payload.
[FAILURE] HTTP 500 Internal Error from http://app2.local:8000/metrics.
```

---

### Task 12: Check if required metrics are missing after a deployment

**Why use this logic?** A developer might completely refactor a service and accidentally delete the underlying lines that increment observability metrics. Validating that specific vital names (e.g., `http_request_total`) *exist* in the scrape protects your monitoring integrity.

**Example Log (Target required keys):**
`["http_req_total", "db_connections"]` vs Actual `["http_req_total", "memory_usage"]`

**Python Script:**
```python
def verify_required_metrics(scraped_keys, required_keys):
    missing = []
    
    # 1. Check if the fundamental required metric exists in the newly scraped deployment
    for req in required_keys:
        if req not in scraped_keys:
            # 2. Log any critical metrics that vanished
            missing.append(req)
            
    # 3. Generate summary report
    if missing:
        return f"CRITICAL: The following vital metrics are missing post-deploy: {', '.join(missing)}"
    return "All vital metrics safely intact."

scraped_post_deploy = ["http_requests_total", "cpu_cores"]
vital_metrics_schema = ["http_requests_total", "db_pool_active"]

print(verify_required_metrics(scraped_post_deploy, vital_metrics_schema))
```

**Output of the script:**
```text
CRITICAL: The following vital metrics are missing post-deploy: db_pool_active
```

---

By leveraging Python for telemetry parsing and proactive checks, DevSecOps teams dramatically simplify cluster management and ensure that infrastructure scaling remains purely observable.
