"""Attack: paid/cloud LLM brand hosts allowed via .local suffix (A1 short-host fix gap)."""

import pytest

from synaptix_api.analytics.explain import _host_allowed, explain_decision
from synaptix_api.analytics.types import DecisionResult, RiskResult
from synaptix_api.settings import get_settings

# A1 blocked bare short names (openai, openrouter, …). Suffix allowlist still
# accepts the same brands as *.local — FQDN fragments never match.
_PAID_LOCAL_HOSTS = (
    "openai.local",
    "openrouter.local",
    "anthropic.local",
    "groq.local",
    "api.openai.local",
    "gemini.local",
)


@pytest.mark.parametrize("host", _PAID_LOCAL_HOSTS)
def test_adv15_paid_cloud_local_suffix_must_not_be_allowed(host):
    """
    Invariant: paid/cloud LLM hosts must be blocked.

    _BLOCKED_SHORT_HOSTS is exact-match only; _ALLOWED_HOST_SUFFIXES=('.local',)
    therefore allows http://openai.local etc.
    """
    url = f"http://{host}:8000"
    assert _host_allowed(url) is False, (
        f"paid/cloud host {host!r} must be blocked; _host_allowed({url!r}) is True"
    )


@pytest.mark.parametrize("host", ("openai.local", "openrouter.local", "anthropic.local"))
def test_adv15_explain_must_not_call_paid_local_suffix_host(monkeypatch, host):
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.setenv("LLM_MODEL", "tinyllama")
    monkeypatch.setenv("LLM_BASE_URL", f"http://{host}:8000")
    get_settings.cache_clear()

    calls: list[str] = []

    def capture(url, payload, timeout):
        calls.append(url)
        return {
            "message": {
                "content": "Заявка одобрена. Поток покрывает платёж, проверки пройдены."
            }
        }

    expl = explain_decision(
        DecisionResult(
            outcome="APPROVED",
            reason_codes=["K_PASS", "RISK_OK", "CHECKS_OK"],
            offered_terms={},
            rules_version="demo-rules-v1",
            metrics={},
        ),
        RiskResult(score=70, factors={}, model_version="adv15"),
        http_post=capture,
    )
    assert calls == [], (
        f"must not POST to paid/cloud .local host {host!r}; called {calls}"
    )
    assert expl.used_llm is False
    assert expl.fallback_reason == "llm_host_not_allowed"
