"""Attack: partial heuristic + substring 'evidence' lets LLM invent missing fields."""

import json

from synaptix_api.analytics.extract import extract_application_fields, extract_heuristic
from synaptix_api.settings import get_settings


def test_adv_extract_b2_llm_must_not_fill_missing_via_substring_evidence(monkeypatch):
    """
    Invariant: when heuristics leave goal/amount missing, an Ollama JSON must not
    invent them merely because some evidence token substring appears in the text.

    Cycle B1 closed wholesale invention on emptyish input and override of already
    grounded fields. Partial fill still accepts LLM goal/amount when evidence is
    any substring of the user text (e.g. «хочу» / «12»), inventing equipment and
    999999 RUB from «хочу кредит на 12 месяцев».
    """
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.setenv("LLM_MODEL", "qwen3:4b")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:11434")
    get_settings.cache_clear()

    text = "хочу кредит на 12 месяцев"
    heuristic = extract_heuristic(text)
    assert heuristic.goal_code is None
    assert heuristic.amount_minor is None
    assert heuristic.term_months == 12

    def inventing_post(url, payload, timeout):
        return {
            "message": {
                "content": json.dumps(
                    {
                        "goal_code": "equipment",
                        "amount_rub": "999999.00",
                        "term_months": 12,
                        "evidence": {
                            "goal": "хочу",
                            "amount": "12",
                            "term": "12 месяцев",
                        },
                        "missing_fields": [],
                        "ambiguities": [],
                    }
                )
            }
        }

    result = extract_application_fields(text, http_post=inventing_post)
    get_settings.cache_clear()

    assert result.goal_code is None, (
        "LLM must not invent goal_code from substring evidence; "
        f"got goal={result.goal_code!r} evidence={result.evidence}"
    )
    assert result.amount_minor is None, (
        "LLM must not invent amount from substring evidence; "
        f"got amount_rub={result.amount_rub!r} evidence={result.evidence}"
    )


def test_adv_extract_b2_llm_must_not_invent_term_from_unrelated_token(monkeypatch):
    """
    Invariant: missing term must not be filled from LLM evidence that is not a
    term utterance (e.g. evidence «кредит» while inventing term_months=36).
    """
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.setenv("LLM_MODEL", "qwen3:4b")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:11434")
    get_settings.cache_clear()

    text = "нужно 500000 на кредит"
    heuristic = extract_heuristic(text)
    assert heuristic.amount_minor == 50_000_000
    assert heuristic.term_months is None
    assert heuristic.goal_code is None

    def inventing_post(url, payload, timeout):
        return {
            "message": {
                "content": json.dumps(
                    {
                        "goal_code": "equipment",
                        "amount_rub": "500000.00",
                        "term_months": 36,
                        "evidence": {
                            "goal": "нужно",
                            "amount": "500000",
                            "term": "кредит",
                        },
                        "missing_fields": [],
                        "ambiguities": [],
                    }
                )
            }
        }

    result = extract_application_fields(text, http_post=inventing_post)
    get_settings.cache_clear()

    assert result.term_months is None, (
        "LLM must not invent term_months from unrelated evidence token; "
        f"got term={result.term_months!r} evidence={result.evidence}"
    )
    assert result.goal_code is None, (
        "LLM must not invent goal_code from substring evidence; "
        f"got goal={result.goal_code!r}"
    )
