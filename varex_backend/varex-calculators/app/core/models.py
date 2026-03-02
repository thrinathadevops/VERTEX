from pydantic import BaseModel
from app.core.enums import ImpactLevel


class TuningParam(BaseModel):
    name:          str
    current_value: str | None = None   # None for NEW mode
    recommended:   str
    impact:        ImpactLevel
    reason:        str
    command:       str                 # sysctl / conf directive to apply
