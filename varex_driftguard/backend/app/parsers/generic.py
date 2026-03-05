import os

def parse_config_file(content: str, component_type: str) -> dict:
    """
    Generic parser taking raw text and returning key-value pairs.
    Supported types: sysctl, nginx, tomcat_properties, env, kv, auto
    """
    parsed = {}
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('//'):
            continue
            
        # Basic K=V or K V parsing
        # Nginx/Tomcat/Sysctl rough parsing
        if '=' in line:
            parts = line.split('=', 1)
            k, v = parts[0].strip(), parts[1].strip()
            # Remove trailing semicolons in nginx
            if v.endswith(';'): v = v[:-1]
            parsed[k] = v
        elif ' ' in line:
            # Handle NGINX style `worker_connections 1024;`
            parts = line.split(' ', 1)
            k, v = parts[0].strip(), parts[1].strip()
            if v.endswith(';'): v = v[:-1]
            parsed[k] = v
            
    return parsed
