"""Attack: Ollama extract invents goal/amount/term when input has none."""

import json

from synaptix_api.analytics.extract import extract_application_fields, extract_heuristic
from synaptix_api.settings import get_settings


def test_adv_extract_llm_must_not_invent_fields_on_emptyish(monkeypatch):
    """
    Invariant: emptyish free-text (no goal/amount/term cues) must stay missing.

    Held-out case `emptyish` and docs/ai-evaluation.md require null fields +
    missing_fields. extract_application_fields returns the LLM payload wholesale
    when Ollama succeeds — no grounding against the input — so a model can
    invent goal_code / amount_rub / term_months on «Здравствуйте».
    """
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.setenv("LLM_MODEL", "qwen3:4b")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:11434")
    get_settings.cache_clear()

    text = "Здравствуйте, хочу кредит"
    heuristic = extract_heuristic(text)
    assert heuristic.goal_code is None
    assert heuristic.amount_minor is None
    assert heuristic.term_months is None
    assert set(heuristic.missing_fields) >= {"goal_code", "amount_rub", "term_months"}

    def inventing_post(url, payload, timeout):
        return {
            "message": {
                "content": json.dumps(
                    {
                        "goal_code": "equipment",
                        "amount_rub": "1234567.00",
                        "term_months": 24,
                        "evidence": {
                            "goal": "hallucinated",
                            "amount": "invented",
                            "term": "fake",
                        },
                        "missing_fields": [],
                        "ambiguities": [],
                        "needs_user_confirm": False,
                    }
                )
            }
        }

    result = extract_application_fields(text, http_post=inventing_post)
    get_settings.cache_clear()

    invented = (
        result.goal_code is not None
        or result.amount_minor is not None
        or result.term_months is not None
    )
    assert not invented, (
        "LLM must not invent extract fields when input has none; "
        f"got goal={result.goal_code!r} amount={result.amount_rub!r} "
        f"term={result.term_months!r} used_llm={result.used_llm} "
        f"backend={result.backend}"
    )


def test_adv_extract_llm_must_not_override_grounded_heuristic(monkeypatch):
    """
    Invariant: when heuristics already ground goal/amount/term from the text,
    an Ollama JSON that invents different values must not replace them.
    """
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.setenv("LLM_MODEL", "qwen3:4b")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:11434")
    get_settings.cache_clear()

    text = "Хочу купить печь для пекарни, нужно полтора миллиона на три года"
    heuristic = extract_heuristic(text)
    assert heuristic.goal_code == "equipment"
    assert heuristic.amount_minor == 150_000_000
    assert heuristic.term_months == 36

    def evil_post(url, payload, timeout):
        return {
            "message": {
                "content": json.dumps(
                    {
                        "goal_code": "working_capital",
                        "amount_rub": "99999999.00",
                        "term_months": 1,
                        "evidence": {"goal": "x", "amount": "y", "term": "z"},
                        "missing_fields": [],
                        "ambiguities": [],
                    }
                )
            }
        }

    result = extract_application_fields(text, http_post=evil_post)
    get_settings.cache_clear()

    assert result.goal_code == heuristic.goal_code, (
        f"LLM invented goal {result.goal_code!r} over grounded {heuristic.goal_code!r}"
    )
    assert result.amount_minor == heuristic.amount_minor, (
        f"LLM invented amount {result.amount_minor!r} over grounded {heuristic.amount_minor!r}"
    )
    assert result.term_months == heuristic.term_months, (
        f"LLM invented term {result.term_months!r} over grounded {heuristic.term_months!r}"
    )
