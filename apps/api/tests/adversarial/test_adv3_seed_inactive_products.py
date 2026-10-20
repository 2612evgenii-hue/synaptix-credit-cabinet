"""Attack: inactive working_capital/equipment still satisfy _seed_complete."""

from synaptix_api.db.passwords import hash_password
from synaptix_api.db.seed import seed_demo
from synaptix_api.models import Company, Product, User
from synaptix_api.models.entities import UserRole
from synaptix_api.settings import get_settings


def test_adv3_seed_must_not_skip_when_demo_products_inactive(db, monkeypatch):
    """
    Cycle 2 fixed rogue codes; completeness still ignores Product.active.
    Inactive canonical rows make seed claim already_seeded and never repair.
    """
    monkeypatch.setenv("APP_ENV", "demo")
    get_settings.cache_clear()

    db.add(
        User(
            role=UserRole.bank,
            company_id=None,
            demo_login="bank.officer@demo.local",
            password_hash=hash_password("demo1234"),
            full_name="Officer inactive catalog",
        )
    )
    db.add(
        Product(
            code="working_capital",
            name="WC dead",
            min_amount_minor=300_000_00,
            max_amount_minor=5_000_000_00,
            min_term_months=6,
            max_term_months=36,
            rules_version="demo-rules-v1",
            active=False,
        )
    )
    db.add(
        Product(
            code="equipment",
            name="EQ dead",
            min_amount_minor=500_000_00,
            max_amount_minor=10_000_000_00,
            min_term_months=12,
            max_term_months=60,
            rules_version="demo-rules-v1",
            active=False,
        )
    )
    db.add(
        Company(
            synthetic_name="Placeholder",
            synthetic_registration_id="SYN-INACTIVE-CAT",
            scenario_key="approval",
        )
    )
    db.commit()

    result = seed_demo(db)
    active_wc = db.query(Product).filter_by(code="working_capital", active=True).first()
    active_eq = db.query(Product).filter_by(code="equipment", active=True).first()

    assert active_wc is not None and active_eq is not None, (
        f"seed returned {result} while demo products remain inactive — "
        "active=False catalog must not count as complete"
    )
