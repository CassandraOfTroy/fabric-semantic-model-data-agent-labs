"""Show what Fabric IQ gives an AI agent for a semantic model, next to what the model stores.

Read-only. Use it to check the Lab 3 readiness lint yourself:
  - AI instructions:   Fabric IQ CustomInstructions vs the model's linguistic schema (LSDL)
  - Verified answers:  does Fabric IQ return any?
  - AI data schema:    fields Fabric IQ returns vs fields hidden in the model or hidden from AI

Usage
  python inspect_model.py --model <semantic model ID or URL>
  python inspect_model.py --model <ID> --no-definition     # Fabric IQ only, no Fabric REST call
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import shutil
import subprocess
import time

import requests

from fabriciq_client import FabricIQClient
from model_checks import relationship_columns

FABRIC_API = "https://api.fabric.microsoft.com"


def fabric_token() -> str:
    az = shutil.which("az") or shutil.which("az.cmd")
    out = subprocess.run([az, "account", "get-access-token", "--resource", FABRIC_API, "--query", "accessToken",
                          "-o", "tsv"], capture_output=True, text=True)
    return out.stdout.strip()


def get_definition(workspace_id: str, model_id: str) -> dict[str, str]:
    """Download the model definition (TMDL). Needs write access (Contributor or higher) on the model."""
    h = {"Authorization": f"Bearer {fabric_token()}"}
    url = f"{FABRIC_API}/v1/workspaces/{workspace_id}/semanticModels/{model_id}/getDefinition?format=TMDL"
    r = requests.post(url, headers=h, timeout=120)
    if r.status_code == 202:
        loc = r.headers["Location"]
        while True:
            time.sleep(3)
            state = requests.get(loc, headers=h, timeout=60).json()
            if state.get("status") not in ("Running", "NotStarted"):
                break
        r = requests.get(loc + "/result", headers=h, timeout=120)
    r.raise_for_status()
    return {p["path"]: base64.b64decode(p["payload"]).decode("utf-8", "replace")
            for p in r.json()["definition"]["parts"]}


def lsdl_from(parts: dict[str, str]) -> dict:
    for path, text in parts.items():
        if path.startswith("definition/cultures/") and "linguisticMetadata" in text:
            start = text.index("{", text.index("linguisticMetadata"))
            return json.JSONDecoder().raw_decode(text[start:].replace("\t", ""))[0]
    return {}


def hidden_in_model(parts: dict[str, str]) -> set[str]:
    hidden = set()
    for path, text in parts.items():
        if not path.startswith("definition/tables/"):
            continue
        table = re.search(r"^table\s+'?([^'\n]+?)'?\s*$", text, re.M).group(1)
        for m in re.finditer(r"^\t(column|measure)\s+'?([^'=\n]+?)'?\s*(=.*)?\n((?:\t\t.*\n|\s*\n)*)", text, re.M):
            if re.search(r"^\t\tisHidden\s*$", m.group(4), re.M):
                hidden.add(f"{table}[{m.group(2).strip()}]")
    return hidden


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", required=True, help="Semantic model ID or browser URL")
    p.add_argument("--no-definition", action="store_true", help="Skip the model definition download")
    args = p.parse_args()

    fiq = FabricIQClient()
    item = fiq.resolve(args.model)
    model_id, ws = item["fabricItemId"], item.get("workspaceId")
    doc = fiq.schema(model_id)
    s = doc["schema"]
    print(f"\n=== Fabric IQ: {doc.get('semanticModel', {}).get('Name')} ({model_id})")
    print("Sections returned:", ", ".join(s.keys()))

    returned = set()
    for t in s.get("Tables", []):
        for c in t.get("Columns", []) or []:
            returned.add(f"{t['Name']}[{c['Name']}]")
        for m in t.get("Measures", []) or []:
            returned.add(f"{t['Name']}[{m['Name']}]")
    print(f"Fields returned: {len(returned)}")

    ci = s.get("CustomInstructions") or ""
    print(f"\n--- AI instructions (CustomInstructions): {len(ci):,} characters")
    print(ci or "(none)")

    va = s.get("VerifiedAnswers")
    print("\n--- Verified answers:", "section not returned" if va is None else f"{len(va)}")
    for v in va or []:
        print(f"  - {v.get('Title')}: {v.get('Question')}")

    if args.no_definition or not ws:
        return
    print("\n=== Model definition (Fabric REST getDefinition, read-only)")
    try:
        parts = get_definition(ws, model_id)
    except requests.HTTPError as exc:
        print(f"Couldn't download the definition ({exc}). You need Contributor or higher on the workspace.")
        return
    lsdl = lsdl_from(parts)
    stored = lsdl.get("CustomInstructions") or ""
    print(f"AI instructions stored in the model: {len(stored):,} characters; "
          f"identical to Fabric IQ: {stored == ci}")
    va_hits = [p for p, t in parts.items() if re.search(r"(?i)verified", t)]
    print("Verified answers in the definition:", ", ".join(va_hits) or "none found")

    ai_hidden = set()
    for ent in lsdl.get("Entities", {}).values():
        if ent.get("Visibility", {}).get("Value") == "Hidden":
            b = ent.get("Definition", {}).get("Binding", {})
            if b.get("ConceptualProperty"):
                ai_hidden.add(f"{b['ConceptualEntity']}[{b['ConceptualProperty']}]")
    model_hidden = hidden_in_model(parts)
    rel_cols = {f"{t}[{c}]" for t, c in relationship_columns(s)}
    ai_only, model_only, both = ai_hidden - model_hidden, model_hidden - ai_hidden, ai_hidden & model_hidden

    def returned_count(fields):
        hits = fields & returned
        keys = hits & rel_cols
        return f"{len(hits)} returned by Fabric IQ ({len(keys)} of them relationship columns)"

    print(f"\nHidden in the model (isHidden): {len(model_hidden)}")
    print(f"Hidden from AI (Prep data for AI > Simplify the data schema): {len(ai_hidden)}")
    print(f"  hidden from AI only:    {len(ai_only):>3}, {returned_count(ai_only)}")
    print(f"  hidden in model only:   {len(model_only):>3}, {returned_count(model_only)}")
    print(f"  hidden in both:         {len(both):>3}, {returned_count(both)}")
    rows = sorted(model_hidden | ai_hidden)
    print(f"\n{'Field':<34}{'hidden in model':<17}{'hidden from AI':<16}returned by Fabric IQ")
    for f in rows:
        print(f"{f:<34}{'yes' if f in model_hidden else '':<17}{'yes' if f in ai_hidden else '':<16}"
              f"{'RETURNED' if f in returned else ''}")


if __name__ == "__main__":
    main()
