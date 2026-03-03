"""
app/calculators/base.py
=======================
Abstract base class shared by every VAREX calculator.

Provides:
  - _require_positive()   input guard
  - _capacity_warning()   75% / 90% threshold alerts
  - _p()                  TuningParam factory shorthand
  - _split()              bucket params into MAJOR / MEDIUM / MINOR lists
  - generate()            abstract method every calculator must implement
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from app.varex_calculators.core.enums import ImpactLevel
from app.varex_calculators.core.models import TuningParam


class BaseCalculator(ABC):

    # ── input guards ─────────────────────────────────────────────────────────
    def _require_positive(self, value: float | int, field: str) -> None:
        """Raise ValueError if value is not strictly positive."""
        if value <= 0:
            raise ValueError(f"{field} must be > 0, got {value}")

    def _require_range(self, value: float | int, lo: float, hi: float, field: str) -> None:
        """Raise ValueError if value is outside [lo, hi]."""
        if not (lo <= value <= hi):
            raise ValueError(f"{field} must be in [{lo}, {hi}], got {value}")

    # ── capacity warning ──────────────────────────────────────────────────────
    @staticmethod
    def _capacity_warning(used: float, capacity: float, label: str) -> str | None:
        """
        Return a human-readable warning string when utilisation is high.

        Thresholds
        ----------
        >= 90%  CRITICAL  – immediate scaling required
        >= 75%  WARNING   – plan expansion
        < 75%   None      – healthy headroom
        """
        if capacity <= 0:
            return f"CRITICAL: {label} capacity is zero or negative."
        ratio = used / capacity
        if ratio >= 0.90:
            return (
                f"CRITICAL: {label} utilisation at {ratio:.0%} "
                f"({used:.0f}/{capacity:.0f}) – scale immediately."
            )
        if ratio >= 0.75:
            return (
                f"WARNING: {label} utilisation at {ratio:.0%} "
                f"({used:.0f}/{capacity:.0f}) – plan capacity expansion."
            )
        return None

    # ── TuningParam factory ───────────────────────────────────────────────────
    @staticmethod
    def _p(
        name:        str,
        recommended: str,
        impact:      ImpactLevel,
        reason:      str,
        command:     str,
        current:     str | None = None,
        safe:        bool       = True,
    ) -> TuningParam:
        """
        Shorthand factory for TuningParam.  All calculators call this
        instead of constructing TuningParam directly.

        Parameters
        ----------
        name        : display name of the parameter
        recommended : VAREX recommended value (always a string)
        impact      : ImpactLevel.MAJOR / MEDIUM / MINOR
        reason      : formula-backed explanation – WHY this value,
                      what breaks if you ignore it
        command     : copy-pasteable shell / config snippet
        current     : current value (EXISTING mode), None for NEW mode
        safe        : True  = rolling apply without restart is OK
                      False = requires service/process restart
        """
        return TuningParam(
            name=name,
            current_value=current,
            recommended=recommended,
            impact=impact,
            reason=reason,
            command=command,
            safe_to_apply_live=safe,
        )

    # ── param bucketing ───────────────────────────────────────────────────────
    @staticmethod
    def _split(
        params: list[TuningParam],
    ) -> tuple[list[TuningParam], list[TuningParam], list[TuningParam]]:
        """
        Split a flat param list into (major, medium, minor) buckets.
        Used by every calculator before building the final response.
        """
        major  = [p for p in params if p.impact == ImpactLevel.MAJOR]
        medium = [p for p in params if p.impact == ImpactLevel.MEDIUM]
        minor  = [p for p in params if p.impact == ImpactLevel.MINOR]
        return major, medium, minor

    # ── abstract interface ────────────────────────────────────────────────────
    @abstractmethod
    def generate(self):
        """
        Run the calculator and return the typed Output model.
        Every concrete calculator (NginxCalculator, RedisCalculator, …)
        must implement this method.
        """
        ...


