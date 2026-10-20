"""Idempotent synthetic seed for APP_ENV=demo. Not production data."""

from __future__ import annotations

import json
from pathlib import Path

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from synaptix_api.models import Company, Product, User
from synaptix_api.models.entities import UserRole
from synaptix_api.settings import get_settings

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
DEMO_PASSWORD = "demo1234"

REPO_ROOT = Path(__file__).resolve().parents[5]
SCENARIOS = REPO_ROOT / "data" / "synthetic" / "scenarios.json"


def seed_demo(db: Session) -> None:
    settings = get_settings()
    if settings.app_env != "demo":
        raise RuntimeError("Seed allowed only when APP_ENV=demo")

    if db.query(User).filter(User.demo_login == "bank.officer@demo.local").first():
        return

    officer = User(
        role=UserRole.bank,
        company_id=None,
        demo_login="bank.officer@demo.local",
        password_hash=pwd.hash(DEMO_PASSWORD),
        full_name="Синтетический сотрудник банка",
    )
    db.add(officer)

    db.add(
        Product(
            code="working_capital",
            name="Оборотные средства (демо)",
            min_amount_minor=300_000_00,
            max_amount_minor=5_000_000_00,
            min_term_months=6,
            max_term_months=36,
            rules_version=settings.rules_version,
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
            rules_version=settings.rules_version,
        )
    )

    payload = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    for case in payload["cases"]:
        company = Company(
            synthetic_name=case["company"],
            synthetic_registration_id=f"SYN-{case['id'].upper()}",
            scenario_key=case["id"],
        )
        db.add(company)
        db.flush()
        db.add(
            User(
                role=UserRole.customer,
                company_id=company.id,
                demo_login=f"client.{case['id']}@demo.local",
                password_hash=pwd.hash(DEMO_PASSWORD),
                full_name=f"Клиент сценария {case['id']}",
            )
        )

    db.commit()
