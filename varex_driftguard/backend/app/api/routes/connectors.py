from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.connectors import get_connector

router = APIRouter(prefix="/api/v1/connectors", tags=["connectors"])

class FetchRequest(BaseModel):
    connector_type: str  # "ssh" or "winrm"
    target: str          # IP or hostname
    config_path: str     # Path on the server
    credentials: Dict[str, Any]

@router.post("/fetch")
async def fetch_remote_config(request: FetchRequest):
    """
    Connects to a remote server using the specified connector and fetches the configuration file.
    """
    try:
        connector = get_connector(request.connector_type, request.credentials)
        content = connector.fetch_config(request.target, request.config_path)
        
        return {
            "status": "success",
            "target": request.target,
            "path": request.config_path,
            "content": content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch config from {request.target}: {str(e)}")
