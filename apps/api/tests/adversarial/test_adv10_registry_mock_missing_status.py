"""Attack: registry profile missing status key remaps to negative (vs bureau)."""

from synaptix_api.analytics.decision import apply_decision_rules
from synaptix_api.analytics.mocks import BUREAU, REGISTRY, run_bureau_check, run_registry_check
from synaptix_api.analytics.types import FinancialInput, RiskResult


def test_adv10_registry_profile_missing_status_must_not_become_negative():
    """
    Cycle 7: bureau profile without ``status`` → CheckOutcome missing_data
    (no crash). Registry still uses ``profile_status != \"active\"`` on
    ``.get(\"status\") is None`` → negative → REGISTRY_NEGATIVE.

    Incomplete registry profile must degrade like bureau (missing_data /
    NEEDS_INFO), not invent a hard credit denial.
    """
    REGISTRY["adv10_reg_no_status"] = {"found": True, "note": "status key absent"}
    BUREAU["adv10_bur_no_status"] = {"overdue_days": 0, "obligations": 0}
    try:
        bureau_incomplete = run_bureau_check("adv10_bur_no_status")
        assert bureau_incomplete.status == "missing_data", (
            f"precondition: bureau missing status → missing_data; got "
            f"{bureau_incomplete.status!r}"
        )

        outcome = run_registry_check("adv10_reg_no_status", "SYN-ADV10-NO-STATUS")
        assert outcome.status == "missing_data", (
            f"registry profile without status must yield missing_data "
            f"(mirror bureau cycle-7 fix); got {outcome.status!r} "
            f"payload={outcome.payload}"
        )

        finances = FinancialInput(
            revenue_minor=900_000_00,
            expenses_minor=500_000_00,
            liabilities_minor=45_000_00,
            amount_minor=1_500_000_00,
            term_months=36,
        )
        bureau_ok = run_bureau_check("approval")
        risk = RiskResult(score=70, factors={"forced": "ok"}, model_version="adv10")
        decision = apply_decision_rules(
            finances,
            risk,
            registry=outcome,
            bureau=bureau_ok,
            product_min_minor=500_000_00,
            product_max_minor=10_000_000_00,
            product_min_term=1,
            product_max_term=120,
        )
        assert decision.outcome == "NEEDS_INFO", (
            f"incomplete registry profile must be NEEDS_INFO not credit reject; "
            f"got {decision.outcome} {decision.reason_codes}"
        )
        assert "CHECKS_INCOMPLETE" in decision.reason_codes
        assert "REGISTRY_NEGATIVE" not in decision.reason_codes
    finally:
        REGISTRY.pop("adv10_reg_no_status", None)
        BUREAU.pop("adv10_bur_no_status", None)
