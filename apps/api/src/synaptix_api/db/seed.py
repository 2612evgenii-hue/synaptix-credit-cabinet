"""Idempotent synthetic seed for APP_ENV=demo. Not production data."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from synaptix_api.db.passwords import hash_password, verify_password
from synaptix_api.models import Company, Product, User
from synaptix_api.models.entities import UserRole
from synaptix_api.settings import get_settings

DEMO_PASSWORD = "demo1234"

REPO_ROOT = Path(__file__).resolve().parents[5]
SCENARIOS = REPO_ROOT / "data" / "synthetic" / "scenarios.json"

CANONICAL_PRODUCTS = (
    ("working_capital", "Оборотные средства (демо)", 300_000_00, 5_000_000_00, 6, 36),
    ("equipment", "Оборудование (демо)", 500_000_00, 10_000_000_00, 12, 60),
)


def _scenarios() -> list[dict]:
    return json.loads(SCENARIOS.read_text(encoding="utf-8"))["cases"]


def _product_matches(row: Product, amin: int, amax: int, tmin: int, tmax: int, rules: str) -> bool:
    return (
        row.active
        and row.min_amount_minor == amin
        and row.max_amount_minor == amax
        and row.min_term_months == tmin
        and row.max_term_months == tmax
        and row.rules_version == rules
    )


def _officer_identity_ok(user: User | None) -> bool:
    return (
        user is not None
        and user.role == UserRole.bank
        and user.company_id is None
        and verify_password(DEMO_PASSWORD, user.password_hash)
    )


def _seed_complete(db: Session, rules_version: str) -> bool:
    officer = db.query(User).filter(User.demo_login == "bank.officer@demo.local").first()
    if not _officer_identity_ok(officer):
        return False
    for code, _name, amin, amax, tmin, tmax in CANONICAL_PRODUCTS:
        row = db.query(Product).filter_by(code=code).first()
        if row is None or not _product_matches(row, amin, amax, tmin, tmax, rules_version):
            return False
    if not SCENARIOS.is_file():
        return False
    for case in _scenarios():
        sid = case["id"]
        reg_id = f"SYN-{sid.upper()}"
        company = db.query(Company).filter_by(synthetic_registration_id=reg_id).first()
        if (
            company is None
            or company.scenario_key != sid
            or company.synthetic_name != case["company"]
        ):
            return False
        login = f"client.{sid}@demo.local"
        user = db.query(User).filter(User.demo_login == login).first()
        if (
            user is None
            or user.role != UserRole.customer
            or user.company_id != company.id
            or not verify_password(DEMO_PASSWORD, user.password_hash)
        ):
            return False
    return True


def seed_demo(db: Session) -> dict:
    settings = get_settings()
    if settings.app_env != "demo":
        raise RuntimeError("Seed allowed only when APP_ENV=demo")

    if not SCENARIOS.is_file():
        raise FileNotFoundError(f"Missing scenarios file: {SCENARIOS}")

    if _seed_complete(db, settings.rules_version):
        return {"seeded": False, "reason": "already_seeded"}

    officer = db.query(User).filter(User.demo_login == "bank.officer@demo.local").first()
    if officer is None:
        db.add(
            User(
                role=UserRole.bank,
                company_id=None,
                demo_login="bank.officer@demo.local",
                password_hash=hash_password(DEMO_PASSWORD),
                full_name="Синтетический сотрудник банка",
            )
        )
    elif not _officer_identity_ok(officer):
        officer.role = UserRole.bank
        officer.company_id = None
        officer.password_hash = hash_password(DEMO_PASSWORD)
        officer.full_name = "Синтетический сотрудник банка"

    for code, name, amin, amax, tmin, tmax in CANONICAL_PRODUCTS:
        row = db.query(Product).filter_by(code=code).first()
        if row is None:
            db.add(
                Product(
                    code=code,
                    name=name,
                    min_amount_minor=amin,
                    max_amount_minor=amax,
                    min_term_months=tmin,
                    max_term_months=tmax,
                    rules_version=settings.rules_version,
                    active=True,
                )
            )
        else:
            row.active = True
            row.name = name
            row.min_amount_minor = amin
            row.max_amount_minor = amax
            row.min_term_months = tmin
            row.max_term_months = tmax
            row.rules_version = settings.rules_version

    created_logins: list[str] = []
    for case in _scenarios():
        sid = case["id"]
        reg_id = f"SYN-{sid.upper()}"
        company = db.query(Company).filter_by(synthetic_registration_id=reg_id).first()
        if company is None:
            company = Company(
                synthetic_name=case["company"],
                synthetic_registration_id=reg_id,
                scenario_key=sid,
            )
            db.add(company)
            db.flush()
        else:
            company.synthetic_name = case["company"]
            company.scenario_key = sid

        login = f"client.{sid}@demo.local"
        user = db.query(User).filter(User.demo_login == login).first()
        if user is None:
            db.add(
                User(
                    role=UserRole.customer,
                    company_id=company.id,
                    demo_login=login,
                    password_hash=hash_password(DEMO_PASSWORD),
                    full_name=f"Клиент сценария {sid}",
                )
            )
            created_logins.append(login)
        else:
            user.role = UserRole.customer
            user.company_id = company.id
            user.password_hash = hash_password(DEMO_PASSWORD)
            user.full_name = f"Клиент сценария {sid}"
            created_logins.append(f"repaired:{login}")

    db.commit()
    return {
        "seeded": True,
        "logins": created_logins or ["repaired"],
        "complete": _seed_complete(db, settings.rules_version),
    }
