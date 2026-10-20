"""Attack: unparseable password_hash crashes seed completeness before repair."""

import pytest
from passlib.exc import UnknownHashError

from synaptix_api.db.passwords import verify_password
from synaptix_api.db.seed import DEMO_PASSWORD, seed_demo
from synaptix_api.models import User
from synaptix_api.models.entities import UserRole
from synaptix_api.settings import get_settings


@pytest.mark.parametrize(
    "login,corrupt_hash",
    [
        ("bank.officer@demo.local", ""),
        ("bank.officer@demo.local", "not-a-valid-hash"),
        ("client.approval@demo.local", ""),
        ("client.approval@demo.local", "not-a-valid-hash"),
    ],
    ids=[
        "officer_empty",
        "officer_garbage",
        "customer_empty",
        "customer_garbage",
    ],
)
def test_adv12_seed_must_repair_unparseable_password_hash(
    db, monkeypatch, login, corrupt_hash
):
    """
    Cycles 5–6 repair wrong-but-valid bcrypt hashes via verify_password → False.
    Empty / unrecognizable password_hash makes passlib raise UnknownHashError inside
    _seed_complete / _officer_identity_ok, so seed_demo aborts before any repair —
    demo bootstrap cannot heal partial DB corruption of the hash column.
    """
    monkeypatch.setenv("APP_ENV", "demo")
    get_settings.cache_clear()

    first = seed_demo(db)
    assert first.get("complete") is True or first.get("seeded") is True

    user = db.query(User).filter_by(demo_login=login).one()
    user.password_hash = corrupt_hash
    db.commit()

    try:
        result = seed_demo(db)
    except UnknownHashError as exc:
        pytest.fail(
            f"seed_demo crashed with UnknownHashError for {login!r} "
            f"password_hash={corrupt_hash!r}: {exc} — corrupt hash must be treated "
            f"as identity failure and repaired to DEMO_PASSWORD, not abort bootstrap"
        )

    repaired = db.query(User).filter_by(demo_login=login).one()
    assert verify_password(DEMO_PASSWORD, repaired.password_hash), (
        f"seed returned {result} but {login} password_hash still not DEMO_PASSWORD "
        f"(hash prefix={repaired.password_hash[:16]!r})"
    )
    if login.startswith("bank.officer"):
        assert repaired.role == UserRole.bank
        assert repaired.company_id is None
    else:
        assert repaired.role == UserRole.customer
