"""Attack: bureau status=ok with overdue_days>0 is neither penalized nor rejected."""

from synaptix_api.analytics.decision import apply_decision_rules
from synaptix_api.analytics.mocks import run_registry_check
from synaptix_api.analytics.risk import assess_risk
from synaptix_api.analytics.types import CheckOutcome, FinancialInput


def test_adv_ok_bureau_with_overdue_must_not_score_like_clean_bureau():
    finances = FinancialInput(
        revenue_minor=900_000_00,
        expenses_minor=100_000_00,
        liabilities_minor=10_000_00,
        amount_minor=1_000_000_00,
        term_months=12,
    )
    registry = run_registry_check("approval", "SYN-ADV")
    clean = CheckOutcome(
        source="credit_bureau",
        status="ok",
        mock_version="adv",
        payload={"overdue_days": 0},
    )
    dirty = CheckOutcome(
        source="credit_bureau",
        status="ok",
        mock_version="adv",
        payload={"overdue_days": 90},
    )

    clean_risk = assess_risk(finances, bureau=clean, registry=registry)
    dirty_risk = assess_risk(finances, bureau=dirty, registry=registry)

    # 90 days overdue must lower score vs clean ok — today both stay at base 70
    assert dirty_risk.score < clean_risk.score, (
        f"overdue_days=90 ignored for status=ok: clean={clean_risk.score} dirty={dirty_risk.score}"
    )


def test_adv_ok_bureau_with_overdue_must_not_auto_approve():
    finances = FinancialInput(
        revenue_minor=900_000_00,
        expenses_minor=100_000_00,
        liabilities_minor=10_000_00,
        amount_minor=1_000_000_00,
        term_months=12,
    )
    registry = run_registry_check("approval", "SYN-ADV")
    bureau = CheckOutcome(
        source="credit_bureau",
        status="ok",
        mock_version="adv",
        payload={"overdue_days": 90, "status": "ok"},
    )
    risk = assess_risk(finances, bureau=bureau, registry=registry)
    decision = apply_decision_rules(
        finances,
        risk,
        registry=registry,
        bureau=bureau,
        product_min_minor=300_000_00,
        product_max_minor=5_000_000_00,
        product_min_term=1,
        product_max_term=120,
    )

    assert decision.outcome != "APPROVED", (
        f"90d overdue with status=ok approved: {decision.outcome} score={risk.score}"
    )
