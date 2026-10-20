"""Attack: officer login string alone satisfies completeness (wrong role/password/company)."""

from synaptix_api.db.passwords import hash_password, verify_password
from synaptix_api.db.seed import CANONICAL_PRODUCTS, DEMO_PASSWORD, seed_demo
from synaptix_api.models import Company, Product, User
from synaptix_api.models.entities import UserRole
from synaptix_api.settings import get_settings


def test_adv6_seed_must_repair_officer_identity(db, monkeypatch):
    """
    Cycle 5 repaired scenario *customer* role/company/password. Officer completeness
    still only checks that bank.officer@demo.local exists. A customer-role officer
    with wrong password and a company_id still yields already_seeded — bank demo
    login is never repaired.
    """
    monkeypatch.setenv("APP_ENV", "demo")
    get_settings.cache_clear()
    rules = get_settings().rules_version

    orphan = Company(
        synthetic_name="orphan",
        synthetic_registration_id="SYN-ORPHAN-OFFICER",
        scenario_key="orphan",
    )
    db.add(orphan)
    db.flush()
    db.add(
        User(
            role=UserRole.customer,
            company_id=orphan.id,
            demo_login="bank.officer@demo.local",
            password_hash=hash_password("not-the-demo-password"),
            full_name="Bad Officer",
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
    for sid, cname in (
        ("approval", "СИНТЕТИКА Альфа-Пример"),
        ("clarification", "СИНТЕТИКА Бета-Пример"),
        ("rejection", "СИНТЕТИКА Гамма-Пример"),
    ):
        company = Company(
            synthetic_name=cname,
            synthetic_registration_id=f"SYN-{sid.upper()}",
            scenario_key=sid,
        )
        db.add(company)
        db.flush()
        db.add(
            User(
                role=UserRole.customer,
                company_id=company.id,
                demo_login=f"client.{sid}@demo.local",
                password_hash=hash_password(DEMO_PASSWORD),
                full_name=f"Клиент сценария {sid}",
            )
        )
    db.commit()

    result = seed_demo(db)
    officer = db.query(User).filter_by(demo_login="bank.officer@demo.local").one()

    assert officer.role == UserRole.bank, (
        f"seed returned {result} but officer role={officer.role} "
        "(login-only completeness skips officer identity repair)"
    )
    assert officer.company_id is None, (
        f"officer company_id={officer.company_id} must be None for bank role"
    )
    assert verify_password(DEMO_PASSWORD, officer.password_hash), (
        f"officer password not restored to DEMO_PASSWORD after seed {result}"
    )
