"""Project-local checks and evidence-bearing BD completion (stdlib only).
Not a sandbox: hooks, this script and configuration can be bypassed.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def run(argv):
    return subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace")


def git(*args):
    result = run(["git", *args])
    if result.returncode:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def fingerprint():
    # Include tracked working-tree contents AND non-ignored untracked files.
    paths = set(git("ls-files", "--cached", "--others", "--exclude-standard", "-z").split("\0"))
    digest = hashlib.sha256()
    for name in sorted(paths - {""}):
        path = Path(name)
        digest.update(name.encode("utf-8") + b"\0")
        if path.is_symlink():
            digest.update(str(path.readlink()).encode("utf-8"))
        elif path.is_file():
            digest.update(path.read_bytes())
        else:
            digest.update(b"<missing-or-directory>")
    digest.update(git("diff", "--cached", "--binary").encode("utf-8"))
    return digest.hexdigest()


def initialize(command):
    config = Path("scripts/dev-check.json")
    hooks = git("rev-parse", "--git-path", "hooks")
    hook = Path(hooks) / "pre-commit"
    if config.exists() or hook.exists():
        raise RuntimeError("Existing config or pre-commit hook: integrate manually; nothing overwritten")
    if not command or not Path("scripts/dev_gate.py").is_file():
        raise RuntimeError("Copy dev_gate.py into scripts/ and supply a real check command after --")
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(json.dumps({"command": command, "timeout_seconds": 600}, indent=2) + "\n", encoding="utf-8")
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text('#!/bin/sh\nexec python scripts/dev_gate.py check\n', encoding="utf-8")
    hook.chmod(0o755)
    print("Initialized. Uses python on PATH. Run check before relying on the hook.")


def check(issue=None):
    config = json.loads(Path("scripts/dev-check.json").read_text(encoding="utf-8"))
    command = config["command"]
    if not isinstance(command, list) or not command or not all(isinstance(x, str) and x for x in command):
        raise RuntimeError("command must be a nonempty argument array; no shell evaluation")
    if issue:
        found = run(["bd", "show", issue, "--json"])
        if found.returncode:
            raise RuntimeError(found.stderr.strip() or found.stdout.strip())
    head = git("rev-parse", "--verify", "HEAD") if run(["git", "rev-parse", "--verify", "HEAD"]).returncode == 0 else "unborn"
    before = fingerprint()
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=config["timeout_seconds"])
    after = fingerprint()
    evidence = {"time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "issue": issue, "head": head, "fingerprint_before": before, "fingerprint_after": after, "command": command, "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
    # Local evidence outside versioned files; may contain private output: do not auto-publish.
    store = Path(git("rev-parse", "--git-path", "rick-dev-evidence"))
    store.mkdir(parents=True, exist_ok=True)
    receipt = store / (datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%f") + ".json")
    receipt.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(result.stdout, end="")
    print(result.stderr, end="", file=sys.stderr)
    print("Evidence:", receipt)
    if result.returncode or before != after:
        raise RuntimeError("Check failed or changed source/index; BD was not closed. Inspect and rerun.")
    if issue:
        reason = f"Project check passed; HEAD={head}; worktree_sha256={after}; command={json.dumps(command)}; local_evidence={receipt}"
        closed = run(["bd", "close", issue, "--reason", reason])
        if closed.returncode:
            raise RuntimeError(closed.stderr.strip() or closed.stdout.strip())
        readback = run(["bd", "show", issue, "--json"])
        if readback.returncode:
            raise RuntimeError("Close requested but readback failed; inspect BD status")
        value = json.loads(readback.stdout)
        records = value if isinstance(value, list) else [value]
        if not any(x.get("id") == issue and x.get("status") == "closed" for x in records):
            raise RuntimeError("BD closed status was not confirmed")
        print("BD closed status confirmed:", issue)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    init = sub.add_parser("init")
    init.add_argument("command", nargs=argparse.REMAINDER)
    sub.add_parser("check")
    done = sub.add_parser("done")
    done.add_argument("issue")
    args = parser.parse_args()
    root = git("rev-parse", "--show-toplevel")
    import os
    os.chdir(root)
    if args.action == "init":
        initialize(args.command[1:] if args.command[:1] == ["--"] else args.command)
    else:
        check(args.issue if args.action == "done" else None)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
        print("BLOCKED:", exc, file=sys.stderr)
        sys.exit(1)
