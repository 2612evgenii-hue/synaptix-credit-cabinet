"""Attack: incomplete BUREAU profile (no status key) KeyErrors in run_bureau_check."""

import pytest

from synaptix_api.analytics.mocks import BUREAU, run_bureau_check, run_registry_check


def test_adv7_bureau_profile_missing_status_must_not_crash():
    """
    Cycle 5 monkeypatched BUREAU with status='pending' (unknown → NEEDS_INFO).
    Registry profiles use ``.get("status")`` and degrade safely; bureau uses
    ``profile["status"]`` so a profile missing the key aborts with KeyError
    instead of a CheckOutcome (missing_data / incomplete).
    """
    BUREAU["adv7_broken"] = {"overdue_days": 0, "obligations": 0}
    try:
        try:
            outcome = run_bureau_check("adv7_broken")
        except KeyError as exc:
            pytest.fail(
                f"BUREAU profile without 'status' raised KeyError({exc!r}); "
                "run_bureau_check must return a CheckOutcome (e.g. missing_data), "
                    f"as registry does via .get; registry smoke: "
                f"{run_registry_check('approval', 'SYN-ADV7-MOCK').status}"
            )
        assert outcome.status in {
            "ok",
            "negative",
            "unavailable",
            "missing_data",
        }, f"unexpected status {outcome.status!r} payload={outcome.payload}"
    finally:
        BUREAU.pop("adv7_broken", None)
