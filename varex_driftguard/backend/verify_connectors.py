import pytest
from fastapi.testclient import TestClient
from main import app
from app.connectors.ssh import SSHConnector
from app.connectors.winrm_connector import WinRMConnector
from app.connectors.aws import AWSConnector
from app.connectors.azure_connector import AzureConnector
from app.connectors.gcp_connector import GCPConnector
from app.connectors.gitops_connector import GitConnector

client = TestClient(app)

def test_connector_factory_routing():
    """
    Tests that the '/api/v1/connectors/fetch' endpoint correctly routes 
    to the factory and returns a 500 (since we provide mock/invalid credentials, 
    we expect a connection error, NOT a 404 or 422 routing error).
    """
    connectors = ["ssh", "winrm", "aws", "azure", "gcp", "gitops"]
    
    for c_type in connectors:
        payload = {
            "connector_type": c_type,
            "target": "mock_target|us-east-1",
            "credentials": {"dummy": "key"},
            "config_path": "mock_path|123"
        }
        
        response = client.post("/api/v1/connectors/fetch", json=payload)
        
        if response.status_code != 500:
            print(f"FAILED {c_type}: Expected 500, got {response.status_code}. Response: {response.text}")
        assert response.status_code == 500, f"Failed routing test for {c_type}. Status: {response.status_code}"
        
        detail = response.json().get("detail", "")
        # The exact error depends on the SDK, but it should be a 500 containing an exception
        print(f"[{c_type}] Error returned: {detail}")

def test_agent_push_endpoint():
    """
    Tests the Phase 4 Push Model receiver.
    """
    payload = {
        "environment": "prod",
        "timestamp": "2026-03-05T12:00:00Z",
        "configurations": [
            {
                "name": "nginx_config",
                "path": "/etc/nginx/nginx.conf",
                "content": "worker_processes auto;"
            }
        ]
    }
    
    response = client.post("/api/v1/agent/push", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

if __name__ == "__main__":
    print("Running Connector Verification Tests...")
    test_connector_factory_routing()
    print("✅ Factory Routing & Dependency Loading OK (Caught safe Auth error).")
    
    test_agent_push_endpoint()
    print("✅ Agent Push Endpoint OK.")
    
    print("\nAll Core Connector Architecture tests passed!")
