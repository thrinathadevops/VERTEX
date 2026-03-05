from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseConnector(ABC):
    """
    Abstract base class for all DriftGuard Automation Connectors.
    Each connector represents a method to securely fetch configurations from a remote source.
    """
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize the connector with necessary credentials and connection parameters.
        """
        self.credentials = credentials

    @abstractmethod
    def fetch_config(self, target: str, config_path_or_identifier: str) -> str:
        """
        Fetch the configuration content from the target.
        
        Args:
            target: The IP, hostname, or resource identifier to connect to.
            config_path_or_identifier: The file path, registry key, or API query needed.
            
        Returns:
            The raw string content of the configuration file.
            
        Raises:
            Exception: If connection fails or file cannot be fetched.
        """
        pass
