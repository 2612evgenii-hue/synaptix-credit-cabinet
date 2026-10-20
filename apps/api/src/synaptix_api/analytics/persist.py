"""Persist analytics outputs into ORM tables (used by API layer later)."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from synaptix_api.analytics.types import CheckOutcome, DecisionResult, RiskResult
from synaptix_api.models import CheckResult, Decision, RiskAssessment


def store_check(db: Session, application_id: uuid.UUID, outcome: CheckOutcome) -> CheckResult:
    row = CheckResult(
        application_id=application_id,
        source=outcome.source,
        mock_version=outcome.mock_version,
        # status from CheckOutcome wins — payload must not clobber it
        result={**outcome.payload, "status": outcome.status},
    )
    db.add(row)
    db.flush()
    return row


def store_risk(db: Session, application_id: uuid.UUID, risk: RiskResult) -> RiskAssessment:
    row = RiskAssessment(
        application_id=application_id,
        score=risk.score,
        factors=risk.factors,
        model_version=risk.model_version,
    )
    db.add(row)
    db.flush()
    return row


def store_decision(
    db: Session,
    application_id: uuid.UUID,
    decision: DecisionResult,
    *,
    actor_id: uuid.UUID | None = None,
) -> Decision:
    row = Decision(
        application_id=application_id,
        outcome=decision.outcome,
        reason_codes=list(decision.reason_codes),
        offered_terms=dict(decision.offered_terms),
        metrics=dict(decision.metrics),
        rules_version=decision.rules_version,
        actor_id=actor_id,
    )
    db.add(row)
    db.flush()
    return row
