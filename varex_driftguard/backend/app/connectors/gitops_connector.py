import subprocess
import os
import tempfile
import shutil
from app.connectors.base import BaseConnector

class GitConnector(BaseConnector):
    """
    Connects to an arbitrary Git repository (GitHub/GitLab/Bitbucket) using a Personal Access Token 
    or SSH Key to pull down IaC manifests or desired state configuration files.
    """
    
    def fetch_config(self, target: str, config_path_or_identifier: str) -> str:
        """
        Clones a repository into a temporary directory, reads the file, and cleans up.
        target: The repository URL, e.g., 'https://github.com/my-org/my-repo.git'
        config_path_or_identifier: The path to the file inside the repo, e.g., 'k8s/deployment.yaml'
        """
        token = self.credentials.get("git_token")
        
        # Inject token into URL if it's HTTPS
        if target.startswith("https://") and token:
            target = target.replace("https://", f"https://oauth2:{token}@")
        elif target.startswith("http://") and token:
            target = target.replace("http://", f"http://oauth2:{token}@")

        temp_dir = tempfile.mkdtemp(prefix="driftguard_git_")
        
        try:
            # Shallow clone for speed (we only need the latest commit)
            clone_cmd = ["git", "clone", "--depth", "1", target, temp_dir]
            
            result = subprocess.run(clone_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                # Be careful not to leak the token in error messages
                safe_err = result.stderr.replace(token, "***") if token else result.stderr
                raise Exception(f"Git clone failed: {safe_err}")
                
            file_to_read = os.path.join(temp_dir, config_path_or_identifier)
            
            if not os.path.exists(file_to_read):
                raise FileNotFoundError(f"File {config_path_or_identifier} not found in the repository.")
                
            with open(file_to_read, "r", encoding="utf-8") as f:
                content = f.read()
                
            return content
            
        finally:
            # Clean up the temporary repository clone unconditionally
            shutil.rmtree(temp_dir, ignore_errors=True)
