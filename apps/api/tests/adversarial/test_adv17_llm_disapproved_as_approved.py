"""Attack: reject-meaning English stems still trip _CUE_APPROVE via «approv»."""

import pytest

from synaptix_api.analytics.explain import explain_decision
from synaptix_api.analytics.types import DecisionResult, RiskResult
from synaptix_api.settings import get_settings


def _approved() -> DecisionResult:
    return DecisionResult(
        outcome="APPROVED",
        reason_codes=["K_PASS", "RISK_OK", "CHECKS_OK"],
        offered_terms={},
        rules_version="demo-rules-v1",
        metrics={},
    )


@pytest.mark.parametrize(
    "text",
    [
        "Application disapproved.",
        "Application unapproved.",
        "This request is disapproved by the committee.",
    ],
)
def test_adv17_reject_meaning_approv_stem_must_not_set_used_llm(monkeypatch, text):
    """
    Invariant: narration that denies approval must not audit as used_llm=True
    for DecisionResult.outcome == APPROVED (reverse of false-APPROVED-on-REJECTED).

    A3 closed spaced polarity («not approved» / «не одобрена»). Prefix forms
    «disapproved» / «unapproved» still contain substring «approv», pass
    _has_positive_cue, and are accepted as LLM client text for APPROVED.
    """
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.setenv("LLM_MODEL", "tinyllama")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:11434")
    get_settings.cache_clear()

    def fake_post(url, payload, timeout):
        return {"message": {"content": text}}

    expl = explain_decision(
        _approved(),
        RiskResult(score=70, factors={}, model_version="adv17"),
        http_post=fake_post,
    )
    assert expl.used_llm is False, (
        f"reject-meaning text for APPROVED must force template fallback; "
        f"got used_llm={expl.used_llm} backend={expl.backend!r} text={expl.text_client!r}"
    )
    assert expl.backend == "template"
    assert expl.fallback_reason == "llm_unavailable_or_invalid"
