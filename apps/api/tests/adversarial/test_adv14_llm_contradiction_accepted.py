"""Attack: contradicting LLM narration still accepted as used_llm=True."""

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


def test_adv14_contradictory_approved_text_must_not_set_used_llm(monkeypatch):
    """
    Invariant: LLM text that contradicts DecisionResult.outcome must not be
    accepted as used_llm=True (fall back to template instead).

    _validate_llm_client_text skips conflict tokens when the RU outcome phrase
    is also present, so dual-cue contradictions pass validation.
    """
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.setenv("LLM_MODEL", "tinyllama")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:11434")
    get_settings.cache_clear()

    contradictory = "Заявка одобрена, но отклонена комитетом."

    def fake_post(url, payload, timeout):
        return {"message": {"content": contradictory}}

    expl = explain_decision(
        _decision("APPROVED", ["K_PASS", "RISK_OK", "CHECKS_OK"]),
        RiskResult(score=70, factors={}, model_version="adv14"),
        http_post=fake_post,
    )
    assert expl.used_llm is False, (
        "LLM client text that both approves and rejects must not set used_llm=True; "
        f"got used_llm={expl.used_llm} backend={expl.backend!r} text={expl.text_client!r}"
    )
    assert expl.backend == "template"
    assert expl.fallback_reason == "llm_unavailable_or_invalid"


def test_adv14_needs_info_must_not_accept_false_approval_narration(monkeypatch):
    """NEEDS_INFO has no conflict tokens — approval language + soft cue passes."""
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.setenv("LLM_MODEL", "tinyllama")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:11434")
    get_settings.cache_clear()

    def fake_post(url, payload, timeout):
        return {
            "message": {
                "content": "Заявка одобрена после уточнения данных."
            }
        }

    expl = explain_decision(
        _decision("NEEDS_INFO", ["CHECKS_INCOMPLETE"]),
        RiskResult(score=70, factors={}, model_version="adv14"),
        http_post=fake_post,
    )
    assert expl.used_llm is False, (
        "NEEDS_INFO explanation claiming approval must not set used_llm=True; "
        f"got used_llm={expl.used_llm} text={expl.text_client!r}"
    )


def test_adv14_check_unavailable_must_not_accept_credit_rejection_narration(monkeypatch):
    """
    CHECK_UNAVAILABLE conflict list looks for the phrase 'отклонён кредит'
    (wrong word order); 'кредит отклонён' still claims a hard reject.
    """
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.setenv("LLM_MODEL", "tinyllama")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:11434")
    get_settings.cache_clear()

    def fake_post(url, payload, timeout):
        return {
            "message": {
                "content": "Проверка временно недоступна; кредит отклонён банком."
            }
        }

    expl = explain_decision(
        _decision("CHECK_UNAVAILABLE", ["CHECK_TECHNICAL_FAILURE"]),
        RiskResult(score=70, factors={}, model_version="adv14"),
        http_post=fake_post,
    )
    assert expl.used_llm is False, (
        "CHECK_UNAVAILABLE must not accept narration that the credit was rejected; "
        f"got used_llm={expl.used_llm} text={expl.text_client!r}"
    )
