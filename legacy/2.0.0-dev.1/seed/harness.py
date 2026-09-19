"""Fixed V2 command entry point. JSON requests, explicit actor and operation key."""
import argparse
import json
from pathlib import Path
import sqlite3
import sys

from core import ContractError, Kernel, encode

MUTATIONS = ("init", "object", "task", "run", "observe", "resume", "mvp", "checkpoint", "propose", "evaluate", "adopt", "rollback", "reconcile")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path.cwd())
    sub = p.add_subparsers(dest="command", required=True)
    for name in MUTATIONS:
        s = sub.add_parser(name)
        s.add_argument("--data", type=Path, required=True)
        s.add_argument("--actor", required=True)
        s.add_argument("--key", required=True)
    sub.add_parser("view")
    sub.add_parser("wiki")
    sub.add_parser("audit")
    resolve = sub.add_parser("resolve")
    resolve.add_argument("--task", required=True)
    resolve.add_argument("--command", dest="resolve_command", required=True)
    backup = sub.add_parser("backup")
    backup.add_argument("--out", type=Path, required=True)
    restore = sub.add_parser("restore")
    restore.add_argument("--source", type=Path, required=True)
    restore.add_argument("--sha256", required=True)
    a = p.parse_args(argv)
    try:
        k = Kernel(a.root)
        if a.command in MUTATIONS:
            data = json.loads(a.data.read_text(encoding="utf-8-sig"))
            result = k.transact(a.command, data, a.key, a.actor)
            # Generated projection is recoverable, never authoritative.
            from wiki import render
            try:
                render(k)
            except (OSError, ContractError) as exc:
                result = {**result, "projection_warning": str(exc), "recovery": "harness.py wiki"}
        elif a.command == "view":
            result = k.view()
        elif a.command == "audit":
            _, records = k.inspect()
            result = {"events": records, "authentication": "local_operator_labels_only"}
        elif a.command == "wiki":
            from wiki import render
            result = render(k)
        elif a.command == "resolve":
            result = k.resolve(a.task, a.resolve_command)
        elif a.command == "restore":
            result = k.restore(a.source, a.sha256)
        else:
            result = k.backup(a.out)
        print(encode(result))
        return 0
    except (ContractError, OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        print(encode({"state": "error", "reason": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
