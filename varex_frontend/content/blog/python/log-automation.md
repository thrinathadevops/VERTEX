---
title: "Python Automation: Log Handling & Analysis"
category: "python"
date: "2026-04-11T12:00:00.000Z"
author: "Admin"
---

Logs are the lifeblood of infrastructure observability. From debugging application errors to triggering critical alerts, how you handle logs determines how quickly you can identify and resolve production issues. In this tutorial, we will explore the 15 most essential Python automation tasks for log collection, parsing, correlation, and enrichment. For each task, you'll find real-world sample logs, line-by-line script explanations, and example outputs.

We chose standard libraries alongside specific powerful utilities (`logging`, `json`, `re`) because Python excels at string processing. For production integration, combining these automated scripts with solutions like Datadog, Grafana, or AWS Lambda creates a robust observability pipeline.

---

### Task 1: Read local log files and rotate/archive them

**Why use this logic?** Logs can grow infinitely, consuming disk space and crashing instances. Rotating logs (zipping the old ones and clearing the current) is a standard systems engineering practice to avoid "disk full" issues. Python's built-in `logging.handlers.RotatingFileHandler` does this automatically, but for legacy logs, a custom rotation script is useful.

**Example Log:**
```
server.log (Large file)
[2026-04-10 10:00:00] INFO Server started.
[2026-04-10 10:01:00] WARN Memory usage climbing.
```

**Python Script:**
```python
import os
import gzip
import shutil
from datetime import datetime

def rotate_and_archive_log(file_path):
    # 1. Check if the log file exists and its size exceeds a limit (e.g. 5MB)
    if os.path.exists(file_path) and os.path.getsize(file_path) > 5 * 1024 * 1024:
        # 2. Construct a timestamped archive filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"{file_path}.{timestamp}.gz"
        
        # 3. Read the original log file and compress it using gzip
        with open(file_path, 'rb') as f_in:
            with gzip.open(archive_name, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # 4. Clear the original log file (truncate it to zero bytes)
        open(file_path, 'w').close()
        
        print(f"Log rotated successfully. Archived to {archive_name}")
    else:
        print("Log file does not need rotation yet.")

# Example usage (commented out for safety):
# rotate_and_archive_log('/var/log/app/server.log')
```

**Output of the script:**
```text
Log rotated successfully. Archived to /var/log/app/server.log.20260411_120530.gz
```

---

### Task 2: Parse plain-text logs with regex

**Why use this logic?** Legacy applications often output unstructured lines. Regular Expressions (`re`) allow us to extract key-value pairs (timestamps, log levels, messages) from custom formats, making unstructured text queryable.

**Example Log:**
```
2026-04-11 08:22:15 [ERROR] [auth-service] Failed login for user obj=admin
```

**Python Script:**
```python
import re

def parse_plaintext_log(log_line):
    # 1. Define a regex pattern with named groups for Date, Level, Component, and Message
    pattern = r"(?P<date>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+\[(?P<level>\w+)\]\s+\[(?P<component>[^\]]+)\]\s+(?P<message>.*)"
    
    # 2. Match the pattern against the given log line
    match = re.match(pattern, log_line)
    
    # 3. If a match is found, return the structured dictionary; else None
    if match:
        return match.groupdict()
    return None

log_sample = "2026-04-11 08:22:15 [ERROR] [auth-service] Failed login for user obj=admin"
parsed = parse_plaintext_log(log_sample)

print(parsed)
```

**Output of the script:**
```text
{'date': '2026-04-11 08:22:15', 'level': 'ERROR', 'component': 'auth-service', 'message': 'Failed login for user obj=admin'}
```

---

### Task 3: Parse JSON logs and normalize field names

**Why use this logic?** Modern microservices output JSON, but different services often use mismatched generic keys (e.g., `lvl` vs `severity` vs `level`). Normalizing fields ensures that unified dashboards in Grafana or Datadog work smoothly without writing a hundred varied SQL queries.

