"""Attack: DecisionResult outcomes ALTERNATIVE / CHECK_UNAVAILABLE ∉ ApplicationState."""

from typing import get_args, get_type_hints

from synaptix_api.analytics.types import DecisionResult
from synaptix_api.models.entities import ApplicationState


def test_adv2_decision_outcomes_must_map_to_application_state():
    """
    Analytics can emit ALTERNATIVE and CHECK_UNAVAILABLE. Application.state enum
    (and OpenAPI) omit both — no legal ApplicationState for those decisions.
    """
    outcome_hint = get_type_hints(DecisionResult)["outcome"]
    decision_outcomes = set(get_args(outcome_hint))
    app_states = {s.value for s in ApplicationState}

    missing = decision_outcomes - app_states
    assert not missing, (
        f"Decision outcomes with no ApplicationState: {sorted(missing)}. "
        f"Cannot persist decision.outcome onto application.state for these paths."
    )
