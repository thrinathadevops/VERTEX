# Calculator Formulas & Parameters Reference

> **Base inputs for all calculators:** `cpu_cores`, `ram_gb`, `expected_rps`, `avg_response_ms`, `os_type`
>
> **Base formula:** `concurrency = ceil(RPS × (response_ms / 1000))`
>
> **Example:** 10,000 RPS × 120ms / 1000 = **1,200 concurrent connections**

---

## Changelog — What Changed & Why

### Session: 2026-03-05 — Practical Enhancements in Active `calculator_engine.py`

- **Audit mode hardened for real payloads**:
  - Reads current values from top-level fields **and** nested `existing/current` blocks.
  - Supports loose-but-safe matching for units (`60s` vs `60000ms`, `1gb` vs `1024mb`), booleans (`on/yes/true`), and spacing.
  - Returns operator-friendly audit findings with summary counts: matches vs mismatches.
- **Per-distro conntrack in active path improved**:
  - RHEL 8/9 uses higher conntrack targets + hashsize recommendations.
  - CentOS 7 uses safer lower baseline tuned for older kernels.
  - Amazon Linux includes conntrack + MTU probing practical command.
- **Operationalization improvements**:
  - Linux tuning output now includes explicit apply/persist step (`sysctl --system`) and conntrack verification hint.

### Session: 2026-03-05 — Old `varex-calculators` Analysis & Cleanup

**What was `varex-calculators/`?**

A standalone microservice folder inside `varex_backend/` with 18 separate Python calculator files (~400KB total), each having 700+ lines with detailed formula-backed explanations, Pydantic schemas, audit mode, and HA suggestions.

**Why was it removed?**

- **11 of 18 files had Python syntax errors** — multiline strings used literal newlines inside regular (non-triple-quoted) strings. These files **never compiled and were never deployed**.
- Only 7 files were syntactically valid Python.
- The folder was a **work-in-progress** that was never integrated into the running API.

**What the old code had that was better (planned for future enhancement):**

| Feature | Current `calculator_engine.py` | Old `varex-calculators/` (broken) |
|---|---|---|
| **NGINX `worker_connections` formula** | `max(1024, min(65535, concurrency ÷ workers × 4))` — RPS-driven | `floor(RAM_per_worker_KB ÷ (16KB + avg_response_kb + 64KB_ssl))` — **RAM-capacity driven** (more accurate) |
| **Redis `maxmemory` reservation** | `int(ram × 0.7)` — flat 70% | Breakdown: 20% OS, 10% fragmentation, 10% COW fork, 5% AOF buffer = **55% usable** (more conservative, safer) |
| **Tomcat thread formula** | `max(25, min(800, concurrency + 50))` — simple clamp | **Goetz formula**: `N = U × C × (1 + W/C)` where U=target CPU util, C=cores, W=wait time (industry standard) |
| **Param explanations** | 1-line: e.g., "Zero-copy for static content" | 4-6 lines: e.g., "sendfile(): zero-copy transfer from disk → socket via kernel, bypassing userspace. Without it: read() to userspace buffer → write() to socket = 2 memory copies. tcp_nopush: batch small TCP segments..." |
| **OS tuning** | 14 sysctl commands (Linux), basic | 22+ params with BBR congestion control, THP disable, conntrack per-distro, BDP-based buffer sizing |
| **Audit mode** | Not implemented | Per-parameter diff against current values with severity ratings |
| **HA suggestions** | Not present | 6+ specific suggestions per calculator (e.g., "Use shared Redis for TLS session tickets") |
| **Config snippets** | Basic key=value | Full production-ready config with section comments and explanations |

**Current state: `calculator_engine.py` (728 lines, WORKING)**

| Metric | Value |
|---|---|
| Calculators | 16 (all working) |
| Total params | ~220+ |
| Config snippets | ✅ All 16 |
| OS tuning | ✅ Linux (14 cmds), Windows (5), Solaris (4), AIX (5), HP-UX (4) |
| Degradation checks | ✅ Per-calculator |
| API contract | `calculate(calculator, payload) → dict` — unchanged |

**Future improvements planned** (from the old code analysis):

1. **RAM-based NGINX worker_connections** — use memory cost per connection instead of RPS ratio
2. **Goetz thread formula for Tomcat** — `N = U × C × (1 + W/C)` for scientifically optimal thread count
3. **Redis COW-aware memory reservation** — account for fork(), fragmentation, AOF buffer
4. **BBR congestion control** — add `net.ipv4.tcp_congestion_control=bbr` to OS tuning
5. **THP disable for Redis/JVM** — `echo never > /sys/kernel/mm/transparent_hugepage/enabled`
6. **Per-distro conntrack tuning** — RHEL 8/9 vs CentOS 7 vs Amazon Linux
7. **Deep formula explanations** — 4-6 line WHY explanations per parameter
8. **Audit mode** — compare current config values against recommendations