**Example Log:**
```json
{"time": "2026-04-11T12:00:00Z", "lvl": "warn", "msg": "DB latency spike"}
```

**Python Script:**
```python
import json

def normalize_json_log(json_str):
    try:
        # 1. Load the JSON string into a Python dictionary
        log_data = json.loads(json_str)
        
        # 2. Normalize the 'level' field
        if 'lvl' in log_data:
            log_data['level'] = log_data.pop('lvl').upper()
        elif 'severity' in log_data:
            log_data['level'] = log_data.pop('severity').upper()
            
        # 3. Normalize the 'timestamp' field
        if 'time' in log_data:
            log_data['timestamp'] = log_data.pop('time')
            
        # 4. Normalize the 'message' field
        if 'msg' in log_data:
            log_data['message'] = log_data.pop('msg')
            
        return log_data
    except json.JSONDecodeError:
        return {"error": "Invalid JSON"}

raw_log = '{"time": "2026-04-11T12:00:00Z", "lvl": "warn", "msg": "DB latency spike"}'
normalized = normalize_json_log(raw_log)

print(json.dumps(normalized, indent=2))
```

**Output of the script:**
```json
{
  "level": "WARN",
  "timestamp": "2026-04-11T12:00:00Z",
  "message": "DB latency spike"
}
```

---

### Task 4: Convert unstructured logs into structured JSON logs

**Why use this logic?** Cloud-native architectures (Kubernetes, AWS CloudWatch) heavily rely on structured logging. Parsing unstructured logs to JSON before forwarding allows log search engines (like Elasticsearch) to index critical fields so they can be queried rapidly.

**Example Log:**
```
INFO: 2026-04-12 11:22:33 - Worker process started gracefully
```

**Python Script:**
```python
import json
import re

def unstructured_to_structured(log_line):
    # 1. Regex to extract parts: LogLevel, Timestamp, and Message
    pattern = r"^(?P<severity>[A-Z]+):\s+(?P<timestamp>\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})\s+-\s+(?P<message>.*)$"
    match = re.match(pattern, log_line)
    
    if match:
        # 2. Create a standardized dictionary from the matched parts
        structured_data = {
            "severity": match.group("severity"),
            "timestamp": match.group("timestamp"),
            "message": match.group("message"),
            "source": "legacy-app-migration"
        }
        # 3. Convert dictionary to JSON string
        return json.dumps(structured_data)
        
    return json.dumps({"unparsed_raw": log_line})

log_line = "INFO: 2026-04-12 11:22:33 - Worker process started gracefully"
json_log = unstructured_to_structured(log_line)

print(json_log)
```

**Output of the script:**
```json
{"severity": "INFO", "timestamp": "2026-04-12 11:22:33", "message": "Worker process started gracefully", "source": "legacy-app-migration"}
```

---

### Task 5: Enrich logs with metadata

**Why use this logic?** When dealing with hundreds of containers, an isolated error trace is meaningless. Appending context (like namespace or pod name) instantly informs the operator precisely *where* the issue resides. Python's `os.environ` pulls system-level details to enrich the application payload.

**Example Log:**
```json
{"level": "ERROR", "message": "SyntaxError: Unexpected token"}
```

**Python Script:**
```python
import os
import json

def enrich_log(log_entry_dict):
    # 1. Gather metadata securely from environment variables (defaults provided)
    metadata = {
        "service": os.environ.get("SERVICE_NAME", "backend-api"),
        "environment": os.environ.get("ENV", "production"),
        "hostname": os.environ.get("HOSTNAME", "ip-10-0-1-55"),
        "pod_name": os.environ.get("POD_NAME", "backend-api-7b89f-xyz"),
        "region": os.environ.get("AWS_REGION", "us-east-1")
    }
    
    # 2. Merge dictionaries securely (in Python 3.9+, log_entry_dict | metadata works too)
    enriched_log = {**metadata, **log_entry_dict}
    
    # 3. Return the newly enriched dictionary
    return json.dumps(enriched_log, indent=2)

base_logger_payload = {"level": "ERROR", "message": "SyntaxError: Unexpected token"}
print(enrich_log(base_logger_payload))
```

