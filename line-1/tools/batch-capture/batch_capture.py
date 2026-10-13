#!/usr/bin/env python3
"""Capture read-only Ethereum eth_call batches at one canonical block hash."""
import argparse
import datetime as dt
import importlib.util
import json
from pathlib import Path
import sys
import urllib.request

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('batch_hash', HERE.parent / 'hash-snapshot/hash_snapshot.py')
hash_snapshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(hash_snapshot)
rpc = hash_snapshot.rpc
SCHEMA = 'ethereum-batch-hash-snapshot/1'
LIMIT = 96_000
PUBLIC_RPC = 'https://ethereum-rpc.publicnode.com'
RELAY = 'http://127.0.0.1:33991/rpc/1'
USER_AGENT = 'Pepeolithic-Batch-Capture/1.0 (read-only Ethereum evidence)'


def loads(raw):
    if len(raw) > LIMIT:
        raise ValueError('JSON exceeds 96000 bytes')
    return json.loads(raw, object_pairs_hook=hash_snapshot.unique_object,
                      parse_constant=hash_snapshot.reject_constant)


def dumps(value):
    output = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n'
    if len(output.encode()) > LIMIT:
        raise ValueError('snapshot exceeds 96000 bytes')
    return output


def post(endpoint, requests):
    """Send only validated hash-pinned eth_call requests; never replay a failure."""
    rpc.validate_endpoint(endpoint)
    if isinstance(requests, list):
        validate_requests(requests)
    else:
        if (not isinstance(requests, dict) or set(requests) != {'jsonrpc', 'id', 'method', 'params'}
                or requests['jsonrpc'] != '2.0' or type(requests['id']) is not int
                or requests['id'] != 1 or requests['method'] not in {'eth_chainId', 'eth_getBlockByNumber'}):
            raise ValueError('unsupported single request')
        rpc.validate_request(requests['method'], requests['params'])
    body = dumps(requests).encode()
    request = urllib.request.Request(endpoint, data=body, headers={
        'Content-Type': 'application/json', 'Accept': 'application/json',
        'Accept-Encoding': 'identity', 'User-Agent': USER_AGENT})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), hash_snapshot.NoRedirect())
    with opener.open(request, timeout=20) as response:
        if response.status != 200:
            raise ValueError('RPC requires HTTP 200')
        if response.headers.get('Content-Encoding', 'identity').lower() != 'identity':
            raise ValueError('compressed RPC response unsupported')
        return loads(response.read(LIMIT + 1))


def single(method, params, send):
    response = send({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})
    hash_snapshot.response_result(response)
    return response


def validate_requests(requests):
    if not isinstance(requests, list) or not 1 <= len(requests) <= 16:
        raise ValueError('expected 1 to 16 requests')
    reference = None
    for index, request in enumerate(requests, 1):
        if (not isinstance(request, dict) or set(request) != {'jsonrpc', 'id', 'method', 'params'}
                or request['jsonrpc'] != '2.0' or type(request['id']) is not int
                or request['id'] != index or request['method'] != 'eth_call'):
            raise ValueError('invalid batch request')
        params = request['params']
        if (not isinstance(params, list) or len(params) != 2 or not isinstance(params[0], dict)
                or set(params[0]) != {'to', 'data'}):
            raise ValueError('invalid call parameters')
        hash_snapshot.check_calls([{'label': 'call', **params[0]}])
        ref = params[1]
        if (not isinstance(ref, dict) or set(ref) != {'blockHash', 'requireCanonical'}
                or not rpc.hex_data(ref['blockHash'], 32) or ref['requireCanonical'] is not True):
            raise ValueError('canonical hash reference required')
        if reference is not None and ref != reference:
            raise ValueError('all calls must use the same hash')
        reference = ref
    return reference


def match_responses(requests, responses):
    """JSON-RPC allows arbitrary response ordering, never positional matching."""
    validate_requests(requests)
    if not isinstance(responses, list) or len(responses) != len(requests):
        raise ValueError('incomplete batch response')
    by_id = {}
    for response in responses:
        if (not isinstance(response, dict) or set(response) != {'jsonrpc', 'id', 'result'}
                or response['jsonrpc'] != '2.0' or type(response['id']) is not int
                or not 1 <= response['id'] <= len(requests) or response['id'] in by_id):
            raise ValueError('failed, duplicate, unknown or malformed batch reply')
        by_id[response['id']] = response
    return [by_id[request['id']] for request in requests]


