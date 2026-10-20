"""AI03 regression: QA A01–A10 amount+term and D01/D04 corrections/ranges."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from synaptix_api.analytics.extract import extract_application_fields
from synaptix_api.settings import get_settings

ROOT = Path(__file__).resolve().parents[3]
PHRASES = json.loads((ROOT / "data" / "qa" / "extract-phrases.json").read_text(encoding="utf-8"))[
    "phrases"
]


@pytest.fixture(autouse=True)
def _heuristic_backend(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "template")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.parametrize("case", PHRASES, ids=[c["id"] for c in PHRASES])
def test_qa_extract_amount_and_term(case: dict) -> None:
    result = extract_application_fields(case["text"])
    assert result.needs_user_confirm is True
    assert result.amount_minor == case["amount_minor"], (
        f"{case['id']}: amount_minor got {result.amount_minor}, "
        f"expected {case['amount_minor']}; amb={result.ambiguities}"
    )
    assert result.term_months == case["term_months"], (
        f"{case['id']}: term_months got {result.term_months}, "
        f"expected {case['term_months']}; amb={result.ambiguities}"
    )
    for forbidden in case.get("forbidden_amounts_minor") or []:
        assert result.amount_minor != forbidden, (
            f"{case['id']}: forbidden amount {forbidden} selected"
        )
    required_amb = case.get("expect_ambiguities_any_of") or []
    if required_amb:
        assert any(a in result.ambiguities for a in required_amb), (
            f"{case['id']}: expected one of {required_amb}, got {result.ambiguities}"
        )


def test_qa_a01_a10_score_is_ten_of_ten() -> None:
    ordinary = [c for c in PHRASES if c["id"].startswith("A")]
    assert len(ordinary) == 10
    ok = 0
    for case in ordinary:
        r = extract_application_fields(case["text"])
        if r.amount_minor == case["amount_minor"] and r.term_months == case["term_months"]:
            ok += 1
    assert ok == 10, f"A01–A10 amount+term score {ok}/10"
