from app.connectors.ssh import SSHConnector
from app.connectors.winrm_connector import WinRMConnector
from app.connectors.aws import AWSConnector
from app.connectors.azure_connector import AzureConnector
from app.connectors.gcp_connector import GCPConnector
from app.connectors.gitops_connector import GitConnector

def get_connector(connector_type: str, credentials: dict):
    """
    Factory method to instantiate the correct connector logic.
    """
    if connector_type.lower() == "ssh":
        return SSHConnector(credentials)
    elif connector_type.lower() == "winrm":
        return WinRMConnector(credentials)
    elif connector_type.lower() == "aws":
        return AWSConnector(credentials)
    elif connector_type.lower() == "azure":
        return AzureConnector(credentials)
    elif connector_type.lower() == "gcp":
        return GCPConnector(credentials)
    elif connector_type.lower() == "gitops":
        return GitConnector(credentials)
    else:
        raise ValueError(f"Unknown connector type: {connector_type}")
