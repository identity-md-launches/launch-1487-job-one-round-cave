"""Offline boundary and wire-ID regressions; no network or generated fixtures."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import batch_capture as batch


class BatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved = batch.loads(Path(__file__).with_name('example-mainnet.json').read_bytes())

    def rejected(self, change):
        value = copy.deepcopy(self.saved)
        change(value)
        with self.assertRaises((ValueError, TypeError, KeyError, RuntimeError)):
            batch.inspect(value)

    def test_real_chain_demo(self):
        summary = batch.inspect(self.saved)
        self.assertEqual(summary['chain_id'], '1')
        self.assertEqual([c['token'] for c in summary['calls']], ['ZTO', 'IMD', 'ZTO', 'IMD'])
        self.assertTrue(all(c['decoded_uint256'].isdigit() for c in summary['calls']))

    def test_out_of_order_wire_ids(self):
        bundle = copy.deepcopy(self.saved)
        bundle['responses'].reverse()
        self.assertEqual(batch.inspect(bundle), batch.inspect(self.saved))

    def test_duplicate_ids(self):
        self.rejected(lambda b: b['responses'].__setitem__(0, b['responses'][1]))

    def test_missing_response(self):
        self.rejected(lambda b: b['responses'].pop())

    def test_unknown_id(self):
        self.rejected(lambda b: b['responses'][0].__setitem__('id', 17))

    def test_boolean_id(self):
        self.rejected(lambda b: b['responses'][0].__setitem__('id', True))

    def test_string_id(self):
        self.rejected(lambda b: b['responses'][0].__setitem__('id', '1'))

    def test_error_is_not_result(self):
        def change(b):
            b['responses'][0] = {'jsonrpc': '2.0', 'id': 1,
                                 'error': {'code': -32000, 'message': 'not available'}}
        self.rejected(change)

    def test_result_plus_error(self):
        self.rejected(lambda b: b['responses'][0].__setitem__('error', {}))

    def test_wrong_version(self):
        self.rejected(lambda b: b['responses'][0].__setitem__('jsonrpc', '1.0'))

    def test_wrong_hash(self):
        self.rejected(lambda b: b['requests'][0]['params'][1].__setitem__('blockHash', '0x' + 'a'*64))

    def test_canonical_boolean_only(self):
        self.rejected(lambda b: b['requests'][0]['params'][1].__setitem__('requireCanonical', 1))

    def test_after_anchor_changed(self):
        self.rejected(lambda b: b['anchor_after'].__setitem__('hash', '0x' + 'a'*64))

    def test_wrong_chain(self):
        self.rejected(lambda b: b['chain_response'].__setitem__('result', '0xa'))

    def test_wrong_explicit_block(self):
        self.rejected(lambda b: b.__setitem__('requested_block', '0x1'))

    def test_duplicate_labels(self):
        self.rejected(lambda b: b['labels'].__setitem__(0, b['labels'][1]))

    def test_unknown_call_field(self):
        self.rejected(lambda b: b['requests'][0]['params'][0].__setitem__('from', batch.hash_snapshot.ZTO))

    def test_short_known_abi_word(self):
        self.rejected(lambda b: b['responses'][0].__setitem__('result', '0x01'))

    def test_batch_request_ids_must_be_consecutive(self):
        self.rejected(lambda b: b['requests'][0].__setitem__('id', 2))

    def test_bad_timestamp(self):
        self.rejected(lambda b: b.__setitem__('captured_at', '2026-02-30T00:00:00Z'))

    def test_strict_json(self):
        for value in (b'{"a":1,"a":2}', b'{"a":NaN}', b' '*96001):
            with self.assertRaises(ValueError):
                batch.loads(value)

    def test_no_network_for_unsafe_request(self):
        request = copy.deepcopy(self.saved['requests'])
        request[0]['method'] = 'eth_sendRawTransaction'
        with patch.object(batch.urllib.request, 'build_opener') as opener:
            with self.assertRaises(ValueError):
                batch.post(batch.PUBLIC_RPC, request)
            opener.assert_not_called()

    def test_invalid_calls_fail_before_send(self):
        with patch.object(batch, 'post') as send:
            with self.assertRaises(ValueError):
                batch.capture(calls=[{'label': 'oops', 'to': '0x123', 'data': '0x'}])
            send.assert_not_called()

    def test_capture_reordered_responses(self):
        saved = self.saved
        def send(request):
            if isinstance(request, list):
                replies = [{**old, 'id': new['id']} for old, new in
                           zip(batch.match_responses(saved['requests'], saved['responses']), request)]
                return list(reversed(replies))
            if request['method'] == 'eth_chainId':
                return saved['chain_response']
            return {'jsonrpc': '2.0', 'id': 1, 'result': saved['anchor']}
        bundle = batch.capture(tag=saved['anchor']['number'], send=send)
        self.assertEqual(bundle['responses'][0]['id'], 4)
        self.assertEqual(batch.inspect(bundle)['block_hash'], saved['anchor']['hash'])

    def test_no_sequential_fallback_on_failed_batch(self):
        sent = []
        def send(request):
            sent.append(request)
            if isinstance(request, list):
                return {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32600, 'message': 'no batch'}}
            if request['method'] == 'eth_chainId':
                return self.saved['chain_response']
            return {'jsonrpc': '2.0', 'id': 1, 'result': self.saved['anchor']}
        with self.assertRaises(ValueError):
            batch.capture(send=send)
        self.assertEqual(len(sent), 3)

    def test_no_pending_tag(self):
        with patch.object(batch, 'post') as send:
            with self.assertRaises(ValueError):
                batch.capture(tag='pending')
            send.assert_not_called()


if __name__ == '__main__':
    unittest.main()
