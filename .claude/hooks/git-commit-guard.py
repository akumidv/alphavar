#!/usr/bin/env python3
"""PreToolUse guard for D5 (owner owns commits) — durable, context-independent.

Runs on every Bash tool call regardless of how long the session is, so the rule
survives context growth. For git commands it:
- DENIES any ``Co-Authored-By`` trailer (never allowed; AGENTS.md "Commits"),
- ASKS the owner for ``push`` / ``tag`` / ``merge`` and for ``commit`` on the default
  branch (``main``/``master``) — these land history and need explicit per-time approval,
- lets ``commit`` on a backup/feature branch through to the normal permission flow.

The deny/ask reason re-states D5 at the moment it is relevant. See
docs/dev/DEVELOPMENT_REQUIREMENTS.md D5.
"""
import json
import re
import subprocess
import sys


def decide(decision: str, reason: str) -> None:
    json.dump({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }}, sys.stdout)
    sys.exit(0)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return  # never block on a parse error
    if payload.get("tool_name") != "Bash":
        return
    command = (payload.get("tool_input") or {}).get("command", "") or ""
    if "git" not in command:
        return

    if re.search(r"co-authored-by", command, re.IGNORECASE):
        decide("deny", "D5 / Commits: no AI 'Co-Authored-By' trailer — the committer is the "
                       "human. Remove it and retry.")

    def is_git(sub: str) -> bool:
        return re.search(r"\bgit\b[^|&;]*\b" + sub + r"\b", command) is not None

    if is_git("push") or is_git("tag") or is_git("merge"):
        decide("ask", "D5: the owner owns commits. push/tag/merge land history — confirm "
                      "this is explicitly requested.")

    if is_git("commit"):
        try:
            branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, timeout=5,
            ).stdout.strip()
        except (subprocess.SubprocessError, OSError):
            branch = ""
        if branch in ("main", "master") or not branch:
            decide("ask", f"D5: the owner owns commits. A commit on '{branch or 'detached HEAD'}' "
                          "is a landing commit — confirm explicitly, or branch to backup/* first.")
        # commit on a backup/feature branch: fall through to the normal permission flow.


if __name__ == "__main__":
    main()
