"""Attack: store_check lets payload['status'] overwrite CheckOutcome.status."""

from synaptix_api.analytics.mocks import run_registry_check
from synaptix_api.analytics.persist import store_check
from synaptix_api.models import Application, Company, User
from synaptix_api.models.entities import ApplicationState, UserRole


def _app(db, reg_id: str):
    company = Company(
        synthetic_name="Adv3 Check Co",
        synthetic_registration_id=reg_id,
        scenario_key="approval",
    )
    db.add(company)
    db.flush()
    user = User(
        role=UserRole.customer,
        company_id=company.id,
        demo_login=f"adv3.check.{reg_id.lower()}@demo.local",
        password_hash="x",
        full_name="Adv3",
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
    return app


def test_adv3_store_check_must_keep_outcome_status(db):
    """
    store_check builds result={"status": outcome.status, **outcome.payload}.
    Registry payload carries entity status 'active' / 'liquidating', which
    clobbers the CheckOutcome status ('ok' / 'negative') in the persisted JSON.
    """
    app_ok = _app(db, "SYN-ADV3-CHK-OK")
    outcome_ok = run_registry_check("approval", "SYN-ADV3-CHK-OK")
    assert outcome_ok.status == "ok"
    assert outcome_ok.payload.get("status") == "active"

    row_ok = store_check(db, app_ok.id, outcome_ok)
    db.flush()
    assert row_ok.result.get("status") == outcome_ok.status, (
        f"persisted status {row_ok.result.get('status')!r} != outcome "
        f"{outcome_ok.status!r} (payload entity status leaked)"
    )

    app_neg = _app(db, "SYN-ADV3-CHK-NEG")
    outcome_neg = run_registry_check("inactive", "SYN-ADV3-CHK-NEG")
    assert outcome_neg.status == "negative"
    assert outcome_neg.payload.get("status") == "liquidating"

    row_neg = store_check(db, app_neg.id, outcome_neg)
    db.flush()
    assert row_neg.result.get("status") == outcome_neg.status, (
        f"persisted status {row_neg.result.get('status')!r} != outcome "
        f"{outcome_neg.status!r} — audit trail cannot recover check verdict"
    )
