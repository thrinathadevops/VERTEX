from enum import Enum


class ImpactLevel(str, Enum):
    MAJOR  = "MAJOR"    # System stability / capacity – must change before go-live
    MEDIUM = "MEDIUM"   # Measurable performance improvement
    MINOR  = "MINOR"    # Fine-tuning / observability


class OSType(str, Enum):
    UBUNTU_20  = "ubuntu-20"
    UBUNTU_22  = "ubuntu-22"
    RHEL_8     = "rhel-8"
    RHEL_9     = "rhel-9"
    CENTOS_7   = "centos-7"
    DEBIAN_11  = "debian-11"
    DEBIAN_12  = "debian-12"
    AMAZON_2   = "amazon-linux-2"
    AMAZON_2023= "amazon-linux-2023"


class CalcMode(str, Enum):
    NEW      = "new"       # No existing deployment – generate fresh config
    EXISTING = "existing"  # Audit and improve an existing deployment
