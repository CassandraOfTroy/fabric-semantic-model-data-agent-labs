"""
Create the folders in the workshop workspace: 00_Shared (shared lakehouse), REF (instructor's
reference items) and one folder per participant (P01..Pnn).

Uses the Fabric REST API "Folders - Create Folder" and an access token from the Azure CLI.
Run `az login` first. You need the Contributor role or higher on the workspace.

Usage:
    python scripts/create_participant_folders.py --workspace-id <guid> --count 25
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import urllib.error
import urllib.request

API = "https://api.fabric.microsoft.com/v1"


def get_token() -> str:
    az = shutil.which("az") or shutil.which("az.cmd")
    if not az:
        raise SystemExit("Azure CLI not found. Install it and run 'az login'.")
    out = subprocess.run(
        [az, "account", "get-access-token", "--resource", "https://api.fabric.microsoft.com", "--query", "accessToken", "-o", "tsv"],
        check=True, capture_output=True, text=True,
    )
    return out.stdout.strip()


def create_folder(token: str, workspace_id: str, name: str) -> str:
    request = urllib.request.Request(
        f"{API}/workspaces/{workspace_id}/folders",
        data=json.dumps({"displayName": name}).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            return f"created ({response.status})"
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", "replace")
        if "FolderDisplayNameAlreadyInUse" in body:
            return "already exists"
        return f"failed ({error.code}): {body[:200]}"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workspace-id", required=True,
                        help="ID of the workshop workspace (the GUID in the workspace URL)")
    parser.add_argument("--count", type=int, default=25, help="number of participant folders to create")
    args = parser.parse_args()

    token = get_token()
    for name in ["00_Shared", "REF"] + [f"P{i:02d}" for i in range(1, args.count + 1)]:
        print(f"{name:<4} {create_folder(token, args.workspace_id, name)}")


if __name__ == "__main__":
    main()
