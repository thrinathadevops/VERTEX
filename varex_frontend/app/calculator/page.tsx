"use client";

import { useMemo, useState } from "react";
import { Calculator, Loader2, Play, RefreshCcw } from "lucide-react";
import { getCalculatorExample, runCalculator } from "@/lib/api";

type FieldType = "number" | "text" | "boolean" | "select";

type OsFamily = "linux" | "windows" | "solaris" | "aix" | "hpux" | "all";

type FieldConfig = {
  key: string;
  label: string;
  type: FieldType;
  required?: boolean;
  min?: number;
  max?: number;
  step?: number;
  placeholder?: string;
  options?: string[];
  category?: "app" | "os" | "perf";
  osFamily?: OsFamily;
};

const OS_TYPES = [
  "RHEL", "CentOS", "Ubuntu", "Debian", "Amazon Linux", "SUSE/SLES",
  "Oracle Linux", "Rocky Linux", "AlmaLinux", "Fedora",
  "Windows Server 2022", "Windows Server 2019", "Windows Server 2016",
  "Solaris 11", "Solaris 10",
  "AIX 7.3", "AIX 7.2",
  "HP-UX 11i v3",
];

const getOsFamily = (osType: string): OsFamily => {
  const lower = osType.toLowerCase();
  if (lower.includes("windows")) return "windows";
  if (lower.includes("solaris")) return "solaris";
  if (lower.includes("aix")) return "aix";
  if (lower.includes("hp")) return "hpux";
  return "linux";
};

type CalculatorConfig = {
  key: string;
  label: string;
  profiles: { key: string; label: string }[];
  fields: FieldConfig[];
};

const COMMON_FIELDS: FieldConfig[] = [
  { key: "mode", label: "Mode", type: "select", options: ["new", "existing"], required: true, category: "app" },
  { key: "os_type", label: "Operating System", type: "select", options: OS_TYPES, required: true, category: "app" },
  { key: "cpu_cores", label: "CPU Cores", type: "number", min: 1, step: 1, required: true, category: "app" },
  { key: "ram_gb", label: "RAM (GB)", type: "number", min: 1, step: 1, required: true, category: "app" },
  { key: "expected_rps", label: "Expected RPS", type: "number", min: 1, step: 1, required: true, category: "app" },
  { key: "avg_response_ms", label: "Avg Response (ms)", type: "number", min: 1, step: 1, required: true, category: "app" },
];

/* ══════════════════════════════════════════════════════════
   Linux sysctl / kernel params
   ══════════════════════════════════════════════════════════ */
const OS_NET: FieldConfig[] = [
  { key: "os_somaxconn", label: "net.core.somaxconn", type: "number", min: 128, step: 1, category: "os", placeholder: "65535", osFamily: "linux" },
  { key: "os_tcp_max_syn_backlog", label: "net.ipv4.tcp_max_syn_backlog", type: "number", min: 128, step: 1, category: "os", placeholder: "65535", osFamily: "linux" },
  { key: "os_tcp_tw_reuse", label: "net.ipv4.tcp_tw_reuse", type: "boolean", category: "os", osFamily: "linux" },
  { key: "os_tcp_fin_timeout", label: "net.ipv4.tcp_fin_timeout (s)", type: "number", min: 5, step: 1, category: "os", placeholder: "15", osFamily: "linux" },
  { key: "os_tcp_keepalive_time", label: "net.ipv4.tcp_keepalive_time (s)", type: "number", min: 30, step: 1, category: "os", placeholder: "600", osFamily: "linux" },
  { key: "os_tcp_keepalive_intvl", label: "net.ipv4.tcp_keepalive_intvl (s)", type: "number", min: 5, step: 1, category: "os", placeholder: "15", osFamily: "linux" },
  { key: "os_tcp_keepalive_probes", label: "net.ipv4.tcp_keepalive_probes", type: "number", min: 1, step: 1, category: "os", placeholder: "5", osFamily: "linux" },
  { key: "os_netdev_max_backlog", label: "net.core.netdev_max_backlog", type: "number", min: 1000, step: 1, category: "os", placeholder: "65536", osFamily: "linux" },
  { key: "os_rmem_max", label: "net.core.rmem_max (bytes)", type: "number", min: 65536, step: 1, category: "os", placeholder: "16777216", osFamily: "linux" },
  { key: "os_wmem_max", label: "net.core.wmem_max (bytes)", type: "number", min: 65536, step: 1, category: "os", placeholder: "16777216", osFamily: "linux" },
];
const OS_FILE: FieldConfig[] = [
  { key: "os_file_max", label: "fs.file-max", type: "number", min: 65536, step: 1, category: "os", placeholder: "2097152", osFamily: "linux" },
  { key: "os_nofile_soft", label: "ulimit nofile (soft)", type: "number", min: 1024, step: 1, category: "os", placeholder: "65535", osFamily: "linux" },
  { key: "os_nofile_hard", label: "ulimit nofile (hard)", type: "number", min: 1024, step: 1, category: "os", placeholder: "65535", osFamily: "linux" },
  { key: "os_nproc_soft", label: "ulimit nproc (soft)", type: "number", min: 1024, step: 1, category: "os", placeholder: "65535", osFamily: "linux" },
];
const OS_VM: FieldConfig[] = [
  { key: "os_overcommit_memory", label: "vm.overcommit_memory", type: "select", options: ["0", "1", "2"], category: "os", osFamily: "linux" },
  { key: "os_swappiness", label: "vm.swappiness", type: "number", min: 0, max: 100, step: 1, category: "os", placeholder: "10", osFamily: "linux" },
  { key: "os_dirty_ratio", label: "vm.dirty_ratio (%)", type: "number", min: 5, max: 80, step: 1, category: "os", placeholder: "40", osFamily: "linux" },
  { key: "os_dirty_bg_ratio", label: "vm.dirty_background_ratio (%)", type: "number", min: 1, max: 50, step: 1, category: "os", placeholder: "10", osFamily: "linux" },
];
const OS_PERF: FieldConfig[] = [
  { key: "perf_thp", label: "Transparent Huge Pages", type: "select", options: ["always", "madvise", "never"], category: "perf", osFamily: "linux" },
  { key: "perf_numa", label: "NUMA Interleave", type: "boolean", category: "perf", osFamily: "linux" },
  { key: "perf_io_sched", label: "I/O Scheduler", type: "select", options: ["noop", "deadline", "cfq", "mq-deadline", "bfq", "none"], category: "perf", osFamily: "linux" },
  { key: "perf_cpu_gov", label: "CPU Governor", type: "select", options: ["performance", "ondemand", "powersave", "conservative"], category: "perf", osFamily: "linux" },
];

