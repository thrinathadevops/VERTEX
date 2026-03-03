"""
app/calculators/rabbitmq_calculator.py
=======================================
RabbitMQ tuning calculator — NEW and EXISTING modes.

Memory formula
--------------
vm_memory_high_watermark = 0.4  (40% of RAM → flow control triggers)
disk_free_limit          = max(RAM × 1.5, 5GB)
channel_max              = min(expected_publishers × 10, 65535)
Erlang +P                = max_connections × 10
"""
from __future__ import annotations

import math

from app.calculators.base import BaseCalculator
from app.calculators.os_tuning import OSTuningEngine
from app.core.enums import ImpactLevel, CalcMode
from app.schemas.rabbitmq import RabbitMQInput, RabbitMQOutput

M   = ImpactLevel.MAJOR
MED = ImpactLevel.MEDIUM
MIN = ImpactLevel.MINOR


class RabbitMQCalculator(BaseCalculator):

    def __init__(self, inp: RabbitMQInput) -> None:
        self._require_positive(inp.cpu_cores,  "cpu_cores")
        self._require_positive(inp.ram_gb,     "ram_gb")
        self.inp = inp

    def _vm_memory_high_watermark(self) -> float:
        return 0.4

    def _disk_free_limit_gb(self) -> float:
        return round(max(self.inp.ram_gb * 1.5, 5), 1)

    def _channel_max(self) -> int:
        return min(self.inp.expected_publishers * 10, 65535)

    def _max_connections(self) -> int:
        return (self.inp.expected_publishers + self.inp.expected_consumers) * 2

    def _erlang_process_limit(self) -> int:
        return max(self._max_connections() * 10, 1048576)

    def _build_params(self) -> list:
        ex   = self.inp.existing
        p    = self._p
        inp  = self.inp
        vmhw = self._vm_memory_high_watermark()
        dfl  = self._disk_free_limit_gb()
        chm  = self._channel_max()
        mc   = self._max_connections()
        epl  = self._erlang_process_limit()

        params = [
            p(
                "vm_memory_high_watermark", str(vmhw), M,
                f"Memory alarm trigger = {vmhw} (40% of RAM = {self.inp.ram_gb * vmhw:.1f}GB). "
                "When RabbitMQ uses more than this, it blocks ALL publishers (flow control). "
                "0.4 is the default and usually correct. "
                "Higher values risk OOM. Lower values trigger premature flow control.",
                f"vm_memory_high_watermark.relative = {vmhw}",
                str(ex.vm_memory_high_watermark) if ex.vm_memory_high_watermark else None,
            ),
            p(
                "disk_free_limit", f"{dfl}GB", M,
                f"Disk space alarm = max(RAM × 1.5, 5GB) = {dfl}GB. "
                "When free disk falls below this, RabbitMQ blocks ALL publishers. "
                f"Formula: RAM({inp.ram_gb}GB) × 1.5 = {inp.ram_gb * 1.5:.1f}GB. "
                "Default 50MB is dangerously low — disk fills up before alarm triggers.",
                f"disk_free_limit.absolute = {dfl}GB",
                ex.disk_free_limit,
            ),
            p(
                "channel_max", str(chm), M,
                f"Maximum channels per connection = {chm}. "
                f"Formula: min(expected_publishers × 10, 65535) = min({inp.expected_publishers * 10}, 65535). "
                "Each channel consumes ~100KB of RAM in RabbitMQ process. "
                "Channel leaks are the #1 cause of RabbitMQ OOM in production.",
                f"channel_max = {chm}",
                str(ex.channel_max) if ex.channel_max else None,
            ),
            p(
                "heartbeat", "60", M,
                "AMQP heartbeat interval in seconds. "
                "Detects dead connections (network partition, client crash). "
                "0 = disabled (connections never time out — dangerous). "
                "60s is the recommended default.",
                "heartbeat = 60",
                str(ex.heartbeat) if ex.heartbeat else None,
            ),

            # ── MEDIUM ────────────────────────────────────────────────────
            p(
                "vm_memory_high_watermark_paging_ratio", "0.5", MED,
                "Start paging messages to disk when memory reaches 50% of watermark. "
                "Prevents sudden flow control by proactively moving messages to disk.",
                "vm_memory_high_watermark_paging_ratio = 0.5",
            ),
            p(
                "queue_master_locator", "min-masters", MED,
                "Spread queue masters across cluster nodes for load balancing. "
                "Default 'client-local': all queues on the connecting node → hot spot.",
                "queue_master_locator = min-masters",
                ex.queue_master_locator,
            ),
            p(
                "cluster_partition_handling", "pause_minority", MED,
                "On network partition: pause minority nodes (prevent split-brain). "
                "Requires odd number of nodes (3, 5). "
                "autoheal: simpler but risks data loss if wrong side heals.",
                "cluster_partition_handling = pause_minority",
                ex.cluster_partition_handling,
            ),
            p(
                "consumer_timeout", "1800000", MED,
                "Consumer acknowledgement timeout = 30 minutes (ms). "
                "Prevents stuck consumers from holding messages indefinitely. "
                "Default: 30 minutes. Adjust based on your longest processing time.",
                "consumer_timeout = 1800000",
            ),
            p(
                "prefetch_count", "250", MED,
                "Consumer prefetch (QoS). "
                "Default unlimited: one fast consumer gets ALL messages, others starve. "
                "250 is a good starting point for balanced distribution. "
                "For ordered processing: set to 1.",
                "# Set in application code:\n"
                "# channel.basic_qos(prefetch_count=250)",
            ),

            # ── MINOR ─────────────────────────────────────────────────────
            p(
                "management plugin", "enabled", MIN,
                "Web management UI on port 15672. Essential for monitoring queues, "
                "connections, channels, and message rates.",
                "management.listener.port = 15672\nmanagement.listener.ssl = false",
                "enabled" if ex.management_enabled else "disabled",
            ),
            p(
                "Erlang +P process limit", str(epl), MIN,
                f"Erlang VM process limit = max_connections × 10 = {epl}. "
                "Each connection/channel/queue creates Erlang processes. "
                f"Default 1,048,576 is usually sufficient for ≤{epl // 10} connections.",
                f"# In rabbitmq-env.conf:\n"
                f"RABBITMQ_SERVER_ADDITIONAL_ERL_ARGS=\"+P {epl}\"",
            ),
            p(
                "collect_statistics_interval", "10000", MIN,
                "Stats collection interval = 10 seconds (ms). "
                "Default 5000ms is aggressive for large clusters. "
                "Reduce overhead with 10000ms.",
                "collect_statistics_interval = 10000",
            ),
        ]

        return [x for x in params if x is not None]

    def _audit(self) -> list[str]:
        findings = []
        ex = self.inp.existing

        if ex.disk_free_limit and "MB" in ex.disk_free_limit.upper():
            findings.append(
                f"[MAJOR] disk_free_limit={ex.disk_free_limit}. "
                f"Dangerously low. Set to {self._disk_free_limit_gb()}GB."
            )
        if ex.heartbeat is not None and ex.heartbeat == 0:
            findings.append(
                "[MAJOR] heartbeat=0. Dead connections are never cleaned up. "
                "Set to 60 seconds."
            )
        if ex.channel_max is not None and ex.channel_max > 10000:
            findings.append(
                f"[MEDIUM] channel_max={ex.channel_max} is very high. "
                "Channel leaks can consume all RAM. "
                f"Recommended: {self._channel_max()}."
            )
        if not ex.management_enabled:
            findings.append(
                "[MEDIUM] Management plugin disabled. No visibility into queues, "
                "connections, or message rates."
            )
        if not ex.ssl_enabled:
            findings.append(
                "[MEDIUM] SSL/TLS disabled. AMQP connections transmit data in plaintext."
            )

        return findings

    def _render_conf(self) -> str:
        inp  = self.inp
        vmhw = self._vm_memory_high_watermark()
        dfl  = self._disk_free_limit_gb()
        chm  = self._channel_max()

        cluster_block = ""
        if inp.clustered:
            cluster_block = (
                "\n# ── Clustering ──────────────────────────────────────────────\n"
                "cluster_formation.peer_discovery_backend = rabbit_peer_discovery_classic_config\n"
                "cluster_partition_handling = pause_minority\n"
                "queue_master_locator = min-masters\n"
            )

        return (
            f"# ╔══════════════════════════════════════════════════════════════╗\n"
            f"# ║  VAREX rabbitmq.conf  [{inp.mode.value.upper():8s}]  "
            f"RAM={inp.ram_gb}GB  cores={inp.cpu_cores}     ║\n"
            f"# ╚══════════════════════════════════════════════════════════════╝\n\n"
            f"# ── Memory ───────────────────────────────────────────────────\n"
            f"vm_memory_high_watermark.relative = {vmhw}\n"
            f"vm_memory_high_watermark_paging_ratio = 0.5\n\n"
            f"# ── Disk ─────────────────────────────────────────────────────\n"
            f"disk_free_limit.absolute = {dfl}GB\n\n"
            f"# ── Connections ──────────────────────────────────────────────\n"
            f"channel_max = {chm}\n"
            f"heartbeat = 60\n"
            f"consumer_timeout = 1800000\n\n"
            f"# ── Management ─────────────────────────────────────────────\n"
            f"management.listener.port = 15672\n"
            f"collect_statistics_interval = 10000\n"
            f"{cluster_block}"
        )

    def generate(self) -> RabbitMQOutput:
        vmhw = self._vm_memory_high_watermark()
        dfl  = self._disk_free_limit_gb()
        chm  = self._channel_max()

        all_params = self._build_params()

        os_engine = OSTuningEngine(
            cpu       = self.inp.cpu_cores,
            ram_gb    = self.inp.ram_gb,
            max_conns = self._max_connections(),
            os_type   = self.inp.os_type,
            existing  = dict(self.inp.existing.os_sysctl),
        )
        all_params += os_engine.generate()

        major, medium, minor = self._split(all_params)

        ha_suggestions = [
            f"Deploy {self.inp.cluster_nodes}-node cluster with quorum queues (RabbitMQ 3.8+).",
            "Use quorum queues instead of classic mirrored queues for data safety.",
            "Enable Shovel or Federation for cross-datacenter replication.",
            "Monitor with Prometheus plugin: rabbitmq_prometheus.",
        ]

        perf_warnings = [w for w in [
            (f"messages_per_sec={self.inp.messages_per_sec} is high. "
             "Consider Kafka/Pulsar for >50K msg/sec throughput.")
            if self.inp.messages_per_sec > 50000 else None,

            (f"message_size_kb={self.inp.message_size_kb} is large. "
             "RabbitMQ performs best with small messages (<64KB).")
            if self.inp.message_size_kb > 64 else None,
        ] if w]

        return RabbitMQOutput(
            mode                        = self.inp.mode,
            vm_memory_high_watermark    = vmhw,
            recommended_disk_free_limit = f"{dfl}GB",
            recommended_channel_max     = chm,
            rabbitmq_conf_snippet       = self._render_conf(),
            major_params                = major,
            medium_params               = medium,
            minor_params                = minor,
            os_sysctl_conf              = os_engine.sysctl_block(),
            ha_suggestions              = ha_suggestions,
            performance_warnings        = perf_warnings,
            capacity_warning            = self._capacity_warning(
                self.inp.ram_gb * vmhw, self.inp.ram_gb,
                "RabbitMQ memory watermark"
            ),
            audit_findings              = self._audit()
                                          if self.inp.mode == CalcMode.EXISTING else [],
        )
