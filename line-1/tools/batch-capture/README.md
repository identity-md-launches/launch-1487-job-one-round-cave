# Batch capture

Capture 1–16 read-only Ethereum contract calls in one JSON-RPC batch, tied to
one block hash, as portable JSON. The default calls observe real ZTO supply
and decimals, with IMD second. Useful when a worker needs several related
observations and wants to preserve the provider's wire replies, including IDs
and arrival ordering, for another worker to inspect without a network.

Run this from the repository root to see it working **offline**:

```sh
python3 -B line-1/tools/batch-capture/batch_capture.py demo
```

This decodes the included real-chain capture, not synthetic token values.
Python 3.10+ and its standard library are sufficient. Keep the unchanged
`hash-snapshot/hash_snapshot.py` and `rpc-snapshot/rpc_snapshot.py` sibling
modules beside this tool when copying it elsewhere; those are the complete
runtime dependencies. No installation, environment configuration or network
is needed for demo or inspect.

## Live read and replay

On this assignment's machine, the contributor relay is selected explicitly:

```sh
python3 -B line-1/tools/batch-capture/batch_capture.py capture --worker-relay
```

For a worker elsewhere, `capture` without that flag uses the public Ethereum
source `https://ethereum-rpc.publicnode.com`. `--rpc https://eth.drpc.org` can
select the other public provider. A rejected batch is a failure: no automatic
resubmission, sequential fallback, change of block, or partial output occurs.

To inspect a saved snapshot from standard input:

```sh
python3 -B line-1/tools/batch-capture/batch_capture.py inspect < line-1/tools/batch-capture/example-mainnet.json
```

`--block` accepts a stable tag or an explicit canonical hexadecimal block
number. `pending` is refused. `--calls-stdin` accepts an array of objects with
exactly `label`, `to`, and `data`. Labels are unique ASCII identifiers. Every
call uses `{"blockHash": "…", "requireCanonical": true}`; there is no fallback
to a block number. The tool verifies chain ID 1, resolves the block, captures
the batch, and rechecks that exact block number and identity afterward.

The format is `ethereum-batch-hash-snapshot/1`. Requests have consecutive
integer IDs starting at 1. Responses retain the provider's original array
order; inspection joins by ID. Missing, duplicate, boolean, string or unknown
IDs, error envelopes, extra fields, mixed block hashes, malformed ABI words
for the recognized token reads, and changed anchors are rejected. Transport
has a dedicated User-Agent, empty proxy handler, redirect refusal, a 20-second
request timeout and a 96,000-byte JSON limit. That limit also bounds custom
inputs and the finished snapshot; even a valid individual result can make a
large combined bundle fail. There are at most 16 calls and 4096 calldata bytes
per call. Only hash-pinned `eth_call`, chain identity and block identity reads
are permitted. No keys, wallets, secrets, environment discovery, signing,
transaction submissions, deployment, payment or external posts are used.

## What happened when tried

A read-only live run on 2026-10-13 at 00:02:18 UTC succeeded through the
assignment's relay. The retained artifact names the advertised public source
rather than the local transport. It checked Ethereum chain ID `0x1` and
observed finalized block **26,179,763**, hash
`0x4193517ef67be0b7e56e6b2d21df04af7c2927d33840873caa8af2cc5d504ebc`.
The anchor was unchanged after the four-call batch. Provider observations:

| Token | totalSupply, base units | decimals |
| --- | ---: | ---: |
| ZTO | 1000000000000000000000000000 | 18 |
| IMD | 4171218214787000000000000 | 18 |

The demo then inspected that artifact offline. All 26 new regression tests
passed, including reversed response order, failed batches, wrong chain/hash,
ID collisions and unsafe-method rejection before networking. The 20
hash-snapshot tests and 10 endpoint-policy tests passed unchanged.

```sh
python3 -B -m unittest discover -s line-1/tools/batch-capture -p 'test_*.py' -v
```

Worker-selected choices: use the existing `finalized` default, four ZTO-first
ancestor call descriptions, a strict all-success batch, and a 96 KB combined
budget so every delivered non-image file stays below 100 KB. These choices
were delegated, not requester-supplied values.

A matching hash and `requireCanonical` are provider observations, not proof
of honesty, independent corroboration, finality or liquidity backing. JSON-RPC
batching does not itself guarantee simultaneous execution. A provider must
support batching and EIP-1898 honestly. Supply is not a holder balance or price.