/* ══════════════════════════════════════════════════════════
   Windows registry / TCP params
   ══════════════════════════════════════════════════════════ */
const OS_WIN: FieldConfig[] = [
  { key: "win_max_user_port", label: "MaxUserPort", type: "number", min: 5000, step: 1, category: "os", placeholder: "65534", osFamily: "windows" },
  { key: "win_tcp_timed_wait_delay", label: "TcpTimedWaitDelay (s)", type: "number", min: 30, step: 1, category: "os", placeholder: "30", osFamily: "windows" },
  { key: "win_dynamic_backlog", label: "Enable Dynamic Backlog", type: "boolean", category: "os", osFamily: "windows" },
  { key: "win_syn_attack_protect", label: "SynAttackProtect", type: "select", options: ["0", "1"], category: "os", osFamily: "windows" },
  { key: "win_max_free_tcbs", label: "MaxFreeTcbs", type: "number", min: 1000, step: 1, category: "os", placeholder: "65536", osFamily: "windows" },
  { key: "win_max_hash_table_size", label: "MaxHashTableSize", type: "number", min: 512, step: 1, category: "os", placeholder: "65536", osFamily: "windows" },
  { key: "win_keep_alive_time", label: "KeepAliveTime (ms)", type: "number", min: 1000, step: 1000, category: "os", placeholder: "300000", osFamily: "windows" },
  { key: "win_keep_alive_interval", label: "KeepAliveInterval (ms)", type: "number", min: 500, step: 500, category: "os", placeholder: "1000", osFamily: "windows" },
  { key: "win_paged_pool_size", label: "Paged Pool Size (MB)", type: "number", min: 128, step: 64, category: "os", osFamily: "windows" },
  { key: "win_nonpaged_pool_size", label: "Non-Paged Pool Size (MB)", type: "number", min: 64, step: 32, category: "os", osFamily: "windows" },
];
const OS_WIN_PERF: FieldConfig[] = [
  { key: "win_perf_power_plan", label: "Power Plan", type: "select", options: ["High Performance", "Balanced", "Power Saver"], category: "perf", osFamily: "windows" },
  { key: "win_perf_dedup", label: "Data Deduplication", type: "boolean", category: "perf", osFamily: "windows" },
  { key: "win_perf_rss", label: "Receive Side Scaling (RSS)", type: "boolean", category: "perf", osFamily: "windows" },
];

/* ══════════════════════════════════════════════════════════
   Solaris ndd / kernel params
   ══════════════════════════════════════════════════════════ */
const OS_SOL: FieldConfig[] = [
  { key: "sol_tcp_conn_req_max_q", label: "tcp_conn_req_max_q", type: "number", min: 128, step: 1, category: "os", placeholder: "1024", osFamily: "solaris" },
  { key: "sol_tcp_conn_req_max_q0", label: "tcp_conn_req_max_q0", type: "number", min: 128, step: 1, category: "os", placeholder: "4096", osFamily: "solaris" },
  { key: "sol_tcp_time_wait_interval", label: "tcp_time_wait_interval (ms)", type: "number", min: 1000, step: 1000, category: "os", placeholder: "60000", osFamily: "solaris" },
  { key: "sol_tcp_keepalive_interval", label: "tcp_keepalive_interval (ms)", type: "number", min: 10000, step: 1000, category: "os", placeholder: "7200000", osFamily: "solaris" },
  { key: "sol_tcp_fin_wait_2_timeout", label: "tcp_fin_wait_2_timeout (ms)", type: "number", min: 10000, step: 1000, category: "os", placeholder: "67500", osFamily: "solaris" },
  { key: "sol_rlim_fd_max", label: "rlim_fd_max", type: "number", min: 1024, step: 1, category: "os", placeholder: "65536", osFamily: "solaris" },
  { key: "sol_rlim_fd_cur", label: "rlim_fd_cur", type: "number", min: 256, step: 1, category: "os", placeholder: "65536", osFamily: "solaris" },
  { key: "sol_shmsys_shmmax", label: "shmsys:shminfo_shmmax", type: "number", min: 1048576, step: 1, category: "os", osFamily: "solaris" },
  { key: "sol_tcp_xmit_hiwat", label: "tcp_xmit_hiwat (bytes)", type: "number", min: 4096, step: 1, category: "os", placeholder: "65536", osFamily: "solaris" },
  { key: "sol_tcp_recv_hiwat", label: "tcp_recv_hiwat (bytes)", type: "number", min: 4096, step: 1, category: "os", placeholder: "65536", osFamily: "solaris" },
];

/* ══════════════════════════════════════════════════════════
   AIX tunables (no / vmo / ioo / schedo)
   ══════════════════════════════════════════════════════════ */
const OS_AIX: FieldConfig[] = [
  { key: "aix_somaxconn", label: "no: somaxconn", type: "number", min: 128, step: 1, category: "os", placeholder: "1024", osFamily: "aix" },
  { key: "aix_rfc1323", label: "no: rfc1323", type: "select", options: ["0", "1"], category: "os", osFamily: "aix" },
  { key: "aix_tcp_keepidle", label: "no: tcp_keepidle (s)", type: "number", min: 60, step: 60, category: "os", placeholder: "600", osFamily: "aix" },
  { key: "aix_tcp_keepintvl", label: "no: tcp_keepintvl (s)", type: "number", min: 5, step: 5, category: "os", placeholder: "15", osFamily: "aix" },
  { key: "aix_tcp_finwait2", label: "no: tcp_finwait2 (s)", type: "number", min: 30, step: 10, category: "os", placeholder: "1200", osFamily: "aix" },
  { key: "aix_maxuproc", label: "vmo: maxuproc", type: "number", min: 128, step: 1, category: "os", placeholder: "4096", osFamily: "aix" },
  { key: "aix_minperm", label: "vmo: minperm%", type: "number", min: 3, max: 80, step: 1, category: "os", placeholder: "5", osFamily: "aix" },
  { key: "aix_maxperm", label: "vmo: maxperm%", type: "number", min: 10, max: 90, step: 1, category: "os", placeholder: "90", osFamily: "aix" },
  { key: "aix_maxpgahead", label: "ioo: maxpgahead", type: "number", min: 8, step: 8, category: "os", placeholder: "64", osFamily: "aix" },
  { key: "aix_nofile_hard", label: "ulimit nofile (hard)", type: "number", min: 1024, step: 1, category: "os", placeholder: "65535", osFamily: "aix" },
];

/* ══════════════════════════════════════════════════════════
   HP-UX kernel params (ndd / kctune)
   ══════════════════════════════════════════════════════════ */