**Output of the script:**
```json
{
  "service": "backend-api",
  "environment": "production",
  "hostname": "ip-10-0-1-55",
  "pod_name": "backend-api-7b89f-xyz",
  "region": "us-east-1",
  "level": "ERROR",
  "message": "SyntaxError: Unexpected token"
}
```

---

### Task 6: Extract trace_id and span_id from logs for correlation

**Why use this logic?** Datadog and other APM tools map application metrics to log lines using specific keys stringed across a distributed environment (Trace Correlation). Extracting or injecting `dd.trace_id` enables single-pane-of-glass observability.

**Example Log:**
```json
{"message": "Payment processed", "traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"}
```

**Python Script:**
```python
import json

def extract_trace_correlation(log_str):
    try:
        log_data = json.loads(log_str)
        
        # 1. Check if W3C traceparent protocol is present
        traceparent = log_data.get("traceparent")
        
        if traceparent:
            # 2. Split the traceparent: version-traceId-spanId-traceFlags
            parts = traceparent.split("-")
            if len(parts) >= 4:
                trace_id = parts[1]
                span_id = parts[2]
                
                # 3. Inject Datadog-friendly standardized trace fields
                log_data["dd.trace_id"] = trace_id
                log_data["dd.span_id"] = span_id
                
        return log_data
    except Exception as e:
        return {"error": str(e)}

raw = '{"message": "Payment processed", "traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"}'
print(json.dumps(extract_trace_correlation(raw), indent=2))
```

**Output of the script:**
```json
{
  "message": "Payment processed",
  "traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01",
  "dd.trace_id": "0af7651916cd43dd8448eb211c80319c",
  "dd.span_id": "b7ad6b7169203331"
}
```

---

### Task 7: Group logs by error type, service, or endpoint

**Why use this logic?** In an investigation, seeing 5,000 continuous errors is overwhelming. Grouping logs logically allows you to summarize and say: "Service X had 4,000 DB timeouts, and Service Y had 1,000 auth failures." Python's `collections.defaultdict` makes aggregation trivial.

**Example Log Input Array:**
Multiple JSON strings specifying `service` and `error_type`.

**Python Script:**
```python
import json
from collections import defaultdict

def group_logs(log_lines):
    # 1. Create a dictionary that defaults values to a fresh dictionary holding integer values
    grouped_stats = defaultdict(lambda: defaultdict(int))
    
    for line in log_lines:
        try:
            data = json.loads(line)
            # 2. Safely extract metadata
            service = data.get("service", "unknown_service")
            err_type = data.get("error_type", "unknown_error")
            
            # 3. Increment the count for that specific service and error type
            if data.get("level") == "ERROR":
                grouped_stats[service][err_type] += 1
        except json.JSONDecodeError:
            continue
            
    # 4. Standard dict conversion for display
    return {k: dict(v) for k, v in grouped_stats.items()}

logs = [
    '{"service": "cart-api", "level": "ERROR", "error_type": "RedisTimeout"}',
    '{"service": "cart-api", "level": "ERROR", "error_type": "RedisTimeout"}',
    '{"service": "user-api", "level": "ERROR", "error_type": "AuthFailure"}',
]

print(json.dumps(group_logs(logs), indent=2))
```

**Output of the script:**
```json
{
  "cart-api": {
    "RedisTimeout": 2
  },
  "user-api": {
    "AuthFailure": 1
  }
}
```

---

### Task 8: Count ERROR/WARN/INFO lines and create summaries

**Why use this logic?** For daily automated email health reports, stakeholders don't want to see individual logs; they want quick counts to verify system steady-state operation. Counting and printing metrics acts as a high-level monitoring baseline.

**Example Log Input:**
List of unstructured text log lines.

