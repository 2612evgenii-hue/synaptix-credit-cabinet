"""Extract goal / amount / term from free-text (AI03 / P10).

Heuristic is the review-build default. Optional Ollama may run but cannot invent
fields the heuristic did not ground (safe merge). LLM never writes DecisionResult.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
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

_FOREIGN_CCY = re.compile(
    r"(\$|usd|eur|gbp|cny|jpy|kzt|евро|доллар(?:ов|а)?|dollar|euro|"
    r"юан(?:ь|я|ей)|фунт(?:ов|а)?|тенге|yuan|pound)",
    re.IGNORECASE,
)

_NBSP = re.compile(r"[\u00a0\u202f\u2009]")

# Slavic word amounts → rubles (not minor)
_WORD_AMOUNT_RUB: list[tuple[re.Pattern[str], int]] = [
    (re.compile(r"семисот\s+тысяч"), 700_000),
    (re.compile(r"шестисот\s+тысяч"), 600_000),
    (re.compile(r"пятисот\s+тысяч"), 500_000),
    (re.compile(r"четыр[её]хсот\s+тысяч"), 400_000),
    (re.compile(r"трёхсот\s+тысяч|трехсот\s+тысяч"), 300_000),
    (re.compile(r"двухсот\s+тысяч"), 200_000),
    (re.compile(r"ста\s+тысяч|сто\s+тысяч"), 100_000),
    (re.compile(r"полтора\s+миллион(?:а|ов)?|полтора\s+млн|1[.,]5\s*млн|полтора\s+мульт"), 1_500_000),
    (re.compile(r"два\s+миллион(?:а|ов)?|два\s+лям(?:а)?"), 2_000_000),
    (re.compile(r"три\s+миллион(?:а|ов)?"), 3_000_000),
    (re.compile(r"пять\s+миллион(?:а|ов)?|миллионов\s+5|5\s+миллион"), 5_000_000),
    (re.compile(r"\bлям(?:а|у)?\b|\bлямов\b|\bмульт(?:а|у)?\b"), 1_000_000),
    # bare «миллион» — credit cue required; see _amount_candidates
    (re.compile(r"(?<!\d)\bмиллион(?:а|ов)?\b"), 1_000_000),
]

_QUANT_BEFORE_MILLION = re.compile(
    r"(полтора|полторы|два|две|три|четыре|пять|шесть|семь|восемь|девять|"
    r"десять|один|одну|одного|\d+[.,]?\d*)\s+$"
)
_MILLION_METAPHOR = re.compile(
    r"миллион(?:а|ов)?\s+(раз|вопрос\w*|причин\w*|дел\w*|сразу|процент\w*)",
    re.IGNORECASE,
)
_CREDIT_CUE_NEAR = re.compile(
    r"(нуж\w*|хочу|прошу|кредит|сумм\w*|взят\w*|дай\w*|полтора|два|три)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ExtractResult:
    schema_version: str
    goal_code: str | None
    goal_text: str | None
    amount_rub: str | None
    amount_minor: int | None
    term_months: int | None
    evidence: dict[str, str | None]
    missing_fields: list[str]
    ambiguities: list[str]
    clarifying_questions: list[str]
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
        normalized = amount_rub.replace(",", ".").strip()
        rubles = float(normalized)
        if rubles < 0 or rubles != rubles:
            return None
        return int(round(rubles * 100))
    except (TypeError, ValueError):
        return None


def _minor_to_rub(minor: int) -> str:
    return f"{minor / 100:.2f}"


def _normalize_text(text: str) -> str:
    t = _NBSP.sub(" ", text or "")
    t = t.replace("ё", "е")
    return t


def _sanitize_for_parse(text: str) -> str:
    cleaned = _INJECTION.sub(" ", text or "")
    cleaned = re.sub(
        r"\b(goal_code|amount|amount_rub|term_months|term)\s*[:=]\s*\S+",
        " ",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned


def _parse_spaced_int(chunk: str) -> int | None:
    digits = re.sub(r"[\s]", "", chunk)
    if not digits.isdigit():
        return None
    return int(digits)


def _amount_candidates(text: str) -> list[tuple[int, str, int]]:
    """Return (amount_minor, evidence, start_index)."""
    found: list[tuple[int, str, int]] = []
    lowered = text.lower()

    # Ranges → handled separately (no candidate from inside range alone)
    for m in re.finditer(
        r"от\s+([\d\s]+)\s*(?:тысяч|тыс|млн|миллион)?\s*до\s+([\d\s]+)",
        lowered,
    ):
        # mark later as ambiguity; do not add as single amount
        pass

    # Spaced / plain digits with optional unit
    for m in re.finditer(
        r"(\d{1,3}(?:[\s]\d{3})+|\d+)(?:[.,](\d+))?\s*"
        r"(млн|миллион(?:а|ов)?|тыс(?:яч[аи]?)?|т\.?\s*р\.?|руб(?:лей|ля)?|₽)?",
        lowered,
    ):
        window = lowered[m.start() : min(len(lowered), m.end() + 14)]
        if _FOREIGN_CCY.search(window):
            continue
        whole = _parse_spaced_int(m.group(1))
        if whole is None:
            continue
        frac = m.group(2)
        unit = m.group(3) or ""
        rubles = float(whole)
        if frac:
            rubles = float(f"{whole}.{frac}")
        if unit.startswith("млн") or unit.startswith("миллион"):
            rubles *= 1_000_000
        elif unit.startswith("тыс") or unit.startswith("т."):
            rubles *= 1_000
        # Bare integers: treat as rubles if >= 1000 or has spaces/unit
        elif not unit and whole < 1000:
            continue
        elif not unit and " " not in m.group(1) and whole < 10_000:
            # short bare numbers without unit are ambiguous (esp. terms) — skip if look like months
            continue
        minor = int(round(rubles * 100))
        if minor >= 10_000_00:  # at least 10k RUB for credit amounts
            found.append((minor, m.group(0).strip(), m.start()))

    # Compact forms: 1.5млн / 300к / 1,2 млн
    for m in re.finditer(
        r"(\d+[.,]\d+|\d+)\s*(млн|млн\.|миллион(?:а|ов)?|к\b|тыс)",
        lowered,
    ):
        val = float(m.group(1).replace(",", "."))
        unit = m.group(2)
        if unit.startswith("к"):
            rubles = val * 1_000
        elif "тыс" in unit:
            rubles = val * 1_000
        else:
            rubles = val * 1_000_000
        found.append((int(round(rubles * 100)), m.group(0), m.start()))

    # Word amounts
    for pat, rubles in _WORD_AMOUNT_RUB:
        for m in pat.finditer(lowered):
            g = m.group(0)
            bare_million = bool(re.fullmatch(r"миллион(?:а|ов)?", g))
            if bare_million:
                # already covered by «полтора/два миллиона»
                if _QUANT_BEFORE_MILLION.search(lowered[: m.start()]):
                    continue
                # metaphorical / negated
                if _MILLION_METAPHOR.match(lowered[m.start() :]):
                    continue
                before = lowered[max(0, m.start() - 24) : m.start()]
                if re.search(r"\bне\s+$", before) or "это не" in lowered[max(0, m.start() - 12) : m.start()]:
                    continue
                window = lowered[max(0, m.start() - 40) : m.end() + 24]
                if not _CREDIT_CUE_NEAR.search(window):
                    continue
            found.append((rubles * 100, g, m.start()))

    # Drop overlapping spans: keep longer evidence; drop shorter nested hits
    found.sort(key=lambda x: (x[2], -len(x[1])))
    deduped: list[tuple[int, str, int]] = []
    for minor, evid, start in found:
        end = start + len(evid)
        overlap = False
        for i, (m, e, s) in enumerate(deduped):
            e_end = s + len(e)
            if start < e_end and end > s:
                # nested / overlapping — keep longer (or equal amount prefer first)
                if len(evid) > len(e):
                    deduped[i] = (minor, evid, start)
                overlap = True
                break
        if not overlap:
            deduped.append((minor, evid, start))
    return deduped


def _is_amount_range(text: str) -> tuple[bool, str | None]:
    lowered = text.lower()
    m = re.search(
        r"от\s+([\d\s]+(?:\s*тысяч|\s*тыс|\s*млн)?|\w+\s+тысяч)\s*до\s+"
        r"([\d\s]+(?:\s*тысяч|\s*тыс|\s*млн)?|миллион(?:а)?)",
        lowered,
    )
    if m:
        return True, m.group(0)
    if re.search(r"миллион\s+или\s+полтора|или\s+полтора", lowered):
        return True, "миллион или полтора"
    return False, None


def _correction_amount(text: str, cands: list[tuple[int, str, int]]) -> tuple[int, str] | None:
    """«сначала/думал X, но хватит/лучше Y» / «не X, а Y»."""
    lowered = text.lower()
    # сначала … но хватит / но лучше / хотя нет
    m = re.search(
        r"(сначала|думал|дума|хотя\s+нет).{0,80}?\b(но|а)\s+(хватит|лучше|нужно)?\s*",
        lowered,
    )
    if m and cands:
        after = m.end()
        after_cands = [c for c in cands if c[2] >= after - 5]
        if after_cands:
            # prefer word/thousand forms after correction marker
            return after_cands[0][0], after_cands[0][1]
    # не X, а Y
    m2 = re.search(r"\bне\b.+?\bа\b\s*", lowered)
    if m2 and len(cands) >= 2:
        after = m2.end()
        after_cands = [c for c in cands if c[2] >= after]
        if after_cands:
            return after_cands[0][0], after_cands[0][1]
    return None


def _pick_amount(
    text: str, cands: list[tuple[int, str, int]]
) -> tuple[int | None, str | None, list[str]]:
    ambiguities: list[str] = []
    is_range, range_ev = _is_amount_range(text)
    if is_range:
        ambiguities.append("amount:range")
        return None, range_ev, ambiguities

    corr = _correction_amount(text, cands)
    if corr:
        return corr[0], corr[1], ambiguities

    if not cands:
        return None, None, ambiguities

    lowered = text.lower()
    scored: list[tuple[int, int, str]] = []
    for minor, evid, idx in cands:
        window = lowered[max(0, idx - 40) : idx + len(evid) + 12]
        score = 0
        if any(w in window for w in ("нуж", "хочу", "кредит", "прошу", "дай", "сумм", "взя")):
            score += 2
        if any(w in window for w in ("выручк", "доход")):
            score -= 3
        scored.append((score, minor, evid))
    scored.sort(key=lambda x: (-x[0],))
    top = scored[0][0]
    tops = [s for s in scored if s[0] == top]
    uniq = {s[1] for s in tops}
    if len(uniq) > 1:
        ambiguities.append("amount:multiple_candidates")
        return None, None, ambiguities
    if tops[0][0] < 0:
        ambiguities.append("amount:looks_like_revenue_not_credit")
        return None, None, ambiguities
    # Same amount may appear twice (word + digit) — fine
    return tops[0][1], tops[0][2], ambiguities


def _term_candidates(text: str) -> list[tuple[int | None, str, str]]:
    """(months|None, evidence, kind) kind=exact|ambiguous."""
    found: list[tuple[int | None, str, str]] = []
    lowered = text.lower()

    if re.search(r"год[а]?\s*[-–—]\s*полтора|год[а]?\s+или\s+на\s+два|полтора|на\s+год\s+или", lowered):
        if re.search(r"год[а]?\s*[-–—/]\s*полтора|годик\s*[-–—]\s*полтора", lowered):
            found.append((None, "год-полтора", "ambiguous"))
        if re.search(r"на\s+год\s+или\s+на\s+два", lowered):
            found.append((None, "год или два", "ambiguous"))

    # полгода / полтора года / годик
    for m in re.finditer(r"полтора\s+год(?:а)?", lowered):
        found.append((18, m.group(0), "exact"))
    for m in re.finditer(r"полгода|на\s+полгода", lowered):
        found.append((6, m.group(0), "exact"))
    for m in re.finditer(r"годик|на\s+год(?!\s*[-–—])|на\s+год\b", lowered):
        # avoid matching inside год-полтора already flagged
        if "полтора" in lowered[max(0, m.start() - 5) : m.end() + 10]:
            continue
        found.append((12, m.group(0), "exact"))

    for m in re.finditer(r"(\d+)\s*(мес(?:яц(?:а|ев)?)?|год(?:а)?|лет)", lowered):
        n, unit = int(m.group(1)), m.group(2)
        months = n if unit.startswith("мес") else n * 12
        found.append((months, m.group(0), "exact"))

    for word, years in (("три", 3), ("два", 2), ("один", 1), ("пять", 5)):
        for m in re.finditer(rf"{word}\s+(года|лет|год(?:ик)?)", lowered):
            found.append((years * 12, m.group(0), "exact"))

    # Correction of term: «на год, хотя нет, лучше … на два года»
    if re.search(r"(хотя\s+нет|лучше).{0,40}два\s+год", lowered):
        found = [f for f in found if f[0] != 12 or "год" not in f[1] or "два" in f[1]]
        for m in re.finditer(r"два\s+год(?:а)?", lowered):
            found.append((24, m.group(0), "exact"))

    return found


def _pick_term(text: str) -> tuple[int | None, str | None, list[str]]:
    ambiguities: list[str] = []
    cands = _term_candidates(text)
    amb = [c for c in cands if c[2] == "ambiguous"]
    if amb:
        ambiguities.append("term_months:ambiguous_range")
        return None, amb[0][1], ambiguities
    exact = [(c[0], c[1]) for c in cands if c[2] == "exact" and c[0] is not None]
    if not exact:
        return None, None, ambiguities
    # correction: last distinct after «лучше/хотя»
    lowered = text.lower()
    if re.search(r"хотя\s+нет|лучше", lowered) and len({e[0] for e in exact}) > 1:
        return exact[-1][0], exact[-1][1], ambiguities
    uniq = {e[0] for e in exact}
    if len(uniq) > 1:
        ambiguities.append("term_months:multiple_candidates")
        return None, None, ambiguities
    return exact[0][0], exact[0][1], ambiguities


def _parse_goal(text: str) -> tuple[str | None, str | None, list[str]]:
    """Return goal_code, goal_text, ambiguities."""
    lowered = text.lower()
    ambiguities: list[str] = []

    # Explicit dual goal choice
    if re.search(r"товар\s+или\s+оборудован|станок\s*,\s*то\s+ли\s+товар|то\s+ли\s+станок", lowered):
        ambiguities.append("goal_code:multiple_candidates")
        return None, None, ambiguities

    equipment_res = (
        (r"оборуд\w*", "оборудование"),
        (r"печ[ьиу]\b", "печь"),
        (r"станк\w*", "станок"),
        (r"холодильн\w*", "холодильник"),
        (r"автомобил\w*|фургон\w*|доставк\w*", "автомобиль/доставка"),
        (r"\bтехника\b", "техника"),
        (r"машин[ауеы]\b", "машина"),
    )
    wc_res = (
        (r"оборотн\w*|пополнен\w*\s+оборот|на\s+оборот\b|\bоборот\b", "оборот"),
        (r"закуп\w*|товар\w*|сырь\w*", "закупка товара"),
        (r"аренд\w*", "аренда"),
        (r"зарплат\w*", "зарплата"),
        (r"касс\w*", "касса"),
        (r"склад\w*", "склад"),
    )
    other_res = (
        (r"ремонт\w*", "ремонт"),
        (r"точк\w*|цех\w*|расшири\w*", "развитие точки/цеха"),
    )

    hits: list[tuple[str, str]] = []
    for pat, label in equipment_res:
        if re.search(pat, lowered) and "машинист" not in lowered:
            hits.append(("equipment", label))
            break
    for pat, label in wc_res:
        if re.search(pat, lowered):
            hits.append(("working_capital", label))
            break
    for pat, label in other_res:
        if re.search(pat, lowered):
            hits.append(("other", label))
            break

    codes = {h[0] for h in hits}
    if len(codes) > 1:
        # equipment + delivery car is still equipment; repair is other
        if codes == {"equipment", "working_capital"}:
            ambiguities.append("goal_code:both_equipment_and_working_capital_cues")
            return None, hits[0][1], ambiguities
        if "other" in codes and "equipment" in codes:
            # e.g. unclear — prefer explicit
            pass
    if not hits:
        return None, None, ambiguities
    # Prefer first hit order: equipment, wc, other as scanned
    code, label = hits[0]
    return code, label, ambiguities


def _questions(missing: list[str], ambiguities: list[str]) -> list[str]:
    q: list[str] = []
    if "amount_rub" in missing or "amount:range" in ambiguities:
        q.append("Укажите точную сумму кредита в рублях.")
    if "term_months" in missing or any(a.startswith("term_months:") for a in ambiguities):
        q.append("Укажите точный срок в месяцах.")
    if "goal_code" in missing or any(a.startswith("goal_code:") for a in ambiguities):
        q.append("Уточните цель финансирования одним вариантом.")
    return q


def extract_heuristic(
    text: str, *, allowed_goals: set[str] | frozenset[str] = ALLOWED_GOALS
) -> ExtractResult:
    injection = bool(_INJECTION.search(text or ""))
    ambiguities: list[str] = []
    if injection:
        ambiguities.append("prompt_injection_ignored_for_decision")
    if _FOREIGN_CCY.search(text or ""):
        ambiguities.append("amount:foreign_currency_mentioned")

    parse_text = _sanitize_for_parse(_normalize_text(text))
    cands = _amount_candidates(parse_text)
    amount_minor, amount_ev, amt_amb = _pick_amount(parse_text, cands)
    ambiguities.extend(amt_amb)
    if amount_minor is not None and _FOREIGN_CCY.search(text or ""):
        amount_minor, amount_ev = None, None
        if "amount:foreign_currency_mentioned" not in ambiguities:
            ambiguities.append("amount:foreign_currency_mentioned")

    term_months, term_ev, term_amb = _pick_term(parse_text)
    ambiguities.extend(term_amb)

    goal, goal_text, goal_amb = _parse_goal(parse_text)
    ambiguities.extend(goal_amb)
    if goal is not None and goal not in allowed_goals:
        ambiguities.append(f"goal_code:not_in_allowed:{goal}")
        goal = None

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
        goal_text=goal_text,
        amount_rub=_minor_to_rub(amount_minor) if amount_minor is not None else None,
        amount_minor=amount_minor,
        term_months=term_months,
        evidence={"goal": goal_text, "amount": amount_ev, "term": term_ev},
        missing_fields=missing,
        ambiguities=ambiguities,
        clarifying_questions=_questions(missing, ambiguities),
        backend="heuristic",
        model_id="ru-heuristic-v2",
        used_llm=False,
        needs_user_confirm=True,
        injection_detected=injection,
    )


def _ground_llm_with_heuristic(
    llm: ExtractResult,
    heuristic: ExtractResult,
    text: str,
) -> ExtractResult:
    """Heuristic owns field values; LLM cannot invent missing ones (AI06 pending soft merge)."""
    del text, llm
    return ExtractResult(
        schema_version=heuristic.schema_version,
        goal_code=heuristic.goal_code,
        goal_text=heuristic.goal_text,
        amount_rub=heuristic.amount_rub,
        amount_minor=heuristic.amount_minor,
        term_months=heuristic.term_months,
        evidence=heuristic.evidence,
        missing_fields=heuristic.missing_fields,
        ambiguities=list(
            dict.fromkeys(heuristic.ambiguities + ["llm:fields_not_trusted_use_heuristic"])
        ),
        clarifying_questions=heuristic.clarifying_questions,
        backend="heuristic",
        model_id=heuristic.model_id,
        used_llm=False,
        needs_user_confirm=True,
        fallback_reason="llm_fields_ignored_heuristic_only",
        injection_detected=heuristic.injection_detected,
    )


def _validate_llm_extract(
    raw: dict[str, Any], allowed_goals: set[str] | frozenset[str]
) -> ExtractResult | None:
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
        goal_text=evidence.get("goal"),
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
        clarifying_questions=_questions(missing, ambiguities),
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
        "Извлеки goal_code, amount_rub, term_months из текста. "
        "Допустимые goal_code: "
        + ", ".join(allowed_goals)
        + ". Недостающие — null. Не одобряй кредит. Только JSON."
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
        goal_text=result.goal_text,
        amount_rub=result.amount_rub,
        amount_minor=result.amount_minor,
        term_months=result.term_months,
        evidence=result.evidence,
        missing_fields=result.missing_fields,
        ambiguities=result.ambiguities,
        clarifying_questions=result.clarifying_questions,
        backend="ollama",
        model_id=model,
        used_llm=True,
        needs_user_confirm=True,
        injection_detected=bool(_INJECTION.search(text)),
    )


def extract_application_fields(
    text: str,
    *,
    currency: str = "RUB",
    allowed_goal_codes: list[str] | None = None,
    http_post: HttpPost | None = None,
) -> ExtractResult:
    allowed = list(allowed_goal_codes or sorted(ALLOWED_GOALS))
    heuristic = extract_heuristic(text, allowed_goals=set(allowed))

    if currency != "RUB":
        return ExtractResult(
            schema_version=SCHEMA_VERSION,
            goal_code=None,
            goal_text=None,
            amount_rub=None,
            amount_minor=None,
            term_months=None,
            evidence={},
            missing_fields=["goal_code", "amount_rub", "term_months"],
            ambiguities=["currency:unsupported"],
            clarifying_questions=["Поддерживается только валюта RUB."],
            backend="heuristic",
            model_id="ru-heuristic-v2",
            used_llm=False,
            needs_user_confirm=True,
            fallback_reason="unsupported_currency",
        )

    settings = get_settings()
    backend = (settings.llm_backend or "template").strip().lower()
    if backend not in {"ollama"}:
        return heuristic

    model = (settings.llm_model or "").strip()
    base = (settings.llm_base_url or "http://127.0.0.1:11434").strip()
    if not model or not _host_allowed(base):
        return ExtractResult(
            schema_version=heuristic.schema_version,
            goal_code=heuristic.goal_code,
            goal_text=heuristic.goal_text,
            amount_rub=heuristic.amount_rub,
            amount_minor=heuristic.amount_minor,
            term_months=heuristic.term_months,
            evidence=heuristic.evidence,
            missing_fields=heuristic.missing_fields,
            ambiguities=heuristic.ambiguities,
            clarifying_questions=heuristic.clarifying_questions,
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
            goal_text=heuristic.goal_text,
            amount_rub=heuristic.amount_rub,
            amount_minor=heuristic.amount_minor,
            term_months=heuristic.term_months,
            evidence=heuristic.evidence,
            missing_fields=heuristic.missing_fields,
            ambiguities=heuristic.ambiguities,
            clarifying_questions=heuristic.clarifying_questions,
            backend="heuristic",
            model_id=heuristic.model_id,
            used_llm=False,
            needs_user_confirm=True,
            fallback_reason="llm_unavailable_or_invalid",
            injection_detected=heuristic.injection_detected,
        )
    return _ground_llm_with_heuristic(llm, heuristic, text)


def extract_result_as_contract(result: ExtractResult) -> dict[str, Any]:
    return {
        "schema_version": result.schema_version,
        "goal_code": result.goal_code,
        "goal_text": result.goal_text,
        "amount_rub": result.amount_rub,
        "amount_minor": result.amount_minor,
        "term_months": result.term_months,
        "evidence": result.evidence,
        "missing_fields": result.missing_fields,
        "ambiguities": result.ambiguities,
        "clarifying_questions": result.clarifying_questions,
        "needs_user_confirm": result.needs_user_confirm,
        "meta": {
            "backend": result.backend,
            "model_id": result.model_id,
            "used_llm": result.used_llm,
            "fallback_reason": result.fallback_reason,
            "injection_detected": result.injection_detected,
        },
    }
