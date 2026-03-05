import paramiko
from app.connectors.base import BaseConnector
from typing import Dict, Any

class SSHConnector(BaseConnector):
    """
    Connects to Linux, AIX, Ubuntu, Solaris via SSH to retrieve configuration files.
    """
    
    def fetch_config(self, target: str, config_path_or_identifier: str) -> str:
        """
        Connects via SSH, reads the file at `config_path_or_identifier`, and returns its contents.
        """
        username = self.credentials.get("username")
        password = self.credentials.get("password")
        key_filename = self.credentials.get("key_filename")
        port = self.credentials.get("port", 22)

        client = paramiko.SSHClient()
        # Automatically add the server's host key
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # Connect to the remote server
            if key_filename:
                client.connect(hostname=target, port=port, username=username, key_filename=key_filename, timeout=10)
            else:
                client.connect(hostname=target, port=port, username=username, password=password, timeout=10)
                
            # Execute command to read file
            # Use sudo if necessary based on credentials flag, though simple 'cat' is safer
            use_sudo = self.credentials.get("use_sudo", False)
            cmd = f"sudo cat {config_path_or_identifier}" if use_sudo else f"cat {config_path_or_identifier}"
            
            stdin, stdout, stderr = client.exec_command(cmd)
            
            err = stderr.read().decode('utf-8')
            if err:
                raise Exception(f"SSH Error reading {config_path_or_identifier} on {target}: {err}")
                
            out = stdout.read().decode('utf-8')
            return out
            
        finally:
            client.close()