---

## Summary: Parameter Counts per Calculator

| # | Calculator | Smart Inputs | Computed Params | Degradation Checks | Config Snippet | OS Tuning |
|---|---|---|---|---|---|---|
| 1 | NGINX | 8 | **30** (max with SSL+proxy+gzip) | 5 | ✅ nginx.conf | ✅ |
| 2 | Redis | 5 | **19** (max with AOF+cluster) | 3 | ✅ redis.conf | ✅ |
| 3 | Tomcat | 6 | **18** (max with SSL+compression+JMX) | 3 | ✅ JAVA_OPTS + server.xml | ✅ |
| 4 | Apache HTTPD | 4 | **17** (max with SSL+event MPM) | 2 | ✅ httpd.conf | ✅ |
| 5 | OHS | 2 | **19** (HTTPD base + OHS extras) | 2 | ✅ ohs.conf | ✅ |
| 6 | IHS | 2 | **18** (HTTPD base + IHS extras) | 2 | ✅ ihs.conf | ✅ |
| 7 | IIS | 4 | **13** (max with SSL+compress+cache) | 0 | ✅ web.config | ✅ |
| 8 | PostgreSQL | 5 | **16** (+ 2 OLAP overrides) | 2 | ✅ postgresql.conf | ✅ |
| 9 | MySQL | 5 | **16** | 1 | ✅ my.cnf | ✅ |
| 10 | MongoDB | 5 | **9** (+ 2 with replica set) | 1 | ✅ mongod.conf | ✅ |
| 11 | HAProxy | 4 | **14** (max with SSL termination) | 1 | ✅ haproxy.cfg | ✅ |
| 12 | Kubernetes | 5 | **12** (max with HPA+PDB) | 0 | ✅ deployment.yaml | ✅ |
| 13 | Docker | 3 | **8** | 0 | ✅ daemon.json | ✅ |
| 14 | Podman | 3 | **8** (+ rootless) | 0 | ✅ containers.conf | ✅ |
| 15 | Linux OS | 2 | **16** | 0 | ✅ sysctl.conf | ✅ |
| 16 | RabbitMQ | 4 | **10** (max with cluster) | 2 | ✅ rabbitmq.conf | ✅ |

**Total: ~220+ unique parameters computed across all calculators**

---

## 1. NGINX (up to 30 params)

### Smart Inputs

| Input | Type | Example |
|---|---|---|
| `avg_response_kb` | number | 50 |
| `ssl_enabled` | boolean | true |
| `reverse_proxy` | boolean | true |
| `static_pct` | number (0-100) | 30 |
| `keepalive_enabled` | boolean | true |
| `gzip_enabled` | boolean | true |
| `http2_enabled` | boolean | true |
| `client_max_body_size_mb` | number | 10 |

### Formulas

| Parameter | Formula | Example (8 CPU, 32GB, 10K RPS, 120ms) |
|---|---|---|
| `worker_processes` | `= cpu_cores` (auto) | `auto` (8) |
| `worker_connections` | `max(1024, min(65535, concurrency ÷ workers × 4))` | `max(1024, min(65535, 1200÷8×4))` = **1024** |
| `worker_rlimit_nofile` | `= worker_connections × 2` | `1024 × 2` = **2048** |
| `keepalive_timeout` | `65s` if enabled, `0` if disabled | **65s** |
| `client_max_body_size` | `= user input` (MB) | **10m** |
| `sendfile` | Fixed `on` | **on** |
| `tcp_nopush` | Fixed `on` | **on** |
| `tcp_nodelay` | Fixed `on` | **on** |
| `multi_accept` | Fixed `on` | **on** |
| `open_file_cache` | `max(10000, worker_connections × 20)` | `max(10000, 1024×20)` = **max=20480 inactive=20s** |
| `open_file_cache_valid` | Fixed `30s` | **30s** |
| `send_timeout` | `60s` (reverse proxy) or `30s` (normal) | **60s** |
| `gzip` | `on` if gzip_enabled | **on** |
| `gzip_comp_level` | Fixed `4` (balance ratio vs CPU) | **4** |
| `gzip_min_length` | Fixed `256` | **256** |
| `gzip_types` | Fixed standard compressible MIME types | **text/plain text/css application/json...** |
| `ssl_protocols` | Fixed `TLSv1.2 TLSv1.3` (if SSL) | **TLSv1.2 TLSv1.3** |
| `ssl_ciphers` | Fixed modern ECDHE suite (if SSL) | **ECDHE-ECDSA-AES128-GCM-SHA256:...** |
| `ssl_session_cache` | Fixed `shared:SSL:50m` (if SSL) | **shared:SSL:50m** |
| `ssl_session_timeout` | Fixed `1d` (if SSL) | **1d** |
| `ssl_prefer_server_ciphers` | Fixed `on` (if SSL) | **on** |
| `http2` | `on` if SSL + HTTP/2 enabled | **on** |
| `proxy_connect_timeout` | Fixed `60s` (if reverse proxy) | **60s** |
| `proxy_read_timeout` | `max(60, response_ms × 3 ÷ 1000 + 30)` s | `max(60, 120×3÷1000+30)` = **60s** |
| `proxy_send_timeout` | `= send_timeout` (if reverse proxy) | **60s** |
| `proxy_buffers` | `max(4, min(32, concurrency ÷ 1000 + 4))` count × buffer_size | `5 32k` |
| `proxy_buffer_size` | `16k` if avg_response < 32KB, else `32k` | avg=50KB → **32k** |
| `proxy_http_version` | Fixed `1.1` (if reverse proxy) | **1.1** |
| `proxy_set_header` | Fixed `Connection ""` (if reverse proxy) | **Connection ""** |
| `access_log` | Recommendation: `off or buffered` | **off or buffered** |
| `error_log` | Recommendation: `warn` level | **/var/log/nginx/error.log warn** |

