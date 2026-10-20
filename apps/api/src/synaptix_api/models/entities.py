"""ORM entities aligned with docs/data-model.md. Money = minor units (kopecks)."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from synaptix_api.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class UserRole(str, enum.Enum):
    customer = "customer"
    bank = "bank"


class ApplicationState(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    VALIDATING = "VALIDATING"
    NEEDS_INFO = "NEEDS_INFO"
    SCORING = "SCORING"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    ALTERNATIVE = "ALTERNATIVE"
    CHECK_UNAVAILABLE = "CHECK_UNAVAILABLE"
    REJECTED = "REJECTED"
    ACCEPTED = "ACCEPTED"
    SIGNED_SIMULATED = "SIGNED_SIMULATED"
    DISBURSED_SIMULATED = "DISBURSED_SIMULATED"


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    synthetic_name: Mapped[str] = mapped_column(String(255), nullable=False)
    synthetic_registration_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    scenario_key: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    users: Mapped[list[User]] = relationship(back_populates="company")
    applications: Mapped[list[Application]] = relationship(back_populates="company")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("companies.id"), nullable=True)
    demo_login: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    company: Mapped[Company | None] = relationship(back_populates="users")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    min_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    max_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    min_term_months: Mapped[int] = mapped_column(Integer, nullable=False)
    max_term_months: Mapped[int] = mapped_column(Integer, nullable=False)
    rules_version: Mapped[str] = mapped_column(String(64), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("companies.id"), index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"))
    product_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("products.id"), nullable=True)
    amount_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    term_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[ApplicationState] = mapped_column(
        Enum(ApplicationState, name="application_state", native_enum=False),
        default=ApplicationState.DRAFT,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    clarification_request: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    company: Mapped[Company] = relationship(back_populates="applications")
    product: Mapped[Product | None] = relationship()
    events: Mapped[list[ApplicationEvent]] = relationship(back_populates="application")
    snapshots: Mapped[list[FinancialSnapshot]] = relationship(back_populates="application")
    decisions: Mapped[list[Decision]] = relationship(back_populates="application")
    assessments: Mapped[list[RiskAssessment]] = relationship(back_populates="application")
    checks: Mapped[list[CheckResult]] = relationship(back_populates="application")


class FinancialSnapshot(Base):
    __tablename__ = "financial_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    application_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("applications.id"), index=True)
    revenue_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    expenses_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    liabilities_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    application: Mapped[Application] = relationship(back_populates="snapshots")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    application_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("applications.id"), index=True)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CheckResult(Base):
    __tablename__ = "check_results"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    application_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("applications.id"), index=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    mock_version: Mapped[str] = mapped_column(String(64), nullable=False)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    application: Mapped[Application] = relationship(back_populates="checks")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    application_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("applications.id"), index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    factors: Mapped[dict] = mapped_column(JSON, default=dict)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    application: Mapped[Application] = relationship(back_populates="assessments")


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    application_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("applications.id"), index=True)
    outcome: Mapped[str] = mapped_column(String(64), nullable=False)
    reason_codes: Mapped[list] = mapped_column(JSON, default=list)
    offered_terms: Mapped[dict] = mapped_column(JSON, default=dict)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    rules_version: Mapped[str] = mapped_column(String(64), nullable=False)
    # Post-hoc open-weight / template narration — never input to credit rules
    explanation_client: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation_bank: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_meta: Mapped[dict] = mapped_column(JSON, default=dict)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    application: Mapped[Application] = relationship(back_populates="decisions")


class ApplicationEvent(Base):
    __tablename__ = "application_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    application_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("applications.id"), index=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    old_state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    new_state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    application: Mapped[Application] = relationship(back_populates="events")


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (UniqueConstraint("actor_id", "route", "key", name="uq_idempotency"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    actor_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    route: Mapped[str] = mapped_column(String(128), nullable=False)
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    response: Mapped[dict] = mapped_column(JSON, default=dict)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
