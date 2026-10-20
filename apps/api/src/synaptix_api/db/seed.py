"""Idempotent synthetic seed for APP_ENV=demo. Not production data.

Product catalog source of truth: data/products.json (D11 / AI02).
"""

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
PRODUCTS_JSON = REPO_ROOT / "data" / "products.json"


def _load_catalog() -> dict:
    return json.loads(PRODUCTS_JSON.read_text(encoding="utf-8"))


def _catalog_products() -> list[dict]:
    return list(_load_catalog()["products"])


# Backward-compatible tuple used by adversarial seed tests
CANONICAL_PRODUCTS = tuple(
    (
        p["code"],
        p["name"],
        int(p["min_amount_minor"]),
        int(p["max_amount_minor"]),
        int(p["min_term_months"]),
        int(p["max_term_months"]),
    )
    for p in _catalog_products()
)


def _scenarios() -> list[dict]:
    return json.loads(SCENARIOS.read_text(encoding="utf-8"))["cases"]


def _product_matches(row: Product, spec: dict, rules: str) -> bool:
    return (
        row.active
        and row.min_amount_minor == int(spec["min_amount_minor"])
        and row.max_amount_minor == int(spec["max_amount_minor"])
        and row.min_term_months == int(spec["min_term_months"])
        and row.max_term_months == int(spec["max_term_months"])
        and row.rules_version == rules
        and row.demo_rate_annual == float(spec.get("demo_rate_annual") or 0)
        and row.product_version == spec.get("version")
        and row.allowed_goals == spec.get("allowed_goals")
        and row.required_fields == spec.get("required_fields")
    )


def _officer_identity_ok(user: User | None) -> bool:
    return (
        user is not None
        and user.role == UserRole.bank
        and user.company_id is None
        and verify_password(DEMO_PASSWORD, user.password_hash)
    )


def _apply_product_fields(row: Product, spec: dict, rules: str) -> None:
    row.active = True
    row.name = spec["name"]
    row.min_amount_minor = int(spec["min_amount_minor"])
    row.max_amount_minor = int(spec["max_amount_minor"])
    row.min_term_months = int(spec["min_term_months"])
    row.max_term_months = int(spec["max_term_months"])
    row.rules_version = rules
    row.demo_rate_annual = float(spec["demo_rate_annual"]) if spec.get("demo_rate_annual") is not None else None
    row.product_version = spec.get("version")
    row.allowed_goals = list(spec.get("allowed_goals") or [])
    row.required_fields = list(spec.get("required_fields") or [])
    row.fit_note = spec.get("fit_note")


def _seed_complete(db: Session, rules_version: str) -> bool:
    officer = db.query(User).filter(User.demo_login == "bank.officer@demo.local").first()
    if not _officer_identity_ok(officer):
        return False
    for spec in _catalog_products():
        row = db.query(Product).filter_by(code=spec["code"]).first()
        if row is None or not _product_matches(row, spec, rules_version):
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
    if not PRODUCTS_JSON.is_file():
        raise FileNotFoundError(f"Missing products catalog: {PRODUCTS_JSON}")

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

    for spec in _catalog_products():
        row = db.query(Product).filter_by(code=spec["code"]).first()
        if row is None:
            row = Product(code=spec["code"], name=spec["name"], rules_version=settings.rules_version,
                          min_amount_minor=int(spec["min_amount_minor"]),
                          max_amount_minor=int(spec["max_amount_minor"]),
                          min_term_months=int(spec["min_term_months"]),
                          max_term_months=int(spec["max_term_months"]))
            db.add(row)
        _apply_product_fields(row, spec, settings.rules_version)

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
        "catalog_source": str(PRODUCTS_JSON.as_posix()),
    }