### Degradation Triggers

| Trigger | Condition | Risk |
|---|---|---|
| High worker_connections | `> 16384` | ~1KB RAM + fd per connection → OOM under burst |
| High keepalive_timeout | `> 60s` and keepalive on | Holds sockets open, exhausts connection slots |
| Gzip at extreme RPS | `RPS > 50,000` and gzip on | Significant CPU consumption |
| SSL without HTTP/2 | SSL on, HTTP/2 off | Each resource needs separate TLS handshake |
| Large body size | `client_max_body > 100MB` | Big uploads block worker connections |
| **Capacity warning** | `concurrency > workers × worker_conn × 0.8` | Approaching system limit |

### Example Config Snippet Output

```nginx
# NGINX Production Config — 8 cores, 32GB RAM, 10000 RPS
worker_processes auto;  # 8 cores
worker_rlimit_nofile 2048;
events {
    worker_connections 1024;
    multi_accept on;
    use epoll;
}
http {
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    client_max_body_size 10m;
    gzip on;
    gzip_comp_level 4;
    gzip_min_length 256;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    proxy_connect_timeout 60s;
    proxy_read_timeout 60s;
    proxy_buffers 5 32k;
}
```

---

## 2. Redis (up to 19 params)

### Smart Inputs

| Input | Type | Example |
|---|---|---|
| `estimated_keys` | number | 5,000,000 |
| `avg_key_size_bytes` | number | 512 |
| `persistence_type` | select: aof/rdb/none | aof |
| `cluster_enabled` | boolean | false |
| `password_enabled` | boolean | true |

### Formulas

| Parameter | Formula | Example (8 CPU, 32GB, 5M keys, 512B avg) |
|---|---|---|
| `maxmemory` | `int(ram_gb × 0.7)` GB | `int(32 × 0.7)` = **22gb** |
| `dataset_estimate` | `keys × avg_key_size ÷ 1024³` GB | `5M × 512 ÷ 1073741824` = **2.38GB** |
| `maxmemory-policy` | Fixed `allkeys-lru` | **allkeys-lru** |
| `tcp-backlog` | `max(511, min(65535, concurrency))` | `max(511, min(65535, 1200))` = **1200** |
| `hz` | `100` if RPS > 10K, else `10` | RPS=10K → **100** |
| `io-threads` | `min(cpu, 4)` if cpu ≥ 4, else `1` | `min(8, 4)` = **4** |
| `io-threads-do-reads` | Fixed `yes` | **yes** |
| `timeout` | Fixed `300` (5min) | **300** |
| `tcp-keepalive` | Fixed `300` | **300** |
| `appendonly` | `yes` if persistence=aof | **yes** |
| `appendfsync` | Fixed `everysec` (if AOF) | **everysec** |
| `auto-aof-rewrite-percentage` | Fixed `100` (if AOF) | **100** |
| `auto-aof-rewrite-min-size` | Fixed `64mb` (if AOF) | **64mb** |
| `save` | `900 1 300 10 60 10000` (if RDB) | **900 1 300 10 60 10000** |
| `lazyfree-lazy-eviction` | Fixed `yes` | **yes** |
| `lazyfree-lazy-expire` | Fixed `yes` | **yes** |
| `lazyfree-lazy-server-del` | Fixed `yes` | **yes** |
| `cluster-enabled` | `yes` if cluster mode | **no** |
| `cluster-node-timeout` | Fixed `15000` (if cluster) | **15000** |
| `protected-mode` | Fixed `yes` | **yes** |
| `rename-command FLUSHALL` | Fixed `""` | **""** |

### Degradation Triggers

| Trigger | Condition | Risk |
|---|---|---|
| Dataset > Memory | `dataset_gb > maxmemory_gb` | Aggressive eviction, data loss |
| AOF high RPS | `persistence=aof` and `RPS > 50K` | I/O pressure from fsync |
| High hz low CPU | `hz=100` and `cpu < 4` | Timer overhead steals CPU cycles |

