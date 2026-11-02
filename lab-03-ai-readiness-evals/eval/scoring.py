"""Deterministic scoring of agent answers: numbers, keywords, DAX behaviour."""

from __future__ import annotations

import re

SCALE = {
    "k": 1e3, "thousand": 1e3,
    "m": 1e6, "mn": 1e6, "mio": 1e6, "million": 1e6, "millions": 1e6,
    "bn": 1e9, "b": 1e9, "billion": 1e9,
}

NUMBER = re.compile(
    r"(?<![\w.])"
    r"(?P<num>\d{1,3}(?:[,.\u202f\u00a0 ]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?)"
    r"\s*(?P<unit>%|k\b|thousand\b|mn\b|mio\b|m\b|millions?\b|bn\b|b\b|billion\b)?",
    re.IGNORECASE,
)

CLARIFY_HINTS = ("which", "do you mean", "would you like", "could you", "can you clarify", "please specify", "clarify")
DECLINE_HINTS = (
    "not available", "isn't available", "is not available", "no data", "doesn't contain", "does not contain",
    "doesn't include", "does not include", "not in the", "isn't in the", "not part of", "cannot", "can't",
    "unable", "no information", "not included", "outside", "don't have", "do not have", "no records",
)


def _to_float(raw: str, scaled: bool = False) -> float:
    s = raw.replace("\u202f", "").replace("\u00a0", "").replace(" ", "")
    if scaled and s.count(".") == 1 and "," not in s:
        return float(s)  # 1.142 M is a decimal, not thousands
    if "," in s and "." in s:
        # The last separator is the decimal mark: 1,234.56 or 1.234,56.
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif s.count(",") > 1 or (s.count(",") == 1 and len(s.split(",")[1]) == 3):
        s = s.replace(",", "")
    elif s.count(".") > 1 or (s.count(".") == 1 and len(s.split(".")[1]) == 3 and len(s.split(".")[0]) <= 3 and s.split(".")[0] != "0"):
        # 293.801.286 or 842.556 (European thousands). A single '.ddd' is ambiguous; treat as thousands.
        s = s.replace(".", "")
    else:
        s = s.replace(",", ".")
    return float(s)


def extract_numbers(text: str) -> list[tuple[float, bool]]:
    """Return (value, is_percent) pairs. Percentages are returned as fractions (9.6% -> 0.096)."""
    clean = re.sub(r"\]\([^)]*\)", "]", text)  # drop markdown link targets (URLs with GUIDs)
    clean = clean.replace("**", "")
    found = []
    for m in NUMBER.finditer(clean):
        unit = (m.group("unit") or "").lower()
        try:
            value = _to_float(m.group("num"), scaled=unit in SCALE or unit == "%")
        except ValueError:
            continue
        if unit == "%":
            found.append((value / 100, True))
        else:
            found.append((value * SCALE.get(unit, 1), False))
    return found


def parse_expected(spec: str) -> list[tuple[float, bool]]:
    values = []
    for token in filter(None, (t.strip() for t in (spec or "").split("|"))):
        if token.endswith("%"):
            values.append((float(token[:-1]) / 100, True))
        else:
            values.append((float(token), False))
    return values


def number_matches(expected: tuple[float, bool], found: list[tuple[float, bool]],
                   rel_tol: float = 0.01, pct_abs_tol: float = 0.001) -> bool:
    value, is_pct = expected
    for got, got_pct in found:
        if is_pct:
            if got_pct and abs(got - value) <= pct_abs_tol:
                return True
        elif not got_pct and value != 0 and abs(got - value) / abs(value) <= rel_tol:
            return True
    return False


def norm_dax(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("'", "").replace('"', "")).lower()


def score_case(case: dict, answer: str, dax_list: list[str]) -> dict:
    """Score one agent run against one test case. Returns check results and an overall pass flag."""
    checks: dict[str, bool] = {}
    notes: list[str] = []
    expect = (case.get("expect") or "answer").strip().lower()
    answer = answer.replace("\u2019", "'").replace("\u2018", "'")
    lower = answer.lower()
    found = extract_numbers(answer)

    if expect == "clarify":
        asked = "?" in answer and any(h in lower for h in CLARIFY_HINTS)
        checks["asks_clarifying_question"] = asked
        if not asked:
            notes.append("expected a clarifying question")
    elif expect == "decline":
        declined = any(h in lower for h in DECLINE_HINTS)
        checks["says_data_not_in_model"] = declined
        if not declined:
            notes.append("expected the agent to say the model doesn't contain this data")
    else:
        if not answer.strip():
            checks["has_answer"] = False
            notes.append("empty answer")
        expected = parse_expected(case.get("expected_values", ""))
        if expected:
            hits = [number_matches(e, found) for e in expected]
            mode = (case.get("match") or "all").strip().lower()
            ok = any(hits) if mode == "any" else all(hits)
            checks["numbers_match"] = ok
            if not ok:
                missing = [f"{v:.4%}" if p else f"{v:,.2f}" for (v, p), h in zip(expected, hits) if not h]
                notes.append("missing expected value(s): " + ", ".join(missing))

    for word in filter(None, (w.strip() for w in (case.get("must_mention") or "").split("|"))):
        ok = word.lower() in lower
        checks[f"mentions:{word}"] = ok
        if not ok:
            notes.append(f"answer doesn't mention '{word}'")

    dax_text = norm_dax("\n".join(dax_list))
    for token in filter(None, (t.strip() for t in (case.get("dax_must_contain") or "").split("|"))):
        alternatives = [norm_dax(a) for a in token.split("~")]
        ok = bool(dax_list) and any(a in dax_text for a in alternatives)
        checks[f"dax_uses:{token}"] = ok
        if not ok:
            notes.append(f"DAX doesn't use {token.replace('~', ' or ')}")
    for token in filter(None, (t.strip() for t in (case.get("dax_must_not_contain") or "").split("|"))):
        ok = norm_dax(token) not in dax_text
        checks[f"dax_avoids:{token}"] = ok
        if not ok:
            notes.append(f"DAX uses {token}, which the AI instructions rule out")

    return {"checks": checks, "passed": all(checks.values()) if checks else False, "notes": notes}
