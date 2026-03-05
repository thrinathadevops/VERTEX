from app.connectors.ssh import SSHConnector
from app.connectors.winrm_connector import WinRMConnector

def get_connector(connector_type: str, credentials: dict):
    """
    Factory method to instantiate the correct connector logic.
    """
    if connector_type.lower() == "ssh":
        return SSHConnector(credentials)
    elif connector_type.lower() == "winrm":
        return WinRMConnector(credentials)
    else:
        raise ValueError(f"Unknown connector type: {connector_type}")