---

## 3. Tomcat (up to 18 params)

### Smart Inputs

| Input | Type | Example |
|---|---|---|
| `app_type` | select: rest/webapp/microservice | rest |
| `ssl_enabled` | boolean | true |
| `max_upload_mb` | number | 50 |
| `session_timeout_min` | number | 30 |
| `enable_compression` | boolean | true |
| `jmx_enabled` | boolean | true |

### Formulas

| Parameter | Formula | Example (8 CPU, 32GB, 10K RPS, 120ms) |
|---|---|---|
| `maxThreads` | `max(25, min(800, concurrency + 50))` | `max(25, min(800, 1250))` = **800** |
| `minSpareThreads` | `max(10, maxThreads ÷ 10)` | `max(10, 80)` = **80** |
| `maxConnections` | `max(maxThreads, concurrency × 2)` | `max(800, 2400)` = **2400** |
| `acceptCount` | `max(100, maxThreads ÷ 2)` | `max(100, 400)` = **400** |
| `connectionTimeout` | `max(5000, min(60000, response_ms × 3))` ms | `max(5000, min(60000, 360))` = **5000ms** |
| `-Xmx / -Xms` | `max(256, int(ram × 1024 × 0.65))` MB | `int(32×1024×0.65)` = **21299m** |
| `-XX:MetaspaceSize` | `max(256, min(512, heap ÷ 8))` MB | `max(256, min(512, 2662))` = **512m** |
| GC algorithm | `G1GC` if heap > 4096MB, else `ParallelGC` | heap=21299 → **G1GC** |
| `protocol` | Fixed `Http11NioProtocol` | **Http11NioProtocol** |
| `maxKeepAliveRequests` | Fixed `100` | **100** |
| `keepAliveTimeout` | Fixed `20000` (20s) | **20000** |
| `max-swallow-size` | `= max_upload_mb` | **50MB** |
| `session-timeout` | `= session_timeout_min` | **30min** |
| `compression` | `on` if enabled | **on** |
| `compressibleMimeType` | Fixed standard types | **text/html,text/xml,...** |
| `sslProtocol` | Fixed `TLSv1.2+TLSv1.3` (if SSL) | **TLSv1.2+TLSv1.3** |
| `HeapDumpOnOutOfMemoryError` | Fixed `enabled` | **enabled** |
| `MaxGCPauseMillis` | Fixed `200` | **200** |

### Degradation Triggers

| Trigger | Condition | Risk |
|---|---|---|
| High threads | `maxThreads > 500` | Context switching overhead, ~1MB stack/thread |
| Heap vs RAM | `heap > ram × 1024 × 0.8` | No room for OS buffers → OOM killer |
| Long timeout | `connectionTimeout > 30000ms` | Slow clients hold threads |

---

## 4. Apache HTTPD / OHS / IHS (up to 19 params)

### Smart Inputs

| Input | Type | Example |
|---|---|---|
| `ssl_enabled` | boolean | true |
| `mpm_type` | select: event/worker/prefork | event |
| `server_limit` | number | 16 |
| `max_clients` (OHS only) | number | 1000 |
| `max_request_workers` (IHS only) | number | 1000 |

### Formulas

| Parameter | Formula | Example (8 CPU, 32GB, 10K RPS, 120ms) |
|---|---|---|
| `MaxRequestWorkers` | `max(150, min(8192, concurrency + 100))` | `max(150, min(8192, 1300))` = **1300** |
| `ThreadsPerChild` | `25` (worker/event), `0` (prefork) | **25** |
| `ServerLimit` | `max(user_input, MaxRequestWorkers ÷ ThreadsPerChild)` | `max(16, 52)` = **52** |
| `StartServers` | `max(2, cpu ÷ 2)` | `max(2, 4)` = **4** |
| `MaxSpareThreads` | `max(StartServers × 2, MaxRequestWorkers ÷ 4)` | `max(8, 325)` = **325** |
| `MinSpareThreads` | `max(StartServers, MaxSpareThreads ÷ 2)` | `max(4, 162)` = **162** |
| `KeepAliveTimeout` | Fixed `5s` | **5s** |
| `MaxKeepAliveRequests` | `max(100, RPS ÷ 10)` | `max(100, 1000)` = **1000** |
| `Timeout` | `max(30, response_ms × 3 ÷ 1000 + 10)` s | `max(30, 10)` = **30s** |
| `LimitRequestLine` | Fixed `8190` | **8190** |
| `LimitRequestBody` | Fixed `1048576` | **1048576** |
| `ListenBacklog` | `max(511, concurrency ÷ 2)` | `max(511, 600)` = **600** |
| `SSLProtocol` | Fixed `all -SSLv3 -TLSv1 -TLSv1.1` | **all -SSLv3 -TLSv1 -TLSv1.1** |
| `SSLCipherSuite` | Fixed `ECDHE:!COMPLEMENTOFDEFAULT` | **ECDHE:!COMPLEMENTOFDEFAULT** |
| `SSLSessionCache` | Fixed `shmcb:/path(512000)` | **shmcb:/path(512000)** |
| `EnableMMAP` | Fixed `on` | **on** |
| `EnableSendfile` | Fixed `on` | **on** |
| `MaxClients` (OHS) | `max(150, user_input)` | **1000** |
| `MaxRequestsPerChild` (OHS) | Fixed `10000` | **10000** |
| `MaxConnectionsPerChild` (IHS) | Fixed `100000` | **100000** |

