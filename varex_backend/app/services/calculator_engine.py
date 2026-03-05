"""Smart Production Calculator Engine — computes maximum parameters from few inputs."""
from __future__ import annotations
import math
from typing import Any

SUPPORTED_CALCULATORS = {
    "nginx","redis","tomcat","httpd","ohs","ihs","iis","podman",
    "k8s","os","postgresql","mysql","mongodb","haproxy","docker","rabbitmq",
}

# ── helpers ──────────────────────────────────────────────
def _f(p: dict, k: str, d: float) -> float:
    try: return float(p.get(k, d))
    except: return d

def _i(p: dict, k: str, d: int) -> int:
    try: return int(float(p.get(k, d)))
    except: return d

def _b(p: dict, k: str, d: bool = False) -> bool:
    v = p.get(k, d)
    if isinstance(v, bool): return v
    return str(v).lower() in ("true","1","yes","on")

def _add(params, name, val, details, impact="MEDIUM", **kw):
    params.append({"name":name,"recommended":str(val),"impact":impact,"details":details,**kw})

def _deg(degradations, name, reason):
    degradations.append({"name":name,"reason":reason,"impact":"DEGRADATION"})


# ── Distro detection ─────────────────────────────────────
def _is_distro(os_type: str, *names) -> bool:
    return any(n in os_type for n in names)

def _is_linux(os_type: str) -> bool:
    return _is_distro(os_type, "rhel","centos","ubuntu","debian","amazon","suse","oracle","rocky","alma","fedora")

# ── OS tuning generator (BBR, THP, conntrack, BDP buffers) ─────
def _os_tuning(p: dict, file_limit: int, somaxconn: int = 65535, *, calculator: str = "") -> dict:
    os_type = str(p.get("os_type","RHEL")).lower()
    ram_gb = max(1, _f(p, "ram_gb", 8))
    cmds = []
    if _is_linux(os_type):
        # BDP-based TCP buffer sizing: BDP = bandwidth(Gbps) × RTT(ms) × 125000
        # For 10Gbps LAN with 1ms RTT: BDP = 10 × 1 × 125000 = 1.25MB
        bdp_bytes = max(16777216, int(ram_gb * 1024 * 1024 * 0.01))  # 1% of RAM, min 16MB
        cmds = [
            f"sysctl -w net.core.somaxconn={somaxconn}",
            f"sysctl -w net.ipv4.tcp_max_syn_backlog={somaxconn}",
            "sysctl -w net.ipv4.tcp_tw_reuse=1",
            "sysctl -w net.ipv4.tcp_fin_timeout=15",
            "sysctl -w net.ipv4.tcp_keepalive_time=600",
            "sysctl -w net.ipv4.tcp_keepalive_intvl=15",
            "sysctl -w net.ipv4.tcp_keepalive_probes=5",
            f"sysctl -w net.core.netdev_max_backlog={max(65536, somaxconn)}",
            # BDP-based buffer sizing instead of fixed 16MB
            f"sysctl -w net.core.rmem_max={bdp_bytes}",
            f"sysctl -w net.core.wmem_max={bdp_bytes}",
            f"sysctl -w net.ipv4.tcp_rmem='4096 87380 {bdp_bytes}'",
            f"sysctl -w net.ipv4.tcp_wmem='4096 65536 {bdp_bytes}'",
            f"sysctl -w fs.file-max={max(2097152, file_limit*4)}",
            f"ulimit -n {file_limit}",
            f"# /etc/security/limits.conf: * soft nofile {file_limit}",
            f"# /etc/security/limits.conf: * hard nofile {file_limit}",
            # BBR congestion control — 2.6x throughput vs Cubic on lossy links
            "sysctl -w net.core.default_qdisc=fq",
            "sysctl -w net.ipv4.tcp_congestion_control=bbr",
            "sysctl -w net.ipv4.tcp_slow_start_after_idle=0",
            "sysctl -w net.ipv4.ip_local_port_range='1024 65535'",
        ]
        # THP disable for Redis, JVM (Tomcat), MongoDB — THP causes latency spikes
        if calculator in ("redis", "tomcat", "mongodb"):
            cmds += [
                "echo never > /sys/kernel/mm/transparent_hugepage/enabled",
                "echo never > /sys/kernel/mm/transparent_hugepage/defrag",
                f"# THP disabled for {calculator}: THP causes 2-5ms latency spikes during",
                f"#   page compaction. Redis/JVM/Mongo use many small allocations that",
                f"#   trigger THP defragmentation, stalling the process.",
            ]
        # Per-distro conntrack tuning (only for proxy/LB workloads)
        if calculator in ("nginx", "haproxy", "httpd", "ohs", "ihs"):
            conntrack_max = max(65536, somaxconn * 4)
            cmds += [
                f"sysctl -w net.netfilter.nf_conntrack_max={conntrack_max}",
                f"sysctl -w net.netfilter.nf_conntrack_tcp_timeout_established=600",
                f"sysctl -w net.netfilter.nf_conntrack_tcp_timeout_time_wait=30",
            ]
            # RHEL/CentOS-specific: conntrack module loading
            if _is_distro(os_type, "rhel", "centos", "rocky", "alma", "oracle"):
                cmds.append("modprobe nf_conntrack  # RHEL: may need 'yum install conntrack-tools'")
            # Amazon Linux: conntrack in different kernel module path
            if _is_distro(os_type, "amazon"):
                cmds.append("modprobe nf_conntrack  # Amazon Linux: pre-loaded on AL2023")
    elif "windows" in os_type:
        cmds = [
            "netsh int tcp set global autotuninglevel=normal",
            f"reg add HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters /v MaxUserPort /t REG_DWORD /d {min(65534, file_limit)}",
            "reg add HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters /v TcpTimedWaitDelay /t REG_DWORD /d 30",
            "reg add HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters /v EnableDynamicBacklog /t REG_DWORD /d 1",
            f"reg add HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters /v MaxFreeTcbs /t REG_DWORD /d {min(65534, somaxconn)}",
            "# Set Power Plan to High Performance:",
            "powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
        ]
    elif "solaris" in os_type:
        cmds = [
            f"ndd -set /dev/tcp tcp_conn_req_max_q {somaxconn}",
            f"ndd -set /dev/tcp tcp_conn_req_max_q0 {somaxconn*4}",
            "ndd -set /dev/tcp tcp_time_wait_interval 60000",
            "ndd -set /dev/tcp tcp_xmit_hiwat 65536",
            "ndd -set /dev/tcp tcp_recv_hiwat 65536",
            f"# /etc/system: set rlim_fd_max={file_limit}",
            f"# /etc/system: set rlim_fd_cur={file_limit}",
        ]
    elif "aix" in os_type:
        cmds = [
            f"no -o somaxconn={somaxconn}",
            "no -o rfc1323=1",
            "no -o tcp_keepidle=600",
            "no -o tcp_keepintvl=15",
            "no -o tcp_keepcnt=5",
            f"no -o sb_max={max(1048576, somaxconn * 32)}",
            f"chdev -l sys0 -a maxuproc={max(4096, file_limit//16)}",
            f"ulimit -n {file_limit}",
        ]
    elif "hp" in os_type:
        cmds = [
            f"ndd -set /dev/tcp tcp_conn_request_max {somaxconn}",
            "ndd -set /dev/tcp tcp_time_wait_interval 60000",
            "ndd -set /dev/tcp tcp_keepalive_interval 600000",
            f"kctune nfile={file_limit}",
            f"kctune maxfiles={file_limit}",
            f"kctune maxfiles_lim={file_limit}",
        ]
    return {"os_type": os_type, "commands": cmds}


