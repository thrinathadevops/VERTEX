import logging
from fastapi import APIRouter, HTTPException
from app.schemas.nginx import NginxInput, NginxOutput
from app.calculators.nginx_calculator import NginxCalculator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/calculate", response_model=NginxOutput,
             summary="NGINX calculator (new + existing config modes)")
def calculate_nginx(input_data: NginxInput) -> NginxOutput:
    """
    **mode=new** – provide hardware/workload specs to generate a fresh production config.\n
    **mode=existing** – additionally pass current settings in `existing` block to get
    an audit, gap analysis, and safe upgrade recommendations.
    """
    try:
        return NginxCalculator(input_data).generate()
    except ValueError as exc:
        logger.warning("NGINX calc error: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
