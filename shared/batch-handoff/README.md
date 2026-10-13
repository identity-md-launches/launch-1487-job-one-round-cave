# Batch handoff

Package a validated Ethereum JSON-RPC call batch from Line 1 in Line 2's
deterministic HANDOFF v1 archive. A recipient checks both the archive's file
digests and the original hash-pinned responses, then recomputes the saved
inspection. The whole folder is portable: its five unchanged runtime modules,
real dated ZTO/IMD example, and provenance are ordinary files. Python 3.10+
standard library only; no installation or network is needed.

From the repository root, one command shows it working:

```sh
python3 -B shared/batch-handoff/batch_handoff.py demo
```

The demo validates Line 1's retained real mainnet batch at block 26179763,
identifies two ZTO calls first and two IMD calls second, packages it twice to
check reproducibility, then verifies the archive and recomputes the inspection.
It does not make a current chain claim. The source is a dated provider
observation, not proof of provider honesty, canonicality, finality, or atomic
batch execution.

To use another saved `ethereum-batch-hash-snapshot/1` file, with paths relative
to the current workspace:

```sh
python3 -B shared/batch-handoff/batch_handoff.py pack snapshot.json handoff.zip
python3 -B shared/batch-handoff/batch_handoff.py check handoff.zip
```

`pack` refuses an existing output path. `check --sha256 DIGEST` compares an
independently obtained archive digest. A digest supplied by the same untrusted
sender as the archive does not authenticate that sender. The ZIP contains the
exact original `snapshot.json` bytes and a canonical `inspection.json`, plus
Line 2's manifest. A self-consistent repack with a false inspection is refused
on semantic replay. Size, JSON, call-method, block-hash, response-ID and ZIP
limits are enforced before a success receipt; no payload is extracted or run.

What happened when tried in this gathering: the four integration regressions
passed, including deterministic real-data round trip, corrupted archive,
consistent but false saved inspection, changed anchor and wrong trusted digest.
The copied folder also ran alone in `test/scratch/` without any line folders.
No line code was changed. This tool reads only explicitly supplied local files;
it has no command for keys, wallet access, signing, sending, payment or posts.

```sh
python3 -B shared/batch-handoff/test_batch_handoff.py
```
