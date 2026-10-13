"""Meaningful offline regressions for the Line 1 to Line 2 handoff."""

import io
import json
from pathlib import Path
import unittest
import zipfile

import batch_handoff as tool


class HandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (Path(__file__).resolve().parent / 'examples/zto-imd-batch.json').read_bytes()

    def test_real_batch_round_trip_is_reproducible(self):
        first = tool.pack_bytes(self.raw)
        self.assertEqual(first, tool.pack_bytes(self.raw))
        report = tool.verify_bytes(first, tool.handoff.digest(first))
        self.assertTrue(report['trusted_digest_matched'])
        self.assertEqual([c['token'] for c in report['calls']],
                         ['ZTO', 'IMD', 'ZTO', 'IMD'])
        self.assertEqual(report['block_hash'],
                         tool.batch.loads(self.raw)['anchor']['hash'])

    def test_manifest_integrity_refuses_corruption(self):
        damaged = bytearray(tool.pack_bytes(self.raw))
        with zipfile.ZipFile(io.BytesIO(damaged)) as archive:
            info = archive.getinfo(tool.SNAPSHOT)
            offset = info.header_offset + 30 + len(info.filename)
        damaged[offset + 10] ^= 1
        with self.assertRaises((ValueError, zipfile.BadZipFile)):
            tool.verify_bytes(bytes(damaged))

    def test_recomputed_inspection_refuses_consistently_repacked_false_summary(self):
        original = tool.pack_bytes(self.raw)
        with zipfile.ZipFile(io.BytesIO(original)) as archive:
            snapshot = archive.read(tool.SNAPSHOT)
            forged = json.loads(archive.read(tool.SUMMARY))
        forged['block_number'] = '1'
        repacked = tool.handoff.build({tool.SNAPSHOT: snapshot,
                                      tool.SUMMARY: tool.canonical(forged)})
        # The generic handoff manifest is self-consistent; semantic replay is needed.
        self.assertTrue(tool.handoff.verify(repacked)['verified'])
        with self.assertRaisesRegex(ValueError, 'saved inspection differs'):
            tool.verify_bytes(repacked)

    def test_changed_anchor_and_trusted_digest_are_refused(self):
        changed = tool.batch.loads(self.raw)
        changed['anchor_after']['hash'] = '0x' + 'a' * 64
        with self.assertRaises(ValueError):
            tool.pack_bytes(tool.canonical(changed))
        with self.assertRaises(ValueError):
            tool.verify_bytes(tool.pack_bytes(self.raw), 'f' * 64)


if __name__ == '__main__':
    unittest.main()
