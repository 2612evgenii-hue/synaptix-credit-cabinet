"""Credit decision rules. Consumes risk score + checks + product limits. Not scoring itself."""

from __future__ import annotations

import math

from synaptix_api.analytics.types import CheckOutcome, DecisionResult, FinancialInput, RiskResult
from synaptix_api.settings import get_settings

K_PASS = 1.3
K_BORDER = 1.0
SCORE_APPROVE_MIN = 55
SCORE_REJECT_MAX = 35
SUPPORTED_CURRENCY = "RUB"


def _annuity_minor(principal: int, annual_rate: float, term_months: int) -> int:
    if term_months <= 0 or principal <= 0:
        return 0
    r = annual_rate / 12.0
    if r == 0:
        return principal // term_months
    factor = (r * (1 + r) ** term_months) / ((1 + r) ** term_months - 1)
    return int(round(principal * factor))


def coverage_ratio(
    finances: FinancialInput,
    *,
    new_payment_minor: int,
    existing_debt_payment_minor: int = 0,
) -> float | None:
    """Exact coverage ratio used for gates — do not round up into K_PASS."""
    available = finances.available_cashflow_minor()
    if available is None:
        return None
    denom = existing_debt_payment_minor + new_payment_minor
    if denom <= 0:
        return None
    return available / denom


