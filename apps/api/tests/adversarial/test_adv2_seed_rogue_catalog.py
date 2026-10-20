"""Attack: any 2 products + officer + company → already_seeded; demo catalog never repaired."""

from synaptix_api.db.passwords import hash_password
from synaptix_api.db.seed import seed_demo
from synaptix_api.models import Company, Product, User
from synaptix_api.models.entities import UserRole
from synaptix_api.settings import get_settings


def test_adv2_seed_skips_when_rogue_products_satisfy_count(db, monkeypatch):
    """
    _seed_complete only checks product_count >= 2, not that working_capital /
    equipment exist. Two arbitrary products make seed claim already_seeded.
    """
    monkeypatch.setenv("APP_ENV", "demo")
    get_settings.cache_clear()

    db.add(
        User(
            role=UserRole.bank,
            company_id=None,
            demo_login="bank.officer@demo.local",
            password_hash=hash_password("demo1234"),
            full_name="Officer with rogue catalog",
        )
    )
    db.add(
        Product(
            code="rogue_a",
            name="Rogue A",
            min_amount_minor=1,
            max_amount_minor=2,
            min_term_months=1,
            max_term_months=2,
            rules_version="x",
        )
    )
    db.add(
        Product(
            code="rogue_b",
            name="Rogue B",
            min_amount_minor=1,
            max_amount_minor=2,
            min_term_months=1,
            max_term_months=2,
            rules_version="x",
        )
    )
    db.add(
        Company(
            synthetic_name="Placeholder",
            synthetic_registration_id="SYN-PLACEHOLDER",
            scenario_key="approval",
        )
    )
    db.commit()

    result = seed_demo(db)

    wc = db.query(Product).filter_by(code="working_capital").first()
    eq = db.query(Product).filter_by(code="equipment").first()
    assert result.get("seeded") is True or (wc is not None and eq is not None), (
        f"seed returned {result} while demo products missing "
        f"(codes={[p.code for p in db.query(Product).all()]}) — count-based false complete"
    )
