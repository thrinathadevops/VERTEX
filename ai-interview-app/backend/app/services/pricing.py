"""
Pricing & Discount Engine
─────────────────────────
Handles all pricing logic for Mock (B2C) and Enterprise (B2B) interviews.

Rules:
  Mock (B2C):
    - First mock → FREE (1 per user lifetime, tracked by free_mock_used)
    - Subsequent mocks → ₹50 per session

  Enterprise (B2B):
    - Base price: ₹500 per interview
    - Volume discounts (interviews/week):
        2  → 5%
        5  → 10%
        10 → 30%
        20 → 50%
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PricingResult:
    interview_mode: str
    package_interviews: int
    base_price_per_interview: int
    discount_percent: int
    base_total_rupees: int
    discount_amount_rupees: int
    final_charge_rupees: int


# ─── Discount tiers (interviews/week → discount %) ────────────────
ENTERPRISE_DISCOUNT_TIERS = [
    (20, 50),
    (10, 30),
    (5, 10),
    (2, 5),
]


def calculate_enterprise_discount(count: int) -> int:
    """
    Calculate discount percentage for Enterprise (B2B) interviews.

    Args:
        count: Number of interviews per week.

    Returns:
        Discount percentage (0–50).
    """
    for threshold, discount in ENTERPRISE_DISCOUNT_TIERS:
        if count >= threshold:
            return discount
    return 0


def calculate_pricing(
    interview_mode: str,
    package_interviews: int = 1,
    free_mock_used: bool = False,
) -> PricingResult:
    """
    Central pricing calculator.

    Args:
        interview_mode: "mock_free", "mock_paid", or "enterprise"
        package_interviews: Number of interviews in the package (enterprise only)
        free_mock_used: Whether the user's free mock has been consumed

    Returns:
        PricingResult with full breakdown.
    """

    # ── Mock Free ─────────────────────────────────────────────
    if interview_mode == "mock_free":
        if free_mock_used:
            # User already consumed their free mock — force paid
            return PricingResult(
                interview_mode="mock_paid",
                package_interviews=1,
                base_price_per_interview=50,
                discount_percent=0,
                base_total_rupees=50,
                discount_amount_rupees=0,
                final_charge_rupees=50,
            )
        return PricingResult(
            interview_mode="mock_free",
            package_interviews=1,
            base_price_per_interview=0,
            discount_percent=0,
            base_total_rupees=0,
            discount_amount_rupees=0,
            final_charge_rupees=0,
        )

    # ── Mock Paid ─────────────────────────────────────────────
    if interview_mode == "mock_paid":
        return PricingResult(
            interview_mode="mock_paid",
            package_interviews=1,
            base_price_per_interview=50,
            discount_percent=0,
            base_total_rupees=50,
            discount_amount_rupees=0,
            final_charge_rupees=50,
        )

    # ── Enterprise (B2B) ──────────────────────────────────────
    if interview_mode == "enterprise":
        base_per = 500
        discount_pct = calculate_enterprise_discount(package_interviews)
        base_total = base_per * package_interviews
        discount_amount = int(base_total * discount_pct / 100)
        final = base_total - discount_amount

        return PricingResult(
            interview_mode="enterprise",
            package_interviews=package_interviews,
            base_price_per_interview=base_per,
            discount_percent=discount_pct,
            base_total_rupees=base_total,
            discount_amount_rupees=discount_amount,
            final_charge_rupees=final,
        )

    # Fallback
    return PricingResult(
        interview_mode=interview_mode,
        package_interviews=1,
        base_price_per_interview=0,
        discount_percent=0,
        base_total_rupees=0,
        discount_amount_rupees=0,
        final_charge_rupees=0,
    )
