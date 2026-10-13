"""Behavioral checks for exact quantities and metadata binding; fully offline."""
import contextlib
import io
import random
import unittest
import amount_view as view


def envelope(data, chain=1, to=view.intent.decoder.ZTO):
    fields = [chain, 0, 1, 2, 100000, bytes.fromhex(to[2:]) if to else b'', 0, data, []]
    return '0x02' + view.intent.decoder.rlp_encode(fields).hex()


class AmountTests(unittest.TestCase):
    def test_one_smallest_unit(self):
        self.assertEqual(view.units(10**18 + 1, 18), '1.000000000000000001')

    def test_zero_and_trailing_zeroes(self):
        self.assertEqual(view.units(0, 255), '0')
        self.assertEqual(view.units(123000, 4), '12.3')
        self.assertEqual(view.units(10**18, 18), '1')

    def test_zero_decimals_and_maximum(self):
        self.assertEqual(view.units(view.intent.UINT256_MAX, 0), str(2**256-1))

    def test_extreme_decimals(self):
        self.assertEqual(view.units(1, 255), '0.' + '0'*254 + '1')

    def test_invalid_numeric_types_and_bounds(self):
        for raw in (-1, 2**256, True, '1', 1.0):
            with self.assertRaises(ValueError): view.units(raw, 18)
        for decimals in (-1, 256, True, '18', 18.0):
            with self.assertRaises(ValueError): view.units(1, decimals)

    def test_seeded_exact_roundtrips(self):
        rng = random.Random(30)
        for _ in range(500):
            raw = rng.randrange(2**256)
            decimals = rng.randrange(256)
            text = view.units(raw, decimals)
            whole, _, fraction = text.partition('.')
            recovered = int(whole)*10**decimals + int(fraction.ljust(decimals, '0') or '0')
            self.assertEqual(raw, recovered)
            self.assertNotIn('e', text)
            self.assertLessEqual(len(fraction), decimals)

    def test_demo_is_exact_approval(self):
        result = view.inspect(view.demo_transaction(), 1, view.intent.decoder.ZTO.upper().replace('0X','0x'), 18)
        self.assertEqual(result['amount']['tokenUnits'], '1.000000000000000001')
        self.assertEqual(result['amount']['method'], 'approve')
        self.assertFalse(result['amount']['maximumApproval'])
        self.assertEqual(result['inspection']['calldata']['arguments']['spender'], view.intent.IMD)

    def test_bound_metadata(self):
        for chain, token in [(2, view.intent.decoder.ZTO), (1, view.intent.IMD)]:
            with self.assertRaisesRegex(ValueError, 'does not match'):
                view.inspect(view.demo_transaction(), chain, token, 18)

    def test_invalid_metadata(self):
        for chain in (0, -1, 2**256, True):
            with self.assertRaises(ValueError): view.inspect(view.demo_transaction(), chain, view.intent.decoder.ZTO, 18)
        for token in ('0xzz', '0x'+'g'*40, None):
            with self.assertRaises(ValueError): view.inspect(view.demo_transaction(), 1, token, 18)

    def test_no_amount_for_unknown_and_read_calls(self):
        for data in (b'', bytes.fromhex('12345678'), bytes.fromhex('18160ddd'), bytes.fromhex('095ea7b3')):
            result = view.inspect(envelope(data), 1, view.intent.decoder.ZTO, 18)
            self.assertIsNone(result['amount'])

    def test_transfer_and_transfer_from(self):
        address = bytes(12) + bytes.fromhex(view.intent.IMD[2:])
        for selector, arguments in [('a9059cbb',address), ('23b872dd',address+address)]:
            result = view.inspect(envelope(bytes.fromhex(selector)+arguments+(12345).to_bytes(32,'big')), 1, view.intent.decoder.ZTO, 3)
            self.assertEqual(result['amount']['tokenUnits'], '12.345')

    def test_max_approval_remains_flagged(self):
        data = bytes.fromhex('095ea7b3')+bytes(12)+bytes.fromhex(view.intent.IMD[2:])+(2**256-1).to_bytes(32,'big')
        result = view.inspect(envelope(data), 1, view.intent.decoder.ZTO, 18)
        self.assertTrue(result['amount']['maximumApproval'])
        self.assertEqual(result['inspection']['calldata']['approvalKind'], 'maximum-uint256')

    def test_signed_and_malformed_are_rejected(self):
        for text in ('0x02', '0x01c0', '0x02' + view.intent.decoder.rlp_encode([1,0,1,2,100000,bytes.fromhex(view.intent.decoder.ZTO[2:]),0,b'',[],0,1,1]).hex()):
            with self.assertRaises(ValueError): view.inspect(text, 1, view.intent.decoder.ZTO, 18)

    def test_cli_requirements_and_zero_decimals(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(view.main(['--transaction',view.demo_transaction(),'--chain-id','1','--token',view.intent.decoder.ZTO,'--decimals','0']), 0)
            self.assertIn('1000000000000000001', output.getvalue())
        for argv in ([], ['--demo','--decimals','18'], ['--demo','--chain-id','01']):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                view.main(argv)
            self.assertEqual(error.exception.code, 2)


if __name__ == '__main__':
    unittest.main()
