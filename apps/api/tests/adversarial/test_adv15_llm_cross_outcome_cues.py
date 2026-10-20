"""Attack: LLM text with wrong-family outcome cues still accepted as used_llm=True."""

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
            "Заявка одобрена; предложена альтернативная сумма.",
        ),
        (
            "APPROVED",
            ["K_PASS", "RISK_OK", "CHECKS_OK"],
            "Заявка одобрена и требует уточнения данных.",
        ),
        (
            "REJECTED",
            ["BUREAU_NEGATIVE"],
            "Заявка отклонена из-за технической недоступности проверки.",
        ),
    ],
)
def test_adv15_cross_outcome_cues_must_not_set_used_llm(
    monkeypatch, outcome, reasons, text
):
    """
    Invariant: LLM client text must not claim a different outcome family than
    DecisionResult.outcome (used_llm=True would audit a lying narration).

    A1 closed approve↔reject duals and NEEDS_INFO/CHECK_UNAVAILABLE false
    terminals. Soft cross-cues (APPROVED+alt/needs, REJECTED+unavailable) still
    pass _validate_llm_client_text.
    """
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.setenv("LLM_MODEL", "tinyllama")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:11434")
    get_settings.cache_clear()

    def fake_post(url, payload, timeout):
        return {"message": {"content": text}}

    expl = explain_decision(
        _decision(outcome, reasons),
        RiskResult(score=70, factors={}, model_version="adv15"),
        http_post=fake_post,
    )
    assert expl.used_llm is False, (
        f"cross-outcome cues for {outcome} must force template fallback; "
        f"got used_llm={expl.used_llm} backend={expl.backend!r} text={expl.text_client!r}"
    )
    assert expl.backend == "template"
    assert expl.fallback_reason == "llm_unavailable_or_invalid"
