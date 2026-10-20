"""End-to-end analytics pipeline for one application snapshot (no HTTP)."""

from __future__ import annotations

from dataclasses import dataclass

from synaptix_api.analytics.decision import apply_decision_rules
from synaptix_api.analytics.mocks import run_bureau_check, run_registry_check
from synaptix_api.analytics.risk import assess_risk
from synaptix_api.analytics.types import CheckOutcome, DecisionResult, FinancialInput, RiskResult


@dataclass(frozen=True)
class ProductLimits:
    min_amount_minor: int
    max_amount_minor: int
    min_term_months: int = 1
    max_term_months: int = 120
    demo_rate_annual: float = 0.16


@dataclass(frozen=True)
class AnalyticsBundle:
    registry: CheckOutcome
    bureau: CheckOutcome
    risk: RiskResult
    decision: DecisionResult


def run_analytics(
    *,
    scenario_key: str,
    registration_id: str,
    finances: FinancialInput,
    product: ProductLimits,
    force_bureau_unavailable: bool = False,
) -> AnalyticsBundle:
    registry = run_registry_check(scenario_key, registration_id)
    bureau = run_bureau_check(scenario_key, force_unavailable=force_bureau_unavailable)
    risk = assess_risk(finances, bureau=bureau, registry=registry)
    decision = apply_decision_rules(
        finances,
        risk,
        registry=registry,
        bureau=bureau,
        product_min_minor=product.min_amount_minor,
        product_max_minor=product.max_amount_minor,
        product_min_term=product.min_term_months,
        product_max_term=product.max_term_months,
        demo_rate_annual=product.demo_rate_annual,
    )
    return AnalyticsBundle(registry=registry, bureau=bureau, risk=risk, decision=decision)
