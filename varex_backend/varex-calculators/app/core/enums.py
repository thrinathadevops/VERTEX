from enum import Enum


class ImpactLevel(str, Enum):
    """Three-tier severity used in every TuningParam response."""
    MAJOR  = "MAJOR"   # Causes crashes / bottlenecks if wrong — fix before go-live
    MEDIUM = "MEDIUM"  # Measurable performance or security improvement
    MINOR  = "MINOR"   # Fine-tuning, observability, hardening


class OSType(str, Enum):
    """Supported host operating systems. Affects conntrack + THP handling."""
    UBUNTU_20    = "ubuntu-20"
    UBUNTU_22    = "ubuntu-22"
    RHEL_8       = "rhel-8"
    RHEL_9       = "rhel-9"
    CENTOS_7     = "centos-7"
    DEBIAN_11    = "debian-11"
    DEBIAN_12    = "debian-12"
    AMAZON_2     = "amazon-linux-2"
    AMAZON_2023  = "amazon-linux-2023"
    WINDOWS      = "windows"


class CalcMode(str, Enum):
    """
    NEW      — Generate a fresh config from hardware + workload specs.
    EXISTING — Audit current settings, return delta + safe upgrade plan.
    """
    NEW      = "new"
    EXISTING = "existing"
