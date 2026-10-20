#!/usr/bin/env python3
"""AI01: upgrade → seed → re-upgrade → re-seed → write demo rows → reconnect → read.

Requires DATABASE_URL pointing at a clean Postgres (see docker-compose.postgres-verify.yml).
Records evidence under docs/evidence/ when --write-log is set.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parents[1]
sys.path.insert(0, str(API_ROOT / "src"))


def _run(cmd: list[str], env: dict[str, str]) -> str:
    proc = subprocess.run(
        cmd,
        cwd=str(API_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        raise RuntimeError(f"cmd failed ({proc.returncode}): {cmd}\n{out}")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--database-url",
        default=os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg2://synaptix:synaptix@127.0.0.1:54329/synaptix_verify",
        ),
    )
    parser.add_argument("--write-log", action="store_true")
    args = parser.parse_args()

    env = os.environ.copy()
    env["DATABASE_URL"] = args.database_url
    env["APP_ENV"] = "demo"
    env["PYTHONPATH"] = str(API_ROOT / "src")
    env["LLM_BACKEND"] = "template"

    log: dict = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "database_url_host": args.database_url.split("@")[-1],
        "steps": [],
    }

    for label, cmd in (
        ("upgrade_1", [sys.executable, "-m", "alembic", "upgrade", "head"]),
        ("upgrade_2_idempotent", [sys.executable, "-m", "alembic", "upgrade", "head"]),
        ("current", [sys.executable, "-m", "alembic", "current"]),
    ):
        out = _run(cmd, env)
        log["steps"].append({"step": label, "ok": True, "output": out.strip()[-500:]})

    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    from synaptix_api.analytics.pipeline import ProductLimits, run_analytics
    from synaptix_api.analytics.persist import store_check, store_decision, store_risk
    from synaptix_api.analytics.types import FinancialInput
    from synaptix_api.db.seed import seed_demo
    from synaptix_api.models import Application, Decision, FinancialSnapshot, Product, User
    from synaptix_api.models.entities import ApplicationState
    from synaptix_api.settings import get_settings

    get_settings.cache_clear()
    engine = create_engine(args.database_url)

    with Session(engine) as db:
        first = seed_demo(db)
        second = seed_demo(db)
        log["steps"].append({"step": "seed", "first": first, "second": second})
        assert first["seeded"] is True
        assert second["seeded"] is False

        customer = db.query(User).filter(User.demo_login == "client.approval@demo.local").one()
        product = db.query(Product).filter_by(code="working_capital").one()
        assert product.product_version is not None
        assert product.allowed_goals is not None

        app = Application(
            company_id=customer.company_id,
            created_by=customer.id,
            product_id=product.id,
            amount_minor=50_000_000,
            term_months=12,
            purpose="working_capital",
            state=ApplicationState.SUBMITTED,
            version=1,
        )
        db.add(app)
        db.flush()
        snap = FinancialSnapshot(
            application_id=app.id,
            revenue_minor=300_000_000,
            expenses_minor=150_000_000,
            liabilities_minor=10_000_000,
            debt_service_monthly_minor=0,
            period_label="month",
        )
        db.add(snap)
        db.flush()

        bundle = run_analytics(
            scenario_key="approval",
            registration_id="SYN-APPROVAL",
            finances=FinancialInput(
                revenue_minor=300_000_000,
                expenses_minor=150_000_000,
                liabilities_minor=10_000_000,
                amount_minor=50_000_000,
                term_months=12,
            ),
            product=ProductLimits(
                min_amount_minor=product.min_amount_minor,
                max_amount_minor=product.max_amount_minor,
                min_term_months=product.min_term_months,
                max_term_months=product.max_term_months,
                demo_rate_annual=product.demo_rate_annual or 0.16,
            ),
        )
        store_check(db, app.id, bundle.registry)
        store_check(db, app.id, bundle.bureau)
        store_risk(db, app.id, bundle.risk)
        store_decision(
            db,
            app.id,
            bundle.decision,
            explanation=bundle.explanation,
            financial_snapshot_id=snap.id,
            product_code=product.code,
            application_version=app.version,
        )
        db.commit()
        app_id = app.id
        snap_id = snap.id

    # Failed transaction must rollback without poisoning session
    with Session(engine) as db:
        try:
            with db.begin():
                db.execute(text("INSERT INTO products (id, code) VALUES (:id, :code)"), {
                    "id": str(uuid.uuid4()),
                    "code": "working_capital",  # unique violation
                })
        except Exception as exc:  # noqa: BLE001
            log["steps"].append({"step": "rollback_unique", "ok": True, "error": type(exc).__name__})

    # Reconnect and read
    with Session(engine) as db:
        row = db.query(Decision).filter_by(application_id=app_id).one()
        assert row.financial_snapshot_id == snap_id
        assert row.product_code == "working_capital"
        assert db.query(FinancialSnapshot).filter_by(id=snap_id).one().period_label == "month"
        # Re-seed must not delete user demo application
        before = db.query(Application).filter_by(id=app_id).count()
        seed_demo(db)
        after = db.query(Application).filter_by(id=app_id).count()
        assert before == after == 1
        log["steps"].append(
            {
                "step": "reconnect_read",
                "decision_outcome": row.outcome,
                "snapshot_bound": True,
                "application_preserved_after_reseed": True,
            }
        )

    log["finished_at"] = datetime.now(timezone.utc).isoformat()
    log["ok"] = True
    print(json.dumps(log, ensure_ascii=False, indent=2))

    if args.write_log:
        out_dir = REPO_ROOT / "docs" / "evidence"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "ai01-postgres-verify.json"
        path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"AI01 verify FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
