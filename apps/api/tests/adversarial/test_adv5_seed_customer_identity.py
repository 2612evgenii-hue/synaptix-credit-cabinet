"""Attack: scenario login string alone satisfies completeness (wrong role/company/password)."""

from synaptix_api.db.passwords import hash_password, verify_password
from synaptix_api.db.seed import CANONICAL_PRODUCTS, DEMO_PASSWORD, seed_demo
from synaptix_api.models import Company, Product, User
from synaptix_api.models.entities import UserRole
from synaptix_api.settings import get_settings


def test_adv5_seed_must_repair_scenario_customer_identity(db, monkeypatch):
    """
    Cycle 4 checks that client.{sid}@demo.local exists. Role, company_id, and
    password are ignored. A bank-role user on an orphan company with a wrong
    password still yields already_seeded — scenario customers are never repaired.
    """
    monkeypatch.setenv("APP_ENV", "demo")
    get_settings.cache_clear()
    rules = get_settings().rules_version

    db.add(
        User(
            role=UserRole.bank,
            company_id=None,
            demo_login="bank.officer@demo.local",
            password_hash=hash_password(DEMO_PASSWORD),
            full_name="Officer",
        )
    )
    for code, name, amin, amax, tmin, tmax in CANONICAL_PRODUCTS:
        db.add(
            Product(
                code=code,
                name=name,
                min_amount_minor=amin,
                max_amount_minor=amax,
                min_term_months=tmin,
                max_term_months=tmax,
                rules_version=rules,
                active=True,
            )
        )
    orphan = Company(
        synthetic_name="orphan",
        synthetic_registration_id="SYN-ORPHAN",
        scenario_key="orphan",
    )
    db.add(orphan)
    db.flush()
    for sid in ("approval", "clarification", "rejection"):
        company = Company(
            synthetic_name=f"c-{sid}",
            synthetic_registration_id=f"SYN-{sid.upper()}",
            scenario_key=sid,
        )
        db.add(company)
        db.flush()
        db.add(
            User(
                role=UserRole.bank,
                company_id=orphan.id,
                demo_login=f"client.{sid}@demo.local",
                password_hash=hash_password("not-the-demo-password"),
                full_name="bad",
            )
        )
    db.commit()

    result = seed_demo(db)
    user = db.query(User).filter_by(demo_login="client.approval@demo.local").one()
    company = db.query(Company).filter_by(synthetic_registration_id="SYN-APPROVAL").one()

    assert user.role == UserRole.customer, (
        f"seed returned {result} but client.approval role={user.role} "
        "(login-only completeness skips identity repair)"
    )
    assert user.company_id == company.id, (
        f"client.approval company_id={user.company_id} != SYN-APPROVAL id={company.id}"
    )
    assert verify_password(DEMO_PASSWORD, user.password_hash), (
        f"client.approval password not restored to DEMO_PASSWORD after seed {result}"
    )