def max_principal_for_k(
    finances: FinancialInput,
    *,
    annual_rate: float,
    term_months: int,
    existing_debt_payment_minor: int = 0,
    target_k: float = K_PASS,
    search_hi_minor: int | None = None,
    min_offer_minor: int = 0,
) -> int:
    available = finances.available_cashflow_minor()
    if available is None:
        return 0
    max_pay = available / target_k - existing_debt_payment_minor
    if max_pay <= 0:
        return 0
    # Search upper bound: explicit hi, else at least requested amount * 2 or 200M RUB
    hi = search_hi_minor if search_hi_minor is not None else max(finances.amount_minor * 2, 200_000_000_00)
    lo, best = 0, 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if _annuity_minor(mid, annual_rate, term_months) <= max_pay:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    floored = (best // 10_000_00) * 10_000_00
    # 10k display grid must not erase an in-band offer at product_min.
    if (
        min_offer_minor > 0
        and floored < min_offer_minor <= best
        and _annuity_minor(min_offer_minor, annual_rate, term_months) <= max_pay
    ):
        return min_offer_minor
    return floored


KNOWN_CHECK_STATUSES = frozenset({"ok", "negative", "unavailable", "missing_data"})
MAX_TERM_MONTHS_HARD = 600


def _is_strict_int(value: object) -> bool:
    """True only for real ints (not bool, not float). Money/term must be discrete."""
    return isinstance(value, int) and not isinstance(value, bool)


def _bureau_overdue_days(bureau: CheckOutcome) -> int | None:
    """Return non-negative overdue days, or None if payload is malformed/corrupt."""
    raw = bureau.payload.get("overdue_days", 0)
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
        parsed = int(raw)
    except (TypeError, ValueError):
        return None
    if parsed < 0:
        return None
    # Reject non-integral string forms that int() would truncate oddly; require round-trip
    try:
        if float(raw) != float(parsed):
            return None
    except (TypeError, ValueError):
        return None
    return parsed


def _non_negative_money(finances: FinancialInput) -> bool:
    for value in (
        finances.revenue_minor,
        finances.expenses_minor,
        finances.liabilities_minor,
        finances.amount_minor,
    ):
        if value is None:
            continue
        if not _is_strict_int(value) or value < 0:
            return False
    return True


def apply_decision_rules(
    finances: FinancialInput,
    risk: RiskResult,
    *,
    registry: CheckOutcome,
    bureau: CheckOutcome,
    product_min_minor: int,
    product_max_minor: int,
    product_min_term: int,
    product_max_term: int,
    demo_rate_annual: float = 0.16,
    rules_version: str | None = None,
) -> DecisionResult:
    settings = get_settings()
    version = rules_version or settings.rules_version
    metrics: dict = {
        "risk_score": risk.score,
        "risk_model_version": risk.model_version,
        "k_pass": K_PASS,
        "k_border": K_BORDER,
    }

    if finances.currency != SUPPORTED_CURRENCY:
        return DecisionResult(
            outcome="REJECTED",
            reason_codes=["UNSUPPORTED_CURRENCY"],
            offered_terms={},
            rules_version=version,
            metrics={**metrics, "currency": finances.currency},
        )

    if not _is_strict_int(finances.term_months) or not _is_strict_int(finances.amount_minor):
        return DecisionResult(
            outcome="REJECTED",
            reason_codes=["INVALID_TERM_OR_AMOUNT"],
            offered_terms={},
            rules_version=version,
            metrics=metrics,
        )

    if (
        finances.term_months <= 0
        or finances.term_months > MAX_TERM_MONTHS_HARD
        or finances.amount_minor <= 0
    ):
        return DecisionResult(
            outcome="REJECTED",
            reason_codes=["INVALID_TERM_OR_AMOUNT"],
            offered_terms={},
            rules_version=version,
            metrics=metrics,
        )

    if not _non_negative_money(finances):
        return DecisionResult(
            outcome="REJECTED",
            reason_codes=["NEGATIVE_MONEY_FIELDS"],
            offered_terms={},
            rules_version=version,
            metrics=metrics,
        )

    if (
        finances.revenue_minor is None
        or finances.expenses_minor is None
        or finances.liabilities_minor is None
    ):
        return DecisionResult(
            outcome="NEEDS_INFO",
            reason_codes=["INCOMPLETE_FINANCIALS"],
            offered_terms={},
            rules_version=version,
            metrics=metrics,
        )

    if not (product_min_minor <= finances.amount_minor <= product_max_minor):
        return DecisionResult(
            outcome="REJECTED",
            reason_codes=["PRODUCT_LIMIT"],
            offered_terms={},
            rules_version=version,
            metrics=metrics,
        )

    if not (product_min_term <= finances.term_months <= product_max_term):
        return DecisionResult(
            outcome="REJECTED",
            reason_codes=["PRODUCT_LIMIT"],
            offered_terms={},
            rules_version=version,
            metrics={
                **metrics,
                "term_months": finances.term_months,
                "product_min_term": product_min_term,
                "product_max_term": product_max_term,
            },
        )

    # Hard credit denials first — soft peer statuses (unavailable / missing_data /
    # unknown) must not rewrite an explicit negative or overdue into retry/info.
    if registry.status == "negative":
        return DecisionResult(
            outcome="REJECTED",
            reason_codes=["REGISTRY_NEGATIVE"],
            offered_terms={},
            rules_version=version,
            metrics=metrics,
        )

    if bureau.status == "negative":
        return DecisionResult(
            outcome="REJECTED",
            reason_codes=["BUREAU_NEGATIVE"],
            offered_terms={},
            rules_version=version,
            metrics={**metrics, "bureau_status": bureau.status},
        )

    if bureau.status == "ok":
        overdue = _bureau_overdue_days(bureau)
        if overdue is None:
            return DecisionResult(
                outcome="NEEDS_INFO",
                reason_codes=["MALFORMED_BUREAU_PAYLOAD"],
                offered_terms={},
                rules_version=version,
                metrics=metrics,
            )
        if overdue > 0:
            return DecisionResult(
                outcome="REJECTED",
                reason_codes=["BUREAU_OVERDUE"],
                offered_terms={},
                rules_version=version,
                metrics={
                    **metrics,
                    "overdue_days": overdue,
                    "bureau_status": bureau.status,
                },
            )

    if bureau.status not in KNOWN_CHECK_STATUSES or registry.status not in KNOWN_CHECK_STATUSES:
        return DecisionResult(
            outcome="NEEDS_INFO",
            reason_codes=["CHECKS_INCOMPLETE"],
            offered_terms={},
            rules_version=version,
            metrics={**metrics, "bureau": bureau.status, "registry": registry.status},
        )

    if bureau.status == "unavailable" or registry.status == "unavailable":
        return DecisionResult(
            outcome="CHECK_UNAVAILABLE",
            reason_codes=["CHECK_TECHNICAL_FAILURE"],
            offered_terms={},
            rules_version=version,
            metrics={**metrics, "bureau": bureau.status, "registry": registry.status},
        )

    if bureau.status == "missing_data" or registry.status == "missing_data":
        return DecisionResult(
            outcome="NEEDS_INFO",
            reason_codes=["CHECKS_INCOMPLETE"],
            offered_terms={},
            rules_version=version,
            metrics={**metrics, "bureau": bureau.status, "registry": registry.status},
        )

    if (
        not isinstance(demo_rate_annual, (int, float))
        or isinstance(demo_rate_annual, bool)
        or not math.isfinite(float(demo_rate_annual))
        or float(demo_rate_annual) < 0
        or float(demo_rate_annual) > 1.0
    ):
        return DecisionResult(
            outcome="REJECTED",
            reason_codes=["INVALID_RATE"],
            offered_terms={},
            rules_version=version,
            metrics={"demo_rate_annual": str(demo_rate_annual)},
        )
    demo_rate_annual = float(demo_rate_annual)

    payment = _annuity_minor(finances.amount_minor, demo_rate_annual, finances.term_months)
    k = coverage_ratio(finances, new_payment_minor=payment)
    metrics["new_payment_minor"] = payment
    # Display rounding must not feed the approve gate (see adv18).
    metrics["coverage_k"] = None if k is None else round(k, 6)

    if k is None:
        return DecisionResult(
            outcome="NEEDS_INFO",
            reason_codes=["K_UNAVAILABLE"],
            offered_terms={},
            rules_version=version,
            metrics=metrics,
        )

    # Hard risk floor: no approve and no alternative offer
    if risk.score <= SCORE_REJECT_MAX:
        return DecisionResult(
            outcome="REJECTED",
            reason_codes=["RISK_FLOOR"],
            offered_terms={},
            rules_version=version,
            metrics=metrics,
        )

    if k >= K_PASS and risk.score >= SCORE_APPROVE_MIN:
        return DecisionResult(
            outcome="APPROVED",
            reason_codes=["K_PASS", "RISK_OK", "CHECKS_OK"],
            offered_terms={
                "amount_minor": finances.amount_minor,
                "term_months": finances.term_months,
                "rate_annual": demo_rate_annual,
                "monthly_payment_minor": payment,
            },
            rules_version=version,
            metrics=metrics,
        )

    alt = max_principal_for_k(
        finances,
        annual_rate=demo_rate_annual,
        term_months=finances.term_months,
        target_k=K_PASS,
        search_hi_minor=product_max_minor,
        min_offer_minor=product_min_minor,
    )
    if alt >= product_min_minor and alt < finances.amount_minor:
        alt_pay = _annuity_minor(alt, demo_rate_annual, finances.term_months)
        return DecisionResult(
            outcome="ALTERNATIVE",
            reason_codes=["ALTERNATIVE_AMOUNT"],
            offered_terms={
                "amount_minor": alt,
                "term_months": finances.term_months,
                "rate_annual": demo_rate_annual,
                "monthly_payment_minor": alt_pay,
                "requested_amount_minor": finances.amount_minor,
            },
            rules_version=version,
            metrics=metrics,
        )

    return DecisionResult(
        outcome="REJECTED",
        reason_codes=["COVERAGE_OR_RISK_FAIL"],
        offered_terms={},
        rules_version=version,
        metrics=metrics,
    )
