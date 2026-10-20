"""Synthetic risk score. Explicitly not a bank model and not a credit decision."""

from __future__ import annotations

import math

from synaptix_api.analytics.types import CheckOutcome, FinancialInput, RiskResult
from synaptix_api.settings import get_settings

SCORE_BASE = 70
OVERDUE_PENALTY_PER_DAY = 0.5
LEVERAGE_PENALTY_CAP = 40


def _parse_overdue_days(raw: object) -> int | None:
    """Non-negative whole days, or None if corrupt (negative / fractional / non-numeric)."""
    if raw is None:
        return 0
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw if raw >= 0 else None
    if isinstance(raw, float):
        if not math.isfinite(raw) or not raw.is_integer() or raw < 0:
            return None
        return int(raw)
    try:
        parsed = int(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if parsed < 0:
        return None
    try:
        if float(raw) != float(parsed):  # type: ignore[arg-type]
            return None
    except (TypeError, ValueError):
        return None
    return parsed


def assess_risk(
    finances: FinancialInput,
    *,
    bureau: CheckOutcome | None = None,
    registry: CheckOutcome | None = None,
    model_version: str | None = None,
) -> RiskResult:
    """Return 0..100 score and factor breakdown. Missing finances reduce score via factors, not silent zeros."""
    settings = get_settings()
    version = model_version or settings.risk_model_version
    factors: dict = {"base": SCORE_BASE}
    score = float(SCORE_BASE)

    available = finances.available_cashflow_minor()
    if available is None:
        factors["missing_cashflow"] = True
        score -= 25
    else:
        factors["available_cashflow_minor"] = available
        liab = finances.liabilities_minor
        if liab is None:
            factors["missing_liabilities"] = True
            score -= 10
        elif available <= 0:
            factors["negative_cashflow"] = True
            score -= 30
        else:
            months_cover = liab / available
            factors["liability_months_cover"] = round(months_cover, 4)
            penalty = min(LEVERAGE_PENALTY_CAP, max(0.0, (months_cover - 6) * 2))
            factors["leverage_penalty"] = round(penalty, 2)
            score -= penalty

    if bureau is None or bureau.status == "missing_data":
        factors["bureau"] = "missing"
        score -= 15
    elif bureau.status == "unavailable":
        factors["bureau"] = "unavailable"
        score -= 5
    else:
        overdue = _parse_overdue_days(bureau.payload.get("overdue_days", 0))
        if overdue is None:
            factors["bureau"] = "malformed_overdue"
            score -= 20
        else:
            factors["overdue_days"] = overdue
            if bureau.status == "negative" or overdue > 0:
                factors["bureau"] = "negative" if bureau.status == "negative" else "ok_with_overdue"
                score -= min(50, overdue * OVERDUE_PENALTY_PER_DAY if overdue > 0 else 20)
            else:
                factors["bureau"] = "ok"

    if registry is None or registry.status == "missing_data":
        factors["registry"] = "missing"
        score -= 10
    elif registry.status == "negative":
        factors["registry"] = "negative"
        score -= 35
    elif registry.status == "unavailable":
        factors["registry"] = "unavailable"
        score -= 5
    else:
        factors["registry"] = "ok"

    clipped = int(max(0, min(100, round(score))))
    factors["raw_score"] = score
    factors["clipped_score"] = clipped
    return RiskResult(score=clipped, factors=factors, model_version=version)
