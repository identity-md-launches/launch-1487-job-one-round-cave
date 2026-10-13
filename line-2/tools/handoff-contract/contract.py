#!/usr/bin/env python3
"""Check a verified HANDOFF against a recipient's exact file contract."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import zipfile


FORMAT = "handoff-contract-v1"
INSPECTOR = Path("line-2/tools/handoff-inspect/inspect_handoff.py")


def load_inspector():
    current = Path.cwd()
    for part in INSPECTOR.parts:
        current /= part
        if current.is_symlink():
            raise ValueError("dependency symlinks are not allowed")
    spec = importlib.util.spec_from_file_location("handoff_contract_inspector", current)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def safe_contract_path(raw):
    if not isinstance(raw, str) or not raw or raw == "HANDOFF.json":
        raise ValueError("contract paths must name non-manifest files")
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts or "\\" in raw or ":" in raw:
        raise ValueError("contract paths must be relative and safe")
    if any(part in ("", ".") or any(ord(c) < 32 or ord(c) == 127 for c in part)
           for part in path.parts):
        raise ValueError("contract paths must be relative and safe")
    return path.as_posix()


def contract_receipt(archive, required, exact=False, expected=None):
    inspector = load_inspector()
    wanted = [safe_contract_path(item) for item in required]
    if len(set(wanted)) != len(wanted):
        raise ValueError("contract paths must be distinct")
    receipt = inspector.inspect_path(archive, expected=expected)
    found = {item["path"]: item for item in receipt["files"]}
    required_set = set(wanted)
    present = sorted(required_set & found.keys())
    missing = sorted(required_set - found.keys())
    unexpected = sorted(found.keys() - required_set)
    passed = not missing and (not exact or not unexpected)
    result = {
        "format": FORMAT,
        "verified": True,
        "contract_passed": passed,
        "archive_sha256": receipt["archive_sha256"],
        "archive_bytes": receipt["archive_bytes"],
        "payload_bytes": receipt["payload_bytes"],
        "required": wanted,
        "present": present,
        "missing": missing,
        "unexpected": unexpected,
        "exact": exact,
        "note": "The archive was integrity-checked before its file contract was evaluated; "
                "no payload was extracted or executed.",
    }
    return result


def demo():
    result = contract_receipt(
        "line-2/handoff.zip", ["README.md", "handoff.py"], exact=True)
    if not result["contract_passed"]:
        raise ValueError("inherited handoff does not satisfy its demo contract")
    result["demo"] = "real inherited handoff checked against an exact two-file contract"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("demo")
    check = commands.add_parser("check")
    check.add_argument("archive", help="relative HANDOFF v1 ZIP path")
    check.add_argument("required", nargs="+", help="required payload paths")
    check.add_argument("--exact", action="store_true",
                       help="also reject verified payload files not listed")
    check.add_argument("--sha256", help="trusted archive SHA-256")
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            result = demo()
        else:
            result = contract_receipt(args.archive, args.required, args.exact, args.sha256)
        print(json.dumps(result, sort_keys=True, indent=2))
        return 0 if result["contract_passed"] else 2
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError,
            zipfile.BadZipFile, EOFError, NotImplementedError) as error:
        print("handoff-contract: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
