#!/usr/bin/env python3
"""Exact offline token amount display with explicitly bound decimal metadata."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'erc20-intent'))
import intent


def units(amount, decimals):
    """Render uint256 base units without floats, rounding or exponent notation."""
    if type(amount) is not int or not 0 <= amount <= intent.UINT256_MAX:
        raise ValueError('amount must be uint256')
    if type(decimals) is not int or not 0 <= decimals <= 255:
        raise ValueError('decimals must be an integer from 0 through 255')
    if not decimals:
        return str(amount)
    digits = str(amount).zfill(decimals + 1)
    fraction = digits[-decimals:].rstrip('0')
    return digits[:-decimals] + ('.' + fraction if fraction else '')


def inspect(transaction, chain_id, token, decimals):
    """Bind caller metadata to chain/destination before displaying calldata units."""
    if type(chain_id) is not int or not 1 <= chain_id <= intent.UINT256_MAX:
        raise ValueError('metadata chain ID must be positive uint256')
    if not isinstance(token, str) or len(token) != 42 or not token.startswith('0x') or any(
            c not in '0123456789abcdefABCDEF' for c in token[2:]):
        raise ValueError('metadata token must be a 20-byte hexadecimal address')
    units(0, decimals)
    report = intent.interpret(transaction)
    tx = report['transaction']
    if int(tx['chainId']) != chain_id or tx['to'] != token.lower():
        raise ValueError('metadata chain/token does not match the unsigned envelope')
    call = report['calldata']
    display = None
    if call['status'] == 'abi-pattern-match' and 'amountBaseUnits' in call['arguments']:
        raw = int(call['arguments']['amountBaseUnits'])
        display = {'baseUnits': str(raw), 'tokenUnits': units(raw, decimals),
                   'method': call['candidateMethod'],
                   'maximumApproval': call.get('approvalKind') == 'maximum-uint256'}
    return {'schema': 'amount-view/v1',
            'metadata': {'chainId': str(chain_id), 'token': token.lower(),
                         'decimals': decimals, 'source': 'explicit caller assertion; not verified'},
            'amount': display, 'inspection': report,
            'limits': ['Exact formatting only; supplied decimals may be false or stale.',
                       'No live balances, execution, token behavior or safety to sign established.',
                       'An approval amount is authority, not a transfer or token balance.',
                       'Native value and gas fees remain ETH wei in the inherited inspection.']}


def demo_transaction():
    # No recipient is invented: demo approves the real supplied IMD address.
    # This is synthetic calldata, not an endorsement of this spender.
    data = bytes.fromhex('095ea7b3') + bytes(12) + bytes.fromhex(intent.IMD[2:])
    data += (10**18 + 1).to_bytes(32, 'big')
    fields = [1, 0, 10**9, 2*10**9, 100000, bytes.fromhex(intent.decoder.ZTO[2:]), 0, data, []]
    return '0x02' + intent.decoder.rlp_encode(fields).hex()


def canonical_decimal(text):
    if not text or len(text) > 78 or any(c not in '0123456789' for c in text) or (
            len(text) > 1 and text[0] == '0'):
        raise argparse.ArgumentTypeError('expected canonical bounded unsigned decimal')
    return int(text)


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--transaction')
    parser.add_argument('--chain-id', type=canonical_decimal)
    parser.add_argument('--token')
    parser.add_argument('--decimals', type=canonical_decimal)
    args = parser.parse_args(argv)
    values = (args.transaction, args.chain_id, args.token, args.decimals)
    if args.demo:
        if any(value is not None for value in values):
            parser.error('--demo cannot be combined with metadata or input')
        result = inspect(demo_transaction(), 1, intent.decoder.ZTO, 18)
        result['demo'] = 'Synthetic unsigned ZTO approval to supplied IMD address; never sent.'
    else:
        if any(value is None for value in values):
            parser.error('--transaction, --chain-id, --token and --decimals are required')
        result = inspect(*values)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main(sys.argv[1:]))
    except ValueError as error:
        print('error: ' + str(error), file=sys.stderr)
        raise SystemExit(2) from None
