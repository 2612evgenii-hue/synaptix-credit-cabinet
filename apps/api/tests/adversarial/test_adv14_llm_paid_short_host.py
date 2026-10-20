"""Attack: paid/cloud LLM short hostnames bypass allowlist via Docker DNS rule."""

import pytest

from synaptix_api.analytics.explain import _host_allowed, explain_decision
from synaptix_api.analytics.types import DecisionResult, RiskResult
from synaptix_api.settings import get_settings

# Well-known paid / cloud LLM service names — FQDN fragments are blocked, but
# bare Docker-style identifiers (no dots) are allowlisted by _host_allowed.
_PAID_SHORT_HOSTS = (
    "openai",
    "anthropic",
    "groq",
    "mistral",
    "cohere",
    "fireworks",
    "together",
    "openrouter",
)


@pytest.mark.parametrize("host", _PAID_SHORT_HOSTS)
def test_adv14_paid_cloud_short_hostname_must_not_be_allowed(host):
    """
    Invariant: paid/cloud LLM hosts must be blocked.

    Blocklist matches substrings like 'openai.com' / 'api.groq.com', but
    hosts with no '.' and isidentifier() are allowed — so http://openai etc.
    pass and explain_decision will POST to them.
    """
    url = f"http://{host}:8000"
    assert _host_allowed(url) is False, (
        f"paid/cloud short host {host!r} must be blocked; _host_allowed({url!r}) is True"
    )


@pytest.mark.parametrize("host", ("openrouter", "openai", "anthropic"))
def test_adv14_explain_must_not_call_paid_short_host(monkeypatch, host):
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
        RiskResult(score=70, factors={}, model_version="adv14"),
        http_post=capture,
    )
    assert calls == [], (
        f"must not POST to paid/cloud short host {host!r}; called {calls}"
    )
    assert expl.used_llm is False
    assert expl.fallback_reason == "llm_host_not_allowed"