const OS_HPUX: FieldConfig[] = [
  { key: "hpux_tcp_conn_request_max", label: "tcp_conn_request_max", type: "number", min: 128, step: 1, category: "os", placeholder: "4096", osFamily: "hpux" },
  { key: "hpux_tcp_keepalive_interval", label: "tcp_keepalive_interval (ms)", type: "number", min: 10000, step: 1000, category: "os", placeholder: "7200000", osFamily: "hpux" },
  { key: "hpux_tcp_time_wait_interval", label: "tcp_time_wait_interval (ms)", type: "number", min: 1000, step: 1000, category: "os", placeholder: "60000", osFamily: "hpux" },
  { key: "hpux_nfile", label: "kctune: nfile", type: "number", min: 1024, step: 1, category: "os", placeholder: "65536", osFamily: "hpux" },
  { key: "hpux_maxfiles", label: "kctune: maxfiles", type: "number", min: 1024, step: 1, category: "os", placeholder: "65536", osFamily: "hpux" },
  { key: "hpux_maxfiles_lim", label: "kctune: maxfiles_lim", type: "number", min: 1024, step: 1, category: "os", placeholder: "65536", osFamily: "hpux" },
  { key: "hpux_shmmax", label: "kctune: shmmax (bytes)", type: "number", min: 1048576, step: 1, category: "os", osFamily: "hpux" },
  { key: "hpux_maxdsiz", label: "kctune: maxdsiz (bytes)", type: "number", min: 67108864, step: 1, category: "os", osFamily: "hpux" },
];

/* All OS fields combined for calculators that want cross-platform support */
const OS_ALL = [...OS_NET, ...OS_FILE, ...OS_VM, ...OS_WIN, ...OS_SOL, ...OS_AIX, ...OS_HPUX];

