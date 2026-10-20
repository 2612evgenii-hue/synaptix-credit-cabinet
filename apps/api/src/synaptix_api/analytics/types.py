from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class FinancialInput:
    """All money in minor units (kopecks). Missing values stay None — never treated as 0."""

    revenue_minor: int | None
    expenses_minor: int | None
    liabilities_minor: int | None
    amount_minor: int
    term_months: int
    currency: str = "RUB"

    def available_cashflow_minor(self) -> int | None:
        if self.revenue_minor is None or self.expenses_minor is None:
            return None
        return self.revenue_minor - self.expenses_minor


@dataclass(frozen=True)
class CheckOutcome:
    source: str
    status: Literal["ok", "negative", "unavailable", "missing_data"]
    mock_version: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RiskResult:
    score: int  # 0..100, higher = lower risk in this demo model
    factors: dict[str, Any]
    model_version: str


@dataclass(frozen=True)
class DecisionResult:
    outcome: Literal["APPROVED", "REJECTED", "NEEDS_INFO", "ALTERNATIVE", "CHECK_UNAVAILABLE"]
    reason_codes: list[str]
    offered_terms: dict[str, Any]
    rules_version: str
    metrics: dict[str, Any] = field(default_factory=dict)
