"""Attack: polarity-blind outcome cues accept negated / antonym narration as used_llm=True."""

import pytest

from synaptix_api.analytics.explain import explain_decision
from synaptix_api.analytics.types import DecisionResult, RiskResult
from synaptix_api.settings import get_settings


def _decision(outcome: str, reasons: list[str] | None = None) -> DecisionResult:
    return DecisionResult(
        outcome=outcome,  # type: ignore[arg-type]
        reason_codes=reasons or ["K_PASS"],
        offered_terms={},
        rules_version="demo-rules-v1",
        metrics={},
    )


@pytest.mark.parametrize(
    ("outcome", "reasons", "text"),
    [
        (
            "APPROVED",
            ["K_PASS", "RISK_OK", "CHECKS_OK"],
            "Заявка не одобрена.",
        ),
        (
            "APPROVED",
            ["K_PASS", "RISK_OK", "CHECKS_OK"],
            "Application not approved.",
        ),
        (
            "APPROVED",
            ["K_PASS", "RISK_OK", "CHECKS_OK"],
            "Application approved; request denied.",
        ),
        (
            "NEEDS_INFO",
            ["CHECKS_INCOMPLETE"],
            "Уточнение не требуется; данные полные.",
        ),
    ],
)
def test_adv16_negated_outcome_cues_must_not_set_used_llm(
    monkeypatch, outcome, reasons, text
):
    """
    Invariant: LLM client text that negates or antonyms DecisionResult.outcome
    must not be accepted as used_llm=True.

    A1/A2 closed dual-family and soft cross-outcome cues. Cue matching is still
    substring-only with no polarity: «не одобрена» / «not approved» still trip
    _CUE_APPROVE via «одобр»/«approv», and English «denied» is absent from
    _CUE_REJECT — so contradictory narration audits as accepted LLM text.
    """
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.setenv("LLM_MODEL", "tinyllama")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:11434")
    get_settings.cache_clear()

    def fake_post(url, payload, timeout):
        return {"message": {"content": text}}

    expl = explain_decision(
        _decision(outcome, reasons),
        RiskResult(score=70, factors={}, model_version="adv16"),
        http_post=fake_post,
    )
    assert expl.used_llm is False, (
        f"negated/antonym cues for {outcome} must force template fallback; "
        f"got used_llm={expl.used_llm} backend={expl.backend!r} text={expl.text_client!r}"
    )
    assert expl.backend == "template"
    assert expl.fallback_reason == "llm_unavailable_or_invalid"
