"""L4 agent evals: run GitHub Copilot CLI headless as the agent under test.

Copilot CLI answers each question with the Fabric IQ MCP tools (and the fabriciq skill
from Skills for Fabric, when installed). The JSONL event stream gives the final answer
plus every tool call, so the scorer can check both the answer and the DAX behind it.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from fabriciq_client import ENDPOINT, TOOLSET

PROMPT = """Answer a business question from the Power BI semantic model "{name}" (semantic model ID {model_id}).
Use the fabriciq skill if it is available, and use only the FabricIQ MCP tools to get data.
Reply to the business user with your final answer.

Question: {question}"""


def copilot_command() -> list[str]:
    override = os.environ.get("COPILOT_CLI_PATH")
    if override:
        return [override]
    found = shutil.which("copilot")
    if not found:
        raise RuntimeError("GitHub Copilot CLI not found. Install it: npm install -g @github/copilot")
    if os.name == "nt":
        # Call node directly so prompts with % or quotes don't pass through cmd.exe.
        base = Path(found).parent
        loader = base / "node_modules" / "@github" / "copilot" / "npm-loader.js"
        if loader.exists():
            node = base / "node.exe"
            return [str(node) if node.exists() else (shutil.which("node") or "node"), str(loader)]
        cmd = shutil.which("copilot.cmd")
        return [cmd] if cmd else [found]
    return [found]


def _mcp_config(token: str) -> dict:
    return {
        "mcpServers": {
            "FabricIQ": {
                "type": "http",
                "url": ENDPOINT,
                "headers": {"Authorization": f"Bearer {token}", "X-Variants": TOOLSET},
                "tools": ["*"],
            }
        }
    }


THROTTLE_HINTS = ("RequestBlocked", "blocked by the upstream", "429", "Throttl", "rate limit", "rate-limit")
BLOCKED_UNTIL = re.compile(r"until:\s*([0-9/]+ [0-9:]+ [AP]M) \(UTC\)")


def _blocked_until(message: str) -> float | None:
    m = BLOCKED_UNTIL.search(message)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%m/%d/%Y %I:%M:%S %p").replace(tzinfo=timezone.utc).timestamp()
    except ValueError:
        return None


def parse_events(lines: list[str]) -> dict:
    answer, dax, tools, errors, llm = "", [], [], [], ""
    throttled, blocked_until = False, None
    started = {}
    for line in lines:
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind, data = event.get("type"), event.get("data") or {}
        if kind == "tool.execution_start":
            name = data.get("mcpToolName") or data.get("toolName", "")
            started[data.get("toolCallId")] = name
            tools.append(name)
            if name == "ExecuteQuery":
                dax.extend((data.get("arguments") or {}).get("daxQueries", []))
        elif kind == "tool.execution_complete":
            payload = json.dumps(data.get("error") or data.get("result") or "")
            if any(h.lower() in payload.lower() for h in THROTTLE_HINTS):
                throttled = True
                blocked_until = _blocked_until(payload) or blocked_until
            if not data.get("success", True):
                errors.append(f"{started.get(data.get('toolCallId'), 'tool')} failed")
        elif kind == "assistant.message":
            llm = data.get("model") or llm
            if data.get("content") and not data.get("toolRequests"):
                answer = data["content"]
    return {"answer": answer.strip(), "dax": dax, "tools": tools, "tool_errors": errors, "llm": llm,
            "throttled": throttled, "blocked_until": blocked_until}


def run_question(question: str, model_id: str, model_name: str, token: str,
                 llm: str | None = None, timeout: int = 420, trace_path: Path | None = None) -> dict:
    workdir = Path(tempfile.mkdtemp(prefix="ai-readiness-"))
    config = workdir / "mcp-config.json"
    config.write_text(json.dumps(_mcp_config(token)), encoding="utf-8")
    cmd = copilot_command() + [
        "-p", PROMPT.format(name=model_name, model_id=model_id, question=question),
        "--additional-mcp-config", f"@{config}",
        "--allow-tool=FabricIQ", "--allow-tool=skill",
        "--no-ask-user", "--no-color", "--no-custom-instructions",
        "--output-format", "json",
    ]
    if llm:
        cmd += ["--model", llm]
    start = time.time()
    try:
        proc = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout)
        lines = proc.stdout.splitlines()
        result = parse_events(lines)
        if proc.returncode != 0 and not result["answer"]:
            result["tool_errors"].append(f"copilot exited {proc.returncode}: {proc.stderr.strip()[:300]}")
    except subprocess.TimeoutExpired:
        lines = []
        result = {"answer": "", "dax": [], "tools": [], "tool_errors": [f"timeout after {timeout}s"], "llm": llm or "",
                  "throttled": False, "blocked_until": None}
    finally:
        shutil.rmtree(workdir, ignore_errors=True)  # removes the token file
    result["seconds"] = round(time.time() - start, 1)
    if trace_path:
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        trace_path.write_text("\n".join(lines), encoding="utf-8")
    return result


JUDGE_PROMPT = """You grade answers from an AI assistant that answers business questions from a Power BI semantic model.
Given the question, the expected answer and the actual answer, decide whether the actual answer is equivalent to the expected answer.
Before you compare amounts, convert both to the same unit: k = thousand, M = million.
Amounts are equal only if they match after rounding to the precision used in the expected answer.
A different order of magnitude is NOT equivalent. Ignore currency symbols and thousands separators.
If the actual answer contains the expected facts plus extra correct context, it is equivalent.
If the expected answer describes a behaviour (for example, asking a clarifying question), judge whether the actual answer shows it.
Reply with exactly one word: yes or no.

Question: {question}

Expected answer:
{expected}

Actual answer:
{actual}"""


def judge(question: str, expected: str, actual: str, llm: str | None = None, timeout: int = 180) -> bool | None:
    """Optional LLM critic, like the data agent evaluation SDK. Uses Copilot CLI with no tools."""
    workdir = Path(tempfile.mkdtemp(prefix="ai-readiness-judge-"))
    cmd = copilot_command() + [
        "-p", JUDGE_PROMPT.format(question=question, expected=expected, actual=actual or "(no answer)"),
        "-s", "--no-ask-user", "--no-color", "--no-custom-instructions", "--disable-builtin-mcps",
    ]
    if llm:
        cmd += ["--model", llm]
    try:
        proc = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout)
        verdict = proc.stdout.strip().lower()
    except subprocess.TimeoutExpired:
        return None
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    if verdict.startswith("yes") or verdict.endswith("yes") or verdict.endswith("yes."):
        return True
    if verdict.startswith("no") or verdict.endswith("no") or verdict.endswith("no."):
        return False
    return None