### Degradation Triggers

| Trigger | Condition | Risk |
|---|---|---|
| Prefork at high RPS | `mpm=prefork` and `RPS > 5000` | One process per connection → massive memory |
| Very large worker pool | `MaxRequestWorkers > 4096` | Scheduling overhead, horizontal scaling preferred |

---

## 5. IIS (up to 13 params)

### Smart Inputs

| Input | Type | Example |
|---|---|---|
| `dotnet_type` | select: core/framework | core |
| `ssl_enabled` | boolean | true |
| `enable_compression` | boolean | true |
| `enable_caching` | boolean | true |

### Formulas

| Parameter | Formula | Example (8 CPU, 32GB, 10K RPS, 120ms) |
|---|---|---|
| `maxConcurrentRequestsPerCPU` | `(concurrency + 200) ÷ cpu` | `1400 ÷ 8` = **175** |
| `appConcurrentRequestLimit` | `max(500, concurrency + 200)` | **1400** |
| `queueLength` | `max(1000, concurrency ÷ 2)` | `max(1000, 600)` = **1000** |
| `connectionTimeout` | `max(60, response_ms × 3 ÷ 1000 + 30)` s | **60s** |
| `idleTimeout` | Fixed `20` min | **20min** |
| `rapidFailProtection` | Fixed `True` | **True** |
| `recycling.periodicRestart` | Fixed `29h` | **29h** |
| `maxUrlSegments` | Fixed `32` | **32** |
| `sslFlags` | Fixed `Ssl, SslNegotiateCert` (if SSL) | **Ssl, SslNegotiateCert** |
| `dynamicCompression` | `True` if compression enabled | **True** |
| `staticCompression` | `True` if compression enabled | **True** |
| `outputCaching` | `True` if caching enabled | **True** |

---

## 6. PostgreSQL (up to 18 params)

### Smart Inputs

| Input | Type | Example |
|---|---|---|
| `max_connections` | number | 300 |
| `disk_type` | select: ssd/hdd/nvme | ssd |
| `workload` | select: oltp/olap/mixed | oltp |
| `wal_level` | select: replica/minimal/logical | replica |
| `ssl_enabled` | boolean | true |

### Formulas

| Parameter | Formula | Example (8 CPU, 32GB, 300 conns, SSD) |
|---|---|---|
| `shared_buffers` | `int(ram × 1024 × 0.25)` MB | `32 × 1024 × 0.25` = **8192MB** |
| `effective_cache_size` | `int(ram × 1024 × 0.75)` MB | `32 × 1024 × 0.75` = **24576MB** |
| `work_mem` | `max(4, int(ram × 1024 × 0.25 ÷ conns))` MB | `max(4, 8192÷300)` = **27MB** |
| `maintenance_work_mem` | `max(64, int(ram × 1024 × 0.05))` MB | `max(64, 1638)` = **1638MB** |
| `wal_buffers` | `max(16, shared_buffers ÷ 32)` MB | `max(16, 256)` = **256MB** |
| `checkpoint_completion_target` | Fixed `0.9` | **0.9** |
| `random_page_cost` | `1.1` (SSD) or `4.0` (HDD) | SSD → **1.1** |
| `effective_io_concurrency` | `200` (SSD) or `2` (HDD) | SSD → **200** |
| `max_wal_size` | `max(1, int(ram × 0.25))` GB | `max(1, 8)` = **8GB** |
| `max_parallel_workers_per_gather` | `min(4, cpu - 2)` | `min(4, 6)` = **4** |
| `max_parallel_workers` | `max(0, cpu - 2)` | **6** |
| `huge_pages` | `try` if ram ≥ 32GB, else `off` | 32GB → **try** |
| `max_connections` | `= user input` | **300** |
| `wal_level` | `= user input` | **replica** |
| `log_min_duration_statement` | Fixed `1000` (1s) | **1000** |
| OLAP: `max_parallel_workers_per_gather` | `min(8, cpu)` (override) | OLAP → **8** |
| OLAP: `work_mem` | `work_mem × 4` (override) | OLAP → **108MB** |

### Degradation Triggers

