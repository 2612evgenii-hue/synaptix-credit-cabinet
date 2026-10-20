"""Local deterministic simulators. Technical failure is never a credit rejection."""

from __future__ import annotations

from typing import Any

from synaptix_api.analytics.types import CheckOutcome

MOCK_VERSION = "local-mock-v1"
# Fixed timestamp for reproducible payloads (not wall-clock)
CHECKED_AT = "1970-01-01T00:00:00+00:00"

REGISTRY: dict[str, dict[str, Any]] = {
    "approval": {"found": True, "status": "active"},
    "clarification": {"found": True, "status": "active"},
    "rejection": {"found": True, "status": "active"},
    "bureau_down": {"found": True, "status": "active"},
    "inactive": {"found": True, "status": "liquidating"},
}

BUREAU: dict[str, dict[str, Any]] = {
    "approval": {"status": "ok", "overdue_days": 0, "obligations": 1},
    "clarification": {"status": "ok", "overdue_days": 0, "obligations": 0},
    "rejection": {"status": "negative", "overdue_days": 90, "obligations": 3},
    "bureau_down": {"status": "unavailable", "error": "simulator_timeout"},
    "inactive": {"status": "ok", "overdue_days": 0, "obligations": 0},
}


def _registry_found(raw: object) -> bool:
    """Presence flag: reject truthy string 'false' / '0' / 'no' as not-found."""
    if raw is True:
        return True
    if raw is False or raw is None:
        return False
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)):
        return raw != 0 and raw == raw  # reject NaN via != self
    if isinstance(raw, str):
        normalized = raw.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        return False
    return False


def run_registry_check(scenario_key: str, registration_id: str) -> CheckOutcome:
    profile = REGISTRY.get(scenario_key)
    if profile is None:
        return CheckOutcome(
            source="company_registry",
            status="missing_data",
            mock_version=MOCK_VERSION,
            payload={"error": "unknown_scenario", "registration_id": registration_id},
        )
    # Adverse legal/entity states → credit-negative. Soft/unknown pass through
    # so decision can map them to CHECK_UNAVAILABLE / NEEDS_INFO (never invent deny).
    ADVERSE_ENTITY = frozenset({"liquidating", "liquidated", "bankrupt", "dissolved", "inactive"})

    if "status" not in profile:
        status = "missing_data"
    else:
        profile_status = profile.get("status")
        # Soft technical statuses win even when ``found`` is omitted.
        if profile_status in {"unavailable", "missing_data"}:
            status = profile_status
        elif "found" not in profile:
            # Presence flag absent → incomplete profile, not company-not-found.
            status = "missing_data"
        elif not _registry_found(profile.get("found")):
            status = "negative"
        elif profile_status == "active":
            status = "ok"
        elif profile_status in (None, ""):
            status = "missing_data"
        elif isinstance(profile_status, str) and profile_status in ADVERSE_ENTITY:
            status = "negative"
        else:
            # pending / error / other incomplete — pass through (not credit-negative)
            status = profile_status  # type: ignore[assignment]
    return CheckOutcome(
        source="company_registry",
        status=status,  # type: ignore[arg-type]
        mock_version=MOCK_VERSION,
        payload={
            **profile,
            "registration_id": registration_id,
            "checked_at": CHECKED_AT,
        },
    )


def run_bureau_check(scenario_key: str, *, force_unavailable: bool = False) -> CheckOutcome:
    if force_unavailable:
        return CheckOutcome(
            source="credit_bureau",
            status="unavailable",
            mock_version=MOCK_VERSION,
            payload={"error": "forced_timeout", "checked_at": CHECKED_AT},
        )
    profile = BUREAU.get(scenario_key)
    if profile is None:
        return CheckOutcome(
            source="credit_bureau",
            status="missing_data",
            mock_version=MOCK_VERSION,
            payload={"error": "unknown_scenario"},
        )
    # Missing key → degrade like registry (.get); unknown present values still
    # pass through so decision can map them to NEEDS_INFO / CHECKS_INCOMPLETE.
    if "status" not in profile:
        return CheckOutcome(
            source="credit_bureau",
            status="missing_data",
            mock_version=MOCK_VERSION,
            payload={**profile, "error": "incomplete_bureau_profile", "checked_at": CHECKED_AT},
        )
    return CheckOutcome(
        source="credit_bureau",
        status=profile["status"],  # type: ignore[arg-type]
        mock_version=MOCK_VERSION,
        payload={**profile, "checked_at": CHECKED_AT},
    )