const CALCULATORS: CalculatorConfig[] = [
  {
    key: "nginx", label: "NGINX",
    profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON_FIELDS,
    { key: "worker_connections", label: "Worker Connections", type: "number", min: 512, step: 1, category: "app" },
    { key: "worker_rlimit_nofile", label: "Worker rlimit nofile", type: "number", min: 1024, step: 1, category: "app", placeholder: "65535" },
    { key: "client_max_body_size_mb", label: "Client Max Body (MB)", type: "number", min: 1, step: 1, category: "app" },
    { key: "keepalive_timeout_s", label: "Keepalive Timeout (s)", type: "number", min: 5, step: 1, category: "app" },
    { key: "send_timeout_s", label: "Send Timeout (s)", type: "number", min: 5, step: 1, category: "app" },
    { key: "proxy_connect_timeout_s", label: "Proxy Connect Timeout (s)", type: "number", min: 5, step: 1, category: "app" },
    { key: "proxy_read_timeout_s", label: "Proxy Read Timeout (s)", type: "number", min: 10, step: 1, category: "app" },
    { key: "open_file_cache_max", label: "Open File Cache Max", type: "number", min: 1000, step: 1, category: "app" },
    { key: "multi_accept", label: "Multi Accept", type: "boolean", category: "app" },
    { key: "gzip_enabled", label: "Enable Gzip", type: "boolean", category: "app" },
    { key: "sendfile", label: "Sendfile", type: "boolean", category: "app" },
    { key: "tcp_nopush", label: "TCP Nopush", type: "boolean", category: "app" },
    { key: "tcp_nodelay", label: "TCP Nodelay", type: "boolean", category: "app" },
    { key: "ssl_protocols", label: "SSL Protocols", type: "text", placeholder: "TLSv1.2 TLSv1.3", category: "app" },
    ...OS_NET, ...OS_FILE,
    { key: "perf_epoll", label: "Use epoll", type: "boolean", category: "perf" },
    ...OS_PERF.slice(2),
    ],
  },
  {
    key: "redis", label: "Redis",
    profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON_FIELDS,
    { key: "estimated_keys", label: "Estimated Keys", type: "number", min: 1, step: 1, category: "app" },
    { key: "maxmemory_gb", label: "Max Memory (GB)", type: "number", min: 1, step: 1, category: "app" },
    { key: "maxmemory_policy", label: "Eviction Policy", type: "select", options: ["allkeys-lru", "volatile-lru", "allkeys-lfu", "volatile-lfu", "allkeys-random", "volatile-ttl", "noeviction"], category: "app" },
    { key: "appendonly", label: "Append Only (AOF)", type: "boolean", category: "app" },
    { key: "appendfsync", label: "AOF Fsync", type: "select", options: ["everysec", "always", "no"], category: "app" },
    { key: "save_rdb", label: "Enable RDB Snapshots", type: "boolean", category: "app" },
    { key: "protected_mode", label: "Protected Mode", type: "boolean", category: "app" },
    { key: "timeout_s", label: "Idle Timeout (s)", type: "number", min: 0, step: 1, category: "app" },
    { key: "tcp_backlog", label: "tcp-backlog", type: "number", min: 128, step: 1, category: "app", placeholder: "511" },
    { key: "hz", label: "Server Hz", type: "number", min: 1, max: 500, step: 1, category: "app", placeholder: "10" },
    { key: "io_threads", label: "I/O Threads", type: "number", min: 1, step: 1, category: "app" },
    { key: "lazyfree_lazy_eviction", label: "Lazy Eviction", type: "boolean", category: "app" },
    { key: "os_overcommit_memory", label: "vm.overcommit_memory", type: "select", options: ["0", "1", "2"], category: "os" },
    { key: "os_somaxconn", label: "net.core.somaxconn", type: "number", min: 128, step: 1, category: "os", placeholder: "65535" },
    ...OS_FILE,
    { key: "os_swappiness", label: "vm.swappiness", type: "number", min: 0, max: 100, step: 1, category: "os", placeholder: "1" },
    { key: "perf_thp", label: "Transparent Huge Pages", type: "select", options: ["always", "madvise", "never"], category: "perf" },
    { key: "perf_io_sched", label: "I/O Scheduler", type: "select", options: ["noop", "deadline", "mq-deadline", "none"], category: "perf" },
    ],
  },
  {
    key: "tomcat", label: "Tomcat",
    profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON_FIELDS,
    { key: "max_threads", label: "Max Threads", type: "number", min: 10, step: 1, category: "app", placeholder: "200" },
    { key: "min_spare_threads", label: "Min Spare Threads", type: "number", min: 5, step: 1, category: "app", placeholder: "25" },
    { key: "max_connections", label: "Max Connections", type: "number", min: 100, step: 1, category: "app", placeholder: "10000" },
    { key: "accept_count", label: "Accept Count (Backlog)", type: "number", min: 50, step: 1, category: "app", placeholder: "100" },
    { key: "connection_timeout_ms", label: "Connection Timeout (ms)", type: "number", min: 1000, step: 100, category: "app", placeholder: "20000" },
    { key: "keep_alive_timeout_ms", label: "Keep-Alive Timeout (ms)", type: "number", min: 1000, step: 100, category: "app" },
    { key: "max_keep_alive_requests", label: "Max Keep-Alive Requests", type: "number", min: 1, step: 1, category: "app" },
    { key: "jvm_heap_min_mb", label: "JVM Heap Min -Xms (MB)", type: "number", min: 128, step: 64, category: "app" },
    { key: "jvm_heap_max_mb", label: "JVM Heap Max -Xmx (MB)", type: "number", min: 256, step: 64, category: "app" },
    { key: "jvm_metaspace_mb", label: "JVM Metaspace (MB)", type: "number", min: 64, step: 32, category: "app" },
    { key: "gc_type", label: "GC Algorithm", type: "select", options: ["G1GC", "ZGC", "ParallelGC", "CMS"], category: "app" },
    { key: "compression_enabled", label: "Enable Compression", type: "boolean", category: "app" },
    { key: "use_nio2", label: "Use NIO2 Connector", type: "boolean", category: "app" },
    ...OS_NET.slice(0, 4), ...OS_FILE, ...OS_VM.slice(0, 2), ...OS_PERF.slice(0, 2),
    ],
  },
  {
    key: "httpd", label: "Apache HTTPD",
    profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON_FIELDS,
    { key: "mpm_type", label: "MPM Module", type: "select", options: ["event", "worker", "prefork"], category: "app" },
    { key: "start_servers", label: "Start Servers", type: "number", min: 1, step: 1, category: "app" },
    { key: "min_spare_threads", label: "Min Spare Threads", type: "number", min: 5, step: 1, category: "app" },
    { key: "max_spare_threads", label: "Max Spare Threads", type: "number", min: 10, step: 1, category: "app" },
    { key: "max_request_workers", label: "Max Request Workers", type: "number", min: 50, step: 1, category: "app" },
    { key: "max_connections_per_child", label: "Max Connections/Child", type: "number", min: 0, step: 1, category: "app" },
    { key: "server_limit", label: "Server Limit", type: "number", min: 16, step: 1, category: "app" },
    { key: "threads_per_child", label: "Threads Per Child", type: "number", min: 10, step: 1, category: "app" },
    { key: "limit_request_line_kb", label: "Limit Request Line (KB)", type: "number", min: 8, step: 1, category: "app" },
    { key: "limit_request_field_size_kb", label: "Limit Header Field (KB)", type: "number", min: 8, step: 1, category: "app" },
    { key: "limit_request_body_kb", label: "Limit Request Body (KB)", type: "number", min: 1024, step: 1, category: "app" },
    { key: "timeout_s", label: "Timeout (s)", type: "number", min: 10, step: 1, category: "app" },
    { key: "keep_alive_timeout_s", label: "Keepalive Timeout (s)", type: "number", min: 5, step: 1, category: "app" },
    { key: "max_keep_alive_requests", label: "Max Keepalive Requests", type: "number", min: 100, step: 1, category: "app" },
    ...OS_NET.slice(0, 6), ...OS_FILE,
    { key: "perf_sendfile", label: "EnableSendfile", type: "boolean", category: "perf" },
    ...OS_PERF.slice(2, 4),
    ],
  },
  {
    key: "ohs", label: "Oracle HTTP Server",
    profiles: [{ key: "new", label: "New" }, { key: "new-fusion", label: "New Fusion" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON_FIELDS,
    { key: "limit_request_line_kb", label: "Limit Request Line (KB)", type: "number", min: 8, step: 1, category: "app" },
    { key: "limit_request_field_size_kb", label: "Limit Header Field (KB)", type: "number", min: 8, step: 1, category: "app" },
    { key: "limit_request_body_kb", label: "Limit Request Body (KB)", type: "number", min: 1024, step: 1, category: "app" },
    { key: "timeout_s", label: "Timeout (s)", type: "number", min: 10, step: 1, category: "app" },
    { key: "keep_alive_timeout_s", label: "Keepalive Timeout (s)", type: "number", min: 5, step: 1, category: "app" },
    { key: "max_keep_alive_requests", label: "Max Keepalive Requests", type: "number", min: 100, step: 1, category: "app" },
    { key: "max_client", label: "Max Client", type: "number", min: 150, step: 1, category: "app" },
    { key: "max_requests_per_child", label: "Max Requests Per Child", type: "number", min: 1000, step: 1, category: "app" },
    { key: "send_buffer_size_kb", label: "Send Buffer Size (KB)", type: "number", min: 16, step: 0.01, category: "app" },
    { key: "receive_buffer_size_kb", label: "Receive Buffer Size (KB)", type: "number", min: 16, step: 0.01, category: "app" },
    ...OS_NET.slice(0, 4), ...OS_FILE, ...OS_PERF.slice(2, 4),
    ],
  },
  {
    key: "ihs", label: "IBM HTTP Server",
    profiles: [{ key: "new", label: "New" }, { key: "new-liberty", label: "New Liberty" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON_FIELDS,
    { key: "limit_request_line_kb", label: "Limit Request Line (KB)", type: "number", min: 8, step: 1, category: "app" },
    { key: "limit_request_field_size_kb", label: "Limit Header Field (KB)", type: "number", min: 8, step: 1, category: "app" },
    { key: "limit_request_body_kb", label: "Limit Request Body (KB)", type: "number", min: 1024, step: 1, category: "app" },
    { key: "timeout_s", label: "Timeout (s)", type: "number", min: 10, step: 1, category: "app" },
    { key: "keep_alive_timeout_s", label: "Keepalive Timeout (s)", type: "number", min: 5, step: 1, category: "app" },
    { key: "max_keep_alive_requests", label: "Max Keepalive Requests", type: "number", min: 100, step: 1, category: "app" },
    { key: "max_request_workers", label: "Max Request Workers", type: "number", min: 150, step: 1, category: "app" },
    { key: "max_connections_per_child", label: "Max Connections/Child", type: "number", min: 1000, step: 1, category: "app" },
    { key: "listen_backlog", label: "Listen Backlog", type: "number", min: 128, step: 1, category: "app" },
    ...OS_NET.slice(0, 4), ...OS_FILE, ...OS_PERF.slice(2, 4),
    ],
  },
  {
    key: "iis", label: "IIS",
    profiles: [{ key: "new-core", label: "New Core" }, { key: "new-fx", label: "New Framework" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON_FIELDS,
    { key: "max_url_length_kb", label: "Max URL Length (KB)", type: "number", min: 1, step: 1, category: "app" },
    { key: "max_query_string_kb", label: "Max Query Length (KB)", type: "number", min: 1, step: 1, category: "app" },
    { key: "max_request_headers_kb", label: "Max Headers (KB)", type: "number", min: 4, step: 1, category: "app" },
    { key: "max_allowed_content_length_mb", label: "Max Content Length (MB)", type: "number", min: 1, step: 1, category: "app" },
    { key: "connection_timeout_s", label: "Connection Timeout (s)", type: "number", min: 10, step: 1, category: "app" },
    { key: "idle_timeout_min", label: "Idle Timeout (min)", type: "number", min: 1, step: 1, category: "app" },
    { key: "max_concurrent_requests", label: "Max Concurrent Requests", type: "number", min: 500, step: 1, category: "app" },
    { key: "queue_length", label: "Queue Length", type: "number", min: 1000, step: 1, category: "app", placeholder: "65535" },
    { key: "enable_keep_alive", label: "Enable Keepalive", type: "boolean", category: "app" },
    { key: "allow_double_escaping", label: "Allow Double Escaping", type: "boolean", category: "app" },
    { key: "perf_output_caching", label: "Output Caching", type: "boolean", category: "perf" },
    { key: "perf_compression", label: "Dynamic Compression", type: "boolean", category: "perf" },
    ],
  },
  {
    key: "podman", label: "Podman",
    profiles: [{ key: "new-web", label: "New Web" }, { key: "new-database", label: "New Database" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON_FIELDS,
    { key: "replicas", label: "Replicas", type: "number", min: 1, step: 1, category: "app" },
    { key: "cgroup_manager", label: "Cgroup Manager", type: "select", options: ["systemd", "cgroupfs"], category: "app" },
    { key: "events_backend", label: "Events Backend", type: "select", options: ["journald", "file"], category: "app" },
    { key: "pids_limit", label: "PIDs Limit", type: "number", min: 256, step: 1, category: "app" },
    { key: "storage_max_size_gb", label: "Storage Max (GB)", type: "number", min: 1, step: 1, category: "app" },
    { key: "storage_driver", label: "Storage Driver", type: "select", options: ["overlay2", "overlay", "btrfs"], category: "app" },
    { key: "log_size_max_mb", label: "Max Log Size (MB)", type: "number", min: 10, step: 1, category: "app" },
    { key: "default_nofile_soft", label: "Container nofile Soft", type: "number", min: 1024, step: 1, category: "app" },
    { key: "default_nofile_hard", label: "Container nofile Hard", type: "number", min: 1024, step: 1, category: "app" },
    ...OS_NET.slice(0, 4), ...OS_FILE,
    { key: "os_inotify_max", label: "fs.inotify.max_user_watches", type: "number", min: 8192, step: 1, category: "os", placeholder: "524288" },
    ...OS_PERF.slice(2, 4),
    ],
  },
  {
    key: "k8s", label: "Kubernetes",
    profiles: [{ key: "new-web", label: "New Web" }, { key: "new-database", label: "New Database" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON_FIELDS,
    { key: "replicas", label: "Replicas", type: "number", min: 1, step: 1, category: "app" },
    { key: "cpu_request_m", label: "CPU Request (millicores)", type: "number", min: 50, step: 50, category: "app" },
    { key: "cpu_limit_m", label: "CPU Limit (millicores)", type: "number", min: 100, step: 50, category: "app" },
    { key: "memory_request_mb", label: "Memory Request (MB)", type: "number", min: 64, step: 64, category: "app" },
    { key: "memory_limit_mb", label: "Memory Limit (MB)", type: "number", min: 128, step: 64, category: "app" },
    { key: "hpa_min_replicas", label: "HPA Min Replicas", type: "number", min: 1, step: 1, category: "app" },
    { key: "hpa_max_replicas", label: "HPA Max Replicas", type: "number", min: 1, step: 1, category: "app" },
    { key: "hpa_target_cpu_pct", label: "HPA Target CPU (%)", type: "number", min: 10, max: 95, step: 5, category: "app" },
    { key: "termination_grace_s", label: "Termination Grace (s)", type: "number", min: 10, step: 1, category: "app" },
    ...OS_NET.slice(0, 4), ...OS_FILE,
    { key: "os_max_map_count", label: "vm.max_map_count", type: "number", min: 65530, step: 1, category: "os", placeholder: "262144" },
    { key: "os_inotify_max", label: "fs.inotify.max_user_watches", type: "number", min: 8192, step: 1, category: "os", placeholder: "524288" },
    ...OS_PERF.slice(0, 2),
    ],
  },
  {
    key: "os", label: "Linux OS",
    profiles: [{ key: "new-web", label: "New Web" }, { key: "new-database", label: "New Database" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON_FIELDS,
    { key: "workload_type", label: "Workload Type", type: "select", options: ["web", "database", "mixed", "compute", "storage"], category: "app" },
    ...OS_NET, ...OS_FILE, ...OS_VM,
    { key: "os_max_map_count", label: "vm.max_map_count", type: "number", min: 65530, step: 1, category: "os", placeholder: "262144" },
    { key: "os_ip_local_port_range", label: "net.ipv4.ip_local_port_range", type: "text", category: "os", placeholder: "1024 65535" },
    { key: "os_tcp_syncookies", label: "net.ipv4.tcp_syncookies", type: "boolean", category: "os" },
    { key: "os_inotify_max", label: "fs.inotify.max_user_watches", type: "number", min: 8192, step: 1, category: "os", placeholder: "524288" },
    { key: "os_shmmax", label: "kernel.shmmax (bytes)", type: "number", min: 1073741824, step: 1, category: "os" },
    { key: "os_shmall", label: "kernel.shmall (pages)", type: "number", min: 262144, step: 1, category: "os" },
    ...OS_PERF,
    ],
  },
  {
    key: "postgresql", label: "PostgreSQL",
    profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON_FIELDS,
    { key: "max_connections", label: "Max Connections", type: "number", min: 50, step: 1, category: "app" },
    { key: "shared_buffers_mb", label: "Shared Buffers (MB)", type: "number", min: 128, step: 64, category: "app" },
    { key: "effective_cache_size_mb", label: "Effective Cache Size (MB)", type: "number", min: 256, step: 64, category: "app" },
    { key: "work_mem_mb", label: "Work Mem (MB)", type: "number", min: 4, step: 1, category: "app" },
    { key: "maintenance_work_mem_mb", label: "Maintenance Work Mem (MB)", type: "number", min: 64, step: 32, category: "app" },
    { key: "wal_buffers_mb", label: "WAL Buffers (MB)", type: "number", min: 4, step: 1, category: "app" },
    { key: "checkpoint_target", label: "Checkpoint Completion Target", type: "number", min: 0.1, max: 1.0, step: 0.1, category: "app" },
    { key: "random_page_cost", label: "Random Page Cost", type: "number", min: 1.0, max: 4.0, step: 0.1, category: "app" },
    { key: "effective_io_concurrency", label: "Effective I/O Concurrency", type: "number", min: 1, max: 200, step: 1, category: "app" },
    { key: "max_wal_size_gb", label: "Max WAL Size (GB)", type: "number", min: 1, step: 1, category: "app" },
    { key: "max_parallel_workers", label: "Max Parallel Workers", type: "number", min: 0, step: 1, category: "app" },
    { key: "huge_pages", label: "Huge Pages", type: "select", options: ["try", "on", "off"], category: "app" },
    { key: "os_shmmax", label: "kernel.shmmax (bytes)", type: "number", min: 1073741824, step: 1, category: "os" },
    { key: "os_shmall", label: "kernel.shmall (pages)", type: "number", min: 262144, step: 1, category: "os" },
    ...OS_VM, ...OS_FILE.slice(0, 3),
    { key: "os_somaxconn", label: "net.core.somaxconn", type: "number", min: 128, step: 1, category: "os", placeholder: "65535" },
    ...OS_PERF.slice(0, 1), ...OS_PERF.slice(2, 3),
    ],
  },
  {
    key: "mysql", label: "MySQL",
    profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON_FIELDS,
    { key: "max_connections", label: "Max Connections", type: "number", min: 50, step: 1, category: "app" },
    { key: "innodb_buffer_pool_mb", label: "InnoDB Buffer Pool (MB)", type: "number", min: 128, step: 64, category: "app" },
    { key: "innodb_pool_instances", label: "Buffer Pool Instances", type: "number", min: 1, max: 64, step: 1, category: "app" },
    { key: "innodb_log_file_mb", label: "InnoDB Log File (MB)", type: "number", min: 48, step: 16, category: "app" },
    { key: "innodb_log_buffer_mb", label: "InnoDB Log Buffer (MB)", type: "number", min: 8, step: 4, category: "app" },
    { key: "innodb_flush_method", label: "Flush Method", type: "select", options: ["O_DIRECT", "O_DSYNC", "fsync"], category: "app" },
    { key: "innodb_io_capacity", label: "InnoDB I/O Capacity", type: "number", min: 100, step: 100, category: "app", placeholder: "2000" },
    { key: "thread_cache_size", label: "Thread Cache Size", type: "number", min: 8, step: 1, category: "app" },
    { key: "table_open_cache", label: "Table Open Cache", type: "number", min: 400, step: 100, category: "app" },
    { key: "tmp_table_size_mb", label: "Tmp Table Size (MB)", type: "number", min: 16, step: 8, category: "app" },
    ...OS_VM, ...OS_FILE,
    { key: "os_somaxconn", label: "net.core.somaxconn", type: "number", min: 128, step: 1, category: "os", placeholder: "65535" },
    ...OS_PERF.slice(0, 1), ...OS_PERF.slice(2, 3),
    ],
  },
  {
    key: "mongodb", label: "MongoDB",
    profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON_FIELDS,
    { key: "max_connections", label: "Max Connections", type: "number", min: 50, step: 1, category: "app" },
    { key: "wiredtiger_cache_gb", label: "WiredTiger Cache (GB)", type: "number", min: 1, step: 1, category: "app" },
    { key: "journal_enabled", label: "Journal Enabled", type: "boolean", category: "app" },
    { key: "oplog_size_mb", label: "Oplog Size (MB)", type: "number", min: 990, step: 100, category: "app" },
    { key: "storage_engine", label: "Storage Engine", type: "select", options: ["wiredTiger", "inMemory"], category: "app" },
    { key: "read_concern", label: "Read Concern", type: "select", options: ["local", "majority", "linearizable"], category: "app" },
    { key: "write_concern", label: "Write Concern", type: "select", options: ["1", "majority"], category: "app" },
    { key: "replica_set_size", label: "Replica Set Size", type: "number", min: 1, max: 7, step: 2, category: "app" },
    { key: "os_max_map_count", label: "vm.max_map_count", type: "number", min: 65530, step: 1, category: "os", placeholder: "262144" },
    ...OS_VM, ...OS_FILE,
    { key: "os_somaxconn", label: "net.core.somaxconn", type: "number", min: 128, step: 1, category: "os", placeholder: "65535" },
    ...OS_PERF.slice(0, 1), ...OS_PERF.slice(1, 3),
    ],
  },
  {
    key: "haproxy", label: "HAProxy",
    profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON_FIELDS,
    { key: "maxconn_global", label: "Global maxconn", type: "number", min: 1000, step: 100, category: "app", placeholder: "100000" },
    { key: "maxconn_frontend", label: "Frontend maxconn", type: "number", min: 500, step: 100, category: "app" },
    { key: "maxconn_server", label: "Server maxconn", type: "number", min: 100, step: 10, category: "app" },
    { key: "nbthread", label: "Threads (nbthread)", type: "number", min: 1, step: 1, category: "app" },
    { key: "timeout_connect_ms", label: "Timeout Connect (ms)", type: "number", min: 1000, step: 500, category: "app" },
    { key: "timeout_client_ms", label: "Timeout Client (ms)", type: "number", min: 5000, step: 1000, category: "app" },
    { key: "timeout_server_ms", label: "Timeout Server (ms)", type: "number", min: 5000, step: 1000, category: "app" },
    { key: "balance", label: "Balance Algorithm", type: "select", options: ["roundrobin", "leastconn", "source", "uri", "hdr"], category: "app" },
    { key: "http_reuse", label: "HTTP Reuse", type: "select", options: ["safe", "aggressive", "always", "never"], category: "app" },
    ...OS_NET, ...OS_FILE,
    ...OS_PERF.slice(3, 4),
    ],
  },
  {
    key: "docker", label: "Docker",
    profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON_FIELDS,
    { key: "storage_driver", label: "Storage Driver", type: "select", options: ["overlay2", "devicemapper", "btrfs", "zfs"], category: "app" },
    { key: "log_driver", label: "Log Driver", type: "select", options: ["json-file", "journald", "syslog", "fluentd"], category: "app" },
    { key: "log_max_size_mb", label: "Log Max Size (MB)", type: "number", min: 10, step: 10, category: "app" },
    { key: "log_max_files", label: "Log Max Files", type: "number", min: 1, step: 1, category: "app" },
    { key: "default_ulimit_nofile", label: "Default ulimit nofile", type: "number", min: 1024, step: 1, category: "app", placeholder: "65535" },
    { key: "default_ulimit_nproc", label: "Default ulimit nproc", type: "number", min: 1024, step: 1, category: "app", placeholder: "65535" },
    { key: "live_restore", label: "Live Restore", type: "boolean", category: "app" },
    { key: "userland_proxy", label: "Userland Proxy", type: "boolean", category: "app" },
    ...OS_NET.slice(0, 4), ...OS_FILE,
    { key: "os_ip_forward", label: "net.ipv4.ip_forward", type: "boolean", category: "os" },
    { key: "os_bridge_nf_call", label: "bridge-nf-call-iptables", type: "boolean", category: "os" },
    { key: "os_inotify_max", label: "fs.inotify.max_user_watches", type: "number", min: 8192, step: 1, category: "os", placeholder: "524288" },
    ...OS_PERF.slice(2, 4),
    ],
  },
  {
    key: "rabbitmq", label: "RabbitMQ",
    profiles: [{ key: "new", label: "New" }, { key: "existing", label: "Existing" }],
    fields: [...COMMON_FIELDS,
    { key: "queues", label: "Queue Count", type: "number", min: 1, step: 1, category: "app" },
    { key: "vm_memory_watermark", label: "VM Memory Watermark (%)", type: "number", min: 10, max: 90, step: 5, category: "app", placeholder: "40" },
    { key: "disk_free_limit_mb", label: "Disk Free Limit (MB)", type: "number", min: 50, step: 50, category: "app", placeholder: "2048" },
    { key: "channel_max", label: "Channel Max", type: "number", min: 128, step: 1, category: "app", placeholder: "2047" },
    { key: "heartbeat_s", label: "Heartbeat (s)", type: "number", min: 0, step: 10, category: "app", placeholder: "60" },
    { key: "prefetch_count", label: "Prefetch Count", type: "number", min: 1, step: 1, category: "app", placeholder: "250" },
    { key: "cluster_nodes", label: "Cluster Nodes", type: "number", min: 1, max: 7, step: 1, category: "app" },
    { key: "ha_mode", label: "HA Mode", type: "select", options: ["none", "all", "exactly", "nodes"], category: "app" },
    ...OS_NET.slice(0, 4), ...OS_FILE,
    { key: "perf_erlang_sched", label: "Erlang Schedulers", type: "number", min: 1, step: 1, category: "perf" },
    ...OS_PERF.slice(2, 3),
    ],
  },
];

