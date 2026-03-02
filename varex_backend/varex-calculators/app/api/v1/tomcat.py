import logging
from fastapi import APIRouter, HTTPException
from app.schemas.tomcat import TomcatInput, TomcatOutput
from app.calculators.tomcat_calculator import TomcatCalculator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/calculate", response_model=TomcatOutput,
             summary="TOMCAT calculator (new + existing config modes)")
def calculate_tomcat(input_data: TomcatInput) -> TomcatOutput:
    """
    **mode=new** – provide hardware/workload specs to generate a fresh production config.\n
    **mode=existing** – additionally pass current settings in `existing` block to get
    an audit, gap analysis, and safe upgrade recommendations.
    """
    try:
        return TomcatCalculator(input_data).generate()
    except ValueError as exc:
        logger.warning("TOMCAT calc error: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
