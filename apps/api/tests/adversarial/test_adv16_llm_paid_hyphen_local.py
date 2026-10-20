"""Attack: paid/cloud brand hosts allowed as hyphenated *.local labels (A2 gap)."""

import pytest

from synaptix_api.analytics.explain import _host_allowed, explain_decision
from synaptix_api.analytics.types import DecisionResult, RiskResult
from synaptix_api.settings import get_settings

# A2 blocks exact DNS labels in _BLOCKED_SHORT_HOSTS (openai.local → label
# "openai"). Compound labels that embed the same brands still pass the
# label-exact check and the .local suffix allowlist.
_PAID_HYPHEN_LOCAL_HOSTS = (
    "openai-api.local",
    "api-openai.local",
    "anthropic-api.local",
    "groq-llm.local",
    "openrouter-gw.local",
    "azure-openai.local",
)


@pytest.mark.parametrize("host", _PAID_HYPHEN_LOCAL_HOSTS)
def test_adv16_paid_cloud_hyphen_local_must_not_be_allowed(host):
    """
    Invariant: paid/cloud LLM hosts must be blocked.

    A2 closed openai.local via per-label exact match; openai-api.local is a
    single label not in _BLOCKED_SHORT_HOSTS, so _host_allowed is True.
    """
    url = f"http://{host}:8000"
    assert _host_allowed(url) is False, (
        f"paid/cloud host {host!r} must be blocked; _host_allowed({url!r}) is True"
    )


@pytest.mark.parametrize("host", ("openai-api.local", "anthropic-api.local", "openrouter-gw.local"))
def test_adv16_explain_must_not_call_paid_hyphen_local_host(monkeypatch, host):
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
        RiskResult(score=70, factors={}, model_version="adv16"),
        http_post=capture,
    )
    assert calls == [], (
        f"must not POST to paid/cloud hyphen .local host {host!r}; called {calls}"
    )
    assert expl.used_llm is False
    assert expl.fallback_reason == "llm_host_not_allowed"
