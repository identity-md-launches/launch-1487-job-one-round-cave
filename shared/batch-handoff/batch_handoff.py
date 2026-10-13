#!/usr/bin/env python3
"""Package and replay a validated, hash-pinned Ethereum call batch offline."""

import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import zipfile

HERE = Path(__file__).resolve().parent
VENDOR = HERE / 'vendor'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


batch = module('batch_handoff_batch', VENDOR / 'batch-capture/batch_capture.py')
handoff = module('batch_handoff_producer', VENDOR / 'handoff/handoff.py')
inspector = module('batch_handoff_inspector', VENDOR / 'handoff-inspect/inspect_handoff.py')
FORMAT = 'ethereum-batch-handoff/1'
SNAPSHOT = 'snapshot.json'
SUMMARY = 'inspection.json'
MAX_ARCHIVE = 250_000


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
                       ensure_ascii=True, allow_nan=False) + '\n').encode('ascii')


def read_workspace(raw, limit):
    path = handoff.workspace_path(raw)
    return handoff.regular_bytes(path, limit)


def pack_bytes(snapshot_raw):
    """Keep original source bytes and a derived inspection in a deterministic ZIP."""
    summary = batch.inspect(batch.loads(snapshot_raw))
    archive = handoff.build({SNAPSHOT: snapshot_raw, SUMMARY: canonical(summary)})
    verify_bytes(archive)
    return archive


def verify_bytes(archive, expected=None):
    if len(archive) > MAX_ARCHIVE:
        raise ValueError('batch archive exceeds 250000 bytes')
    receipt = inspector.inspect_stream(io.BytesIO(archive), expected=expected)
    if {row['path'] for row in receipt['files']} != {SNAPSHOT, SUMMARY}:
        raise ValueError('batch handoff requires exactly two payloads')
    # The general archive check detects accidental corruption. Reinspect the
    # original RPC evidence because a valid manifest can describe false data.
    with zipfile.ZipFile(io.BytesIO(archive)) as source:
        snapshot_raw = source.read(SNAPSHOT)
        saved_summary = source.read(SUMMARY)
    summary = batch.inspect(batch.loads(snapshot_raw))
    if saved_summary != canonical(summary):
        raise ValueError('saved inspection differs from recomputed evidence')
    return {'format': FORMAT, 'verified': True,
            'archive_sha256': receipt['archive_sha256'],
            'trusted_digest_matched': receipt['trusted_digest_matched'],
            'snapshot_sha256': hashlib.sha256(snapshot_raw).hexdigest(),
            'block_number': summary['block_number'],
            'block_hash': summary['block_hash'],
            'calls': summary['calls'],
            'limits': ('Integrity and internal consistency only. The archive '
                       'does not authenticate its sender or prove provider '
                       'honesty, current canonicality, finality, or atomic execution.')}


def demo():
    raw = (HERE / 'examples/zto-imd-batch.json').read_bytes()
    archive = pack_bytes(raw)
    if archive != pack_bytes(raw):
        raise ValueError('packaging is not reproducible')
    result = verify_bytes(archive, hashlib.sha256(archive).hexdigest())
    result['demo'] = ('Retained real ZTO-first and IMD-second provider calls; '
                      'offline validation and deterministic handoff only.')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('demo')
    pack = commands.add_parser('pack')
    pack.add_argument('snapshot', help='relative workspace JSON file')
    pack.add_argument('archive', help='new relative workspace ZIP file')
    check = commands.add_parser('check')
    check.add_argument('archive', help='relative workspace ZIP file')
    check.add_argument('--sha256', help='archive digest obtained independently')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            result = demo()
        elif args.command == 'pack':
            target = handoff.workspace_path(args.archive, must_exist=False)
            archive = pack_bytes(read_workspace(args.snapshot, batch.LIMIT))
            with target.open('xb') as output:
                output.write(archive)
            result = verify_bytes(archive)
            result['output'] = args.archive
        else:
            result = verify_bytes(read_workspace(args.archive, MAX_ARCHIVE), args.sha256)
        print(json.dumps(result, sort_keys=True, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError,
            RecursionError, OverflowError, zipfile.BadZipFile, EOFError):
        print('batch-handoff: invalid input, inconsistent evidence, or archive failure',
              file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
