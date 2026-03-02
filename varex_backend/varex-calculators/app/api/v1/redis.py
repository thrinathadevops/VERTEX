import logging
from fastapi import APIRouter, HTTPException
from app.schemas.redis import RedisInput, RedisOutput
from app.calculators.redis_calculator import RedisCalculator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/calculate", response_model=RedisOutput,
             summary="REDIS calculator (new + existing config modes)")
def calculate_redis(input_data: RedisInput) -> RedisOutput:
    """
    **mode=new** – provide hardware/workload specs to generate a fresh production config.\n
    **mode=existing** – additionally pass current settings in `existing` block to get
    an audit, gap analysis, and safe upgrade recommendations.
    """
    try:
        return RedisCalculator(input_data).generate()
    except ValueError as exc:
        logger.warning("REDIS calc error: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
