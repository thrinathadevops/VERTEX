from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services.calculator_engine import (
    SUPPORTED_CALCULATORS,
    calculate,
    example_payload,
)

router = APIRouter()

SUPPORTED_PROFILES = {
    "new",
    "existing",
    "new-web",
    "new-database",
    "new-core",
    "new-fx",
    "new-fusion",
    "new-liberty",
}


def _ensure_supported(calculator: str) -> str:
    key = calculator.strip().lower()
    if key not in SUPPORTED_CALCULATORS:
        raise HTTPException(status_code=404, detail=f"Unknown calculator: {calculator}")
    return key


@router.get("/status", tags=["Calculators"])
def calculators_status():
    return {
        "status": "ok",
        "mode": "active",
        "available_calculators": sorted(SUPPORTED_CALCULATORS),
    }


@router.post("/{calculator}/example/{profile}", tags=["Calculators"])
def calculator_example(calculator: str, profile: str):
    key = _ensure_supported(calculator)
    p = profile.strip().lower()
    if p not in SUPPORTED_PROFILES:
        raise HTTPException(status_code=404, detail=f"Unknown example profile: {profile}")
    return example_payload(key, p)


@router.post("/{calculator}/calculate", tags=["Calculators"])
def calculator_calculate(calculator: str, payload: dict):
    key = _ensure_supported(calculator)
    return calculate(key, payload or {})
