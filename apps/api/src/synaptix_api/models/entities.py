"""ORM entities aligned with docs/data-model.md. Money = minor units (kopecks)."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

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
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from synaptix_api.db.base import Base


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


# JSON that works on SQLite tests and PostgreSQL demo
JsonType = JSON().with_variant(JSONB(), "postgresql")


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
    REJECTED = "REJECTED"
    ACCEPTED = "ACCEPTED"
    SIGNED_SIMULATED = "SIGNED_SIMULATED"
    DISBURSED_SIMULATED = "DISBURSED_SIMULATED"


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    synthetic_name: Mapped[str] = mapped_column(String(255), nullable=False)
    synthetic_registration_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    scenario_key: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    users: Mapped[list[User]] = relationship(back_populates="company")
    applications: Mapped[list[Application]] = relationship(back_populates="company")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False, index=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    demo_login: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    company: Mapped[Company | None] = relationship(back_populates="users")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
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

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), index=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=True
    )
    amount_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    term_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[ApplicationState] = mapped_column(
        Enum(ApplicationState, name="application_state"),
        default=ApplicationState.DRAFT,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    clarification_request: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    company: Mapped[Company] = relationship(back_populates="applications")
    events: Mapped[list[ApplicationEvent]] = relationship(back_populates="application")


class FinancialSnapshot(Base):
    __tablename__ = "financial_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), index=True
    )
    revenue_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    expenses_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    liabilities_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), index=True
    )
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class CheckResult(Base):
    __tablename__ = "check_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), index=True
    )
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    mock_version: Mapped[str] = mapped_column(String(64), nullable=False)
    result: Mapped[dict] = mapped_column(JsonType, default=dict)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), index=True
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    factors: Mapped[dict] = mapped_column(JsonType, default=dict)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), index=True
    )
    outcome: Mapped[str] = mapped_column(String(64), nullable=False)
    reason_codes: Mapped[list] = mapped_column(JsonType, default=list)
    offered_terms: Mapped[dict] = mapped_column(JsonType, default=dict)
    rules_version: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ApplicationEvent(Base):
    __tablename__ = "application_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), index=True
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    old_state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    new_state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    payload: Mapped[dict] = mapped_column(JsonType, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, index=True
    )

    application: Mapped[Application] = relationship(back_populates="events")


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (UniqueConstraint("actor_id", "route", "key", name="uq_idempotency"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    actor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    route: Mapped[str] = mapped_column(String(128), nullable=False)
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    response: Mapped[dict] = mapped_column(JsonType, default=dict)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
