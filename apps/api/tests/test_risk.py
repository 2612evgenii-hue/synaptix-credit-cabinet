from synaptix_api.analytics.mocks import run_bureau_check, run_registry_check
from synaptix_api.analytics.risk import assess_risk
from synaptix_api.analytics.types import FinancialInput


def test_missing_finances_not_treated_as_zero():
    fin = FinancialInput(
        revenue_minor=None,
        expenses_minor=None,
        liabilities_minor=None,
        amount_minor=1_500_000_00,
        term_months=36,
    )
    risk = assess_risk(fin)
    assert risk.factors.get("missing_cashflow") is True
    assert risk.score < 70


def test_overdue_lowers_score_more_than_unavailable():
    fin = FinancialInput(
        revenue_minor=900_000_00,
        expenses_minor=500_000_00,
        liabilities_minor=45_000_00,
        amount_minor=1_500_000_00,
        term_months=36,
    )
    ok = assess_risk(fin, bureau=run_bureau_check("approval"), registry=run_registry_check("approval", "x"))
    bad = assess_risk(fin, bureau=run_bureau_check("rejection"), registry=run_registry_check("rejection", "x"))
    down = assess_risk(
        fin,
        bureau=run_bureau_check("bureau_down"),
        registry=run_registry_check("approval", "x"),
    )
    assert bad.score < ok.score
    assert down.score > bad.score  # technical issue is not overdue penalty