| Trigger | Condition | Risk |
|---|---|---|
| Memory overflow | `conns × work_mem > ram × 1024 × 0.5` | OOM under concurrent complex queries |
| High connections | `conns > 500` | Per-connection overhead → use PgBouncer |

---

## 7. MySQL (16 params)

### Smart Inputs

| Input | Type | Example |
|---|---|---|
| `max_connections` | number | 300 |
| `disk_type` | select: ssd/hdd/nvme | ssd |
| `workload` | select: oltp/olap/mixed | oltp |
| `replication` | boolean | false |
| `ssl_enabled` | boolean | true |

### Formulas

| Parameter | Formula | Example (8 CPU, 32GB, 300 conns, SSD) |
|---|---|---|
| `innodb_buffer_pool_size` | `int(ram × 1024 × 0.7)` MB | `32 × 1024 × 0.7` = **22938MB** |
| `innodb_buffer_pool_instances` | `max(1, min(64, pool ÷ 1024))` | `min(64, 22)` = **22** |
| `innodb_log_file_size` | `max(48, pool ÷ 4)` MB | `max(48, 5734)` = **5734MB** |
| `innodb_log_buffer_size` | `max(16, min(256, pool ÷ 32))` MB | `max(16, min(256, 717))` = **256MB** |
| `innodb_flush_method` | `O_DIRECT` (SSD) or `fsync` (HDD) | SSD → **O_DIRECT** |
| `innodb_io_capacity` | `2000` (SSD) or `200` (HDD) | SSD → **2000** |
| `innodb_io_capacity_max` | `io_capacity × 2` | `2000 × 2` = **4000** |
| `max_connections` | `= user input` | **300** |
| `thread_cache_size` | `max(8, min(100, conns ÷ 4))` | `max(8, min(100, 75))` = **75** |
| `table_open_cache` | `max(400, conns × 2)` | `max(400, 600)` = **600** |
| `tmp_table_size` | `max(16, int(ram × 1024 × 0.02))` MB | `max(16, 655)` = **655MB** |
| `innodb_flush_log_at_trx_commit` | Fixed `1` (full ACID) | **1** |
| `sync_binlog` | Fixed `1` | **1** |
| `innodb_file_per_table` | Fixed `ON` | **ON** |
| `slow_query_log` | Fixed `ON` | **ON** |
| `long_query_time` | Fixed `1` (1s) | **1** |

### Degradation Triggers

| Trigger | Condition | Risk |
|---|---|---|
| Pool too large | `pool > ram × 1024 × 0.85` | No room for OS cache, connections, tmp tables |

---

## 8. MongoDB (up to 11 params)

### Smart Inputs

| Input | Type | Example |
|---|---|---|
| `max_connections` | number | 500 |
| `disk_type` | select: ssd/hdd/nvme | ssd |
| `replica_set` | boolean | true |
| `sharding` | boolean | false |
| `auth_enabled` | boolean | true |

### Formulas

| Parameter | Formula | Example (8 CPU, 32GB, 500 conns) |
|---|---|---|
| `wiredTiger.cacheSizeGB` | `max(1, int((ram - 1) × 0.5))` | `max(1, int(31×0.5))` = **15** |
| `net.maxIncomingConnections` | `= user input` | **500** |
| `storage.journal.enabled` | Fixed `true` | **true** |
| `replication.oplogSizeMB` | `max(990, int(ram × 1024 × 0.05))` | `max(990, 1638)` = **1638** |
| `operationProfiling.slowOpThresholdMs` | Fixed `100` | **100** |
| `wiredTigerConcurrentReadTransactions` | `max(128, cpu × 16)` | `max(128, 128)` = **128** |
| `wiredTigerConcurrentWriteTransactions` | `max(128, cpu × 16)` | **128** |
| `replication.replSetName` (if RS) | Fixed `rs0` | **rs0** |
| `net.bindIp` (if RS) | Fixed `0.0.0.0` | **0.0.0.0** |

### Degradation Triggers

| Trigger | Condition | Risk |
|---|---|---|
| Very high connections | `conns > 10,000` | ~1MB each stack → use connection pooling |

---

## 9. HAProxy (up to 14 params)

### Smart Inputs

| Input | Type | Example |
|---|---|---|
| `backends_count` | number | 10 |
| `ssl_termination` | boolean | true |
| `http_mode` | boolean | true |
| `health_check_interval_s` | number | 5 |

### Formulas

