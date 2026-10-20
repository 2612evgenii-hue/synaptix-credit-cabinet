"""Unit tests for post-decision open-weight / template explanations."""

from synaptix_api.analytics.explain import explain_decision, render_template_explanation
from synaptix_api.analytics.pipeline import ProductLimits, run_analytics
from synaptix_api.analytics.types import DecisionResult, FinancialInput, RiskResult
from synaptix_api.settings import get_settings


def _decision(outcome: str = "APPROVED") -> DecisionResult:
    return DecisionResult(
        outcome=outcome,  # type: ignore[arg-type]
        reason_codes=["K_PASS", "RISK_OK", "CHECKS_OK"]
        if outcome == "APPROVED"
        else ["BUREAU_OVERDUE"],
        offered_terms={},
        rules_version="demo-rules-v1",
        metrics={"coverage_k": 1.5},
    )


def test_template_explanation_always_available():
    risk = RiskResult(score=70, factors={}, model_version="demo-risk-v1")
    expl = render_template_explanation(_decision("REJECTED"), risk)
    assert expl.used_llm is False
    assert expl.backend == "template"
    assert "отклон" in expl.text_client.lower()
    assert "BUREAU_OVERDUE" in expl.text_bank


def test_pipeline_includes_explanation_without_ollama(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "template")
    get_settings.cache_clear()
    bundle = run_analytics(
        scenario_key="approval",
        registration_id="SYN-EXPLAIN",
        finances=FinancialInput(
            revenue_minor=900_000_00,
            expenses_minor=500_000_00,
            liabilities_minor=45_000_00,
            amount_minor=1_500_000_00,
            term_months=36,
        ),
        product=ProductLimits(min_amount_minor=500_000_00, max_amount_minor=10_000_000_00),
    )
    assert bundle.decision.outcome == "APPROVED"
    assert bundle.explanation.text_client
    assert bundle.explanation.used_llm is False


def test_ollama_success_path(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.setenv("LLM_MODEL", "tinyllama")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:11434")
    get_settings.cache_clear()

    def fake_post(url, payload, timeout):
        assert "11434" in url
        assert payload["model"] == "tinyllama"
        return {
            "message": {
                "content": "Заявка одобрена. Поток покрывает платёж, проверки пройдены."
            }
        }

    expl = explain_decision(_decision("APPROVED"), RiskResult(70, {}, "v"), http_post=fake_post)
    assert expl.used_llm is True
    assert expl.backend == "ollama"
    assert "одобр" in expl.text_client.lower()


def test_ollama_failure_falls_back_to_template(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.setenv("LLM_MODEL", "tinyllama")
    get_settings.cache_clear()

    def boom(url, payload, timeout):
        raise TimeoutError("llm down")

    expl = explain_decision(_decision("APPROVED"), RiskResult(70, {}, "v"), http_post=boom)
    assert expl.used_llm is False
    assert expl.backend == "template"
    assert expl.fallback_reason == "llm_unavailable_or_invalid"


def test_blocked_cloud_host_falls_back(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("LLM_MODEL", "gpt-4")
    get_settings.cache_clear()
    expl = explain_decision(_decision("APPROVED"), RiskResult(70, {}, "v"))
    assert expl.used_llm is False
    assert expl.fallback_reason == "llm_host_not_allowed"
