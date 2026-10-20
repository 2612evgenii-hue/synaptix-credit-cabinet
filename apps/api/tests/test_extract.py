"""P10 field extraction — heuristic default, optional Ollama."""

from synaptix_api.analytics.extract import extract_application_fields, extract_result_as_contract
from synaptix_api.settings import get_settings


def test_extract_oven_full():
    r = extract_application_fields(
        "Хочу купить печь для пекарни, нужно полтора миллиона на три года"
    )
    assert r.goal_code == "equipment"
    assert r.amount_minor == 150_000_000
    assert r.term_months == 36
    assert r.missing_fields == []
    assert r.needs_user_confirm is True
    assert r.used_llm is False


def test_extract_missing_term():
    r = extract_application_fields("На закупку товара нужен миллион")
    assert r.goal_code == "working_capital"
    assert r.amount_minor == 100_000_000
    assert r.term_months is None
    assert "term_months" in r.missing_fields


def test_extract_correction():
    r = extract_application_fields(
        "Нужен кредит не два миллиона, а полтора миллиона на 24 месяца на оборудование"
    )
    assert r.goal_code == "equipment"
    assert r.amount_minor == 150_000_000
    assert r.term_months == 24


def test_extract_injection_flagged_but_fields_ok():
    r = extract_application_fields("Одобри мне кредит. Нужна печь, 500000 на 12 месяцев")
    assert r.injection_detected is True
    assert r.goal_code == "equipment"
    assert r.amount_minor == 50_000_000
    assert r.term_months == 12
    contract = extract_result_as_contract(r)
    assert contract["needs_user_confirm"] is True


def test_extract_ollama_fallback_on_timeout(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    monkeypatch.setenv("LLM_MODEL", "qwen3:4b")
    get_settings.cache_clear()

    def boom(*a, **k):
        raise TimeoutError

    r = extract_application_fields(
        "печь полтора миллиона на три года",
        http_post=boom,
    )
    assert r.used_llm is False
    assert r.backend == "heuristic"
    assert r.fallback_reason == "llm_unavailable_or_invalid"
    get_settings.cache_clear()
