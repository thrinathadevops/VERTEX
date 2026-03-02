from __future__ import annotations
from typing import Annotated, Literal
from pydantic import BaseModel, Field
from app.core.enums import OSType, CalcMode
from app.core.models import TuningParam


class TomcatExistingConfig(BaseModel):
    max_threads:          int   | None = None
    min_spare_threads:    int   | None = None
    accept_count:         int   | None = None
    connection_timeout_ms: int  | None = None
    jvm_xmx:              str   | None = None  # e.g. "4g"
    jvm_xms:              str   | None = None
    gc_type:              str   | None = None  # e.g. "G1GC"
    tomcat_version:       str   | None = None
    connector_protocol:   str   | None = None
    os_sysctl:            dict[str, str] = Field(default_factory=dict)


class TomcatInput(BaseModel):
    mode:                       CalcMode = CalcMode.NEW
    cpu_cores:                  Annotated[int,   Field(ge=1, le=512)]
    ram_gb:                     Annotated[float, Field(gt=0, le=4096)]
    os_type:                    OSType = OSType.UBUNTU_22
    expected_concurrent_users:  Annotated[int,   Field(ge=1)]
    avg_request_time_ms:        Annotated[int,   Field(ge=1, le=300_000)]
    avg_cpu_time_ms:            Annotated[int,   Field(ge=1, le=300_000)]
    target_cpu_utilization:     Annotated[float, Field(gt=0, le=1.0, default=0.70)]
    connector_type:             Literal["NIO", "NIO2", "APR"] = "NIO"
    jvm_heap_ratio:             Annotated[float, Field(gt=0, le=0.85, default=0.70)]
    existing:                   TomcatExistingConfig = Field(default_factory=TomcatExistingConfig)

    model_config = {"json_schema_extra": {"examples": {
        "new": {"mode": "new", "cpu_cores": 8, "ram_gb": 16, "os_type": "ubuntu-22",
                "expected_concurrent_users": 500, "avg_request_time_ms": 200,
                "avg_cpu_time_ms": 20, "target_cpu_utilization": 0.75,
                "connector_type": "NIO", "jvm_heap_ratio": 0.70},
        "existing": {"mode": "existing", "cpu_cores": 8, "ram_gb": 16, "os_type": "rhel-8",
                     "expected_concurrent_users": 500, "avg_request_time_ms": 200,
                     "avg_cpu_time_ms": 20, "target_cpu_utilization": 0.75,
                     "connector_type": "NIO", "jvm_heap_ratio": 0.70,
                     "existing": {"max_threads": 50, "min_spare_threads": 5,
                                  "accept_count": 20, "jvm_xmx": "2g",
                                  "gc_type": "SerialGC",
                                  "os_sysctl": {"net.core.somaxconn": "128"}}}
    }}}


class TomcatOutput(BaseModel):
    mode:                  CalcMode
    max_threads:           int
    min_spare_threads:     int
    accept_count:          int
    connection_timeout_ms: int
    jvm_xms:               str
    jvm_xmx:               str
    server_xml_snippet:    str
    jvm_args:              str
    major_params:          list[TuningParam]
    medium_params:         list[TuningParam]
    minor_params:          list[TuningParam]
    os_sysctl_conf:        str
    ha_suggestions:        list[str]
    performance_warnings:  list[str]
    capacity_warning:      str | None
    audit_findings:        list[str] = []