**Python Script:**
```python
def count_log_levels(log_file_lines):
    # 1. Initialize counter dictionary for recognized thresholds
    counts = {"INFO": 0, "WARN": 0, "ERROR": 0, "DEBUG": 0}
    
    # 2. Iterate through rows checking for severity keywords
    for line in log_file_lines:
        line_upper = line.upper()
        if "ERROR" in line_upper:
            counts["ERROR"] += 1
        elif "WARN" in line_upper:
            counts["WARN"] += 1
        elif "INFO" in line_upper:
            counts["INFO"] += 1
        elif "DEBUG" in line_upper:
            counts["DEBUG"] += 1
            
    # 3. Create formatted summary string for alerts
    summary = (
        f"--- Daily Log Summary ---\n"
        f"Errors: {counts['ERROR']}  (Critical)\n"
        f"Warnings: {counts['WARN']}  (Watch)\n"
        f"Infos: {counts['INFO']}\n"
        f"Total Analyzed: {sum(counts.values())}"
    )
    return summary

samples = [
    "2026-04-11 [INFO] Startup successful",
    "2026-04-11 [WARN] CPU approaching 80%",
    "2026-04-11 [ERROR] DB sync failed",
    "2026-04-11 [ERROR] Deadlock detected"
]

print(count_log_levels(samples))
```

**Output of the script:**
```text
--- Daily Log Summary ---
Errors: 2  (Critical)
Warnings: 1  (Watch)
Infos: 1
Total Analyzed: 4
```

---

### Task 9: Detect recurring failures

**Why use this logic?** Critical systemic events like `CrashLoopBackOff` or `OOMKilled` shouldn't go unnoticed. We scan strings to rapidly identify infrastructure-level failures that indicate immediate action is necessary (like increasing memory sizes).

**Example Logs:**
```
Container user-db terminated with exit code 137 (OOMKilled)
Connection refused on port 5432
```

**Python Script:**
```python
def detect_system_failures(log_lines):
    # 1. Define typical high-priority failure signatures
    failure_patterns = {
        "OOMKilled": ["OOMKilled", "out of memory", "exit code 137"],
        "ConnectionRefused": ["connection refused", "timeout tcp", "504 Gateway"],
        "CrashLoop": ["CrashLoopBackOff", "restarting continually"]
    }
    
    detections = []
    
    # 2. Parse logs against signature sets
    for line in log_lines:
        for fault_type, indicators in failure_patterns.items():
            # Any() matches if ANY string from the list appears in the log line
            if any(indicator.lower() in line.lower() for indicator in indicators):
                detections.append(f"[{fault_type} DETECTED]: {line}")
                
    return detections

logs = [
    "Container cache-node terminated with exit code 137 (OOMKilled)",
    "API request normal",
    "HTTP 504 Gateway Timeout while reaching upstream server"
]

for d in detect_system_failures(logs):
    print(d)
```

**Output of the script:**
```text
[OOMKilled DETECTED]: Container cache-node terminated with exit code 137 (OOMKilled)
[ConnectionRefused DETECTED]: HTTP 504 Gateway Timeout while reaching upstream server
```

---

### Task 10: Filter noisy logs and suppress known harmless patterns

**Why use this logic?** High-volume "noisy" errors, such as bots scraping invalid endpoints, obscure genuine issues and inflate SIEM storage costs. Removing known exceptions pre-ingestion cuts down costs dramatically.

**Example Logs:**
Healthy user errors, plus noise.

**Python Script:**
```python
def filter_noisy_logs(log_lines):
    # 1. Define substrings identified as "safe to ignore"
    noise_patterns = [
        "favicon.ico not found",
        "bot user agent",
        "HealthCheck OK",
    ]
    
    filtered = []
    
    # 2. Iterate and append only if it contains none of the noise patterns
    for line in log_lines:
        # Check if the line cleanly lacks noise
        is_noisy = any(noise in line for noise in noise_patterns)
        if not is_noisy:
            filtered.append(line)
            
    return filtered

logs = [
    "12:00:01 [ERROR] favicon.ico not found",
    "12:00:02 [INFO] HealthCheck OK",
    "12:00:03 [ERROR] Database Transaction Interrupted!"
]

clean_logs = filter_noisy_logs(logs)
for cl in clean_logs:
    print(cl)
```

