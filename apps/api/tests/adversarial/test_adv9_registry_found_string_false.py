"""Attack: registry mock treats truthy string found='false' as found → false approve."""

from synaptix_api.analytics.decision import apply_decision_rules
from synaptix_api.analytics.mocks import REGISTRY, run_bureau_check, run_registry_check
from synaptix_api.analytics.risk import assess_risk
from synaptix_api.analytics.types import FinancialInput


def test_adv9_registry_found_string_false_must_not_approve():
    """
    run_registry_check uses ``not profile.get("found")`` for presence.
    Boolean False correctly → negative; the string \"false\" is truthy in Python,
    so a corrupt / loosely-typed profile with found=\"false\" and status=active
    yields CheckOutcome ok and can APPROVE — company-not-found smuggled as clean.
    """
    REGISTRY["adv9_found_str"] = {"found": "false", "status": "active"}
    try:
        # Precondition: real False is negative
        REGISTRY["adv9_found_bool"] = {"found": False, "status": "active"}
        assert run_registry_check("adv9_found_bool", "SYN-ADV9-F").status == "negative"

        outcome = run_registry_check("adv9_found_str", "SYN-ADV9-F")
        assert outcome.status != "ok", (
            f"found='false' (string) must not be treated as present/ok; "
            f"got status={outcome.status!r} payload={outcome.payload}"
        )

        finances = FinancialInput(
            revenue_minor=900_000_00,
            expenses_minor=500_000_00,
            liabilities_minor=45_000_00,
            amount_minor=1_500_000_00,
            term_months=36,
        )
        bureau = run_bureau_check("approval")
        risk = assess_risk(finances, bureau=bureau, registry=outcome)
        decision = apply_decision_rules(
            finances,
            risk,
            registry=outcome,
            bureau=bureau,
            product_min_minor=500_000_00,
            product_max_minor=10_000_000_00,
            product_min_term=1,
            product_max_term=120,
        )
        assert decision.outcome != "APPROVED", (
            f"string found='false' must not reach APPROVED; "
            f"got {decision.outcome} {decision.reason_codes}"
        )
    finally:
        REGISTRY.pop("adv9_found_str", None)
        REGISTRY.pop("adv9_found_bool", None)
