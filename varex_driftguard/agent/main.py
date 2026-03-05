import time
import json
import yaml
import requests
import subprocess
from datetime import datetime

class DriftGuardAgent:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
            
        self.server_url = self.config.get("server_url", "http://localhost:8000")
        self.api_key = self.config.get("api_key", "default-agent-key")
        self.environment = self.config.get("environment", "prod")
        self.targets = self.config.get("targets", [])
        
    def read_target(self, target):
        """Reads a file or executes a safe command to get configuration state."""
        type = target.get("type")
        path = target.get("path")
        
        try:
            if type == "file":
                with open(path, "r", encoding="utf-8") as f:
                    return {"status": "success", "content": f.read()}
            elif type == "command":
                # Ensure commands are safe in production!
                result = subprocess.run(path, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    return {"status": "success", "content": result.stdout}
                else:
                    return {"status": "error", "content": result.stderr}
        except Exception as e:
            return {"status": "error", "content": str(e)}

    def run_sweep(self):
        """Iterates through all targets and pushes the state to DriftGuard."""
        print(f"[{datetime.now()}] Starting DriftGuard Agent Sweep (Env: {self.environment})")
        
        payloads = []
        for target in self.targets:
            result = self.read_target(target)
            if result["status"] == "success":
                payloads.append({
                    "name": target["name"],
                    "path": target["path"],
                    "content": result["content"]
                })
            else:
                print(f"Error reading {target['name']}: {result['content']}")
                
        if payloads:
            self._push_to_server(payloads)
            
    def _push_to_server(self, payloads):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "environment": self.environment,
            "timestamp": datetime.now().isoformat(),
            "configurations": payloads
        }
        
        try:
            res = requests.post(f"{self.server_url}/api/v1/agent/push", json=data, headers=headers)
            res.raise_for_status()
            print(f"[{datetime.now()}] Successfully pushed {len(payloads)} configurations to {self.server_url}")
        except Exception as e:
            print(f"[{datetime.now()}] Failed to push to server: {e}")

if __name__ == "__main__":
    agent = DriftGuardAgent()
    agent.run_sweep()
