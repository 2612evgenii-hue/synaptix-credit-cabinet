"""Attack: active canonical product codes with corrupt limits still count as complete."""

from synaptix_api.db.passwords import hash_password
from synaptix_api.db.seed import seed_demo
from synaptix_api.models import Company, Product, User
from synaptix_api.models.entities import UserRole
from synaptix_api.settings import get_settings

# Canonical demo bounds written by seed_demo._ensure_product
WC_MIN, WC_MAX = 300_000_00, 5_000_000_00
EQ_MIN, EQ_MAX = 500_000_00, 10_000_000_00


def test_adv4_seed_must_repair_corrupt_canonical_product_limits(db, monkeypatch):
    """
    Cycle 3 fixed inactive codes. Completeness still ignores amount/term bounds.
    Active working_capital/equipment with absurd limits + officer + customer +
    company → already_seeded; _ensure_product repair never runs.
    """
    monkeypatch.setenv("APP_ENV", "demo")
    get_settings.cache_clear()

    db.add(
        User(
            role=UserRole.bank,
            company_id=None,
            demo_login="bank.officer@demo.local",
            password_hash=hash_password("demo1234"),
            full_name="Officer corrupt limits",
        )
    )
    db.add(
        Product(
            code="working_capital",
            name="corrupt WC",
            min_amount_minor=1,
            max_amount_minor=2,
            min_term_months=1,
            max_term_months=1,
            rules_version="old-rules",
            active=True,
        )
    )
    db.add(
        Product(
            code="equipment",
            name="corrupt EQ",
            min_amount_minor=1,
            max_amount_minor=2,
            min_term_months=1,
            max_term_months=1,
            rules_version="old-rules",
            active=True,
        )
    )
    company = Company(
        synthetic_name="Limits orphan",
        synthetic_registration_id="SYN-CORRUPT-LIMITS",
        scenario_key="approval",
    )
    db.add(company)
    db.flush()
    db.add(
        User(
            role=UserRole.customer,
            company_id=company.id,
            demo_login="client.approval@demo.local",
            password_hash=hash_password("demo1234"),
            full_name="Client approval",
        )
    )
    db.commit()

    result = seed_demo(db)
    wc = db.query(Product).filter_by(code="working_capital").one()
    eq = db.query(Product).filter_by(code="equipment").one()

    assert (
        wc.min_amount_minor == WC_MIN
        and wc.max_amount_minor == WC_MAX
        and eq.min_amount_minor == EQ_MIN
        and eq.max_amount_minor == EQ_MAX
    ), (
        f"seed returned {result} but left corrupt limits "
        f"wc=({wc.min_amount_minor},{wc.max_amount_minor}) "
        f"eq=({eq.min_amount_minor},{eq.max_amount_minor}) — "
        "canonical active codes with wrong bounds must be repaired, not already_seeded"
    )
