from abc import ABC, abstractmethod
from typing import Any
from app.core.enums import ImpactLevel
from app.core.models import TuningParam


class BaseCalculator(ABC):

    # ── Guards ────────────────────────────────────────────────────────────
    def _require_positive(self, value: float, field: str) -> None:
        if value <= 0:
            raise ValueError(f"{field} must be > 0, got {value}")

    def _require_range(self, value: float, lo: float, hi: float, field: str) -> None:
        if not (lo <= value <= hi):
            raise ValueError(f"{field} must be between {lo} and {hi}, got {value}")

    # ── Capacity ──────────────────────────────────────────────────────────
    @staticmethod
    def _capacity_warning(used: float, capacity: float, label: str) -> str | None:
        ratio = used / capacity if capacity else 1.0
        if ratio >= 0.90:
            return f"CRITICAL: {label} utilisation at {ratio:.0%} – scale immediately."
        if ratio >= 0.75:
            return f"WARNING: {label} utilisation at {ratio:.0%} – plan capacity expansion."
        return None

    # ── Helpers for building TuningParam lists ────────────────────────────
    @staticmethod
    def _param(name: str, recommended: str, impact: ImpactLevel, reason: str,
               command: str, current: str | None = None) -> TuningParam:
        return TuningParam(
            name=name,
            current_value=current,
            recommended=recommended,
            impact=impact,
            reason=reason,
            command=command,
        )

    @abstractmethod
    def generate(self) -> dict[str, Any]: ...