| Parameter | Formula | Example (8 CPU, 10 backends, conc=1200) |
|---|---|---|
| `global.maxconn` | `max(1000, concurrency × 2)` | `max(1000, 2400)` = **2400** |
| `global.nbthread` | `= cpu_cores` | **8** |
| `defaults.timeout connect` | `max(5000, response_ms × 2)` ms | `max(5000, 240)` = **5000ms** |
| `defaults.timeout client` | `max(30000, response_ms × 10)` ms | `max(30000, 1200)` = **30000ms** |
| `defaults.timeout server` | `max(30000, response_ms × 10)` ms | **30000ms** |
| `defaults.timeout http-keep-alive` | Fixed `10s` | **10s** |
| `frontend maxconn` | `= global.maxconn` | **2400** |
| `server maxconn` | `max(100, global_maxconn ÷ backends)` | `max(100, 240)` = **240** |
| `balance` | Fixed `leastconn` | **leastconn** |
| `option http-server-close` | Fixed `enabled` | **enabled** |
| `option forwardfor` | Fixed `enabled` | **enabled** |
| `ssl-default-bind-ciphers` (if SSL) | Fixed `ECDHE+AESGCM` | **ECDHE+AESGCM** |
| `ssl-default-bind-options` (if SSL) | Fixed `no-sslv3 no-tlsv10 no-tlsv11` | **no-sslv3 no-tlsv10 no-tlsv11** |
| `tune.ssl.default-dh-param` (if SSL) | Fixed `2048` | **2048** |

### Degradation Triggers

| Trigger | Condition | Risk |
|---|---|---|
| Very high maxconn | `maxconn > 100,000` | ~32KB per connection → verify RAM |

---

## 10. Kubernetes (up to 12 params)

### Smart Inputs

| Input | Type | Example |
|---|---|---|
| `replicas` | number | 3 |
| `workload_type` | select: web/database/worker/mixed | web |
| `hpa_enabled` | boolean | true |
| `pdb_enabled` | boolean | true |
| `ingress_enabled` | boolean | true |

### Formulas

| Parameter | Formula | Example (8 CPU, 32GB, 3 replicas) |
|---|---|---|
| `replicas` | `= user input` | **3** |
| `resources.requests.cpu` | `int((cpu ÷ replicas) × 1000 × 0.7)` m | `int((8÷3)×700)` = **1866m** |
| `resources.limits.cpu` | `int((cpu ÷ replicas) × 1000)` m | `int((8÷3)×1000)` = **2666m** |
| `resources.requests.memory` | `int((ram ÷ replicas) × 1024 × 0.7)` Mi | `int((32÷3)×716.8)` = **7645Mi** |
| `resources.limits.memory` | `int((ram ÷ replicas) × 1024 × 0.9)` Mi | `int((32÷3)×921.6)` = **9830Mi** |
| `HPA minReplicas` | `= replicas` | **3** |
| `HPA maxReplicas` | `= replicas × 4` | **12** |
| `HPA targetCPU` | Fixed `70%` | **70%** |
| `PDB minAvailable` | `max(1, replicas - 1)` | **2** |
| `terminationGracePeriodSeconds` | Fixed `30` | **30** |
| `livenessProbe.initialDelaySeconds` | Fixed `15` | **15** |
| `readinessProbe.initialDelaySeconds` | Fixed `5` | **5** |

---

## 11. Docker / Podman (up to 8 params)

### Smart Inputs

| Input | Type | Example |
|---|---|---|
| `workload_type` | select: web/database/worker/mixed | web |
| `replicas` (Podman) | number | 2 |
| `rootless` (Podman) | boolean | true |
| `compose` (Docker) | boolean | true |
| `swarm` (Docker) | boolean | false |

### Computed Parameters

| Parameter | Value | Details |
|---|---|---|
| `storage-driver` | `overlay2` | Best performance and compatibility |
| `log-driver` | `json-file` | Default structured logging |
| `log-opts.max-size` | `100m` | Limit log file growth |
| `log-opts.max-file` | `5` | Rotate log files |
| `default-ulimits.nofile` | `65535:65535` | Container file descriptor limit |
| `default-ulimits.nproc` | `65535:65535` | Container process limit |
| `live-restore` | `true` | Keep containers on daemon restart |
| `userland-proxy` (Docker) | `false` | Use iptables for better performance |
| `rootless mode` (Podman) | `enabled` if rootless | Unprivileged containers |

---

## 12. Linux OS (16 params)

### Smart Inputs

| Input | Type | Example |
|---|---|---|
| `workload_type` | select: web/database/mixed/compute/storage | web |
| `disk_type` | select: ssd/hdd/nvme | ssd |

### Formulas

