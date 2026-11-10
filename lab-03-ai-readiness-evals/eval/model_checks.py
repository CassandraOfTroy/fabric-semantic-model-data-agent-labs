"""Deterministic checks over what Fabric IQ exposes for a semantic model.

L1 readiness lint   - fields agents see, descriptions, AI instructions, model design, discoverability
L2 value grounding  - business terms resolve to the right column and value (ValueSearch)
L3 ground truth     - reference DAX returns the expected numbers (ExecuteQuery)

What Fabric IQ returns was checked against the model definition (see the Lab 3 README):
AI instructions are returned verbatim, the AI data schema is applied except for relationship
columns, and verified answers aren't returned.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from fabriciq_client import FabricIQClient, FabricIQError
from scoring import extract_numbers, parse_expected

PASS, WARN, FAIL, INFO = "PASS", "WARN", "FAIL", "INFO"
REL_END = re.compile(r"^'?(.+?)'?\[(.+)\]$")


def _finding(layer, check, status, detail, feature):
    return {"layer": layer, "check": check, "status": status, "detail": detail, "feature": feature}


def _iter_fields(schema: dict):
    for table in schema.get("Tables", []):
        yield "table", table["Name"], None, table
        for col in table.get("Columns", []) or []:
            yield "column", table["Name"], col["Name"], col
        for mea in table.get("Measures", []) or []:
            yield "measure", table["Name"], mea["Name"], mea


def relationship_columns(schema: dict) -> set[tuple[str, str]]:
    """(table, column) pairs used in active relationships. Fabric IQ returns these even when hidden from AI."""
    cols = set()
    for r in schema.get("ActiveRelationships", []) or []:
        for end in (r.get("PK", ""), r.get("FK", "")):
            m = REL_END.match(end.strip())
            if m:
                cols.add((m.group(1), m.group(2)))
    return cols


def _repo_instructions(path: Path) -> str | None:
    """AI instructions kept in source control: the first ```text block of the file, or the whole file."""
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    match = re.search(r"```text\s*\n(.*?)```", text, re.DOTALL)
    return match.group(1) if match else text


def _lines(text: str) -> set[str]:
    return {re.sub(r"\s+", " ", ln.strip()) for ln in text.splitlines() if ln.strip()}


def discoverability(client: FabricIQClient, model_id: str, name: str) -> list[dict]:
    """Agents that start from a name (standalone Copilot, Microsoft 365 Copilot, Fabric IQ) must find the model."""
    L = "L1 readiness"
    try:
        items = client.discover(name).get("artifacts") or []
    except FabricIQError as exc:
        return [_finding(L, "Discoverable by name", WARN, f"Search failed: {exc}", "Discoverability")]
    ids = [a.get("ArtifactId") for a in items]
    if model_id in ids:
        rank = ids.index(model_id) + 1
        return [_finding(L, "Discoverable by name", PASS, f"Search for '{name}' returns it at rank {rank}",
                         "Discoverability")]
    seen = ", ".join(a.get("Name", "?") for a in items) or "nothing"
    return [_finding(L, "Discoverable by name", WARN,
                     f"Search for '{name}' doesn't return it (returned: {seen}). Agents that start from a name "
                     "won't find this model. Check the model description, endorsement and Approved for Copilot; "
                     "new or renamed models can take time to be indexed", "Discoverability")]


def readiness_lint(schema_doc: dict, rules: dict, base_dir: Path) -> list[dict]:
    """base_dir is the folder of readiness-rules.json; source_of_truth paths are relative to it."""
    L = "L1 readiness"
    schema = schema_doc.get("schema", {})
    out: list[dict] = []
    fields = list(_iter_fields(schema))
    all_names = {n.lower() for _, _, n, _ in fields if n} | {t.lower() for kind, t, n, _ in fields if kind == "table"}
    rel_cols = relationship_columns(schema)
    rel_names = {c for _, c in rel_cols}

    # AI data schema: fields agents must not see. Relationship columns are always returned, so they can't fail.
    exposed = {n for _, _, n, _ in fields if n}
    rules_fields = rules.get("must_not_expose", [])
    leaked = [f for f in rules_fields if f in exposed and f not in rel_names]
    rel_seen = [f for f in rules_fields if f in exposed and f in rel_names]
    detail = ("Returned by Fabric IQ: " + ", ".join(leaked)) if leaked else \
        f"None of the {len(rules_fields) - len(rel_seen)} fields are returned"
    if rel_seen:
        detail += f". Relationship columns are always returned, even when hidden from AI: {', '.join(rel_seen)}"
    out.append(_finding(L, "Technical fields not exposed to agents", FAIL if leaked else PASS, detail,
                        "AI data schema"))

    # Descriptions. Relationship columns are skipped: they're structural and returned regardless.
    skip = re.compile(rules.get("ignore_description_columns_regex", r"$^"))
    missing, too_long, rel_missing, counted = [], [], [], 0
    max_chars = rules.get("description_max_chars", 200)
    for kind, table, name, obj in fields:
        desc = (obj.get("Description") or "").strip()
        label = f"{table}[{name}]" if name else f"table {table}"
        if kind == "column" and (table, name) in rel_cols:
            if not desc and not skip.search(name):
                rel_missing.append(label)
            continue
        if kind == "column" and skip.search(name):
            continue
        counted += 1
        if not desc:
            missing.append(label)
        elif len(desc) > max_chars:
            too_long.append(f"{label} ({len(desc)})")
    coverage = 1 - len(missing) / counted if counted else 0
    status = PASS if coverage >= rules.get("min_description_coverage", 0.9) else FAIL
    detail = f"{coverage:.0%} of {counted} tables, columns and measures" + \
        (f". Missing: {', '.join(missing)}" if missing else "")
    if rel_missing:
        detail += f". Relationship columns without a description (agents see them anyway): {', '.join(rel_missing)}"
    out.append(_finding(L, "Description coverage", status, detail, "Descriptions"))
    out.append(_finding(L, f"Descriptions within {max_chars} characters", WARN if too_long else PASS,
                        ("Copilot reads only the first 200 characters: " + ", ".join(too_long)) if too_long
                        else "All descriptions fit", "Descriptions"))

    # Measures.
    no_format = [f"{t}[{n}]" for kind, t, n, o in fields if kind == "measure" and not o.get("FormatString")]
    out.append(_finding(L, "Measures have a format string", WARN if no_format else PASS,
                        ", ".join(no_format) or "All measures formatted", "Model design"))

    # Ambiguous names: the same column name in more than one table, ignoring relationship columns.
    owners = defaultdict(set)
    for kind, t, n, _ in fields:
        if kind == "column" and (t, n) not in rel_cols and not skip.search(n):
            owners[n].add(t)
    dupes = [f"{n} ({', '.join(sorted(ts))})" for n, ts in owners.items() if len(ts) > 1]
    out.append(_finding(L, "No ambiguous column names", WARN if dupes else PASS,
                        ", ".join(dupes) or "Every visible column name is unique", "Model design"))

    # Relationships and the date table.
    rels = schema.get("ActiveRelationships", []) or []
    rel_text = " ".join(f"{r.get('PK')} {r.get('FK')}" for r in rels)
    date_table = rules.get("date_table", "Date")
    has_date = f"'{date_table}'[" in rel_text
    out.append(_finding(L, "Date table related to the facts", PASS if has_date else FAIL,
                        f"'{date_table}' {'is' if has_date else 'is not'} in an active relationship. "
                        "Fabric IQ doesn't show whether it's marked as a date table; check that in the model",
                        "Model design"))
    tables = [t["Name"] for t in schema.get("Tables", [])]
    orphans = [t for t in tables if f"'{t}'[" not in rel_text]
    out.append(_finding(L, "Every table is related", WARN if orphans else PASS,
                        ", ".join(orphans) or f"{len(rels)} active relationships", "Model design"))
    bidi = [f"{r.get('PK')} - {r.get('FK')}" for r in rels if "UnidirectionalFilter" not in r]
    out.append(_finding(L, "Single-direction relationships", WARN if bidi else PASS,
                        ", ".join(bidi) or "All relationships filter one way", "Model design"))

    # AI instructions.
    ai = (schema.get("CustomInstructions") or "").strip()
    cfg = rules.get("ai_instructions", {})
    if not ai:
        out.append(_finding(L, "AI instructions present", FAIL, "No AI instructions on the model", "AI instructions"))
    else:
        limit = cfg.get("max_chars", 10000)
        out.append(_finding(L, "AI instructions present", PASS if len(ai) <= limit else FAIL,
                            f"{len(ai):,} of {limit:,} characters", "AI instructions"))
        absent = [t for t in cfg.get("must_mention", []) if t.lower() not in ai.lower()]
        out.append(_finding(L, "AI instructions cover the business terms", FAIL if absent else PASS,
                            ("Not mentioned: " + ", ".join(absent)) if absent
                            else f"All {len(cfg.get('must_mention', []))} terms covered", "AI instructions"))
        unknown = [o for o in cfg.get("referenced_objects", []) if o.lower() not in all_names]
        out.append(_finding(L, "Objects named in AI instructions exist", FAIL if unknown else PASS,
                            ("Not in the AI schema: " + ", ".join(unknown)) if unknown
                            else f"All {len(cfg.get('referenced_objects', []))} referenced objects exist",
                            "AI instructions"))
        repo_file = (base_dir / cfg["source_of_truth"]).resolve() if cfg.get("source_of_truth") else None
        repo_text = _repo_instructions(repo_file) if repo_file else None
        if repo_file and repo_text is None:
            out.append(_finding(L, "AI instructions match source control", WARN,
                                f"source_of_truth file not found: {repo_file}", "AI instructions"))
        if repo_text is not None:
            only_repo = sorted(_lines(repo_text) - _lines(ai))
            only_model = sorted(_lines(ai) - _lines(repo_text))
            drift = only_repo or only_model
            detail = "Deployed text matches the repository" if not drift else (
                f"{len(only_repo)} line(s) only in the repo, {len(only_model)} only in the model. "
                + " | ".join([f"repo: {x}" for x in only_repo] + [f"model: {x}" for x in only_model]))
            out.append(_finding(L, "AI instructions match source control", WARN if drift else PASS, detail,
                                "AI instructions"))

    # Verified answers. Fabric IQ didn't return them in our tests, Copilot with Fabric IQ doesn't use them, and
    # Microsoft doesn't support them through REST APIs or Git. So a missing section is information, not a failure.
    va_cfg = rules.get("verified_answers", {})
    if "VerifiedAnswers" not in schema:
        out.append(_finding(L, "Verified answers", INFO,
                            "Fabric IQ returns no verified answers, so agents that use Fabric IQ don't see them. "
                            "Verified answers still serve Copilot in Power BI without Fabric IQ. Check them in "
                            "Prep data for AI > Verified answers, and test them in the Copilot pane",
                            "Verified answers"))
        return out
    vas = schema.get("VerifiedAnswers") or []
    minimum = va_cfg.get("min_count", 1)
    out.append(_finding(L, "Verified answers present", PASS if len(vas) >= minimum else FAIL,
                        f"{len(vas)} verified answer(s), expected at least {minimum}", "Verified answers"))
    va_text = " ".join(f"{v.get('Title', '')} {v.get('Question', '')}" for v in vas).lower()
    missing_va = [e for e in va_cfg.get("expected", []) if e.lower() not in va_text]
    if va_cfg.get("expected"):
        out.append(_finding(L, "Expected verified answers exist", FAIL if missing_va else PASS,
                            ("Missing: " + ", ".join(missing_va)) if missing_va else "All expected answers exist",
                            "Verified answers"))
    return out


def value_grounding(client: FabricIQClient, model_id: str, probes: list[dict]) -> list[dict]:
    L = "L2 grounding"
    out = []
    terms = [p["term"] for p in probes]
    results = {}
    for i in range(0, len(terms), 20):
        batch = client.value_search(model_id, terms[i:i + 20]).get("Results", {})
        results.update({k.lower(): v for k, v in batch.items()})
    for p in probes:
        hits = sorted(results.get(p["term"].lower(), []) or [], key=lambda h: -h.get("Score", 0))
        if not hits:
            out.append(_finding(L, f"'{p['term']}'", FAIL, "No match in the model", p.get("feature", "")))
            continue
        top_score = hits[0].get("Score", 0)
        ties = [h for h in hits if h.get("Score", 0) >= top_score - 1e-9]

        def is_expected(h):
            return (h["Table"].lower() == p["expected_table"].lower()
                    and h["Column"].lower() == p["expected_column"].lower()
                    and str(h["Value"]).lower() == p["expected_value"].lower())

        top = next((h for h in ties if is_expected(h)), hits[0])
        ok = is_expected(top)
        where = f"{top['Table']}[{top['Column']}] = {top['Value']}"
        rivals = [h for h in hits if h is not top and h.get("Score", 0) >= 0.5
                  and (h["Table"], h["Column"]) != (top["Table"], top["Column"])]
        status = FAIL if not ok else (WARN if rivals else PASS)
        detail = f"Top match {where} (score {top.get('Score', 0):.2f})"
        if not ok:
            detail += f"; expected {p['expected_table']}[{p['expected_column']}] = {p['expected_value']}"
        if rivals:
            detail += "; also close: " + ", ".join(
                f"{h['Table']}[{h['Column']}] = {h['Value']} ({h.get('Score', 0):.2f})" for h in rivals)
        out.append(_finding(L, f"'{p['term']}'", status, detail, p.get("feature", "")))
    return out


def _numeric_cells(rows: list[dict]) -> list[float]:
    cells = []
    for row in rows:
        for v in row.values():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                cells.append(float(v))
            elif isinstance(v, str):
                # A column alias equal to a measure name returns the measure's formatted, locale-specific text.
                cells.extend(n for n, is_pct in extract_numbers(v) if not is_pct)
    return cells


def ground_truth(client: FabricIQClient, model_id: str, cases: list[dict]) -> list[dict]:
    L = "L3 ground truth"
    out = []
    for case in cases:
        dax = (case.get("reference_dax") or "").strip()
        expected = parse_expected(case.get("expected_values", ""))
        if not dax or not expected:
            continue
        try:
            cells = _numeric_cells(client.execute(model_id, dax))
        except FabricIQError as exc:
            out.append(_finding(L, case["id"], FAIL, f"Reference DAX failed: {exc}", case.get("feature", "")))
            continue
        misses = []
        for value, is_pct in expected:
            tol = 0.00005 if is_pct else max(abs(value) * 0.0001, 0.01)
            if not any(abs(c - value) <= tol for c in cells):
                misses.append(f"{value:.4%}" if is_pct else f"{value:,.2f}")
        detail = (f"Model returns the expected value(s) for: {case['question']}" if not misses
                  else f"Expected {', '.join(misses)}; model returned {', '.join(f'{c:,.4f}' for c in cells[:6])}")
        out.append(_finding(L, case["id"], FAIL if misses else PASS, detail, case.get("feature", "")))
    return out