# ── example payloads ─────────────────────────────────────
def example_payload(calculator: str, profile: str) -> dict[str, Any]:
    mode = "existing" if "existing" in profile else "new"
    base = {"mode":mode,"os_type":"RHEL","cpu_cores":8,"ram_gb":32,"expected_rps":10000,"avg_response_ms":120}
    extras = {
        "nginx":{"ssl_enabled":True,"reverse_proxy":True,"static_pct":30,"keepalive_enabled":True,"avg_response_kb":50,"gzip_enabled":True,"http2_enabled":True},
        "redis":{"estimated_keys":5000000,"avg_key_size_bytes":512,"persistence_type":"aof","cluster_enabled":False,"password_enabled":True},
        "tomcat":{"app_type":"rest","ssl_enabled":True,"max_upload_mb":50,"session_timeout_min":30,"enable_compression":True,"jmx_enabled":True},
        "httpd":{"ssl_enabled":True,"mpm_type":"event","enable_mod_deflate":True,"enable_status":True,"server_limit":16},
        "ohs":{"ssl_enabled":True,"max_clients":1000},
        "ihs":{"ssl_enabled":True,"max_request_workers":1000},
        "iis":{"dotnet_type":"core","ssl_enabled":True,"enable_compression":True,"enable_caching":True},
        "postgresql":{"max_connections":300,"disk_type":"ssd","workload":"oltp","wal_level":"replica","ssl_enabled":True},
        "mysql":{"max_connections":300,"disk_type":"ssd","workload":"oltp","replication":False,"ssl_enabled":True},
        "mongodb":{"max_connections":500,"disk_type":"ssd","replica_set":True,"sharding":False,"auth_enabled":True},
        "haproxy":{"backends_count":10,"ssl_termination":True,"health_check_interval_s":5,"http_mode":True},
        "k8s":{"replicas":3,"workload_type":"web","hpa_enabled":True,"pdb_enabled":True,"ingress_enabled":True},
        "podman":{"replicas":2,"workload_type":"web","rootless":True},
        "docker":{"workload_type":"web","compose":True,"swarm":False},
        "os":{"workload_type":"web","disk_type":"ssd"},
        "rabbitmq":{"queue_count":200,"consumers":50,"cluster_enabled":True,"ssl_enabled":True},
    }
    base.update(extras.get(calculator, {}))
    return base


