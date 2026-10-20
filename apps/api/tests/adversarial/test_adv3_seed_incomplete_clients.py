"""Attack: officer + canonical products + company with zero clients → already_seeded."""

from synaptix_api.db.passwords import hash_password
from synaptix_api.db.seed import seed_demo
from synaptix_api.models import Company, Product, User
from synaptix_api.models.entities import UserRole
from synaptix_api.settings import get_settings


def test_adv3_seed_must_create_clients_when_catalog_present(db, monkeypatch):
    """
    _seed_complete ignores customer users. A DB with officer, working_capital,
    equipment and one company (no clients) is treated as already_seeded — scenario
    logins from scenarios.json never materialize.
    """
    monkeypatch.setenv("APP_ENV", "demo")
    get_settings.cache_clear()

    db.add(
        User(
            role=UserRole.bank,
            company_id=None,
            demo_login="bank.officer@demo.local",
            password_hash=hash_password("demo1234"),
            full_name="Officer without clients",
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
        )
    )
    db.add(
        Company(
            synthetic_name="Orphan company",
            synthetic_registration_id="SYN-ORPHAN",
            scenario_key="approval",
        )
    )
    db.commit()

    result = seed_demo(db)
    approval_client = (
        db.query(User).filter(User.demo_login == "client.approval@demo.local").first()
    )
    customer_count = db.query(User).filter(User.role == UserRole.customer).count()

    assert approval_client is not None and customer_count >= 3, (
        f"seed returned {result} with customer_count={customer_count} — "
        "canonical catalog without clients must not short-circuit as already_seeded"
    )
