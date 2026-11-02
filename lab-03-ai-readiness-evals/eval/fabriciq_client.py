"""Minimal Fabric IQ MCP client (Streamable HTTP, JSON-RPC) for scripted checks.

Fabric IQ MCP accepts delegated Microsoft Entra tokens only. This client uses the
token of the account signed in to the Azure CLI (`az login`), or the token in the
FABRICIQ_TOKEN environment variable.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time

import requests

ENDPOINT = os.environ.get("FABRICIQ_ENDPOINT", "https://fabriciq.svc.cloud.microsoft/v1/mcp/fabriciq")
TOOLSET = "Fabric.Routing.FabricIQ.V1"
POWER_BI_RESOURCE = "https://analysis.windows.net/powerbi/api"


class FabricIQError(RuntimeError):
    pass


def get_token() -> str:
    token = os.environ.get("FABRICIQ_TOKEN")
    if token:
        return token
    az = shutil.which("az") or shutil.which("az.cmd")
    if not az:
        raise FabricIQError("Azure CLI not found. Install it and run `az login`, or set FABRICIQ_TOKEN.")
    proc = subprocess.run(
        [az, "account", "get-access-token", "--resource", POWER_BI_RESOURCE, "--query", "accessToken", "-o", "tsv"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        raise FabricIQError(f"Could not get a token with the Azure CLI. Run `az login`.\n{proc.stderr.strip()}")
    return proc.stdout.strip()


class FabricIQClient:
    def __init__(self, token: str | None = None, endpoint: str = ENDPOINT):
        self.endpoint = endpoint
        self.token = token or get_token()
        self.session_id: str | None = None
        self._id = 0
        self._initialize()

    def _headers(self) -> dict:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "X-Variants": TOOLSET,
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        return headers

    def _post(self, payload: dict, retries: int = 3) -> dict | None:
        for attempt in range(retries):
            resp = requests.post(self.endpoint, headers=self._headers(), json=payload, timeout=180)
            if resp.status_code == 429 or resp.status_code >= 500:
                time.sleep(2 ** (attempt + 1))
                continue
            if resp.status_code >= 400:
                raise FabricIQError(f"HTTP {resp.status_code}: {resp.text[:500]}")
            if resp.headers.get("mcp-session-id"):
                self.session_id = resp.headers["mcp-session-id"]
            if "id" not in payload:
                return None
            return self._parse(resp)
        raise FabricIQError(f"Fabric IQ throttled or unavailable after {retries} attempts.")

    @staticmethod
    def _parse(resp: requests.Response) -> dict:
        if resp.headers.get("content-type", "").startswith("text/event-stream"):
            for line in resp.text.splitlines():
                if line.startswith("data:"):
                    message = json.loads(line[5:])
                    if "result" in message or "error" in message:
                        return message
            raise FabricIQError(f"No JSON-RPC result in the event stream: {resp.text[:300]}")
        return resp.json()

    def _initialize(self):
        self._id += 1
        self._post({
            "jsonrpc": "2.0",
            "id": self._id,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "ai-readiness-evals", "version": "1.0"},
            },
        })
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def call(self, tool: str, arguments: dict, retries: int = 4) -> dict:
        for attempt in range(retries):
            self._id += 1
            message = self._post({
                "jsonrpc": "2.0",
                "id": self._id,
                "method": "tools/call",
                "params": {"name": tool, "arguments": arguments},
            })
            if "error" in message:
                raise FabricIQError(f"{tool}: {message['error']}")
            result = message["result"]
            text = "".join(c.get("text", "") for c in result.get("content", []) if c.get("type") == "text")
            if result.get("isError"):
                if '"IsRetryable":true' in text.replace(" ", "") and attempt < retries - 1:
                    time.sleep(3 * (attempt + 1))
                    continue
                raise FabricIQError(f"{tool}: {text[:500]}")
            # Some tools return two JSON documents in one text block; keep the first.
            decoded, _ = json.JSONDecoder().raw_decode(text.strip())
            return decoded
        raise FabricIQError(f"{tool}: still failing after {retries} attempts")

    def resolve(self, item: str) -> dict:
        return self.call("ResolveFabricItem", {"fabricItemId": item})

    def discover(self, query: str) -> dict:
        return self.call("DiscoverArtifacts", {"searchQuery": query, "artifactTypes": ["SemanticModel"], "maxResults": 5})

    def schema(self, artifact_id: str) -> dict:
        return self.call("GetSemanticModelSchema", {"artifactId": artifact_id})

    def value_search(self, artifact_id: str, terms: list[str]) -> dict:
        return self.call("ValueSearch", {"artifactId": artifact_id, "searchTerms": terms})

    def execute(self, artifact_id: str, dax: str, max_rows: int = 250) -> list[dict]:
        out = self.call("ExecuteQuery", {"artifactId": artifact_id, "daxQueries": [dax], "maxRows": max_rows})
        tables = out.get("executionResult", {}).get("tables", [])
        if not tables:
            raise FabricIQError(f"ExecuteQuery returned no table: {json.dumps(out)[:500]}")
        table = tables[0]
        if "error" in table:
            raise FabricIQError(f"DAX error: {table['error']}")
        names = [c["name"] for c in table.get("columns", [])]
        return [dict(zip(names, row)) for row in table.get("rows", [])]