**Output of the script:**
```text
12:00:03 [ERROR] Database Transaction Interrupted!
```

---

### Task 11: Compare logs between two time ranges or builds

**Why use this logic?** When deploying a new release alongside a canary, comparing the error velocity of "v1.0" versus "v2.0" lets you instantly verify stability or detect regressions.

**Example Input Models:**
Arrays of dictionaries from Build A vs Build B.

**Python Script:**
```python
def compare_build_logs(build_1_logs, build_2_logs):
    # 1. Inline helper to tally error occurrence arrays
    def count_errors(logs_array):
        return sum(1 for log in logs_array if log.get('level') == 'ERROR')
    
    # 2. Execute counts
    err_count_1 = count_errors(build_1_logs)
    err_count_2 = count_errors(build_2_logs)
    
    # 3. Analyze differences
    diff = err_count_2 - err_count_1
    status = "REGRESSION" if diff > 0 else "STABLE / IMPROVED"
    
    return f"Comparison Result: build v1 errors ({err_count_1}) vs build v2 errors ({err_count_2}). Status: {status}"

v1_logs = [{"level": "ERROR", "msg": "timeout"}, {"level": "INFO", "msg": "ok"}]
v2_logs = [{"level": "ERROR", "msg": "timeout"}, {"level": "ERROR", "msg": "timeout"}, {"level": "ERROR", "msg": "auth"}]

print(compare_build_logs(v1_logs, v2_logs))
```

**Output of the script:**
```text
Comparison Result: build v1 errors (1) vs build v2 errors (3). Status: REGRESSION
```

---

### Task 12: Fetch logs from APIs and save them locally

**Why use this logic?** For detailed forensic analysis or regulatory auditing, pulling massive telemetry segments down to disk locally allows engineers to utilize powerful local `grep` tools offline.

**Example Scenario:**
Using `requests` to pull logs from a mock Datadog API edge.

**Python Script:**
```python
import os
import json
# import requests # Used in production

def fetch_and_save_api_logs(api_endpoint, output_path):
    # 1. Mocking an API call (Replace with real requests.get(url, headers={}))
    mock_api_response = {
        "data": [
            {"id": 1, "log": "System OK", "status": 200},
            {"id": 2, "log": "Network Reset", "status": 500}
        ]
    }
    
    # 2. Serialize fetched content iteratively
    try:
        with open(output_path, "w") as f:
            for item in mock_api_response["data"]:
                # Convert dict to JSON line to make it easily parsable
                f.write(json.dumps(item) + "\n")
        return f"Successfully saved {len(mock_api_response['data'])} logs to {output_path}"
    except Exception as e:
        return f"Failed saving logs local: {e}"

# Running mock operation to a temp file
print(fetch_and_save_api_logs("https://api.thirdpartyylogs.com/v1/query", "local_backup.jsonl"))
```

**Output of the script:**
```text
Successfully saved 2 logs to local_backup.jsonl
```

---

### Task 13: Search logs for incident keywords during outages

**Why use this logic?** Time is crucial. When an outage occurs, executing a parallel search for high-value symptoms (e.g., `PaymentDeclined`, `StripeRateLimit`) cuts straight through terabytes of irrelevant data to identify root causes.

**Example Log Sequence:**
Application trace dumping large datasets.

