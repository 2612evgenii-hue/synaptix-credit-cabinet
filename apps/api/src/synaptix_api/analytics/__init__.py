"""Deterministic credit analytics: mocks, risk score, decision rules, explanations.

Risk score is NOT a credit decision. Decision rules consume score + checks + product limits.
Optional open-weight LLM only narrates an already-computed decision (REQ-20).
"""

from synaptix_api.analytics.decision import apply_decision_rules
from synaptix_api.analytics.explain import ExplanationResult, explain_decision
from synaptix_api.analytics.mocks import run_bureau_check, run_registry_check
from synaptix_api.analytics.pipeline import AnalyticsBundle, ProductLimits, run_analytics
from synaptix_api.analytics.risk import assess_risk
from synaptix_api.analytics.types import (
    CheckOutcome,
    DecisionResult,
    FinancialInput,
    RiskResult,
)

__all__ = [
    "assess_risk",
    "apply_decision_rules",
    "explain_decision",
    "run_bureau_check",
    "run_registry_check",
    "run_analytics",
    "AnalyticsBundle",
    "ProductLimits",
    "CheckOutcome",
    "DecisionResult",
    "ExplanationResult",
    "FinancialInput",
    "RiskResult",
]