# ══════════════════════════════════════════════════════════
#  MAIN CALCULATE
# ══════════════════════════════════════════════════════════
def calculate(calculator: str, payload: dict[str, Any]) -> dict[str, Any]:
    mode = str(payload.get("mode","new")).lower()
    cpu = max(1, _i(payload,"cpu_cores",4))
    ram = max(1.0, _f(payload,"ram_gb",8.0))
    rps = max(1, _i(payload,"expected_rps",1000))
    resp_ms = max(1, _i(payload,"avg_response_ms",100))

    concurrency = max(1, math.ceil(rps * (resp_ms / 1000.0)))
    params = []          # recommended_params
    degradations = []    # DEGRADATION warnings
    capacity_warnings = []
    calc_specific = {}
    snippet_lines = []

    # ── NGINX ────────────────────────────────────────────
    if calculator == "nginx":
        ssl = _b(payload,"ssl_enabled")
        rproxy = _b(payload,"reverse_proxy")
        static_pct = min(100, max(0, _i(payload,"static_pct",20)))
        keepalive = _b(payload,"keepalive_enabled",True)
        avg_kb = max(1, _f(payload,"avg_response_kb",50))
        gzip = _b(payload,"gzip_enabled",True)
        http2 = _b(payload,"http2_enabled",True)

        workers = cpu
        # RAM-capacity-driven worker_connections (improved formula)
        # Memory cost per connection = 16KB base + avg_response_kb + 64KB SSL overhead
        mem_base_kb = 16.0  # kernel socket send/recv buffers
        ssl_extra_kb = 64.0 if ssl else 0.0  # SSL session cache + context
        mem_per_conn_kb = mem_base_kb + avg_kb + ssl_extra_kb
        ram_per_worker_kb = (ram * 1024 * 1024) / workers  # RAM in KB per worker
        raw_wc = math.floor(ram_per_worker_kb / mem_per_conn_kb)
        worker_conn = max(1024, min(65535, raw_wc))
        rlimit_nofile = worker_conn * 2
        # Keepalive: 65s for SSL (avoid TLS re-handshake), 30s plain; reduced if RPS > 10K
        keepalive_to = 0 if not keepalive else (max(10, (65 if ssl else 30) - (20 if rps > 10000 else 0)))
        client_max_body = max(1, min(100, int(avg_kb * 4 / 1024))) if not _i(payload,"client_max_body_size_mb",0) else max(1, _i(payload,"client_max_body_size_mb",10))
        # Proxy buffer: next power-of-2 >= avg_response_kb, min 8k
        proxy_buf_kb = max(8, int(2 ** math.ceil(math.log2(max(1, avg_kb))))) if rproxy else 8
        proxy_buf_size = f"{proxy_buf_kb}k"
        proxy_buffers = max(4, min(32, concurrency // 1000 + 4)) if rproxy else 4
        open_file_cache = max(10000, worker_conn * 20)
        send_to = 60 if rproxy else 30
        proxy_connect_to = 10  # fail fast on dead upstreams (was 60)
        proxy_read_to = max(30, resp_ms * 3 // 1000 + 10)
        est_max_clients = (workers * worker_conn) // (4 if rproxy else 1)

        _add(params,"worker_processes","auto",
            f"Must equal vCPU count = {workers}. Each NGINX worker is single-threaded and pinned to one core. "
            f"Under-provisioning: CPUs idle while requests queue. Over-provisioning: context-switch overhead "
            f"degrades throughput. Formula: 1 worker = 1 core.","MAJOR")
        _add(params,"worker_connections",worker_conn,
            f"Max simultaneous connections per worker = {worker_conn}. "
            f"Formula: RAM_per_worker ({int(ram_per_worker_kb):,} KB) / mem_per_conn ({mem_per_conn_kb:.0f} KB) = {worker_conn}. "
            f"mem_per_conn = 16KB base + {avg_kb:.0f}KB response{' + 64KB SSL' if ssl else ''}. "
            f"Total estimated_max_clients = {workers}×{worker_conn}"
            f"{'÷4 (proxy FD cost)' if rproxy else ''} = {est_max_clients:,}.","MAJOR")
        _add(params,"worker_rlimit_nofile",rlimit_nofile,
            f"Must be ≥ worker_connections × 2 = {rlimit_nofile}. Each proxied connection uses 2 FDs "
            f"(client socket + upstream socket). If rlimit_nofile < worker_connections×2, NGINX silently "
            f"rejects connections with EMFILE ('too many open files') in error.log.","MAJOR")
        _add(params,"keepalive_timeout",f"{keepalive_to}s",
            f"Idle keep-alive timeout = {keepalive_to}s. "
            f"Base: {'65s (SSL — avoids TLS re-handshake)' if ssl else '30s (plain HTTP)'}. "
            f"{'Reduced by 20s because RPS=' + str(rps) + ' > 10K.' if rps > 10000 else ''} "
            f"Tradeoff: higher = fewer TCP+TLS handshakes; lower = fewer idle FD holders.","MAJOR")
        _add(params,"use epoll + multi_accept","epoll + on",
            "epoll is Linux O(1) event notification — scales to millions of FDs with constant CPU cost. "
            "select/poll are O(n). multi_accept: accept ALL new connections per epoll event "
            "instead of one-at-a-time, preventing accept queue buildup during bursts.","MAJOR")
        _add(params,"server_tokens","off",
            "Default 'on' exposes NGINX version in Server header and error pages. "
            "Attackers use this for version-specific CVE targeting. Always off in production.","MAJOR")
        _add(params,"client_max_body_size",f"{client_max_body}m",
            f"Hard upload size limit = {client_max_body}m. Too small → 413 errors. "
            f"Unlimited (0) → OOM risk from oversized uploads.","MEDIUM")
        _add(params,"sendfile + tcp_nopush + tcp_nodelay","on",
            f"sendfile(): zero-copy transfer from disk → socket via kernel, bypassing userspace. "
            f"Without it: read() to userspace buffer → write() to socket = 2 memory copies. "
            f"tcp_nopush: batch small TCP segments. tcp_nodelay: disable Nagle's for low-latency. "
            f"Together: 30-50% throughput improvement for static content ({static_pct}% of traffic).","MEDIUM")
        _add(params,"open_file_cache",f"max={open_file_cache} inactive=20s",
            f"Cache open file descriptors, stat() results, and directory lookups. "
            f"Without this, each static file request calls: open() + fstat() + close() = 3 syscalls. "
            f"With {open_file_cache:,} cached entries these become memory lookups.","MEDIUM")
        _add(params,"send_timeout",f"{send_to}s",
            f"Timeout for sending response data to client. A dead or very slow client "
            f"holds a worker connection open. Under high load: {send_to}s frees FDs faster.","MEDIUM")
        _add(params,"reset_timedout_connection","on",
            "Send TCP RST on timeout instead of waiting for the full FIN→FIN-ACK sequence. "
            "RST frees the FD immediately. FIN sequence adds up to 60s TIME_WAIT.","MEDIUM")
        if gzip:
            _add(params,"gzip","on",
                "GZIP reduces text/JSON/HTML payload size by 60-80%. CPU cost: <1% on modern hardware. "
                "gzip_vary adds 'Vary: Accept-Encoding' — required for correct CDN behaviour. "
                "gzip_min_length 1024: don't compress small responses (overhead > savings for <1KB).","MEDIUM")
            _add(params,"gzip_comp_level","4","Level 4 = good compression ratio without CPU burn. Level 9 uses 3x CPU for only 5% more savings.","MINOR")
            _add(params,"gzip_min_length","1024","Skip responses < 1KB. Compression overhead exceeds savings below this.","MINOR")
            _add(params,"gzip_types","text/plain text/css application/json application/javascript text/xml application/xml","Standard compressible MIME types.","MINOR")
        if ssl:
            _add(params,"ssl_protocols","TLSv1.2 TLSv1.3",
                "Disable TLSv1.0 (POODLE, CVE-2014-3566) and TLSv1.1 (BEAST). "
                "TLSv1.3: 1-RTT handshake vs 2-RTT for TLSv1.2 — saves ~50ms per new connection. "
                "PCI-DSS 3.2.1 mandates removal of TLS < 1.2.","MAJOR")
            _add(params,"ssl_ciphers","ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384",
                "Forward-secrecy (ECDHE) + authenticated encryption (AES-GCM). No CBC mode (BEAST-vulnerable).","MAJOR")
            _add(params,"ssl_session_cache","shared:SSL:50m",
                "Shared TLS session cache across ALL worker processes. 50MB ≈ 200,000 sessions. "
                "Without shared cache, a client reconnecting to a different worker gets full handshake. "
                "Session resumption eliminates 2-RTT handshake saving ~100ms/connection.","MEDIUM")
            _add(params,"ssl_session_timeout","600s","10 minute session ticket lifetime. Balanced for security vs performance.","MINOR")
            _add(params,"ssl_buffer_size","4k",
                "Default 16KB fragments typical API responses (1-4KB) into multiple TCP segments. "
                "4KB aligns to Ethernet MTU reducing TCP segment count and improving TTFB.","MEDIUM")
            _add(params,"ssl_stapling","on",
                "OCSP stapling: NGINX fetches and caches cert revocation status, stapling it to TLS handshake. "
                "Without it, browsers fetch OCSP themselves adding 50-200ms per new TLS connection.","MINOR")
            _add(params,"ssl_prefer_server_ciphers","on","Server-side cipher preference.","MINOR")
            if http2: _add(params,"http2","on","HTTP/2 multiplexing for SSL connections. Single TCP connection handles many requests.","MEDIUM")
        if rproxy:
            _add(params,"proxy_connect_timeout",f"{proxy_connect_to}s",
                f"Fail fast on dead upstreams = {proxy_connect_to}s. Default 60s means each dead backend "
                f"holds a worker for 60s. At 100 dead attempts: all workers blocked.","MEDIUM")
            _add(params,"proxy_read_timeout",f"{proxy_read_to}s",f"Based on avg response {resp_ms}ms × 3 + 10s buffer.","MEDIUM")
            _add(params,"proxy_send_timeout",f"{send_to}s","Upstream send timeout.","MEDIUM")
            _add(params,"proxy_buffer_size",proxy_buf_size,
                f"Buffer for upstream response headers = {proxy_buf_size}. "
                f"Formula: next power-of-2 ≥ avg_response_kb ({avg_kb:.0f}KB). "
                f"If header > buffer, NGINX falls through to disk buffering adding I/O latency.","MEDIUM")
            _add(params,"proxy_buffers",f"{proxy_buffers} {proxy_buf_size}","Proxy response body buffering.","MEDIUM")
            _add(params,"upstream keepalive","32",
                "Idle keepalive connections per worker to upstream backends. Without keepalive: every "
                "proxied request opens a new TCP connection. At 10K RPS: 10K TCP handshakes/sec.","MEDIUM")
            _add(params,"proxy_http_version","1.1","Required for upstream keepalive. HTTP/1.0 closes after each request.","MINOR")
            _add(params,"proxy_set_header","Connection \"\"","Clear 'Connection: close' header for keepalive.","MINOR")
        _add(params,"access_log","buffer=512k flush=5s",
            "Without buffering, every request triggers a write() syscall. At 10K RPS: 10,000 write() calls/sec. "
            "512KB buffer flushes every 5s = ~1 write/5s, reducing log I/O by 99.99%.","MINOR")
        _add(params,"error_log","/var/log/nginx/error.log warn","debug/info log every connection event. At 10K RPS: GB/hour. warn logs only actionable issues.","MINOR")

        # degradation checks
        if worker_conn > 16384:
            _deg(degradations,"worker_connections",f"Value {worker_conn} is very high. Each connection uses ~{mem_per_conn_kb:.0f}KB RAM + fd. At {workers} workers = {int(workers*worker_conn*mem_per_conn_kb/1024)}MB. May cause OOM under burst.")
        if keepalive and keepalive_to > 60:
            _deg(degradations,"keepalive_timeout",f"High keepalive ({keepalive_to}s) holds sockets open. Idle FD consumption = RPS × timeout. Under burst traffic, may exhaust connection slots.")
        if gzip and rps > 50000:
            _deg(degradations,"gzip","At >50K RPS, gzip compression consumes significant CPU. Consider offloading to CDN or reducing comp_level to 1.")
        if ssl and not http2:
            _deg(degradations,"SSL without HTTP/2","SSL adds latency per request. Without HTTP/2 multiplexing, each resource needs a separate TLS handshake.")
        if client_max_body > 100:
            _deg(degradations,"client_max_body_size",f"Large body size ({client_max_body}MB) allows big uploads that block worker connections during transfer.")
        if rps > est_max_clients:
            capacity_warnings.append(f"CAPACITY WARNING: Expected RPS ({rps:,}) > estimated max_clients ({est_max_clients:,}). Add more nodes or increase RAM.")
        if cpu == 1:
            capacity_warnings.append("Single CPU core — multi-core is mandatory for production NGINX workloads.")
        if ram < 2:
            capacity_warnings.append("RAM < 2GB — severely constrained for production NGINX.")

        snippet_lines = [
            f"# NGINX Production Config — {cpu} cores, {ram}GB RAM, {rps} RPS",
            f"worker_processes      auto;   # {workers} cores",
            f"worker_rlimit_nofile  {rlimit_nofile};",
            f"worker_cpu_affinity   auto;",
            "",
            "events {",
            f"    worker_connections  {worker_conn};",
            "    use                 epoll;",
            "    multi_accept        on;",
            "}",
            "",
            "http {",
            "    sendfile              on;",
            "    tcp_nopush            on;",
            "    tcp_nodelay           on;",
            "    server_tokens         off;",
            f"    keepalive_timeout     {keepalive_to};",
            "    keepalive_requests    1000;",
            f"    client_max_body_size  {client_max_body}m;",
            "    client_body_timeout   30s;",
            "    send_timeout          30s;",
            "    reset_timedout_connection on;",
        ]
        if gzip:
            snippet_lines += ["    gzip on;","    gzip_vary on;","    gzip_comp_level 4;","    gzip_min_length 1024;"]
        if ssl:
            snippet_lines += [
                "    ssl_protocols TLSv1.2 TLSv1.3;",
                "    ssl_prefer_server_ciphers on;",
                "    ssl_session_cache shared:SSL:50m;",
                "    ssl_buffer_size 4k;",
                "    ssl_stapling on;",
            ]
        if rproxy:
            snippet_lines += [
                f"    proxy_buffer_size      {proxy_buf_size};",
                f"    proxy_buffers          4 {proxy_buf_size};",
                f"    proxy_connect_timeout  {proxy_connect_to}s;",
                f"    proxy_read_timeout     {proxy_read_to}s;",
                "    proxy_http_version     1.1;",
            ]
        snippet_lines += [
            "    access_log /var/log/nginx/access.log main buffer=512k flush=5s;",
            "    error_log  /var/log/nginx/error.log warn;",
            "}",
        ]

        file_limit = rlimit_nofile
        somaxconn = max(65535, worker_conn)

    # ── REDIS ────────────────────────────────────────────
    elif calculator == "redis":
        keys = max(1, _i(payload,"estimated_keys",1000000))
        key_size = max(64, _i(payload,"avg_key_size_bytes",512))
        persist = str(payload.get("persistence_type","aof")).lower()
        cluster = _b(payload,"cluster_enabled")
        dataset_gb = round(keys * key_size / (1024**3), 2)
        # COW-aware memory reservation (improved formula)
        # 20% OS reserve + 10% fragmentation + 10% COW fork + 5% AOF buffer = 45% reserved
        os_reserve_pct = 0.20   # OS needs RAM for buffers, caches, kernel
        frag_pct = 0.10         # jemalloc fragmentation ratio
        cow_pct = 0.10          # copy-on-write during BGSAVE/BGREWRITEAOF fork
        aof_buf_pct = 0.05 if persist == "aof" else 0.0  # AOF rewrite buffer
        usable_pct = 1.0 - os_reserve_pct - frag_pct - cow_pct - aof_buf_pct
        maxmem_gb = max(1, int(ram * usable_pct))
        hz_val = 100 if rps > 10000 else 10
        io_threads = min(cpu, 4) if cpu >= 4 else 1
        tcp_backlog_val = max(511, min(65535, concurrency))

        _add(params,"maxmemory",f"{maxmem_gb}gb",
            f"COW-aware reservation: {ram}GB × {usable_pct:.0%} usable = {maxmem_gb}GB. "
            f"Breakdown: {os_reserve_pct:.0%} OS + {frag_pct:.0%} jemalloc fragmentation + "
            f"{cow_pct:.0%} COW fork overhead{' + ' + str(int(aof_buf_pct*100)) + '% AOF buffer' if persist=='aof' else ''}. "
            f"Dataset estimate: {dataset_gb}GB ({keys:,} keys × {key_size}B avg).","MAJOR")
        _add(params,"maxmemory-policy","allkeys-lru",
            "Evict least-recently-used keys when maxmemory is reached. Prevents OOM crash. "
            "Use volatile-lru if only TTL keys should be evicted.","MAJOR")
        _add(params,"tcp-backlog",tcp_backlog_val,
            f"SYN backlog queue = {tcp_backlog_val}. Must match net.core.somaxconn. "
            f"If lower than OS somaxconn, kernel silently SYN-drops under burst.","MAJOR")
        _add(params,"hz",hz_val,
            f"Internal timer frequency = {hz_val} ticks/sec. At 100hz: expired keys checked 100x/sec instead of 10x. "
            f"Required for high-throughput ({rps:,} RPS) to avoid stale key buildup. "
            f"CPU cost: ~1% additional.","MEDIUM")
        _add(params,"io-threads",io_threads,
            f"Dedicated I/O threads = {io_threads}. Redis 6.0+ can offload network I/O to threads "
            f"while main thread handles commands. On {cpu}-core system: min(cpu, 4) = {io_threads}. "
            f"More than 4 threads shows diminishing returns.","MEDIUM")
        _add(params,"io-threads-do-reads","yes","Also parallelize read I/O — not just writes.","MEDIUM")
        _add(params,"timeout","300","Close idle clients after 5min. Prevents FD leak from abandoned connections.","MINOR")
        _add(params,"tcp-keepalive","300","Detect dead peers via TCP keepalive every 5min.","MINOR")
        if persist == "aof":
            _add(params,"appendonly","yes",
                "AOF logs every write command. On crash: replay log to recover. "
                "Data loss window: max 1 second with everysec fsync.","MAJOR")
            _add(params,"appendfsync","everysec",
                "Fsync once per second. 'always' = zero data loss but 100x slower. "
                "'no' = OS decides (up to 30s data loss). everysec = best tradeoff.","MAJOR")
            _add(params,"auto-aof-rewrite-percentage","100","Rewrite AOF when it doubles in size.","MINOR")
            _add(params,"auto-aof-rewrite-min-size","64mb","Don't rewrite tiny AOF files.","MINOR")
            _add(params,"aof-use-rdb-preamble","yes",
                "Hybrid persistence: RDB snapshot + AOF tail. Faster restart (load RDB first) "
                "with AOF durability.","MEDIUM")
        elif persist == "rdb":
            _add(params,"save","900 1 300 10 60 10000","RDB snapshot schedule: save if 1 key changes in 900s, 10 in 300s, or 10K in 60s.","MAJOR")
        else:
            _add(params,"save","\"\"","No persistence — data loss on restart. Use for cache-only deployments.","MAJOR")
        _add(params,"lazyfree-lazy-eviction","yes",
            "Background eviction: when maxmemory is hit, keys are freed in a background thread. "
            "Without this, eviction blocks the main thread causing latency spikes.","MEDIUM")
        _add(params,"lazyfree-lazy-expire","yes","Background key expiry avoids main-thread stalls.","MEDIUM")
        _add(params,"lazyfree-lazy-server-del","yes","Background DEL for large keys avoids blocking.","MINOR")
        if cluster:
            _add(params,"cluster-enabled","yes","Redis Cluster mode for horizontal scaling.","MAJOR")
            _add(params,"cluster-node-timeout","15000","Node failure detection timeout (15s). Lower = faster failover but more false positives.","MEDIUM")
        _add(params,"protected-mode","yes","Block external access without explicit bind/auth configuration.","MEDIUM")
        _add(params,"rename-command FLUSHALL","\"\"","Disable dangerous commands in production. Prevents accidental data wipe.","MINOR")
        _add(params,"rename-command FLUSHDB","\"\"","Disable FLUSHDB as well.","MINOR")

        if dataset_gb > maxmem_gb:
            _deg(degradations,"Dataset vs Memory",f"Dataset (~{dataset_gb}GB) exceeds maxmemory ({maxmem_gb}GB). Eviction will be aggressive — data loss likely.")
        if persist == "aof" and rps > 50000:
            _deg(degradations,"AOF at high RPS",f"AOF appendfsync=everysec at {rps:,} RPS generates ~{rps*50//1024}KB/s I/O. Consider RDB or no persistence for cache-only.")
        if hz_val == 100 and cpu < 4:
            _deg(degradations,"High hz on low CPU",f"hz=100 increases CPU usage for timers. On {cpu}-core system this steals cycles from request handling.")
        if maxmem_gb * 1024 < dataset_gb * 1024 * 1.5:
            _deg(degradations,"COW spike risk",f"During BGSAVE, Redis forks and copy-on-write duplicates modified pages. With {dataset_gb}GB dataset, a write-heavy workload can spike to {dataset_gb*2}GB momentarily.")

        file_limit = max(65535, concurrency * 2)
        somaxconn = tcp_backlog_val
        snippet_lines = [
            f"# Redis Production Config — {cpu} cores, {ram}GB RAM",
            f"# COW-aware maxmemory: {usable_pct:.0%} of {ram}GB = {maxmem_gb}GB",
            f"maxmemory {maxmem_gb}gb",
            "maxmemory-policy allkeys-lru",
            f"tcp-backlog {tcp_backlog_val}",
            f"hz {hz_val}",
            f"io-threads {io_threads}",
            "io-threads-do-reads yes",
            f"appendonly {'yes' if persist=='aof' else 'no'}",
            "lazyfree-lazy-eviction yes",
            f"timeout 300",
        ]

    # ── TOMCAT (Goetz thread formula) ─────────────────────
    elif calculator == "tomcat":
        app_type = str(payload.get("app_type","rest")).lower()
        ssl = _b(payload,"ssl_enabled")
        max_upload = max(1, _i(payload,"max_upload_mb",50))
        session_to = max(1, _i(payload,"session_timeout_min",30))
        compress = _b(payload,"enable_compression",True)
        jmx = _b(payload,"jmx_enabled")

        # Brian Goetz formula: N = U × C × (1 + W/C)
        # U = target CPU utilization (0.8), C = cores, W = wait time, C_time = compute time
        # I/O wait ratio: REST ~0.7, webapp ~0.5, microservice ~0.8
        io_wait = {"rest": 0.7, "webapp": 0.5, "microservice": 0.8}.get(app_type, 0.7)
        target_util = 0.8  # 80% CPU utilization target
        goetz_threads = int(target_util * cpu * (1 + io_wait / (1 - io_wait)))
        max_threads = max(25, min(800, goetz_threads))
        min_spare = max(10, max_threads // 10)
        max_conn = max(max_threads, concurrency * 2)
        accept_count = max(100, max_threads // 2)
        heap_max = max(256, int(ram * 1024 * 0.65))
        heap_min = heap_max
        metaspace = max(256, min(512, heap_max // 8))
        gc = "G1GC" if heap_max > 4096 else "ParallelGC"
        gc_threads = max(2, min(cpu, 8))
        conn_timeout = max(5000, min(60000, resp_ms * 3))

        _add(params,"maxThreads",max_threads,
            f"Goetz formula: N = U × C × (1 + W/S) = {target_util} × {cpu} × (1 + {io_wait}/{1-io_wait:.1f}) = {goetz_threads}. "
            f"U=80% CPU target, C={cpu} cores, W/S={io_wait:.1f}/{1-io_wait:.1f} (I/O wait ratio for {app_type}). "
            f"Clamped to [{25}, {800}] = {max_threads}. "
            f"Under-provisioning: requests queue. Over-provisioning: context-switch overhead (~1MB stack/thread).","MAJOR")
        _add(params,"minSpareThreads",min_spare,
            f"Pre-warmed threads = {min_spare} (10% of maxThreads). Absorbs burst traffic without "
            f"thread creation latency (~1ms per new thread).","MEDIUM")
        _add(params,"maxConnections",max_conn,
            f"Total socket connections = {max_conn}. Must be ≥ maxThreads. When maxConnections is reached, "
            f"OS queues new connections in the acceptCount backlog.","MAJOR")
        _add(params,"acceptCount",accept_count,
            f"OS-level backlog queue = {accept_count}. When all {max_threads} threads are busy, "
            f"up to {accept_count} connections wait in kernel queue. Beyond this: connection refused.","MAJOR")
        _add(params,"connectionTimeout",f"{conn_timeout}ms",
            f"Socket timeout = {conn_timeout}ms = 3 × avg response ({resp_ms}ms). "
            f"Too short: legit slow requests timeout. Too long: slow clients hold threads.","MEDIUM")
        _add(params,"-Xmx / -Xms",f"{heap_max}m",
            f"JVM heap = {heap_max}MB = 65% of {ram}GB RAM. Set Xms=Xmx to avoid runtime resize "
            f"(resize triggers Full GC pause). Remaining 35% for: OS ({int(ram*1024*0.15)}MB), "
            f"Metaspace ({metaspace}MB), thread stacks ({max_threads}MB), NIO buffers.","MAJOR")
        _add(params,"-XX:+Use"+gc,"enabled",
            f"{'G1GC: region-based collector for large heaps (>4GB). Targets ' + str(200) + 'ms max pause. Concurrent marking reduces stop-the-world pauses.' if gc=='G1GC' else 'ParallelGC: throughput-optimized for smaller heaps. Uses all cores for GC.'}. "
            f"GC threads = {gc_threads} (ParallelGCThreads).","MAJOR")
        _add(params,"-XX:MetaspaceSize",f"{metaspace}m",
            f"Class metadata space = {metaspace}MB. Pre-size to avoid early Full GC triggered by "
            f"Metaspace expansion. heap/{8} = {heap_max//8}MB, clamped [256, 512].","MEDIUM")
        _add(params,"protocol","org.apache.coyote.http11.Http11NioProtocol",
            "NIO connector: non-blocking I/O multiplexes many connections over fewer threads. "
            "BIO (default in old Tomcat): 1 thread per connection. NIO handles 10x more connections.","MAJOR")
        _add(params,"maxKeepAliveRequests","100","Requests per keepalive connection before reconnection.","MEDIUM")
        _add(params,"keepAliveTimeout","20000","20s keepalive timeout. Frees threads from idle connections.","MINOR")
        _add(params,"server.tomcat.max-swallow-size",f"{max_upload}MB",f"Max upload size = {max_upload}MB.","MEDIUM")
        _add(params,"session-timeout",f"{session_to}min",f"HTTP session expiry = {session_to} minutes.","MINOR")
        if compress:
            _add(params,"compression","on","HTTP response compression. 60-80% size reduction for text.","MEDIUM")
            _add(params,"compressibleMimeType","text/html,text/xml,text/css,application/json,application/javascript","Standard compressible MIME types.","MINOR")
        if ssl:
            _add(params,"sslProtocol","TLSv1.2+TLSv1.3","Disable TLSv1.0/1.1 (CVE-vulnerable). TLSv1.3: 1-RTT handshake.","MAJOR")
        if jmx:
            _add(params,"JMX Remote","enabled","JMX monitoring endpoint for GC, thread, heap dashboards.","MINOR")
        _add(params,"-XX:+HeapDumpOnOutOfMemoryError","enabled",
            "Auto-dump heap on OOM for post-mortem analysis. Critical for diagnosing memory leaks.","MEDIUM")
        _add(params,"-XX:MaxGCPauseMillis","200","G1GC pause target = 200ms. G1 adjusts region count to meet this target.","MINOR")
        _add(params,"-XX:ParallelGCThreads",str(gc_threads),f"GC worker threads = {gc_threads}. Match to CPU cores.","MINOR")

        if max_threads > 500:
            _deg(degradations,"maxThreads",f"High thread count ({max_threads}) increases context switching overhead and memory usage (~1MB stack/thread = {max_threads}MB total stack memory).")
        if heap_max > ram * 1024 * 0.8:
            _deg(degradations,"JVM Heap",f"Heap ({heap_max}MB) uses >80% of RAM ({int(ram*1024)}MB). No room for OS buffers. Risk of OOM killer.")
        if conn_timeout > 30000:
            _deg(degradations,"connectionTimeout",f"Long timeout ({conn_timeout}ms) causes slow clients to hold threads. Reduces effective concurrency.")
        if max_threads > cpu * 50:
            _deg(degradations,"Thread-to-CPU ratio",f"Ratio {max_threads}/{cpu} = {max_threads//cpu}:1 exceeds recommended 50:1. Excessive context switching.")

        file_limit = max(65535, max_conn * 2)
        somaxconn = max(65535, accept_count * 2)
        snippet_lines = [
            f"# Tomcat Production — {cpu} cores, {ram}GB RAM, {rps} RPS",
            f"# Goetz formula: N = {target_util} × {cpu} × (1 + {io_wait}/{1-io_wait:.1f}) = {goetz_threads}",
            f'JAVA_OPTS="-Xms{heap_max}m -Xmx{heap_max}m -XX:+Use{gc} -XX:MetaspaceSize={metaspace}m',
            f'  -XX:ParallelGCThreads={gc_threads} -XX:MaxGCPauseMillis=200',
            f'  -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/tmp/heapdump.hprof"',
            f"# server.xml Connector:",
            f'<Connector port="8080" protocol="Http11NioProtocol"',
            f'  maxThreads="{max_threads}" minSpareThreads="{min_spare}"',
            f'  maxConnections="{max_conn}" acceptCount="{accept_count}"',
            f'  connectionTimeout="{conn_timeout}" />',
        ]

    # ── HTTPD / OHS / IHS ────────────────────────────────
    elif calculator in ("httpd","ohs","ihs"):
        ssl = _b(payload,"ssl_enabled")
        mpm = str(payload.get("mpm_type","event")).lower()
        server_limit = max(1, _i(payload,"server_limit",16))
        max_req_workers = max(150, min(8192, concurrency + 100))
        threads_per_child = 25 if mpm in ("worker","event") else 0
        start_servers = max(2, cpu // 2)
        max_spare = max(start_servers * 2, max_req_workers // 4)
        min_spare = max(start_servers, max_spare // 2)
        keepalive_to = 5
        max_keepalive_req = max(100, rps // 10)
        timeout = max(30, resp_ms * 3 // 1000 + 10)
        limit_req_line = 8190
        limit_req_body = 1048576

        _add(params,"MPM",mpm,f"{'Event MPM for async I/O' if mpm=='event' else 'Worker MPM' if mpm=='worker' else 'Prefork (legacy CGI)'}.","MAJOR")
        _add(params,"MaxRequestWorkers",max_req_workers,f"Cap for {concurrency} concurrency.","MAJOR")
        if mpm in ("worker","event"):
            _add(params,"ThreadsPerChild",threads_per_child,"Threads per child process.","MAJOR")
            actual_procs = max(1, max_req_workers // threads_per_child)
            _add(params,"ServerLimit",max(server_limit, actual_procs),f"Process limit ({actual_procs} needed).","MAJOR")
        _add(params,"StartServers",start_servers,"Pre-fork on startup.","MEDIUM")
        _add(params,"MinSpareThreads" if mpm!="prefork" else "MinSpareServers",min_spare,"Ready pool for bursts.","MEDIUM")
        _add(params,"MaxSpareThreads" if mpm!="prefork" else "MaxSpareServers",max_spare,"Reclaim idle resources.","MEDIUM")
        _add(params,"KeepAliveTimeout",f"{keepalive_to}s","Short for high-concurrency.","MEDIUM")
        _add(params,"MaxKeepAliveRequests",max_keepalive_req,"Requests per persistent connection.","MEDIUM")
        _add(params,"Timeout",f"{timeout}s","I/O timeout.","MEDIUM")
        _add(params,"LimitRequestLine",limit_req_line,"Max request line bytes.","MINOR")
        _add(params,"LimitRequestBody",limit_req_body,"Max body bytes.","MINOR")
        _add(params,"ListenBacklog",max(511, concurrency // 2),"Kernel listen queue.","MEDIUM")
        if ssl:
            _add(params,"SSLProtocol","all -SSLv3 -TLSv1 -TLSv1.1","Modern TLS.","MAJOR")
            _add(params,"SSLCipherSuite","ECDHE:!COMPLEMENTOFDEFAULT","Strong ciphers.","MAJOR")
            _add(params,"SSLSessionCache",f"shmcb:/path(512000)","Session cache.","MEDIUM")
        _add(params,"EnableMMAP","on","Memory-mapped file delivery.","MINOR")
        _add(params,"EnableSendfile","on","Kernel sendfile.","MINOR")
        if calculator == "ohs":
            mc = max(150, _i(payload,"max_clients",max_req_workers))
            _add(params,"MaxClients",mc,"OHS max simultaneous clients.","MAJOR")
            _add(params,"MaxRequestsPerChild",10000,"Recycle children to prevent leaks.","MEDIUM")
        if calculator == "ihs":
            _add(params,"MaxConnectionsPerChild",100000,"IHS connection recycling.","MEDIUM")

        if mpm == "prefork" and rps > 5000:
            _deg(degradations,"Prefork MPM",f"Prefork creates one process per connection. At {rps} RPS this consumes massive memory ({max_req_workers * 50}MB+).")
        if max_req_workers > 4096:
            _deg(degradations,"MaxRequestWorkers","Very large worker pool increases scheduling overhead and memory. Consider horizontal scaling.")

        file_limit = max(65535, max_req_workers * 4)
        somaxconn = max(65535, concurrency)
        snippet_lines = [
            f"# {'Apache HTTPD' if calculator=='httpd' else calculator.upper()} — {cpu} cores, {ram}GB RAM",
            f"# MPM {mpm}",
            f"MaxRequestWorkers {max_req_workers}",
            f"StartServers {start_servers}",
            f"KeepAliveTimeout {keepalive_to}",
            f"Timeout {timeout}",
        ]
        if mpm in ("worker","event"):
            snippet_lines.append(f"ThreadsPerChild {threads_per_child}")

    # ── remaining calculators use generic logic ──────────
    else:
        file_limit = max(65535, concurrency * 2)
        somaxconn = 65535
        # delegate to per-calculator blocks below
        file_limit, somaxconn, snippet_lines = _calc_remaining(
            calculator, payload, cpu, ram, rps, resp_ms, concurrency,
            params, degradations, capacity_warnings
        )

    # ── OS Tuning ────────────────────────────────────────
    os_tuning = _os_tuning(payload, file_limit, somaxconn, calculator=calculator)

    # ── Assemble response ────────────────────────────────
    audit = []
    if mode == "existing":
        # Compare current payload values against recommended configs
        for param_obj in params:
            name = param_obj["name"]
            rec_val = param_obj.get("recommended") or param_obj.get("recommended_value")
            
            # Normalize parameter names for payload lookup
            # e.g., "worker_connections" -> "worker_connections", "keepAliveTimeout" -> "keepalivetimeout"
            clean_name = name.replace("-", "_").lower()
            # Try to find corresponding key in payload
            payload_keys = {k.lower(): k for k in payload.keys()}
            
            if clean_name in payload_keys:
                og_key = payload_keys[clean_name]
                current_val = payload[og_key]
                
                # Loose comparison: convert both to string and lowercase
                if str(current_val).lower() != str(rec_val).lower():
                    audit.append({
                        "parameter": name,
                        "current_value": current_val,
                        "recommended_value": rec_val,
                        "finding": "MISMATCH",
                        "impact": param_obj["impact"],
                        "remediation": f"Change {name} from {current_val} to {rec_val}"
                    })

        if not audit:
            audit.append({
                "parameter": "All Parameters",
                "finding": "MATCH",
                "message": "All provided parameters match the mathematically recommended values for this workload."
            })

    return {
        "calculator": calculator,
        "mode": mode,
        "summary": "Production-grade computation complete.",
        "config_snippet": "\n".join(snippet_lines),
        "os_tuning": os_tuning,
        "capacity_warnings": capacity_warnings,
        "recommended_params": params,
        "degradation_params": degradations,
        "audit_findings": audit,
    }


# ══════════════════════════════════════════════════════════
#  Remaining calculators
# ══════════════════════════════════════════════════════════
def _calc_remaining(calc, p, cpu, ram, rps, resp_ms, conc, params, degs, warns):
    fl = 65535; smx = 65535; snip = []

    if calc == "iis":
        dotnet = str(p.get("dotnet_type","core")).lower()
        ssl = _b(p,"ssl_enabled")
        compress = _b(p,"enable_compression",True)
        cache = _b(p,"enable_caching",True)
        max_conc = max(500, conc + 200)
        queue_len = max(1000, conc // 2)
        conn_to = max(60, resp_ms * 3 // 1000 + 30)
        idle_to = 20

        _add(params,"maxConcurrentRequestsPerCPU",max_conc // cpu,f"Per-CPU limit. Total: {max_conc}.","MAJOR")
        _add(params,"appConcurrentRequestLimit",max_conc,"Application-wide limit.","MAJOR")
        _add(params,"queueLength",queue_len,"Request queue depth.","MAJOR")
        _add(params,"connectionTimeout",f"{conn_to}s","Connection timeout.","MEDIUM")
        _add(params,"idleTimeout",f"{idle_to}min","App pool idle timeout.","MEDIUM")
        _add(params,"rapidFailProtection","True","Auto-restart failed pools.","MEDIUM")
        _add(params,"recycling.periodicRestart","29h","Staggered recycle.","MINOR")
        _add(params,"maxUrlSegments","32","URL segment limit.","MINOR")
        if ssl:
            _add(params,"sslFlags","Ssl, SslNegotiateCert","TLS binding.","MAJOR")
        if compress:
            _add(params,"dynamicCompression","True","Gzip responses.","MEDIUM")
            _add(params,"staticCompression","True","Pre-compress static.","MEDIUM")
        if cache:
            _add(params,"outputCaching","True","Kernel-mode caching.","MEDIUM")
        fl = max(65535, max_conc * 2)
        snip = [f"# IIS {dotnet.upper()} — {cpu} cores, {ram}GB RAM",f"<!-- maxConcurrentRequestsPerCPU={max_conc//cpu} -->",f"<!-- queueLength={queue_len} -->"]

    elif calc == "postgresql":
        conns = max(50, _i(p,"max_connections",300))
        disk = str(p.get("disk_type","ssd")).lower()
        wl = str(p.get("workload","oltp")).lower()
        shared_buf = int(ram * 1024 * 0.25)
        eff_cache = int(ram * 1024 * 0.75)
        work_mem = max(4, int((ram * 1024 * 0.25) / max(1, conns)))
        maint_mem = max(64, int(ram * 1024 * 0.05))
        wal_buf = max(16, shared_buf // 32)
        checkpoint = 0.9
        rpc = 1.1 if disk == "ssd" else 4.0
        io_conc = 200 if disk == "ssd" else 2
        max_wal = max(1, int(ram * 0.25))
        par_workers = max(0, cpu - 2)
        huge = "try" if ram >= 32 else "off"
        wal_level = str(p.get("wal_level","replica"))

        _add(params,"shared_buffers",f"{shared_buf}MB","25% of RAM for shared buffer cache.","MAJOR")
        _add(params,"effective_cache_size",f"{eff_cache}MB","75% of RAM — OS + PG cache estimate.","MAJOR")
        _add(params,"work_mem",f"{work_mem}MB",f"Per-sort memory ({conns} conns × {work_mem}MB).","MAJOR")
        _add(params,"maintenance_work_mem",f"{maint_mem}MB","VACUUM/CREATE INDEX memory.","MEDIUM")
        _add(params,"wal_buffers",f"{wal_buf}MB","WAL write buffer.","MEDIUM")
        _add(params,"checkpoint_completion_target",checkpoint,"Spread checkpoint I/O.","MEDIUM")
        _add(params,"random_page_cost",rpc,f"{'SSD' if disk=='ssd' else 'HDD'} cost model.","MAJOR")
        _add(params,"effective_io_concurrency",io_conc,f"{'SSD parallel I/O' if disk=='ssd' else 'HDD sequential'}.","MEDIUM")
        _add(params,"max_wal_size",f"{max_wal}GB","WAL retention before checkpoint.","MEDIUM")
        _add(params,"max_parallel_workers_per_gather",min(4, par_workers),"Parallel query workers.","MEDIUM")
        _add(params,"max_parallel_workers",par_workers,"Global parallel pool.","MEDIUM")
        _add(params,"huge_pages",huge,f"{'Enabled for large RAM' if huge=='try' else 'Disabled'}.","MINOR")
        _add(params,"max_connections",conns,"Connection cap.","MAJOR")
        _add(params,"wal_level",wal_level,"WAL detail level.","MEDIUM")
        _add(params,"log_min_duration_statement","1000","Log queries >1s.","MINOR")
        if wl == "olap":
            _add(params,"max_parallel_workers_per_gather",min(8, cpu),"OLAP: more parallel workers.","MAJOR")
            _add(params,"work_mem",f"{work_mem*4}MB","OLAP: larger sort memory.","MAJOR")

        if conns * work_mem > ram * 1024 * 0.5:
            _deg(degs,"work_mem × connections",f"{conns} connections × {work_mem}MB = {conns*work_mem}MB. Exceeds 50% RAM. Risk of OOM under concurrent complex queries.")
        if conns > 500:
            _deg(degs,"High max_connections",f"{conns} connections increases per-connection overhead. Use PgBouncer for connection pooling instead.")

        fl = max(65535, conns * 3)
        smx = max(65535, conns)
        snip = [f"# PostgreSQL — {cpu} cores, {ram}GB RAM, {conns} conns",f"shared_buffers = {shared_buf}MB",f"effective_cache_size = {eff_cache}MB",f"work_mem = {work_mem}MB",f"max_connections = {conns}"]

    elif calc == "mysql":
        conns = max(50, _i(p,"max_connections",300))
        disk = str(p.get("disk_type","ssd")).lower()
        pool = int(ram * 1024 * 0.7)
        pool_inst = max(1, min(64, pool // 1024))
        log_file = max(48, pool // 4)
        log_buf = max(16, min(256, pool // 32))
        flush = "O_DIRECT" if disk == "ssd" else "fsync"
        io_cap = 2000 if disk == "ssd" else 200
        thread_cache = max(8, min(100, conns // 4))
        table_cache = max(400, conns * 2)
        tmp_table = max(16, int(ram * 1024 * 0.02))

        _add(params,"innodb_buffer_pool_size",f"{pool}MB","70% of RAM for InnoDB cache.","MAJOR")
        _add(params,"innodb_buffer_pool_instances",pool_inst,"Reduce contention.","MAJOR")
        _add(params,"innodb_log_file_size",f"{log_file}MB","Redo log size.","MAJOR")
        _add(params,"innodb_log_buffer_size",f"{log_buf}MB","Redo log buffer.","MEDIUM")
        _add(params,"innodb_flush_method",flush,f"{'Direct I/O for SSD' if flush=='O_DIRECT' else 'Default for HDD'}.","MAJOR")
        _add(params,"innodb_io_capacity",io_cap,"I/O operations/sec budget.","MEDIUM")
        _add(params,"innodb_io_capacity_max",io_cap*2,"Burst I/O cap.","MEDIUM")
        _add(params,"max_connections",conns,"Connection limit.","MAJOR")
        _add(params,"thread_cache_size",thread_cache,"Reuse threads for new connections.","MEDIUM")
        _add(params,"table_open_cache",table_cache,"Cached open tables.","MEDIUM")
        _add(params,"tmp_table_size",f"{tmp_table}MB","In-memory temp tables.","MINOR")
        _add(params,"innodb_flush_log_at_trx_commit","1","Full ACID durability.","MAJOR")
        _add(params,"sync_binlog","1","Sync binary log per commit.","MAJOR")
        _add(params,"innodb_file_per_table","ON","Separate tablespace files.","MINOR")
        _add(params,"slow_query_log","ON","Enable slow log.","MINOR")
        _add(params,"long_query_time","1","Log queries >1s.","MINOR")

        if pool > ram * 1024 * 0.85:
            _deg(degs,"innodb_buffer_pool_size","Pool >85% of RAM. No room for OS cache, connections, tmp tables.")

        fl = max(65535, conns * 3)
        smx = max(65535, conns)
        snip = [f"# MySQL — {cpu} cores, {ram}GB RAM",f"innodb_buffer_pool_size = {pool}M",f"max_connections = {conns}"]

    elif calc == "mongodb":
        conns = max(50, _i(p,"max_connections",500))
        disk = str(p.get("disk_type","ssd")).lower()
        rs = _b(p,"replica_set")
        wt_cache = max(1, int((ram - 1) * 0.5))
        oplog_mb = max(990, int(ram * 1024 * 0.05))

        _add(params,"storage.wiredTiger.engineConfig.cacheSizeGB",wt_cache,f"50% of (RAM - 1GB) for WiredTiger.","MAJOR")
        _add(params,"net.maxIncomingConnections",conns,"Connection cap.","MAJOR")
        _add(params,"storage.journal.enabled","true","Crash recovery.","MAJOR")
        _add(params,"replication.oplogSizeMB",oplog_mb,"Oplog for replication window.","MAJOR" if rs else "MEDIUM")
        _add(params,"operationProfiling.slowOpThresholdMs","100","Log slow ops.","MINOR")
        _add(params,"setParameter.wiredTigerConcurrentReadTransactions",max(128, cpu * 16),"Concurrent reads.","MEDIUM")
        _add(params,"setParameter.wiredTigerConcurrentWriteTransactions",max(128, cpu * 16),"Concurrent writes.","MEDIUM")
        if rs:
            _add(params,"replication.replSetName","rs0","Replica set name.","MAJOR")
            _add(params,"net.bindIp","0.0.0.0","Bind for replica communication.","MEDIUM")

        if conns > 10000:
            _deg(degs,"maxIncomingConnections",f"{conns} connections use ~1MB each stack. Total ~{conns//1024}GB. Use connection pooling.")

        fl = max(65535, conns * 2)
        smx = 65535
        snip = [f"# MongoDB — {cpu} cores, {ram}GB RAM",f"storage.wiredTiger.engineConfig.cacheSizeGB: {wt_cache}",f"net.maxIncomingConnections: {conns}"]

    elif calc == "haproxy":
        backends = max(1, _i(p,"backends_count",5))
        ssl_term = _b(p,"ssl_termination")
        global_maxconn = max(1000, conc * 2)
        fe_maxconn = global_maxconn
        srv_maxconn = max(100, global_maxconn // backends)
        nbthread = cpu
        to_connect = max(5000, resp_ms * 2)
        to_client = max(30000, resp_ms * 10)
        to_server = max(30000, resp_ms * 10)

        _add(params,"global.maxconn",global_maxconn,f"Global connection cap for {conc} concurrency.","MAJOR")
        _add(params,"global.nbthread",nbthread,"One thread per core.","MAJOR")
        _add(params,"defaults.timeout connect",f"{to_connect}ms","Backend connect timeout.","MEDIUM")
        _add(params,"defaults.timeout client",f"{to_client}ms","Client inactivity timeout.","MEDIUM")
        _add(params,"defaults.timeout server",f"{to_server}ms","Server response timeout.","MEDIUM")
        _add(params,"defaults.timeout http-keep-alive","10s","Keepalive timeout.","MINOR")
        _add(params,"frontend maxconn",fe_maxconn,"Frontend connection cap.","MAJOR")
        _add(params,"server maxconn",srv_maxconn,f"Per-server cap ({backends} backends).","MAJOR")
        _add(params,"balance","leastconn","Distribute by least connections.","MEDIUM")
        _add(params,"option http-server-close","enabled","Close server-side after response.","MEDIUM")
        _add(params,"option forwardfor","enabled","X-Forwarded-For header.","MINOR")
        if ssl_term:
            _add(params,"ssl-default-bind-ciphers","ECDHE+AESGCM","Modern ciphers.","MAJOR")
            _add(params,"ssl-default-bind-options","no-sslv3 no-tlsv10 no-tlsv11","Disable legacy.","MAJOR")
            _add(params,"tune.ssl.default-dh-param","2048","DH parameter size.","MEDIUM")

        if global_maxconn > 100000:
            _deg(degs,"Very high maxconn",f"maxconn={global_maxconn} uses ~32KB per connection = {global_maxconn*32//1024}MB. Ensure RAM suffices.")

        fl = max(65535, global_maxconn * 2)
        smx = max(65535, global_maxconn)
        snip = [f"# HAProxy — {cpu} cores",f"global",f"    maxconn {global_maxconn}",f"    nbthread {nbthread}"]

    elif calc == "k8s":
        replicas = max(1, _i(p,"replicas",3))
        wl = str(p.get("workload_type","web")).lower()
        hpa = _b(p,"hpa_enabled",True)
        pdb = _b(p,"pdb_enabled",True)
        cpu_req = int((cpu / replicas) * 1000 * 0.7)
        cpu_lim = int((cpu / replicas) * 1000)
        mem_req = int((ram / replicas) * 1024 * 0.7)
        mem_lim = int((ram / replicas) * 1024 * 0.9)

        _add(params,"replicas",replicas,"Baseline replica count.","MAJOR")
        _add(params,"resources.requests.cpu",f"{cpu_req}m","CPU request per pod.","MAJOR")
        _add(params,"resources.limits.cpu",f"{cpu_lim}m","CPU limit per pod.","MAJOR")
        _add(params,"resources.requests.memory",f"{mem_req}Mi","Memory request per pod.","MAJOR")
        _add(params,"resources.limits.memory",f"{mem_lim}Mi","Memory limit per pod.","MAJOR")
        if hpa:
            _add(params,"HPA minReplicas",replicas,"HPA minimum.","MEDIUM")
            _add(params,"HPA maxReplicas",replicas * 4,"HPA maximum.","MEDIUM")
            _add(params,"HPA targetCPU","70%","Scale-up threshold.","MEDIUM")
        if pdb:
            _add(params,"PDB minAvailable",max(1, replicas - 1),"Disruption budget.","MEDIUM")
        _add(params,"terminationGracePeriodSeconds","30","Graceful shutdown window.","MINOR")
        _add(params,"livenessProbe.initialDelaySeconds","15","Liveness start delay.","MEDIUM")
        _add(params,"readinessProbe.initialDelaySeconds","5","Readiness start delay.","MEDIUM")

        fl = 65535; smx = 65535
        snip = [f"# K8s Deployment — {replicas} replicas",f"resources:",f"  requests: {{ cpu: {cpu_req}m, memory: {mem_req}Mi }}",f"  limits: {{ cpu: {cpu_lim}m, memory: {mem_lim}Mi }}"]

    elif calc in ("docker","podman"):
        wl = str(p.get("workload_type","web")).lower()
        replicas = max(1, _i(p,"replicas",1))
        rootless = _b(p,"rootless") if calc == "podman" else False

        _add(params,"storage-driver","overlay2","Best performance and compatibility.","MAJOR")
        _add(params,"log-driver","json-file","Default structured logging.","MEDIUM")
        _add(params,"log-opts.max-size","100m","Limit log file growth.","MEDIUM")
        _add(params,"log-opts.max-file","5","Rotate log files.","MINOR")
        _add(params,"default-ulimits.nofile","65535:65535","Container file descriptor limit.","MAJOR")
        _add(params,"default-ulimits.nproc","65535:65535","Container process limit.","MEDIUM")
        _add(params,"live-restore","true","Keep containers on daemon restart.","MEDIUM")
        if calc == "docker":
            _add(params,"userland-proxy","false","Use iptables for better performance.","MEDIUM")
        if calc == "podman" and rootless:
            _add(params,"rootless mode","enabled","Unprivileged containers.","MEDIUM")
        fl = 65535; smx = 65535
        snip = [f"# {calc.title()} daemon.json",f'"storage-driver": "overlay2"',f'"log-driver": "json-file"']

    elif calc == "os":
        wl = str(p.get("workload_type","web")).lower()
        disk = str(p.get("disk_type","ssd")).lower()
        swap = 1 if wl == "database" else 10
        dirty = 40 if wl == "database" else 20
        dirty_bg = 10 if wl == "database" else 5

        _add(params,"vm.swappiness",swap,f"{'Minimal swap for DB' if wl=='database' else 'Low swap for web'}.","MAJOR")
        _add(params,"vm.dirty_ratio",f"{dirty}%","Max dirty pages before sync.","MAJOR")
        _add(params,"vm.dirty_background_ratio",f"{dirty_bg}%","Background flush threshold.","MEDIUM")
        _add(params,"vm.overcommit_memory","1" if wl=="database" else "0","Memory overcommit policy.","MAJOR")
        _add(params,"net.core.somaxconn","65535","Listen backlog.","MAJOR")
        _add(params,"net.ipv4.tcp_max_syn_backlog","65535","SYN queue.","MAJOR")
        _add(params,"net.ipv4.tcp_tw_reuse","1","Reuse TIME_WAIT sockets.","MEDIUM")
        _add(params,"net.ipv4.tcp_fin_timeout","15","FIN timeout.","MEDIUM")
        _add(params,"net.ipv4.ip_local_port_range","1024 65535","Ephemeral ports.","MAJOR")
        _add(params,"fs.file-max",f"{max(2097152, int(ram*1024*256))}","System-wide fd limit.","MAJOR")
        _add(params,"net.core.rmem_max","16777216","TCP receive buffer.","MEDIUM")
        _add(params,"net.core.wmem_max","16777216","TCP send buffer.","MEDIUM")
        _add(params,"kernel.pid_max","65536","Max PIDs.","MINOR")
        _add(params,"Transparent Huge Pages","madvise" if wl=="database" else "always","{'Disable for DB' if wl=='database' else 'Default'}.","MAJOR" if wl=="database" else "MINOR")
        if disk == "ssd":
            _add(params,"I/O Scheduler","none/noop","No reordering for SSD.","MEDIUM")
        else:
            _add(params,"I/O Scheduler","mq-deadline","Deadline for HDD.","MEDIUM")
        _add(params,"CPU Governor","performance","Max CPU frequency.","MEDIUM")
        fl = max(65535, int(ram * 1024 * 256))
        smx = 65535
        snip = [f"# Linux OS Tuning — {wl} workload",f"vm.swappiness = {swap}",f"net.core.somaxconn = 65535","fs.file-max = 2097152"]

    elif calc == "rabbitmq":
        queues = max(1, _i(p,"queue_count",200))
        consumers = max(1, _i(p,"consumers",50))
        cluster = _b(p,"cluster_enabled")
        wm = min(0.6, max(0.2, 0.4 if ram >= 16 else 0.3))
        disk_limit = max(50, int(ram * 1024 * 0.1))
        ch_max = max(128, consumers * 4)
        prefetch = max(1, min(250, rps // max(1, consumers)))
        hb = 60

        _add(params,"vm_memory_high_watermark",wm,f"{int(wm*100)}% of RAM before flow control.","MAJOR")
        _add(params,"disk_free_limit",f"{disk_limit}MB","Min free disk before alarm.","MAJOR")
        _add(params,"channel_max",ch_max,f"Channels for {consumers} consumers.","MEDIUM")
        _add(params,"heartbeat",hb,"Client heartbeat interval.","MINOR")
        _add(params,"consumer_timeout","1800000","30min consumer ack timeout.","MEDIUM")
        _add(params,"prefetch_count",prefetch,f"Messages per consumer batch.","MEDIUM")
        _add(params,"queue_index_embed_msgs_below","4096","Inline small messages.","MINOR")
        if cluster:
            _add(params,"cluster_formation.peer_discovery_backend","rabbit_peer_discovery_classic_config","Cluster discovery.","MAJOR")
            _add(params,"ha-mode","all","Mirror all queues.","MAJOR")
            _add(params,"ha-sync-mode","automatic","Auto-sync new mirrors.","MEDIUM")

        if queues > 10000:
            _deg(degs,"Queue count",f"{queues} queues consume memory for metadata. Consider lazy queues or streams.")
        if consumers > 1000 and ch_max < consumers:
            _deg(degs,"Channel exhaustion",f"More consumers ({consumers}) than channels ({ch_max}). Increase channel_max.")

        fl = max(65535, queues * 4 + consumers * 4)
        smx = 65535
        snip = [f"# RabbitMQ — {cpu} cores, {ram}GB RAM",f"vm_memory_high_watermark.relative = {wm}",f"disk_free_limit.absolute = {disk_limit}MB"]

    else:
        snip = [f"# {calc} — generic baseline","workers={cpu}"]

    return fl, smx, snip
