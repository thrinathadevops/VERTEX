import winrm
from app.connectors.base import BaseConnector
from typing import Dict, Any

class WinRMConnector(BaseConnector):
    """
    Connects to Windows machines via WinRM (Windows Remote Management) to execute PowerShell.
    """
    
    def fetch_config(self, target: str, config_path_or_identifier: str) -> str:
        """
        Uses WinRM to connect and read a remote configuration file via PowerShell's `Get-Content`.
        """
        username = self.credentials.get("username")
        password = self.credentials.get("password")
        # Can be 'http' (5985) or 'https' (5986)
        transport = self.credentials.get("transport", "ntlm")
        server_url = self.credentials.get("server_url", f"http://{target}:5985/wsman")
        
        # In a real environment, you might need 'cert_validation=False' for self-signed HTTPs
        session = winrm.Session(
            server_url, 
            auth=(username, password), 
            transport=transport
        )
        
        # Sanitize path to avoid basic injection (highly simplified)
        safe_path = config_path_or_identifier.replace("'", "''")
        
        # Use PowerShell to read the file contents.
        # Out-String ensures we get a flat text response back.
        ps_script = f"Get-Content -Path '{safe_path}' -Raw"
        
        response = session.run_ps(ps_script)
        
        if response.status_code != 0:
            err = response.std_err.decode("utf-8")
            raise Exception(f"WinRM Error reading {config_path_or_identifier} on {target}: {err}")
            
        return response.std_out.decode("utf-8")
