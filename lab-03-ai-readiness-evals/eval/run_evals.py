"""Evaluate how ready a Power BI semantic model is for AI, using only the Fabric IQ MCP server.

Layers
  lint       L1  readiness lint of what Fabric IQ exposes (no LLM)
  grounding  L2  business terms resolve to the right column and value (no LLM)
  truth      L3  reference DAX returns the expected numbers (no LLM)
  agent      L4  GitHub Copilot CLI answers the test questions through Fabric IQ, scored per run

Examples
  python run_evals.py --model REF_Sales_Model --layers lint,grounding,truth
  python run_evals.py --model <semantic-model-guid-or-url> --repeat 3 --parallel 3
  python run_evals.py --model REF_Sales_Model --questions Q02,Q05 --judge
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from agent_eval import judge, run_question
from fabriciq_client import FabricIQClient, FabricIQError, get_token
from model_checks import FAIL, PASS, WARN, discoverability, ground_truth, readiness_lint, value_grounding
from scoring import score_case

LAB = Path(__file__).resolve().parent.parent
GUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
FIX_HINTS = {
    "AI data schema": "Prep data for AI > Simplify the data schema",
    "AI instructions": "Prep data for AI > Add AI instructions",
    "Verified answers": "Report visual > ... > Set up a verified answer",
    "Descriptions": "Model descriptions (Copilot reads the first 200 characters)",
    "Value grounding": "Column values, names and synonyms in the model",
    "Model design": "Model relationships, date table and formats",
    "Groundedness": "AI instructions: say what the model doesn't contain",
    "Discoverability": "Model name, description, endorsement and Approved for Copilot",
}


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        return
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def resolve_model(client: FabricIQClient, ref: str) -> dict:
    if GUID.match(ref) or ref.lower().startswith("http"):
        item = client.resolve(ref)
        if item.get("itemType") != "SemanticModel":
            raise FabricIQError(f"{ref} is a {item.get('itemType')}. Pass a semantic model.")
        model_id = item["fabricItemId"]
    else:
        found = client.discover(ref)
        items = found.get("artifacts") or found.get("Artifacts") or []
        exact = [a for a in items if str(a.get("Name", "")).lower() == ref.lower()]
        if not exact:
            seen = ", ".join(a.get("Name", "?") for a in items) or "nothing"
            raise FabricIQError(f"Search for '{ref}' found {seen}, but no semantic model with that exact name. "
                                "Pass the semantic model ID or its browser URL instead.")
        if len(exact) > 1:
            raise FabricIQError(f"{len(exact)} semantic models are named '{ref}'. Pass the ID or URL instead.")
        model_id = exact[0]["ArtifactId"]
    schema_doc = client.schema(model_id)
    name = (schema_doc.get("semanticModel") or {}).get("Name", ref)
    return {"id": model_id, "name": name, "schema": schema_doc}


def feature_group(feature: str) -> str:
    for key in FIX_HINTS:
        if feature.lower().startswith(key.lower()):
            return key
    return feature or "Other"


def run_agent_layer(cases, model, repeat, parallel, llm, use_judge, out_dir, max_attempts=3) -> list[dict]:
    jobs = [(c, r) for c in cases for r in range(1, repeat + 1)]
    pause = {"until": 0.0}
    lock = threading.Lock()

    def wait_if_blocked():
        while True:
            with lock:
                delay = pause["until"] - time.time()
            if delay <= 0:
                return
            time.sleep(min(delay, 30))

    def work(job):
        case, run = job
        for attempt in range(1, max_attempts + 1):
            wait_if_blocked()
            token = get_token()  # refreshed per run; long evaluations outlive one token
            try:
                res = run_question(case["question"], model["id"], model["name"], token, llm=llm,
                                   trace_path=out_dir / "traces" / f"{case['id']}-run{run}.jsonl")
            except Exception as exc:  # one broken run must not stop the batch
                res = {"answer": "", "dax": [], "tools": [], "tool_errors": [f"runner error: {exc}"],
                       "llm": llm or "", "seconds": 0, "throttled": False, "blocked_until": None}
            if not res.get("throttled") or attempt == max_attempts:
                break
            until = res.get("blocked_until") or time.time() + 60 * attempt
            with lock:
                pause["until"] = max(pause["until"], until + 5)
            print(f"  {case['id']} run {run}: throttled by Power BI, pausing until "
                  f"{datetime.fromtimestamp(pause['until']):%H:%M:%S} (attempt {attempt}/{max_attempts})", flush=True)

        if res.get("throttled"):
            status, score, verdict = "ERROR", {"passed": False, "notes": ["throttled by Power BI"]}, None
        else:
            score = score_case(case, res["answer"], res["dax"])
            verdict = judge(case["question"], case["expected_answer"], res["answer"], llm) if use_judge else None
            ok = score["passed"] and (verdict is not False) and not (res["tool_errors"] and not res["answer"])
            status = "PASS" if ok else "FAIL"
        print(f"  {case['id']} run {run}: {status} ({res['seconds']}s)", flush=True)
        return {
            "id": case["id"], "run": run, "feature": case["feature"], "question": case["question"],
            "expected": case["expected_answer"], "status": status, "passed": status == "PASS",
            "checks_passed": score["passed"], "judge": "" if verdict is None else verdict,
            "notes": "; ".join(score["notes"] + res["tool_errors"]),
            "answer": res["answer"], "dax": "\n---\n".join(res["dax"]),
            "tools": " > ".join(res["tools"]), "llm": res["llm"], "seconds": res["seconds"],
        }

    with ThreadPoolExecutor(max_workers=max(1, parallel)) as pool:
        runs = list(pool.map(work, jobs))
    return sorted(runs, key=lambda r: (r["id"], r["run"]))


def md_escape(text: str, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", str(text)).replace("|", "\\|")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def build_report(model, findings, runs, args, started) -> str:
    icon = {PASS: "✅", WARN: "⚠️", FAIL: "❌"}
    lines = [
        f"# AI readiness evaluation: {model['name']}",
        "",
        f"- **Semantic model:** {model['name']} (`{model['id']}`)",
        f"- **Run:** {started:%Y-%m-%d %H:%M} · layers `{args.layers}` · repeat {args.repeat}"
        + (f" · agent LLM `{runs[0]['llm']}`" if runs and runs[0].get("llm") else ""),
        "- **Data access:** Fabric IQ MCP only, as the signed-in user",
        "",
        "## Scorecard",
        "",
        "| Layer | Pass | Warn | Fail | Score |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    by_layer = defaultdict(list)
    for f in findings:
        by_layer[f["layer"]].append(f["status"])
    for layer, st in by_layer.items():
        lines.append(f"| {layer} | {st.count(PASS)} | {st.count(WARN)} | {st.count(FAIL)} | "
                     f"{(st.count(PASS) + 0.5 * st.count(WARN)) / len(st):.0%} |")
    scored = [r for r in runs if r["status"] != "ERROR"]
    errors = len(runs) - len(scored)
    if runs:
        ok = sum(r["passed"] for r in scored)
        rate = f"{ok / len(scored):.0%}" if scored else "–"
        lines.append(f"| L4 agent | {ok} | – | {len(scored) - ok} | {rate} |")
        if errors:
            lines += ["", f"> {errors} agent run(s) were throttled by Power BI and are excluded from the scores. "
                          "Rerun them with `--questions` and a lower `--parallel`."]

    feats = defaultdict(lambda: [0, 0])
    for f in findings:
        g = feature_group(f["feature"])
        feats[g][0] += f["status"] == PASS
        feats[g][1] += 1
    for r in scored:
        g = feature_group(r["feature"])
        feats[g][0] += bool(r["passed"])
        feats[g][1] += 1
    lines += ["", "## By Prep data for AI feature", "", "| Feature | Passed | Where to fix |", "| --- | ---: | --- |"]
    for g, (p, n) in sorted(feats.items(), key=lambda kv: kv[1][0] / kv[1][1]):
        lines.append(f"| {g} | {p}/{n} ({p / n:.0%}) | {FIX_HINTS.get(g, '')} |")

    for layer in by_layer:
        lines += ["", f"## {layer}", "", "| | Check | Detail |", "| --- | --- | --- |"]
        for f in [x for x in findings if x["layer"] == layer]:
            lines.append(f"| {icon[f['status']]} | {md_escape(f['check'], 80)} | {md_escape(f['detail'], 600)} |")

    if runs:
        lines += ["", "## L4 agent", "", "| | ID | Feature | Question | Pass rate | Notes |",
                  "| --- | --- | --- | --- | ---: | --- |"]
        grouped = defaultdict(list)
        for r in runs:
            grouped[r["id"]].append(r)
        for cid, rs in grouped.items():
            done = [r for r in rs if r["status"] != "ERROR"]
            ok = sum(r["passed"] for r in done)
            mark = "⏳" if not done else ("✅" if ok == len(done) else ("⚠️" if ok else "❌"))
            notes = sorted({n for r in rs for n in r["notes"].split("; ") if n})
            rate = f"{ok}/{len(done)}" + (f" (+{len(rs) - len(done)} throttled)" if len(done) < len(rs) else "")
            lines.append(f"| {mark} | {cid} | {rs[0]['feature']} | {md_escape(rs[0]['question'], 90)} | "
                         f"{rate} | {md_escape('; '.join(notes), 200)} |")
        failed = [r for r in runs if r["status"] == "FAIL"]
        if failed:
            lines += ["", "### Failed runs", ""]
            for r in failed:
                lines += [f"**{r['id']} run {r['run']}**: {r['question']}", "",
                          f"- Expected: {r['expected']}", f"- Answer: {md_escape(r['answer'], 500)}",
                          f"- Notes: {r['notes'] or '–'}", f"- Tools: {r['tools'] or '–'}"]
                if r["dax"]:
                    lines += ["", "```dax", r["dax"].strip()[:1500], "```"]
                lines.append("")
    lines += ["", "Traces: `traces/` (Copilot CLI JSONL per run). Raw rows: `findings.csv`, `agent-runs.csv`."]
    return "\n".join(lines) + "\n"


def rescore(run_dir: Path, testset: Path, args) -> int:
    """Re-apply the scoring rules to a saved run, without calling Fabric IQ or the agent again."""
    cases = {c["id"]: c for c in read_csv(testset / "questions.csv")}
    schema_doc = json.loads((run_dir / "schema.json").read_text(encoding="utf-8"))
    sm = schema_doc.get("semanticModel") or {}
    model = {"id": sm.get("ArtifactId", ""), "name": sm.get("Name", "")}
    findings = read_csv(run_dir / "findings.csv") if (run_dir / "findings.csv").exists() else []
    runs = read_csv(run_dir / "agent-runs.csv") if (run_dir / "agent-runs.csv").exists() else []
    for r in runs:
        r["run"] = int(r["run"])
        if r["status"] == "ERROR" or r["id"] not in cases:
            r["passed"] = False
            continue
        score = score_case(cases[r["id"]], r["answer"], [d for d in r["dax"].split("\n---\n") if d.strip()])
        ok = score["passed"] and r.get("judge") != "False"
        r.update(status="PASS" if ok else "FAIL", passed=ok, checks_passed=score["passed"],
                 notes="; ".join(score["notes"]))
    write_csv(run_dir / "agent-runs.csv", runs)
    started = datetime.strptime(run_dir.name, "%Y%m%d-%H%M%S")
    args.repeat = max((r["run"] for r in runs), default=1)
    (run_dir / "report.md").write_text(build_report(model, findings, runs, args, started), encoding="utf-8")
    scored = [r for r in runs if r["status"] != "ERROR"]
    if scored:
        print(f"L4 agent pass rate: {sum(r['passed'] for r in scored) / len(scored):.0%} "
              f"({sum(r['passed'] for r in scored)}/{len(scored)})")
    print(f"Report: {run_dir / 'report.md'}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", default=os.environ.get("FABRIC_SEMANTIC_MODEL"),
                   help="Semantic model name, ID or browser URL (or set FABRIC_SEMANTIC_MODEL)")
    p.add_argument("--layers", default="lint,grounding,truth,agent")
    p.add_argument("--questions", help="Comma-separated question IDs, for example Q01,Q05")
    p.add_argument("--repeat", type=int, default=1, help="Runs per question; answers are nondeterministic")
    p.add_argument("--parallel", type=int, default=1,
                   help="Agent runs at the same time. Power BI throttles bursts; keep it at 1-2")
    p.add_argument("--llm", help="Model for Copilot CLI, for example claude-sonnet-5 (default: CLI default)")
    p.add_argument("--judge", action="store_true", help="Also grade answers with an LLM critic (Copilot CLI)")
    p.add_argument("--testset", default=str(LAB / "testset"))
    p.add_argument("--out", default=str(LAB / "results"))
    p.add_argument("--fail-under", type=float, default=0.0,
                   help="Exit with code 1 if the L4 pass rate is below this value (0-1), or any L1-L3 check fails")
    p.add_argument("--rescore", metavar="RUN_DIR",
                   help="Re-score a saved run folder with the current test set, without calling Power BI")
    args = p.parse_args()
    if args.rescore:
        return rescore(Path(args.rescore), Path(args.testset), args)
    if not args.model:
        p.error("--model is required (name, ID or URL of the semantic model)")

    layers = {x.strip() for x in args.layers.split(",")}
    testset = Path(args.testset)
    rules = json.loads((testset / "readiness-rules.json").read_text(encoding="utf-8"))
    cases = read_csv(testset / "questions.csv")
    if args.questions:
        wanted = {q.strip().upper() for q in args.questions.split(",")}
        cases = [c for c in cases if c["id"].upper() in wanted]

    started = datetime.now()
    out_dir = Path(args.out) / started.strftime("%Y%m%d-%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)

    client = FabricIQClient()
    model = resolve_model(client, args.model)
    print(f"Semantic model: {model['name']} ({model['id']})")
    (out_dir / "schema.json").write_text(json.dumps(model["schema"], indent=2), encoding="utf-8")

    findings: list[dict] = []
    if "lint" in layers:
        print("L1 readiness lint")
        findings += readiness_lint(model["schema"], rules, LAB)
        findings += discoverability(client, model["id"], model["name"])
    if "grounding" in layers:
        print("L2 value grounding")
        findings += value_grounding(client, model["id"], read_csv(testset / "value-probes.csv"))
    if "truth" in layers:
        print("L3 ground truth")
        findings += ground_truth(client, model["id"], cases)
    runs: list[dict] = []
    if "agent" in layers:
        print(f"L4 agent: {len(cases)} question(s) x {args.repeat} run(s)")
        runs = run_agent_layer(cases, model, args.repeat, args.parallel, args.llm, args.judge, out_dir)

    write_csv(out_dir / "findings.csv", findings)
    write_csv(out_dir / "agent-runs.csv", runs)
    report = build_report(model, findings, runs, args, started)
    (out_dir / "report.md").write_text(report, encoding="utf-8")

    for f in findings:
        print(f"  {f['status']:<4} {f['layer']:<16} {f['check']}: {f['detail'][:140]}")
    scored = [r for r in runs if r["status"] != "ERROR"]
    rate = sum(r["passed"] for r in scored) / len(scored) if scored else None
    if rate is not None:
        print(f"L4 agent pass rate: {rate:.0%} ({sum(r['passed'] for r in scored)}/{len(scored)})"
              + (f", {len(runs) - len(scored)} throttled run(s) excluded" if len(scored) < len(runs) else ""))
    print(f"Report: {out_dir / 'report.md'}")

    hard_fail = any(f["status"] == FAIL for f in findings)
    if args.fail_under and (hard_fail or (rate is not None and rate < args.fail_under)):
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except FabricIQError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)