**Python Script:**
```python
def incident_search(log_lines, incident_keywords):
    detected = []
    
    # 1. Search line by line efficiently avoiding heavy RAM loading
    for count, line in enumerate(log_lines, 1):
        for keyword in incident_keywords:
            # 2. Check if the specific severe keyword is part of the trace format string
            if keyword.lower() in line.lower():
                detected.append(f"[Line {count}] {keyword.upper()} Match: {line.strip()}")
                break # Move to next line once matched
                
    return detected

incident_logs = [
    "Normal startup process finished",
    "User authentication successful",
    "FATAL StripeRateLimit reached, retrying in 30s",
    "StripeRateLimit retries failed"
]

results = incident_search(incident_logs, ["StripeRateLimit", "FATAL", "Deadlock"])
for r in results:
    print(r)
```

**Output of the script:**
```text
[Line 3] FATAL Match: FATAL StripeRateLimit reached, retrying in 30s
[Line 4] STRIPERATELIMIT Match: StripeRateLimit retries failed
```

---

### Task 14: Generate daily log health reports

**Why use this logic?** Automated CI/CD pipes can pull these scripts to dynamically generate HTML or Markdown summaries, pushing a clear "Observability Health Check" update to Slack channels for immediate team transparency.

**Python Script:**
```python
from datetime import datetime

def generate_health_report(error_count, warn_count, total_lines):
    # 1. Determine relative health metric thresholds
    health_score = 100 - (error_count * 2) - warn_count
    health_status = "🟢 HEALTHY" if health_score > 90 else "🟡 DEGRADED" if health_score > 70 else "🔴 CRITICAL"
    
    # 2. Format a structured Markdown report
    report = f"""
## Daily Log Health Report ({datetime.now().strftime('%Y-%m-%d')})
**Status:** {health_status}
**Health Score:** {health_score}/100

| Metric        | Count |
|---------------|-------|
| Total Logs    | {total_lines} |
| **Errors**    | {error_count}  |
| Warnings      | {warn_count}  |

*Generated automatically via Python Logging Service.*
"""
    return report

print(generate_health_report(error_count=2, warn_count=5, total_lines=15000))
```

**Output of the script:**
```markdown
## Daily Log Health Report (2026-04-11)
**Status:** 🟢 HEALTHY
**Health Score:** 91/100

| Metric        | Count |
|---------------|-------|
| Total Logs    | 15000 |
| **Errors**    | 2  |
| Warnings      | 5  |

*Generated automatically via Python Logging Service.*
```

---

### Task 15: Forward logs from scripts to Datadog or OTLP endpoints

**Why use this logic?** Modern microservices don't write to disk. They leverage real-time transit HTTP protocols to ship structured telemetry streams over the network. Scripting POST methods is the backbone of integration strategies with Datadog and Elasticsearch.

**Python Script:**
```python
import json
# import requests # Used in production

def send_to_datadog(log_payload, api_key):
    # 1. Construct endpoint targeting the standard HTTP intake for Datadog V2 Logs
    url = "https://http-intake.logs.datadoghq.com/api/v2/logs"
    
    # 2. Add secure application keys to HTTP headers
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "DD-API-KEY": api_key
    }
    
    # 3. Ship data array
    # response = requests.post(url, headers=headers, data=json.dumps([log_payload]))
    # return response.status_code
    
    # Note: Returning mocked integer for dry-run representation.
    payload_dump = json.dumps([log_payload], indent=2)
    return f"Simulating POST to {url}\nHeaders: DD-API-KEY: ***\nPayload:\n{payload_dump}\n\nStatus Response: 202 Accepted"

sample = {"service": "vault-script", "level": "INFO", "message": "Keys rotated."}
print(send_to_datadog(sample, "fake_api_key_hidden"))
```

**Output of the script:**
```text
Simulating POST to https://http-intake.logs.datadoghq.com/api/v2/logs
Headers: DD-API-KEY: ***
Payload:
[
  {
    "service": "vault-script",
    "level": "INFO",
    "message": "Keys rotated."
  }
]

Status Response: 202 Accepted
```

---

With these 15 patterns, you establish a solid bedrock for observability pipelines capable of maintaining production stability across complex distributed software arrays.