def inspect(bundle):
    fields = {'schema', 'endpoint', 'captured_at', 'requested_block', 'chain_response',
              'anchor', 'anchor_after', 'labels', 'requests', 'responses'}
    if not isinstance(bundle, dict) or set(bundle) != fields or bundle['schema'] != SCHEMA:
        raise ValueError('invalid batch snapshot schema')
    rpc.validate_endpoint(bundle['endpoint'])
    stamp = bundle['captured_at']
    if not isinstance(stamp, str) or len(stamp) != 20:
        raise ValueError('canonical UTC capture timestamp required')
    parsed = dt.datetime.strptime(stamp, '%Y-%m-%dT%H:%M:%SZ')
    if parsed.strftime('%Y-%m-%dT%H:%M:%SZ') != stamp:
        raise ValueError('canonical UTC capture timestamp required')
    if hash_snapshot.response_result(bundle['chain_response']) != '0x1':
        raise ValueError('Ethereum mainnet required')
    anchor = hash_snapshot.identity(bundle['anchor'])
    if bundle['anchor'] != anchor or bundle['anchor_after'] != anchor:
        raise ValueError('changed or invalid anchor')
    tag = bundle['requested_block']
    if not rpc.block_tag(tag) or tag == 'pending':
        raise ValueError('stable block tag required')
    if tag.startswith('0x') and tag != anchor['number']:
        raise ValueError('wrong requested block number')
    requests = bundle['requests']
    ref = validate_requests(requests)
    if ref != {'blockHash': anchor['hash'], 'requireCanonical': True}:
        raise ValueError('batch hash differs from anchor')
    labels = bundle['labels']
    if not isinstance(labels, list) or len(labels) != len(requests):
        raise ValueError('one label per request required')
    hash_snapshot.check_calls([{'label': label, **request['params'][0]}
                               for label, request in zip(labels, requests)])
    replies = match_responses(requests, bundle['responses'])
    summaries = []
    for label, request, reply in zip(labels, requests, replies):
        # Reuse semantic inspection with a temporary id=1 envelope. The original
        # wire envelopes and their actual ids remain untouched in the artifact.
        row = {'label': label, 'method': 'eth_call', 'params': request['params'],
               'response': {**reply, 'id': 1}}
        summaries.append({'id': request['id'], **hash_snapshot.validate_observation(row, ref)})
    dumps(bundle)
    return {'schema': SCHEMA + '-summary', 'chain_id': '1', 'endpoint': bundle['endpoint'],
            'captured_at': stamp, 'block_number': str(int(anchor['number'], 16)),
            'block_hash': anchor['hash'], 'calls': summaries,
            'evidence_limits': hash_snapshot.LIMITS + ' A batch is not atomic execution; every call uses the same hash.'}


def capture(endpoint=PUBLIC_RPC, tag='finalized', calls=None, send=None, source=None):
    rpc.validate_endpoint(endpoint)
    source = endpoint if source is None else source
    rpc.validate_endpoint(source)
    if not rpc.block_tag(tag) or tag == 'pending':
        raise ValueError('stable block tag required')
    if tag.startswith('0x') and not hash_snapshot.quantity(tag):
        raise ValueError('canonical block number required')
    calls = hash_snapshot.check_calls(hash_snapshot.DEFAULT_CALLS if calls is None else calls)
    send = send or (lambda requests: post(endpoint, requests))
    chain = single('eth_chainId', [], send)
    if chain['result'] != '0x1':
        raise ValueError('Ethereum mainnet required')
    anchor = hash_snapshot.identity(single('eth_getBlockByNumber', [tag, False], send)['result'])
    if tag.startswith('0x') and anchor['number'] != tag:
        raise ValueError('wrong requested block number')
    ref = {'blockHash': anchor['hash'], 'requireCanonical': True}
    requests = [{'jsonrpc': '2.0', 'id': index, 'method': 'eth_call',
                 'params': [{'to': call['to'], 'data': call['data']}, dict(ref)]}
                for index, call in enumerate(calls, 1)]
    responses = send(requests)
    match_responses(requests, responses)
    after = hash_snapshot.identity(single('eth_getBlockByNumber', [anchor['number'], False], send)['result'])
    bundle = {'schema': SCHEMA, 'endpoint': source,
              'captured_at': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
              'requested_block': tag, 'chain_response': chain, 'anchor': anchor,
              'anchor_after': after, 'labels': [call['label'] for call in calls],
              'requests': requests, 'responses': responses}
    inspect(bundle)
    return bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    cap = sub.add_parser('capture', help='hash-pinned ZTO-first calls; snapshot on stdout')
    cap.add_argument('--rpc', default=PUBLIC_RPC)
    cap.add_argument('--worker-relay', action='store_true', help='use assignment relay, record public source')
    cap.add_argument('--block', default='finalized')
    cap.add_argument('--calls-stdin', action='store_true', help='1–16 label/to/data objects from stdin')
    sub.add_parser('inspect', help='offline snapshot from stdin')
    sub.add_parser('demo', help='offline inspection of retained real-chain batch')
    args = parser.parse_args()
    try:
        if args.command == 'capture':
            if args.worker_relay and args.rpc != PUBLIC_RPC:
                raise ValueError('worker relay source is fixed to the advertised public source')
            calls = loads(sys.stdin.buffer.read(LIMIT + 1)) if args.calls_stdin else None
            output = capture(RELAY if args.worker_relay else args.rpc, args.block, calls,
                             source=PUBLIC_RPC if args.worker_relay else None)
        else:
            raw = ((HERE / 'example-mainnet.json').read_bytes() if args.command == 'demo'
                   else sys.stdin.buffer.read(LIMIT + 1))
            output = inspect(loads(raw))
        sys.stdout.write(dumps(output))
        return 0
    except (ValueError, TypeError, KeyError, RuntimeError, OSError, RecursionError, OverflowError):
        print('batch-capture: invalid input, inconsistent evidence, or RPC failure; no snapshot emitted',
              file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
