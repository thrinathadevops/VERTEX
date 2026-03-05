from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List
import io
from fastapi.responses import StreamingResponse

from app.engine.drifter import analyze_drift
from app.reports.excel_gen import generate_excel_report
from app.parsers.generic import parse_config_file

app = FastAPI(title="VAREX DriftGuard", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev only, configure properly in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok", "service": "VAREX DriftGuard Backend"}

@app.post("/api/v1/drift/analyze")
async def analyze_drift_endpoint(
    prod_file: UploadFile = File(...),
    dr_file: UploadFile = File(...),
    component_type: str = "auto"
):
    try:
        # 1. Read files
        prod_content = (await prod_file.read()).decode("utf-8")
        dr_content = (await dr_file.read()).decode("utf-8")

        # 2. Parse configurations
        prod_data = parse_config_file(prod_content, component_type)
        dr_data = parse_config_file(dr_content, component_type)

        # 3. Analyze drift
        drift_results = analyze_drift(prod_data, dr_data)

        # 4. Return JSON
        return {"status": "success", "drift_results": drift_results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing drift: {str(e)}")


@app.post("/api/v1/drift/export")
async def export_drift_endpoint(
    prod_file: UploadFile = File(...),
    dr_file: UploadFile = File(...),
    component_type: str = "auto"
):
    try:
        # 1. Read files
        prod_content = (await prod_file.read()).decode("utf-8")
        dr_content = (await dr_file.read()).decode("utf-8")

        # 2. Parse configurations
        prod_data = parse_config_file(prod_content, component_type)
        dr_data = parse_config_file(dr_content, component_type)

        # 3. Analyze drift
        drift_results = analyze_drift(prod_data, dr_data)

        # 4. Generate Excel
        excel_stream = generate_excel_report(drift_results, component_type)

        return StreamingResponse(
            excel_stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=drift_report_{component_type}.xlsx"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting drift report: {str(e)}")
