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


# ── OS tuning generator ─────────────────────────────────
def _os_tuning(p: dict, file_limit: int, somaxconn: int = 65535) -> dict:
    os_type = str(p.get("os_type","RHEL")).lower()
    cmds = []
    if any(x in os_type for x in ("rhel","centos","ubuntu","debian","amazon","suse","oracle","rocky","alma","fedora")):
        cmds = [
            f"sysctl -w net.core.somaxconn={somaxconn}",
            f"sysctl -w net.ipv4.tcp_max_syn_backlog={somaxconn}",
            "sysctl -w net.ipv4.tcp_tw_reuse=1",
            "sysctl -w net.ipv4.tcp_fin_timeout=15",
            "sysctl -w net.ipv4.tcp_keepalive_time=600",
            "sysctl -w net.ipv4.tcp_keepalive_intvl=15",
            "sysctl -w net.ipv4.tcp_keepalive_probes=5",
            f"sysctl -w net.core.netdev_max_backlog={max(65536, somaxconn)}",
            "sysctl -w net.core.rmem_max=16777216",
            "sysctl -w net.core.wmem_max=16777216",
            f"sysctl -w fs.file-max={max(2097152, file_limit*4)}",
            f"ulimit -n {file_limit}",
            f"# /etc/security/limits.conf: * soft nofile {file_limit}",
            f"# /etc/security/limits.conf: * hard nofile {file_limit}",
        ]
    elif "windows" in os_type:
        cmds = [
            "netsh int tcp set global autotuninglevel=normal",
            f"reg add HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters /v MaxUserPort /t REG_DWORD /d {min(65534, file_limit)}",
            "reg add HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters /v TcpTimedWaitDelay /t REG_DWORD /d 30",
            "reg add HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters /v EnableDynamicBacklog /t REG_DWORD /d 1",
            "# Set Power Plan to High Performance",
        ]
    elif "solaris" in os_type:
        cmds = [
            f"ndd -set /dev/tcp tcp_conn_req_max_q {somaxconn}",
            f"ndd -set /dev/tcp tcp_conn_req_max_q0 {somaxconn*4}",
            "ndd -set /dev/tcp tcp_time_wait_interval 60000",
            f"# /etc/system: set rlim_fd_max={file_limit}",
        ]
    elif "aix" in os_type:
        cmds = [
            f"no -o somaxconn={somaxconn}",
            "no -o rfc1323=1",
            "no -o tcp_keepidle=600",
            f"chdev -l sys0 -a maxuproc={max(4096, file_limit//16)}",
            f"ulimit -n {file_limit}",
        ]
    elif "hp" in os_type:
        cmds = [
            f"ndd -set /dev/tcp tcp_conn_request_max {somaxconn}",
            "ndd -set /dev/tcp tcp_time_wait_interval 60000",
            f"kctune nfile={file_limit}",
            f"kctune maxfiles={file_limit}",
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
        worker_conn = max(1024, min(65535, concurrency // workers * 4))
        rlimit_nofile = worker_conn * 2
        keepalive_to = 65 if keepalive else 0
        client_max_body = max(1, _i(payload,"client_max_body_size_mb",10))
        proxy_buffers = max(4, min(32, concurrency // 1000 + 4)) if rproxy else 4
        proxy_buf_size = "16k" if avg_kb < 32 else "32k"
        open_file_cache = max(10000, worker_conn * 20)
        send_to = 60 if rproxy else 30
        proxy_connect_to = 60
        proxy_read_to = max(60, resp_ms * 3 // 1000 + 30)

        _add(params,"worker_processes","auto",f"Auto = {workers} cores. Matches CPU topology.","MAJOR")
        _add(params,"worker_connections",worker_conn,f"Each worker handles {worker_conn} sockets. Total capacity: {workers*worker_conn}.","MAJOR")
        _add(params,"worker_rlimit_nofile",rlimit_nofile,f"2x worker_connections for fd headroom.","MAJOR")
        _add(params,"keepalive_timeout",f"{keepalive_to}s","Balanced for connection reuse without socket exhaustion.","MAJOR")
        _add(params,"client_max_body_size",f"{client_max_body}m","Max upload size. Increase for file uploads.","MEDIUM")
        _add(params,"sendfile","on",f"Zero-copy for static content ({static_pct}% of traffic).","MEDIUM")
        _add(params,"tcp_nopush","on","Optimize packet assembly with sendfile.","MEDIUM")
        _add(params,"tcp_nodelay","on","Disable Nagle for low-latency responses.","MEDIUM")
        _add(params,"multi_accept","on","Accept multiple connections per event loop.","MEDIUM")
        _add(params,"open_file_cache",f"max={open_file_cache} inactive=20s","Cache file descriptors for hot paths.","MEDIUM")
        _add(params,"open_file_cache_valid","30s","Revalidate cached descriptors every 30s.","MINOR")
        _add(params,"send_timeout",f"{send_to}s","Response write timeout to client.","MEDIUM")
        if gzip:
            _add(params,"gzip","on","Compress responses to save bandwidth.","MEDIUM")
            _add(params,"gzip_comp_level","4","Level 4 = good ratio without CPU burn.","MINOR")
            _add(params,"gzip_min_length","256","Skip tiny responses.","MINOR")
            _add(params,"gzip_types","text/plain text/css application/json application/javascript text/xml","Compressible MIME types.","MINOR")
        if ssl:
            _add(params,"ssl_protocols","TLSv1.2 TLSv1.3","Drop legacy TLS for security.","MAJOR")
            _add(params,"ssl_ciphers","ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256","Modern cipher suite.","MAJOR")
            _add(params,"ssl_session_cache","shared:SSL:50m","Reuse TLS sessions across workers.","MEDIUM")
            _add(params,"ssl_session_timeout","1d","24h session ticket lifetime.","MINOR")
            _add(params,"ssl_prefer_server_ciphers","on","Server-side cipher preference.","MINOR")
            if http2: _add(params,"http2","on","HTTP/2 multiplexing for SSL connections.","MEDIUM")
        if rproxy:
            _add(params,"proxy_connect_timeout",f"{proxy_connect_to}s","Backend connect timeout.","MEDIUM")
            _add(params,"proxy_read_timeout",f"{proxy_read_to}s",f"Based on avg response {resp_ms}ms × 3 + 30s buffer.","MEDIUM")
            _add(params,"proxy_send_timeout",f"{send_to}s","Upstream send timeout.","MEDIUM")
            _add(params,"proxy_buffers",f"{proxy_buffers} {proxy_buf_size}","Proxy response buffering.","MEDIUM")
            _add(params,"proxy_buffer_size",proxy_buf_size,"Initial buffer for headers.","MINOR")
            _add(params,"proxy_http_version","1.1","Required for keepalive to upstream.","MINOR")
            _add(params,"proxy_set_header","Connection \"\"","Enable upstream keepalive.","MINOR")
        _add(params,"access_log","off or buffered","Disable sync logging under high RPS.","MINOR")
        _add(params,"error_log","/var/log/nginx/error.log warn","Only warn+ level in production.","MINOR")

        # degradation checks
        if worker_conn > 16384:
            _deg(degradations,"worker_connections",f"Value {worker_conn} is very high. Each connection uses ~1KB RAM + fd. At {workers} workers = {workers*worker_conn*1//1024}MB+ fd memory. May cause OOM under burst.")
        if keepalive and keepalive_to > 60:
            _deg(degradations,"keepalive_timeout","High keepalive holds sockets open. Under burst traffic, may exhaust connection slots before timeout fires.")
        if gzip and rps > 50000:
            _deg(degradations,"gzip","At >50K RPS, gzip compression consumes significant CPU. Consider offloading to CDN or reducing comp_level to 1.")
        if ssl and not http2:
            _deg(degradations,"SSL without HTTP/2","SSL adds latency per request. Without HTTP/2 multiplexing, each resource needs a separate TLS handshake.")
        if client_max_body > 100:
            _deg(degradations,"client_max_body_size",f"Large body size ({client_max_body}MB) allows big uploads that block worker connections during transfer.")
        if concurrency > workers * worker_conn * 0.8:
            capacity_warnings.append(f"CAPACITY WARNING: Expected concurrency ({concurrency}) approaches max capacity ({workers*worker_conn}). Scale horizontally or increase CPU cores.")

        snippet_lines = [
            f"# NGINX Production Config — {cpu} cores, {ram}GB RAM, {rps} RPS",
            f"worker_processes auto;  # {workers} cores",
            f"worker_rlimit_nofile {rlimit_nofile};",
            "events {",
            f"    worker_connections {worker_conn};",
            "    multi_accept on;",
            "    use epoll;",
            "}",
            "http {",
            "    sendfile on;",
            "    tcp_nopush on;",
            "    tcp_nodelay on;",
            f"    keepalive_timeout {keepalive_to};",
            f"    client_max_body_size {client_max_body}m;",
        ]
        if gzip:
            snippet_lines += ["    gzip on;","    gzip_comp_level 4;","    gzip_min_length 256;"]
        if ssl:
            snippet_lines += [f"    ssl_protocols TLSv1.2 TLSv1.3;","    ssl_prefer_server_ciphers on;"]
        if rproxy:
            snippet_lines += [f"    proxy_connect_timeout {proxy_connect_to}s;",f"    proxy_read_timeout {proxy_read_to}s;",f"    proxy_buffers {proxy_buffers} {proxy_buf_size};"]
        snippet_lines.append("}")

        file_limit = rlimit_nofile
        somaxconn = max(65535, worker_conn)

    # ── REDIS ────────────────────────────────────────────
    elif calculator == "redis":
        keys = max(1, _i(payload,"estimated_keys",1000000))
        key_size = max(64, _i(payload,"avg_key_size_bytes",512))
        persist = str(payload.get("persistence_type","aof")).lower()
        cluster = _b(payload,"cluster_enabled")
        dataset_gb = round(keys * key_size / (1024**3), 2)
        maxmem_gb = max(1, int(ram * 0.7))
        hz_val = 100 if rps > 10000 else 10
        io_threads = min(cpu, 4) if cpu >= 4 else 1
        tcp_backlog_val = max(511, min(65535, concurrency))

        _add(params,"maxmemory",f"{maxmem_gb}gb",f"70% of {ram}GB RAM. Dataset ~{dataset_gb}GB.","MAJOR")
        _add(params,"maxmemory-policy","allkeys-lru","LRU eviction when memory full.","MAJOR")
        _add(params,"tcp-backlog",tcp_backlog_val,f"Match expected concurrency ({concurrency}).","MAJOR")
        _add(params,"hz",hz_val,f"{'High' if hz_val==100 else 'Default'} tick rate for {rps} RPS.","MEDIUM")
        _add(params,"io-threads",io_threads,f"I/O threads for {cpu}-core system.","MEDIUM")
        _add(params,"io-threads-do-reads","yes","Parallelize read I/O.","MEDIUM")
        _add(params,"timeout","300","Close idle clients after 5min.","MINOR")
        _add(params,"tcp-keepalive","300","Detect dead peers.","MINOR")
        if persist == "aof":
            _add(params,"appendonly","yes","AOF persistence.","MAJOR")
            _add(params,"appendfsync","everysec","Fsync once/sec — balance durability vs throughput.","MAJOR")
            _add(params,"auto-aof-rewrite-percentage","100","Rewrite AOF when doubled.","MINOR")
            _add(params,"auto-aof-rewrite-min-size","64mb","Min size before rewrite.","MINOR")
        elif persist == "rdb":
            _add(params,"save","900 1 300 10 60 10000","RDB snapshot schedule.","MAJOR")
        else:
            _add(params,"save","\"\"","No persistence — data loss on restart.","MAJOR")
        _add(params,"lazyfree-lazy-eviction","yes","Background eviction avoids latency spikes.","MEDIUM")
        _add(params,"lazyfree-lazy-expire","yes","Background key expiry.","MEDIUM")
        _add(params,"lazyfree-lazy-server-del","yes","Background deletions.","MINOR")
        if cluster:
            _add(params,"cluster-enabled","yes","Redis Cluster mode.","MAJOR")
            _add(params,"cluster-node-timeout","15000","Node failure detection.","MEDIUM")
        _add(params,"protected-mode","yes","Require auth.","MEDIUM")
        _add(params,"rename-command FLUSHALL","\"\"","Disable dangerous commands.","MINOR")

        if dataset_gb > maxmem_gb:
            _deg(degradations,"Dataset vs Memory",f"Dataset (~{dataset_gb}GB) exceeds maxmemory ({maxmem_gb}GB). Eviction will be aggressive — data loss likely.")
        if persist == "aof" and rps > 50000:
            _deg(degradations,"AOF at high RPS",f"AOF appendfsync=everysec at {rps} RPS causes I/O pressure. Consider RDB or no persistence for cache-only nodes.")
        if hz_val == 100 and cpu < 4:
            _deg(degradations,"High hz on low CPU","hz=100 increases CPU usage for timers. On {cpu}-core system this steals cycles from request handling.")

        file_limit = max(65535, concurrency * 2)
        somaxconn = tcp_backlog_val
        snippet_lines = [
            f"# Redis Production Config — {cpu} cores, {ram}GB RAM",
            f"maxmemory {maxmem_gb}gb",
            "maxmemory-policy allkeys-lru",
            f"tcp-backlog {tcp_backlog_val}",
            f"hz {hz_val}",
            f"io-threads {io_threads}",
            f"appendonly {'yes' if persist=='aof' else 'no'}",
            f"timeout 300",
        ]

    # ── TOMCAT ───────────────────────────────────────────
    elif calculator == "tomcat":
        app_type = str(payload.get("app_type","rest")).lower()
        ssl = _b(payload,"ssl_enabled")
        max_upload = max(1, _i(payload,"max_upload_mb",50))
        session_to = max(1, _i(payload,"session_timeout_min",30))
        compress = _b(payload,"enable_compression",True)
        jmx = _b(payload,"jmx_enabled")

        max_threads = max(25, min(800, concurrency + 50))
        min_spare = max(10, max_threads // 10)
        max_conn = max(max_threads, concurrency * 2)
        accept_count = max(100, max_threads // 2)
        heap_max = max(256, int(ram * 1024 * 0.65))
        heap_min = heap_max
        metaspace = max(256, min(512, heap_max // 8))
        gc = "G1GC" if heap_max > 4096 else "ParallelGC"
        conn_timeout = max(5000, min(60000, resp_ms * 3))

        _add(params,"maxThreads",max_threads,f"Thread pool cap for {concurrency} concurrency.","MAJOR")
        _add(params,"minSpareThreads",min_spare,"Pre-warmed threads for burst absorption.","MEDIUM")
        _add(params,"maxConnections",max_conn,"Total socket connections.","MAJOR")
        _add(params,"acceptCount",accept_count,"Backlog queue when all threads busy.","MAJOR")
        _add(params,"connectionTimeout",f"{conn_timeout}ms",f"3x avg response ({resp_ms}ms).","MEDIUM")
        _add(params,"-Xmx / -Xms",f"{heap_max}m",f"65% of {ram}GB RAM. Equal Xmx=Xms avoids resize.","MAJOR")
        _add(params,"-XX:+Use"+gc,"enabled",f"{'G1GC for large heap' if gc=='G1GC' else 'ParallelGC for smaller heap'}.","MAJOR")
        _add(params,"-XX:MetaspaceSize",f"{metaspace}m","Class metadata space.","MEDIUM")
        _add(params,"protocol","org.apache.coyote.http11.Http11NioProtocol","NIO for non-blocking I/O.","MAJOR")
        _add(params,"maxKeepAliveRequests","100","Requests per keepalive connection.","MEDIUM")
        _add(params,"keepAliveTimeout","20000","20s keepalive.","MINOR")
        _add(params,"server.tomcat.max-swallow-size",f"{max_upload}MB","Max upload.","MEDIUM")
        _add(params,"session-timeout",f"{session_to}min","Session expiry.","MINOR")
        if compress:
            _add(params,"compression","on","HTTP compression.","MEDIUM")
            _add(params,"compressibleMimeType","text/html,text/xml,text/css,application/json,application/javascript","Compressible types.","MINOR")
        if ssl:
            _add(params,"sslProtocol","TLSv1.2+TLSv1.3","Modern TLS only.","MAJOR")
        if jmx:
            _add(params,"JMX Remote","enabled","Monitoring endpoint.","MINOR")
        _add(params,"-XX:+HeapDumpOnOutOfMemoryError","enabled","Capture OOM for analysis.","MEDIUM")
        _add(params,"-XX:MaxGCPauseMillis","200","G1GC pause target.","MINOR")

        if max_threads > 500:
            _deg(degradations,"maxThreads",f"High thread count ({max_threads}) increases context switching overhead and memory usage (~1MB stack/thread).")
        if heap_max > ram * 1024 * 0.8:
            _deg(degradations,"JVM Heap","Heap uses >80% of RAM. No room for OS buffers and other processes. Risk of OOM killer.")
        if conn_timeout > 30000:
            _deg(degradations,"connectionTimeout",f"Long timeout ({conn_timeout}ms) causes slow clients to hold threads. Reduces effective concurrency.")

        file_limit = max(65535, max_conn * 2)
        somaxconn = max(65535, accept_count * 2)
        snippet_lines = [
            f"# Tomcat Production — {cpu} cores, {ram}GB RAM, {rps} RPS",
            f'JAVA_OPTS="-Xms{heap_max}m -Xmx{heap_max}m -XX:+Use{gc} -XX:MetaspaceSize={metaspace}m -XX:+HeapDumpOnOutOfMemoryError"',
            f"# server.xml Connector:",
            f'  maxThreads="{max_threads}" minSpareThreads="{min_spare}"',
            f'  maxConnections="{max_conn}" acceptCount="{accept_count}"',
            f'  connectionTimeout="{conn_timeout}" protocol="Http11NioProtocol"',
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
    os_tuning = _os_tuning(payload, file_limit, somaxconn)

    # ── Assemble response ────────────────────────────────
    audit = []
    if mode == "existing":
        audit = [
            "Compare current values against recommended before applying.",
            "Validate in staging first. Use canary rollout for production.",
        ]

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