| Parameter | Formula | Example (web, SSD, 32GB) |
|---|---|---|
| `vm.swappiness` | `1` (database) or `10` (web) | web → **10** |
| `vm.dirty_ratio` | `40%` (database) or `20%` (web) | web → **20%** |
| `vm.dirty_background_ratio` | `10%` (database) or `5%` (web) | web → **5%** |
| `vm.overcommit_memory` | `1` (database) or `0` (web) | web → **0** |
| `net.core.somaxconn` | Fixed `65535` | **65535** |
| `net.ipv4.tcp_max_syn_backlog` | Fixed `65535` | **65535** |
| `net.ipv4.tcp_tw_reuse` | Fixed `1` | **1** |
| `net.ipv4.tcp_fin_timeout` | Fixed `15` | **15** |
| `net.ipv4.ip_local_port_range` | Fixed `1024 65535` | **1024 65535** |
| `fs.file-max` | `max(2097152, int(ram × 1024 × 256))` | `max(2097152, 8388608)` = **8388608** |
| `net.core.rmem_max` | Fixed `16777216` (16MB) | **16777216** |
| `net.core.wmem_max` | Fixed `16777216` (16MB) | **16777216** |
| `kernel.pid_max` | Fixed `65536` | **65536** |
| THP | `madvise` (database) or `always` (web) | web → **always** |
| I/O Scheduler | `none/noop` (SSD) or `mq-deadline` (HDD) | SSD → **none** |
| CPU Governor | Fixed `performance` | **performance** |

---

## 13. RabbitMQ (up to 10 params)

### Smart Inputs

| Input | Type | Example |
|---|---|---|
| `queue_count` | number | 200 |
| `consumers` | number | 50 |
| `cluster_enabled` | boolean | true |
| `ssl_enabled` | boolean | true |

### Formulas

| Parameter | Formula | Example (8 CPU, 32GB, 200 queues, 50 consumers) |
|---|---|---|
| `vm_memory_high_watermark` | `0.4` if ram ≥ 16GB, else `0.3` (capped 0.2–0.6) | 32GB → **0.4** |
| `disk_free_limit` | `max(50, int(ram × 1024 × 0.1))` MB | `max(50, 3276)` = **3276MB** |
| `channel_max` | `max(128, consumers × 4)` | `max(128, 200)` = **200** |
| `heartbeat` | Fixed `60` | **60** |
| `consumer_timeout` | Fixed `1800000` (30min) | **1800000** |
| `prefetch_count` | `max(1, min(250, RPS ÷ consumers))` | `max(1, min(250, 200))` = **200** |
| `queue_index_embed_msgs_below` | Fixed `4096` | **4096** |
| `cluster_formation.peer_discovery_backend` (if cluster) | Fixed `classic_config` | **classic_config** |
| `ha-mode` (if cluster) | Fixed `all` | **all** |
| `ha-sync-mode` (if cluster) | Fixed `automatic` | **automatic** |

### Degradation Triggers

| Trigger | Condition | Risk |
|---|---|---|
| Excessive queues | `> 10,000` | Memory for metadata → use lazy queues/streams |
| Channel exhaustion | `consumers > channel_max` | Connection failures |

---

## OS Tuning Commands (auto-generated per OS)

| OS Family | # Commands | Tool | Example Command |
|---|---|---|---|
| **Linux** (RHEL, Ubuntu, etc.) | 14 | `sysctl`, `ulimit`, `limits.conf` | `sysctl -w net.core.somaxconn=65535` |
| **Windows Server** | 5 | `reg add`, `netsh` | `reg add ...MaxUserPort /t REG_DWORD /d 65534` |
| **Solaris** | 4 | `ndd`, `/etc/system` | `ndd -set /dev/tcp tcp_conn_req_max_q 65535` |
| **AIX** | 5 | `no`, `chdev`, `ulimit` | `no -o somaxconn=65535` |
| **HP-UX** | 4 | `ndd`, `kctune` | `kctune nfile=65535` |

### Linux OS Tuning (14 commands)

```bash
sysctl -w net.core.somaxconn={somaxconn}
sysctl -w net.ipv4.tcp_max_syn_backlog={somaxconn}
sysctl -w net.ipv4.tcp_tw_reuse=1
sysctl -w net.ipv4.tcp_fin_timeout=15
sysctl -w net.ipv4.tcp_keepalive_time=600
sysctl -w net.ipv4.tcp_keepalive_intvl=15
sysctl -w net.ipv4.tcp_keepalive_probes=5
sysctl -w net.core.netdev_max_backlog={max(65536, somaxconn)}
sysctl -w net.core.rmem_max=16777216
sysctl -w net.core.wmem_max=16777216
sysctl -w fs.file-max={max(2097152, file_limit×4)}
ulimit -n {file_limit}
# /etc/security/limits.conf: * soft nofile {file_limit}
# /etc/security/limits.conf: * hard nofile {file_limit}
```

### Windows OS Tuning (5 commands)

```powershell
netsh int tcp set global autotuninglevel=normal
reg add HKLM\SYSTEM\...\Tcpip\Parameters /v MaxUserPort /t REG_DWORD /d {min(65534, file_limit)}
reg add HKLM\SYSTEM\...\Tcpip\Parameters /v TcpTimedWaitDelay /t REG_DWORD /d 30
reg add HKLM\SYSTEM\...\Tcpip\Parameters /v EnableDynamicBacklog /t REG_DWORD /d 1
# Set Power Plan to High Performance
```
