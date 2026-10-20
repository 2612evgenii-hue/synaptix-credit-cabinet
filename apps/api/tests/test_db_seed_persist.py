import uuid

from synaptix_api.analytics.pipeline import ProductLimits, run_analytics
from synaptix_api.analytics.persist import store_check, store_decision, store_risk
from synaptix_api.analytics.types import FinancialInput
from synaptix_api.db.seed import seed_demo
from synaptix_api.models import Application, CheckResult, Decision, FinancialSnapshot, RiskAssessment, User
from synaptix_api.models.entities import ApplicationState, UserRole
from synaptix_api.settings import get_settings


def test_seed_idempotent(db, monkeypatch):
    monkeypatch.setenv("APP_ENV", "demo")
    get_settings.cache_clear()
    first = seed_demo(db)
    second = seed_demo(db)
    assert first["seeded"] is True
    assert second["seeded"] is False
    assert db.query(User).filter(User.role == UserRole.bank).count() == 1
    assert db.query(User).filter(User.role == UserRole.customer).count() >= 3


def test_persist_analytics_rows(db, monkeypatch):
    monkeypatch.setenv("APP_ENV", "demo")
    get_settings.cache_clear()
    seed_demo(db)
    from synaptix_api.models import Product

    customer = db.query(User).filter(User.demo_login == "client.approval@demo.local").one()
    company = customer.company
    equipment = db.query(Product).filter_by(code="equipment").one()
    app = Application(
        company_id=company.id,
        created_by=customer.id,
        product_id=equipment.id,
        amount_minor=1_500_000_00,
        term_months=36,
        purpose="equipment",
        state=ApplicationState.SUBMITTED,
    )
    db.add(app)
    db.flush()
    snap = FinancialSnapshot(
        application_id=app.id,
        revenue_minor=900_000_00,
        expenses_minor=500_000_00,
        liabilities_minor=45_000_00,
        debt_service_monthly_minor=0,
        period_label="month",
    )
    db.add(snap)
    db.flush()

    bundle = run_analytics(
        scenario_key="approval",
        registration_id=company.synthetic_registration_id,
        finances=FinancialInput(
            revenue_minor=900_000_00,
            expenses_minor=500_000_00,
            liabilities_minor=45_000_00,
            amount_minor=1_500_000_00,
            term_months=36,
        ),
        product=ProductLimits(
            min_amount_minor=equipment.min_amount_minor,
            max_amount_minor=equipment.max_amount_minor,
            demo_rate_annual=equipment.demo_rate_annual or 0.16,
        ),
    )
    store_check(db, app.id, bundle.registry)
    store_check(db, app.id, bundle.bureau)
    store_risk(db, app.id, bundle.risk)
    store_decision(
        db,
        app.id,
        bundle.decision,
        actor_id=None,
        explanation=bundle.explanation,
        financial_snapshot_id=snap.id,
        product_code=equipment.code,
        application_version=app.version,
    )
    db.commit()

    assert db.query(CheckResult).filter_by(application_id=app.id).count() == 2
    assert db.query(RiskAssessment).filter_by(application_id=app.id).one().score == bundle.risk.score
    row = db.query(Decision).filter_by(application_id=app.id).one()
    assert row.outcome == "APPROVED"
    assert row.explanation_client
    assert row.llm_meta.get("backend") == "template"
    assert row.financial_snapshot_id == snap.id
    assert row.product_code == "equipment"
    assert equipment.product_version == "equipment-demo-1"


def test_seed_blocked_outside_demo(db, monkeypatch):
    monkeypatch.setenv("APP_ENV", "prod")
    get_settings.cache_clear()
    try:
        import pytest

        with pytest.raises(RuntimeError):
            seed_demo(db)
    finally:
        monkeypatch.setenv("APP_ENV", "demo")
        get_settings.cache_clear()
