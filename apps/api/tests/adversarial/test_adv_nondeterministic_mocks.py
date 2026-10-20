"""Attack: mock checks embed datetime.now — same inputs yield unequal persisted payloads."""

import time

from synaptix_api.analytics.mocks import run_bureau_check, run_registry_check


def test_adv_registry_check_payload_not_deterministic():
    a = run_registry_check("approval", "SYN-ADV")
    time.sleep(0.01)
    b = run_registry_check("approval", "SYN-ADV")

    assert a.status == b.status
    # Audit/analytics invariant: identical inputs must produce identical check payloads
    assert a.payload == b.payload, (
        "registry mock injects checked_at=datetime.now; payloads diverge for same inputs "
        f"{a.payload.get('checked_at')!r} vs {b.payload.get('checked_at')!r}"
    )


def test_adv_bureau_check_payload_not_deterministic():
    a = run_bureau_check("approval")
    time.sleep(0.01)
    b = run_bureau_check("approval")

    assert a.status == b.status
    assert a.payload == b.payload, (
        "bureau mock injects checked_at=datetime.now; payloads diverge for same inputs "
        f"{a.payload.get('checked_at')!r} vs {b.payload.get('checked_at')!r}"
    )
