from __future__ import annotations
from pydantic import BaseModel
from app.varex_calculators.core.enums import ImpactLevel


class TuningParam(BaseModel):
    """
    A single tuning recommendation returned in every calculator response.

    Fields
    ------
    name            : parameter name (e.g. "maxmemory", "worker_connections")
    current_value   : what is set right now (EXISTING mode only, else None)
    recommended     : VAREX recommended value
    impact          : MAJOR / MEDIUM / MINOR
    reason          : formula-backed explanation — WHY this value, what breaks if wrong
    command         : copy-pasteable sysctl / config snippet
    safe_to_apply_live : True = rolling apply OK, False = requires service restart
    """
    name:               str
    current_value:      str | None = None
    recommended:        str
    impact:             ImpactLevel
    reason:             str
    command:            str
    safe_to_apply_live: bool = True


