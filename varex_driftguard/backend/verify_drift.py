import sys
import os
import json
from fastapi.testclient import TestClient

# Add current dir to pythonpath
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app

client = TestClient(app)

def run_tests():
    print("Running DriftGuard Verification...")
    
    with open("test_prod.json", "rb") as prod_f, open("test_dr.json", "rb") as dr_f:
        # Test 1: JSON Analyze Endpoint
        response = client.post(
            "/api/v1/drift/analyze",
            files={"prod_file": ("test_prod.json", prod_f, "application/json"),
                   "dr_file": ("test_dr.json", dr_f, "application/json")}
        )
        
        assert response.status_code == 200, f"Analyze Failed: {response.text}"
        data = response.json()
        assert "drift_results" in data
        
        results = data["drift_results"]
        print(f"✅ /analyze returned {len(results)} parameters")
        
        # Verify specific drift
        matches = [r for r in results if r["status"] == "MATCH"]
        drifts = [r for r in results if r["status"] == "DRIFT"]
        
        print(f"   Matches: {len(matches)}, Drifts: {len(drifts)}")
        assert len(drifts) > 0, "Expected some drifts between prod and dr config"
    
    with open("test_prod.json", "rb") as prod_f, open("test_dr.json", "rb") as dr_f:
        # Test 2: Excel Export Endpoint
        response = client.post(
            "/api/v1/drift/export",
            files={"prod_file": ("test_prod.json", prod_f, "application/json"),
                   "dr_file": ("test_dr.json", dr_f, "application/json")}
        )
        
        assert response.status_code == 200, f"Export Failed: {response.text}"
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
        with open("drift_report_test.xlsx", "wb") as f:
            f.write(response.content)
            
        print("✅ /export returned valid Excel stream and saved as drift_report_test.xlsx")

if __name__ == "__main__":
    run_tests()
