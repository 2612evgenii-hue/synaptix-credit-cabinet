"""Attack: company reg_id match ignores scenario_key / synthetic_name drift."""

from synaptix_api.db.passwords import hash_password
from synaptix_api.db.seed import CANONICAL_PRODUCTS, seed_demo
from synaptix_api.models import Company, Product, User
from synaptix_api.models.entities import UserRole
from synaptix_api.settings import get_settings


def test_adv5_seed_must_repair_company_scenario_identity(db, monkeypatch):
    """
    Cycle 4 requires SYN-{ID} companies to exist. Completeness does not check
    scenario_key or synthetic_name. Rows with correct reg_id but scenario_key
    'rogue' / name 'WRONG' yield already_seeded; seed never rewrites company
    fields — demo scenario wiring stays corrupt.
    """
    monkeypatch.setenv("APP_ENV", "demo")
    get_settings.cache_clear()
    rules = get_settings().rules_version

    db.add(
        User(
            role=UserRole.bank,
            company_id=None,
            demo_login="bank.officer@demo.local",
            password_hash=hash_password("demo1234"),
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
    for sid in ("approval", "clarification", "rejection"):
        company = Company(
            synthetic_name="WRONG",
            synthetic_registration_id=f"SYN-{sid.upper()}",
            scenario_key="rogue",
        )
        db.add(company)
        db.flush()
        db.add(
            User(
                role=UserRole.customer,
                company_id=company.id,
                demo_login=f"client.{sid}@demo.local",
                password_hash=hash_password("demo1234"),
                full_name=f"Клиент сценария {sid}",
            )
        )
    db.commit()

    result = seed_demo(db)
    approval = db.query(Company).filter_by(synthetic_registration_id="SYN-APPROVAL").one()

    assert approval.scenario_key == "approval", (
        f"seed returned {result} but SYN-APPROVAL.scenario_key={approval.scenario_key!r} "
        "(expected 'approval') — reg_id-only completeness skips company repair"
    )
    assert approval.synthetic_name == "СИНТЕТИКА Альфа-Пример", (
        f"synthetic_name left as {approval.synthetic_name!r} after seed {result}"
    )