export default function CalculatorPage() {
  const [calculator, setCalculator] = useState(CALCULATORS[0].key);
  const [profile, setProfile] = useState(CALCULATORS[0].profiles[0].key);
  const [values, setValues] = useState<Record<string, string | number | boolean>>({
    mode: "new",
    os_type: "RHEL",
    cpu_cores: 4,
    ram_gb: 16,
    expected_rps: 1000,
    avg_response_ms: 120,
  });
  const [loadingExample, setLoadingExample] = useState(false);
  const [loadingRun, setLoadingRun] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<any>(null);

  const selected = useMemo(
    () => CALCULATORS.find((c) => c.key === calculator) ?? CALCULATORS[0],
    [calculator]
  );

  // Auto-inject cross-platform OS fields: calculators define Linux fields,
  // this adds Windows/Solaris/AIX/HP-UX equivalents so the OS dropdown works.
  const effectiveFields = useMemo(() => {
    const existing = new Set(selected.fields.map((f) => f.key));
    // Collect all non-Linux OS field sets not already in the calculator
    const extras = [...OS_WIN, ...OS_WIN_PERF, ...OS_SOL, ...OS_AIX, ...OS_HPUX]
      .filter((f) => !existing.has(f.key));
    return [...selected.fields, ...extras];
  }, [selected]);

  const setValue = (key: string, val: string | number | boolean) => {
    setValues((prev) => ({ ...prev, [key]: val }));
  };

  const loadExample = async () => {
    setLoadingExample(true);
    setError("");
    try {
      const data = await getCalculatorExample(calculator, profile);
      setValues(data ?? {});
      setResult(null);
    } catch (e: any) {
      setError(e?.detail ?? e?.message ?? "Failed to load example.");
    } finally {
      setLoadingExample(false);
    }
  };

  const run = async () => {
    setLoadingRun(true);
    setError("");
    try {
      const payload: Record<string, unknown> = {};
      for (const f of effectiveFields) {
        const raw = values[f.key];
        if (raw === undefined || raw === "") continue;
        if (f.type === "number") payload[f.key] = Number(raw);
        else if (f.type === "boolean") payload[f.key] = Boolean(raw);
        else payload[f.key] = raw;
      }
      if (!payload.mode) payload.mode = profile.includes("existing") ? "existing" : "new";
      const res = await runCalculator(calculator, payload);
      setResult(res);
    } catch (e: any) {
      const detail = Array.isArray(e?.detail)
        ? e.detail.map((x: any) => x?.msg ?? JSON.stringify(x)).join(", ")
        : e?.detail;
      setError(detail ?? e?.message ?? "Calculation failed.");
    } finally {
      setLoadingRun(false);
    }
  };

  const resultText = useMemo(() => {
    if (!result) return "Run calculation to see result";
    const lines: string[] = [];
    lines.push(`Calculator: ${result.calculator ?? calculator}`);
    lines.push(`Mode: ${result.mode ?? values.mode ?? "new"}`);
    if (result.summary) lines.push(`Summary: ${result.summary}`);
    if (typeof result.estimated_concurrency !== "undefined") {
      lines.push(`Estimated Concurrency: ${result.estimated_concurrency}`);
    }
    if (typeof result.workers !== "undefined") {
      lines.push(`Workers: ${result.workers}`);
    }
    if (typeof result.max_connections !== "undefined") {
      lines.push(`Max Connections: ${result.max_connections}`);
    }
    if (result.config_snippet) {
      lines.push("");
      lines.push("Recommended Config:");
      lines.push(String(result.config_snippet));
    }
    if (Array.isArray(result.major_params) && result.major_params.length > 0) {
      lines.push("");
      lines.push("Major Recommendations:");
      for (const p of result.major_params) {
        lines.push(`- ${p.name}: ${p.recommended} (${p.reason})`);
      }
    }
    if (Array.isArray(result.medium_params) && result.medium_params.length > 0) {
      lines.push("");
      lines.push("Medium Recommendations:");
      for (const p of result.medium_params) {
        lines.push(`- ${p.name}: ${p.recommended} (${p.reason})`);
      }
    }
    if (Array.isArray(result.minor_params) && result.minor_params.length > 0) {
      lines.push("");
      lines.push("Minor Recommendations:");
      for (const p of result.minor_params) {
        lines.push(`- ${p.name}: ${p.recommended} (${p.reason})`);
      }
    }
    if (Array.isArray(result.recommended_params) && result.recommended_params.length > 0) {
      lines.push("");
      lines.push("Detailed Parameter Recommendations:");
      for (const p of result.recommended_params) {
        const impact = p.impact ? ` [${p.impact}]` : "";
        lines.push(`- ${p.name}: ${p.recommended}${impact}${p.details ? ` (${p.details})` : ""}`);
      }
    }

    const skip = new Set([
      "calculator",
      "mode",
      "summary",
      "estimated_concurrency",
      "workers",
      "max_connections",
      "config_snippet",
      "major_params",
      "medium_params",
      "minor_params",
      "recommended_params",
      "audit_findings",
    ]);
    const extraKeys = Object.keys(result).filter((k) => !skip.has(k));
    if (extraKeys.length > 0) {
      lines.push("");
      lines.push("Additional Outputs:");
      for (const k of extraKeys) {
        const v = result[k];
        if (typeof v === "string" || typeof v === "number" || typeof v === "boolean") {
          lines.push(`- ${k}: ${String(v)}`);
        }
      }
    }
    if (Array.isArray(result.audit_findings) && result.audit_findings.length > 0) {
      lines.push("");
      lines.push("Audit Findings:");
      for (const f of result.audit_findings) lines.push(`- ${f}`);
    }
    return lines.join("\n");
  }, [result, calculator, values.mode]);

  return (
    <main className="mx-auto max-w-7xl px-4 py-6">
      <section className="rounded-2xl border border-slate-800 bg-slate-950/80 p-5">
        <div className="mb-5 flex items-center gap-3">
          <div className="rounded-lg bg-cyan-500/15 p-2 text-cyan-300">
            <Calculator className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Infrastructure Calculator</h1>
            <p className="text-sm text-slate-400">Enter values in form fields and run instantly.</p>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-[280px_minmax(0,1fr)]">
          <aside className="rounded-xl border border-slate-800 bg-slate-900/70 p-3">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Calculator</p>
            <div className="space-y-2">
              {CALCULATORS.map((c) => (
                <button
                  key={c.key}
                  type="button"
                  onClick={() => {
                    setCalculator(c.key);
                    setProfile(c.profiles[0].key);
                    setError("");
                    setResult(null);
                  }}
                  className={`w-full rounded-lg border px-3 py-2 text-left text-sm ${calculator === c.key ? "border-cyan-500/70 bg-cyan-500/10 text-cyan-100" : "border-slate-800 bg-slate-900 text-slate-200 hover:border-slate-700"}`}
                >
                  {c.label}
                </button>
              ))}
            </div>
          </aside>

          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="flex flex-col gap-1.5">
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">Profile</span>
                <select
                  value={profile}
                  onChange={(e) => setProfile(e.target.value)}
                  className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                >
                  {selected.profiles.map((p) => <option key={p.key} value={p.key}>{p.label}</option>)}
                </select>
              </label>
              <div className="flex items-end gap-2">
                <button
                  type="button"
                  onClick={loadExample}
                  disabled={loadingExample}
                  className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-4 text-sm text-slate-100 disabled:opacity-60"
                >
                  {loadingExample ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCcw className="h-4 w-4" />}
                  Load Example
                </button>
              </div>
            </div>

            <div className="mt-4 space-y-4">
              {/* Group fields by category, filter os/perf by selected OS family */}
              {(["app", "os", "perf"] as const).map((cat) => {
                const selectedOs = (values.os_type ?? "RHEL").toString();
                const family = getOsFamily(selectedOs);
                const catFields = effectiveFields.filter((f) => {
                  if ((f.category ?? "app") !== cat) return false;
                  if (cat === "app") return true;
                  // Show field if it has no osFamily, matches the family, or is 'all'
                  const ff = f.osFamily ?? "linux";
                  return ff === family || ff === "all";
                });
                if (catFields.length === 0) return null;
                const osLabel = family === "windows" ? "🪟 Windows Registry Tuning"
                  : family === "solaris" ? "☀️ Solaris ndd / Kernel Tuning"
                    : family === "aix" ? "🖥️ AIX no/vmo/ioo Tuning"
                      : family === "hpux" ? "🔧 HP-UX kctune/ndd Tuning"
                        : "🐧 Linux sysctl / Kernel Tuning";
                const catLabels = { app: "⚙️ Application Parameters", os: osLabel, perf: "⚡ Performance (Minor Priority)" };
                const catColors = { app: "text-cyan-400", os: "text-amber-400", perf: "text-emerald-400" };
                return (
                  <div key={cat}>
                    <p className={`mb-2 text-xs font-bold uppercase tracking-widest ${catColors[cat]}`}>{catLabels[cat]}</p>
                    <div className="grid gap-3 md:grid-cols-2">
                      {catFields.map((f) => (
                        <label key={f.key} className="flex flex-col gap-1.5">
                          <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">{f.label}</span>
                          {f.type === "select" ? (
                            <select
                              value={(values[f.key] ?? "").toString()}
                              onChange={(e) => setValue(f.key, e.target.value)}
                              className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                            >
                              {(f.options ?? []).map((opt) => <option key={opt} value={opt}>{opt}</option>)}
                            </select>
                          ) : f.type === "boolean" ? (
                            <input
                              type="checkbox"
                              checked={Boolean(values[f.key])}
                              onChange={(e) => setValue(f.key, e.target.checked)}
                              className="h-5 w-5"
                            />
                          ) : (
                            <input
                              type={f.type === "number" ? "number" : "text"}
                              value={(values[f.key] ?? "").toString()}
                              placeholder={f.placeholder}
                              min={f.min}
                              max={f.max}
                              step={f.step}
                              onChange={(e) => setValue(f.key, f.type === "number" ? e.target.value : e.target.value)}
                              className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                            />
                          )}
                        </label>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="mt-4 flex items-center gap-3">
              <button
                type="button"
                onClick={run}
                disabled={loadingRun}
                className="inline-flex min-h-11 items-center gap-2 rounded-lg bg-cyan-600 px-5 text-sm font-semibold text-white disabled:opacity-60"
              >
                {loadingRun ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                Run Calculator
              </button>
              {error ? <p className="text-sm text-rose-400">{error}</p> : null}
            </div>

            <div className="mt-5">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Result</p>
              <pre className="max-h-[460px] overflow-auto rounded-xl border border-slate-800 bg-slate-900 p-3 text-xs text-slate-100">
                {resultText}
              </pre>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
