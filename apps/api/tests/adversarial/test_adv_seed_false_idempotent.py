"""Attack: seed treats presence of bank officer alone as full seed — products/companies never created."""

from synaptix_api.db.passwords import hash_password
from synaptix_api.db.seed import seed_demo
from synaptix_api.models import Company, Product, User
from synaptix_api.models.entities import UserRole
from synaptix_api.settings import get_settings


def test_adv_seed_skips_when_only_officer_exists(db, monkeypatch):
    monkeypatch.setenv("APP_ENV", "demo")
    get_settings.cache_clear()

    db.add(
        User(
            role=UserRole.bank,
            company_id=None,
            demo_login="bank.officer@demo.local",
            password_hash=hash_password("demo1234"),
            full_name="Orphan officer without products",
        )
    )
    db.commit()

    assert db.query(Product).count() == 0
    assert db.query(Company).count() == 0

    result = seed_demo(db)

    # Claiming already_seeded while demo catalog is empty breaks demo bootstrap
    assert result.get("seeded") is True or db.query(Product).count() >= 1, (
        f"seed returned {result} with products={db.query(Product).count()} "
        f"companies={db.query(Company).count()} — false idempotency"
    )
    assert db.query(Company).count() >= 1
    assert db.query(Product).count() >= 1
