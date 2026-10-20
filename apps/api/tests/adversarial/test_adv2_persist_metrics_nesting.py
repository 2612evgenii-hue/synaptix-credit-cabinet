"""Attack: store_decision nests DecisionResult.metrics inside offered_terms JSON."""

from synaptix_api.analytics.persist import store_decision
from synaptix_api.analytics.types import DecisionResult
from synaptix_api.models import Application, Company, User
from synaptix_api.models.entities import ApplicationState, UserRole


def test_adv2_store_decision_must_not_nest_metrics_in_offered_terms(db):
    """
    DecisionResult keeps metrics separate from offered_terms. Persist merges
    metrics into offered_terms, polluting commercial terms and overwriting any
    offered_terms['metrics'] key.
    """
    company = Company(
        synthetic_name="Adv2 Co",
        synthetic_registration_id="SYN-ADV2-PERSIST",
        scenario_key="approval",
    )
    db.add(company)
    db.flush()
    user = User(
        role=UserRole.customer,
        company_id=company.id,
        demo_login="adv2.persist@demo.local",
        password_hash="x",
        full_name="Adv2",
    )
    db.add(user)
    db.flush()
    app = Application(
        company_id=company.id,
        created_by=user.id,
        amount_minor=500_000_00,
        term_months=12,
        state=ApplicationState.SUBMITTED,
    )
    db.add(app)
    db.flush()

    decision = DecisionResult(
        outcome="APPROVED",
        reason_codes=["K_PASS", "RISK_OK", "CHECKS_OK"],
        offered_terms={
            "amount_minor": 500_000_00,
            "term_months": 12,
            "rate_annual": 0.16,
            "monthly_payment_minor": 10_000_00,
        },
        rules_version="demo-rules-v1",
        metrics={"coverage_k": 2.5, "risk_score": 70, "k_pass": 1.3},
    )
    row = store_decision(db, app.id, decision)
    db.flush()

    commercial_keys = set(decision.offered_terms.keys())
    stored_keys = set(row.offered_terms.keys())

    assert "metrics" not in row.offered_terms, (
        f"metrics nested into offered_terms: {row.offered_terms.get('metrics')!r}"
    )
    assert stored_keys == commercial_keys, (
        f"offered_terms mutated on persist: stored={sorted(stored_keys)} "
        f"expected={sorted(commercial_keys)}"
    )
