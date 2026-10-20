"""Extract goal / amount / term from free-text (P10).

Primary path: optional local open-weight LLM (Ollama). Default/fallback: deterministic
Russian heuristics. LLM never approves credit and never writes DecisionResult.
Extracted fields always require user confirmation before becoming application input.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable

from synaptix_api.analytics.explain import _host_allowed, default_http_post
from synaptix_api.settings import get_settings

SCHEMA_VERSION = "1"
ALLOWED_GOALS = frozenset({"working_capital", "equipment", "other"})

HttpPost = Callable[[str, dict[str, Any], float], dict[str, Any]]

_INJECTION = re.compile(
    r"((ignore|forget|disregard)\s+(all\s+)?(previous|prior|above)|"
    r"одобри\s+(мне\s+)?кредит|approve\s+(my\s+)?(loan|credit)|"
    r"previous\s+instructions|jailbreak)",
    re.IGNORECASE,
)

_WORD_MILLIONS = {
    "полтора": 1.5,
    "два": 2.0,
    "три": 3.0,
    "четыре": 4.0,
    "пять": 5.0,
    "шесть": 6.0,
    "семь": 7.0,
    "восемь": 8.0,
    "девять": 9.0,
    "десять": 10.0,
    "миллион": 1.0,
    "миллиона": 1.0,
    "миллионов": 1.0,
}


@dataclass(frozen=True)
class ExtractResult:
    schema_version: str
    goal_code: str | None
    amount_rub: str | None
    amount_minor: int | None
    term_months: int | None
    evidence: dict[str, str | None]
    missing_fields: list[str]
    ambiguities: list[str]
    backend: str
    model_id: str
    used_llm: bool
    needs_user_confirm: bool = True
    fallback_reason: str | None = None
    injection_detected: bool = False


def _rub_to_minor(amount_rub: str | None) -> int | None:
    if amount_rub is None:
        return None
    try:
        # Accept "1500000.00" / "1500000"
        normalized = amount_rub.replace(",", ".").strip()
        rubles = float(normalized)
        if rubles < 0 or rubles != rubles:  # NaN
            return None
        return int(round(rubles * 100))
    except (TypeError, ValueError):
        return None


def _minor_to_rub(minor: int) -> str:
    return f"{minor / 100:.2f}"


_FOREIGN_CCY = re.compile(
    r"(\$|usd|eur|gbp|cny|jpy|kzt|евро|доллар(?:ов|а)?|dollar|euro|"
    r"юан(?:ь|я|ей)|фунт(?:ов|а)?|тенге|yuan|pound)",
    re.IGNORECASE,
)


def _sanitize_for_parse(text: str) -> str:
    """Strip injection / assignment noise before heuristic parse."""
    cleaned = _INJECTION.sub(" ", text or "")
    cleaned = re.sub(
        r"\b(goal_code|amount|amount_rub|term_months|term)\s*[:=]\s*\S+",
        " ",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned


def _parse_amount_candidates(text: str) -> list[tuple[int, str]]:
    """Return (amount_minor, evidence) candidates in appearance order."""
    found: list[tuple[int, str]] = []
    lowered = text.lower()

    # Digits with млн/тыс — skip if foreign currency in the same window
    for m in re.finditer(
        r"(\d+(?:[.,]\d+)?)\s*(млн|миллион(?:а|ов)?|тыс(?:яч[аи]?)?|т\.?\s*р\.?)",
        lowered,
    ):
        window = lowered[m.start() : min(len(lowered), m.end() + 12)]
        if _FOREIGN_CCY.search(window):
            continue
        raw, unit = m.group(1), m.group(2)
        val = float(raw.replace(",", "."))
        if unit.startswith("млн") or unit.startswith("миллион"):
            minor = int(round(val * 1_000_000 * 100))
        else:
            minor = int(round(val * 1_000 * 100))
        found.append((minor, m.group(0)))

    # Plain large integers (rubles) — reject foreign-currency neighbours
    for m in re.finditer(r"(?<!\d)(\d{5,9})(?!\d)", lowered):
        span = m.group(1)
        window = lowered[max(0, m.start() - 2) : min(len(lowered), m.end() + 16)]
        if _FOREIGN_CCY.search(window):
            continue
        found.append((int(span) * 100, span))

    # Word forms: полтора миллиона / нужен миллион (credit context)
    for word, mult in _WORD_MILLIONS.items():
        if word in {"миллион", "миллиона", "миллионов"}:
            continue
        for m in re.finditer(rf"{word}\s+миллион(?:а|ов)?", lowered):
            found.append((int(round(mult * 1_000_000 * 100)), m.group(0)))

    for m in re.finditer(
        r"(?:нужен|нужна|нужно|нужны|кредит|сумма|сумму|финансирование|заявка)\s+"
        r"миллион(?:а|ов)?(?!\s+раз)",
        lowered,
    ):
        found.append((100_000_000, m.group(0)))

    return found


def _parse_term_months(text: str) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    lowered = text.lower()
    word_years = {
        "год": 1,
        "года": 1,
        "лет": 1,
        "один": 1,
        "два": 2,
        "три": 3,
        "четыре": 4,
        "пять": 5,
    }
    for m in re.finditer(r"(\d+)\s*(мес(?:яц(?:а|ев)?)?|год(?:а)?|лет)", lowered):
        n, unit = int(m.group(1)), m.group(2)
        months = n if unit.startswith("мес") else n * 12
        found.append((months, m.group(0)))
    for word, years in (("три", 3), ("два", 2), ("один", 1), ("пять", 5)):
        for m in re.finditer(rf"{word}\s+(года|лет|год)", lowered):
            found.append((years * 12, m.group(0)))
    return found


def _parse_goal(text: str) -> tuple[str | None, str | None, list[str]]:
    lowered = text.lower()
    ambiguities: list[str] = []
    # Word-ish cues — avoid stems that hit обеспечение / техник (occupation)
    equipment_res = (
        (r"оборуд\w*", "оборуд"),
        (r"печ[ьиу]\b", "печь"),
        (r"станк\w*", "станк"),
        (r"холодильн\w*", "холодильн"),
        (r"\bтехника\b", "техника"),
        (r"\bfridge\b", "fridge"),
        (r"машин[ауеы]\b", "машин"),
    )
    eq_hit = None
    for pat, label in equipment_res:
        if re.search(pat, lowered) and "машинист" not in lowered:
            eq_hit = label
            break
    wc_cues = ("оборот", "товар", "закуп", "сырь", "касс", "зарплат", "аренда")
    wc = any(c in lowered for c in wc_cues)
    eq = eq_hit is not None
    if eq and wc:
        ambiguities.append("goal_code:both_equipment_and_working_capital_cues")
        return None, None, ambiguities
    if eq:
        return "equipment", eq_hit, ambiguities
    if wc:
        evid = next((c for c in wc_cues if c in lowered), "working_capital")
        return "working_capital", evid, ambiguities
    return None, None, ambiguities


def _prefer_credit_amount(
    text: str, candidates: list[tuple[int, str]]
) -> tuple[int | None, str | None, list[str]]:
    if not candidates:
        return None, None, []
    ambiguities: list[str] = []
    lowered = text.lower()

    # Correction: «не X, а Y» — take the first amount whose evidence starts after «а»
    corr = re.search(r"\bне\b.+?\bа\b\s*", lowered)
    if corr and len(candidates) >= 2:
        after = corr.end()
        after_cands = [
            (mi, ev)
            for mi, ev in candidates
            if (idx := lowered.find(ev.lower())) >= 0 and idx >= after
        ]
        if after_cands:
            return after_cands[0][0], after_cands[0][1], ambiguities
        # fallback: last candidate (often the correction)
        return candidates[-1][0], candidates[-1][1], ambiguities

    # Prefer amounts near credit request verbs over revenue
    credit_ctx = re.compile(
        r"(нужн|хочу|кредит|заявк|финанс|сумм).{0,40}" + re.escape(""),
        re.I,
    )
    scored: list[tuple[int, int, str]] = []
    for minor, evid in candidates:
        idx = lowered.find(evid.lower())
        window = lowered[max(0, idx - 40) : idx + len(evid) + 10]
        score = 0
        if any(w in window for w in ("нужн", "хочу", "кредит", "заявк", "сумм", "финанс")):
            score += 2
        if any(w in window for w in ("выручк", "оборот выруч", "доход")):
            score -= 2
        scored.append((score, minor, evid))
    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_minor, best_evid = scored[0]
    if len({m for _, m, _ in scored}) > 1 and scored[0][0] == scored[1][0]:
        ambiguities.append("amount:multiple_candidates")
        return None, None, ambiguities
    if best_score < 0:
        ambiguities.append("amount:looks_like_revenue_not_credit")
        return None, None, ambiguities
    return best_minor, best_evid, ambiguities


def extract_heuristic(text: str, *, allowed_goals: set[str] | frozenset[str] = ALLOWED_GOALS) -> ExtractResult:
    injection = bool(_INJECTION.search(text or ""))
    ambiguities: list[str] = []
    if injection:
        ambiguities.append("prompt_injection_ignored_for_decision")
    if _FOREIGN_CCY.search(text or ""):
        ambiguities.append("amount:foreign_currency_mentioned")

    parse_text = _sanitize_for_parse(text)

    goal, goal_ev, goal_amb = _parse_goal(parse_text)
    ambiguities.extend(goal_amb)
    if goal is not None and goal not in allowed_goals:
        ambiguities.append(f"goal_code:not_in_allowed:{goal}")
        goal = None
        goal_ev = None

    amount_cands = _parse_amount_candidates(parse_text)
    amount_minor, amount_ev, amt_amb = _prefer_credit_amount(parse_text, amount_cands)
    ambiguities.extend(amt_amb)
    # Foreign currency in original text → never keep a parsed amount
    if amount_minor is not None and _FOREIGN_CCY.search(text or ""):
        amount_minor, amount_ev = None, None
        if "amount:foreign_currency_mentioned" not in ambiguities:
            ambiguities.append("amount:foreign_currency_mentioned")

    terms = _parse_term_months(parse_text)
    term_months: int | None = None
    term_ev: str | None = None
    if len(terms) == 1:
        term_months, term_ev = terms[0]
    elif len(terms) > 1:
        # Prefer last (often correction) if distinct
        uniq = {t[0] for t in terms}
        if len(uniq) == 1:
            term_months, term_ev = terms[-1]
        else:
            ambiguities.append("term_months:multiple_candidates")
            term_months, term_ev = None, None

    amount_rub = _minor_to_rub(amount_minor) if amount_minor is not None else None
    missing: list[str] = []
    if goal is None:
        missing.append("goal_code")
    if amount_minor is None:
        missing.append("amount_rub")
    if term_months is None:
        missing.append("term_months")

    return ExtractResult(
        schema_version=SCHEMA_VERSION,
        goal_code=goal,
        amount_rub=amount_rub,
        amount_minor=amount_minor,
        term_months=term_months,
        evidence={"goal": goal_ev, "amount": amount_ev, "term": term_ev},
        missing_fields=missing,
        ambiguities=ambiguities,
        backend="heuristic",
        model_id="ru-heuristic-v1",
        used_llm=False,
        needs_user_confirm=True,
        injection_detected=injection,
    )


def _validate_llm_extract(raw: dict[str, Any], allowed_goals: set[str] | frozenset[str]) -> ExtractResult | None:
    if not isinstance(raw, dict):
        return None
    goal = raw.get("goal_code")
    if goal is not None and goal not in allowed_goals:
        return None
    amount_rub = raw.get("amount_rub")
    if amount_rub is not None and not isinstance(amount_rub, str):
        amount_rub = str(amount_rub)
    amount_minor = _rub_to_minor(amount_rub) if amount_rub else None
    term = raw.get("term_months")
    if term is not None:
        if isinstance(term, bool) or not isinstance(term, int) or term <= 0 or term > 600:
            return None
    missing = list(raw.get("missing_fields") or [])
    ambiguities = list(raw.get("ambiguities") or [])
    evidence = raw.get("evidence") if isinstance(raw.get("evidence"), dict) else {}
    # Recompute missing if model omitted
    for field_name, value in (
        ("goal_code", goal),
        ("amount_rub", amount_rub),
        ("term_months", term),
    ):
        if value is None and field_name not in missing:
            missing.append(field_name)
    return ExtractResult(
        schema_version=SCHEMA_VERSION,
        goal_code=goal,
        amount_rub=amount_rub if amount_minor is not None else None,
        amount_minor=amount_minor,
        term_months=term,
        evidence={
            "goal": evidence.get("goal"),
            "amount": evidence.get("amount"),
            "term": evidence.get("term"),
        },
        missing_fields=missing,
        ambiguities=ambiguities,
        backend="ollama",
        model_id="pending",
        used_llm=True,
        needs_user_confirm=True,
    )


def _ollama_extract(
    text: str,
    *,
    allowed_goals: list[str],
    base_url: str,
    model: str,
    timeout: float,
    http_post: HttpPost,
) -> ExtractResult | None:
    if not _host_allowed(base_url):
        return None
    endpoint = base_url.rstrip("/") + "/api/chat"
    system = (
        "Ты локальная open-weight модель. Извлеки из текста предпринимателя "
        "goal_code, amount_rub (строка рублей с копейками), term_months (целое). "
        "Допустимые goal_code: "
        + ", ".join(allowed_goals)
        + ". Недостающие поля — null и в missing_fields. "
        "Неоднозначности — в ambiguities. Не одобряй кредит и не меняй правила. "
        "Верни только JSON объект."
    )
    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ],
    }
    try:
        raw = http_post(endpoint, payload, timeout)
    except Exception:  # noqa: BLE001
        return None
    content = None
    if isinstance(raw.get("message"), dict):
        content = raw["message"].get("content")
    if not isinstance(content, str):
        return None
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return None
    result = _validate_llm_extract(parsed, set(allowed_goals))
    if result is None:
        return None
    return ExtractResult(
        schema_version=result.schema_version,
        goal_code=result.goal_code,
        amount_rub=result.amount_rub,
        amount_minor=result.amount_minor,
        term_months=result.term_months,
        evidence=result.evidence,
        missing_fields=result.missing_fields,
        ambiguities=result.ambiguities,
        backend="ollama",
        model_id=model,
        used_llm=True,
        needs_user_confirm=True,
        injection_detected=bool(_INJECTION.search(text)),
    )


def _ground_llm_with_heuristic(
    llm: ExtractResult,
    heuristic: ExtractResult,
    text: str,
) -> ExtractResult:
    """Heuristic is the only source of field values; LLM cannot invent missing ones.

    Ollama may confirm values already grounded by heuristics (same values) for
    meta/used_llm bookkeeping, but never fills None gaps via weak evidence tokens.
    """
    del text, llm  # LLM values are not trusted for field fill
    return ExtractResult(
        schema_version=heuristic.schema_version,
        goal_code=heuristic.goal_code,
        amount_rub=heuristic.amount_rub,
        amount_minor=heuristic.amount_minor,
        term_months=heuristic.term_months,
        evidence=heuristic.evidence,
        missing_fields=heuristic.missing_fields,
        ambiguities=list(
            dict.fromkeys(heuristic.ambiguities + ["llm:fields_not_trusted_use_heuristic"])
        ),
        backend="heuristic",
        model_id=heuristic.model_id,
        used_llm=False,
        needs_user_confirm=True,
        fallback_reason="llm_fields_ignored_heuristic_only",
        injection_detected=heuristic.injection_detected,
    )


def extract_application_fields(
    text: str,
    *,
    currency: str = "RUB",
    allowed_goal_codes: list[str] | None = None,
    http_post: HttpPost | None = None,
) -> ExtractResult:
    """Extract fields for form prefill. Always needs_user_confirm=True."""
    allowed = list(allowed_goal_codes or sorted(ALLOWED_GOALS))
    heuristic = extract_heuristic(text, allowed_goals=set(allowed))

    if currency != "RUB":
        return ExtractResult(
            schema_version=SCHEMA_VERSION,
            goal_code=None,
            amount_rub=None,
            amount_minor=None,
            term_months=None,
            evidence={},
            missing_fields=["goal_code", "amount_rub", "term_months"],
            ambiguities=["currency:unsupported"],
            backend="heuristic",
            model_id="ru-heuristic-v1",
            used_llm=False,
            needs_user_confirm=True,
            fallback_reason="unsupported_currency",
        )

    settings = get_settings()
    backend = (settings.llm_backend or "template").strip().lower()
    # template/heuristic is the review default; ollama optional
    if backend not in {"ollama"}:
        return heuristic

    model = (settings.llm_model or "").strip()
    base = (settings.llm_base_url or "http://127.0.0.1:11434").strip()
    if not model or not _host_allowed(base):
        return ExtractResult(
            schema_version=heuristic.schema_version,
            goal_code=heuristic.goal_code,
            amount_rub=heuristic.amount_rub,
            amount_minor=heuristic.amount_minor,
            term_months=heuristic.term_months,
            evidence=heuristic.evidence,
            missing_fields=heuristic.missing_fields,
            ambiguities=heuristic.ambiguities,
            backend="heuristic",
            model_id=heuristic.model_id,
            used_llm=False,
            needs_user_confirm=True,
            fallback_reason="llm_unavailable_or_host_blocked",
            injection_detected=heuristic.injection_detected,
        )

    timeout = float(settings.llm_timeout_seconds) if settings.llm_timeout_seconds > 0 else 8.0
    llm = _ollama_extract(
        text,
        allowed_goals=allowed,
        base_url=base,
        model=model,
        timeout=min(timeout, 120.0),
        http_post=http_post or default_http_post,
    )
    if llm is None:
        return ExtractResult(
            schema_version=heuristic.schema_version,
            goal_code=heuristic.goal_code,
            amount_rub=heuristic.amount_rub,
            amount_minor=heuristic.amount_minor,
            term_months=heuristic.term_months,
            evidence=heuristic.evidence,
            missing_fields=heuristic.missing_fields,
            ambiguities=heuristic.ambiguities,
            backend="heuristic",
            model_id=heuristic.model_id,
            used_llm=False,
            needs_user_confirm=True,
            fallback_reason="llm_unavailable_or_invalid",
            injection_detected=heuristic.injection_detected,
        )
    return _ground_llm_with_heuristic(llm, heuristic, text)


def extract_result_as_contract(result: ExtractResult) -> dict[str, Any]:
    """JSON-serializable payload matching contracts/ai-extract.output.schema.json."""
    return {
        "schema_version": result.schema_version,
        "goal_code": result.goal_code,
        "amount_rub": result.amount_rub,
        "term_months": result.term_months,
        "evidence": result.evidence,
        "missing_fields": result.missing_fields,
        "ambiguities": result.ambiguities,
        "needs_user_confirm": result.needs_user_confirm,
        "meta": {
            "backend": result.backend,
            "model_id": result.model_id,
            "used_llm": result.used_llm,
            "fallback_reason": result.fallback_reason,
            "injection_detected": result.injection_detected,
            "amount_minor": result.amount_minor,
        },
    }
