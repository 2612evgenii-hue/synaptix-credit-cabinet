"""Attack: any single customer satisfies customers>=1; scenario logins never created."""

from synaptix_api.db.passwords import hash_password
from synaptix_api.db.seed import seed_demo
from synaptix_api.models import Company, Product, User
from synaptix_api.models.entities import UserRole
from synaptix_api.settings import get_settings

SCENARIO_LOGINS = (
    "client.approval@demo.local",
    "client.clarification@demo.local",
    "client.rejection@demo.local",
)


def test_adv4_seed_must_create_scenario_clients_not_any_customer(db, monkeypatch):
    """
    Cycle 3 required customers >= 1. A rogue customer (non-scenario login) plus
    officer + active canonical products + one company still yields already_seeded;
    client.approval@demo.local etc. never materialize — contradicts _seed_complete
    docstring ('at least one customer per scenario company').
    """
    monkeypatch.setenv("APP_ENV", "demo")
    get_settings.cache_clear()

    db.add(
        User(
            role=UserRole.bank,
            company_id=None,
            demo_login="bank.officer@demo.local",
            password_hash=hash_password("demo1234"),
            full_name="Officer rogue-customer catalog",
        )
    )
    db.add(
        Product(
            code="working_capital",
            name="Оборотные средства (демо)",
            min_amount_minor=300_000_00,
            max_amount_minor=5_000_000_00,
            min_term_months=6,
            max_term_months=36,
            rules_version="demo-rules-v1",
            active=True,
        )
    )
    db.add(
        Product(
            code="equipment",
            name="Оборудование (демо)",
            min_amount_minor=500_000_00,
            max_amount_minor=10_000_000_00,
            min_term_months=12,
            max_term_months=60,
            rules_version="demo-rules-v1",
            active=True,
        )
    )
    company = Company(
        synthetic_name="Rogue-only company",
        synthetic_registration_id="SYN-ROGUE-CUST",
        scenario_key="approval",
    )
    db.add(company)
    db.flush()
    db.add(
        User(
            role=UserRole.customer,
            company_id=company.id,
            demo_login="client.rogue@demo.local",
            password_hash=hash_password("demo1234"),
            full_name="Non-scenario customer",
        )
    )
    db.commit()

    result = seed_demo(db)
    missing = [
        login
        for login in SCENARIO_LOGINS
        if db.query(User).filter(User.demo_login == login).first() is None
    ]

    assert not missing, (
        f"seed returned {result} but scenario logins missing={missing} — "
        "customers>=1 with a rogue login must not short-circuit as already_seeded"
    )
