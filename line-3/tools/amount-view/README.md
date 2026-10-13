# Exact token amount display

Read token amounts in an unsigned EIP-1559 envelope without losing the smallest
base unit. This offline Python standard-library tool reuses the unchanged
committed `erc20-intent` reader and `zto-eip1559-decoder`. It accepts original
envelope bytes, requires explicit chain, token and decimal metadata, and refuses
metadata whose chain or address differs from the transaction. No floating point
arithmetic is used. It preserves the original inspection, raw base units and
maximum-approval warning alongside the display amount.

One command from the repository root shows it working:

```sh
python3 -B line-3/tools/amount-view/amount_view.py --demo
```

When tried, the synthetic unsigned ZTO approval displayed raw
`1000000000000000001` as exactly `1.000000000000000001` token units with 18
decimals. The demo uses the task's real ZTO destination and real IMD address
as the spender; it is an inspection example, not a proposed approval or an
endorsement of IMD as a spender. Nothing was signed or sent.

During this round, a separate read-only Ethereum `eth_call` to ZTO's
`decimals()` selector `0x313ce567` returned the 32-byte integer 18. The public
source endpoint is `https://ethereum-rpc.publicnode.com` (accessed through the
worker's supplied relay). This was a latest-state observation on 2026-10-13,
not pinned historical evidence or verified metadata. It is not fetched by this
tool and does not authenticate user-supplied decimals. No live supply, balance
or allowance claim is made.

To inspect your own envelope:

```sh
python3 -B line-3/tools/amount-view/amount_view.py --transaction YOUR_COMPLETE_UNSIGNED_HEX --chain-id 1 --token 0xd782bdea4ef02a0bd391eb9089470c8080f0a68e --decimals 18
```

Replace `YOUR_COMPLETE_UNSIGNED_HEX` with the complete actual bytes. Supply
metadata established independently for that exact chain and token. A token
address on another chain needs its own metadata; the tool supplies no defaults.
Decoding does not establish contract behavior: selector collisions, malicious
metadata, changed decimals and execution failure remain possible. Approvals
describe authority, not a token transfer or balance. Native value and gas fees
remain ETH wei in the inherited inspection. Unknown, empty, malformed-known,
read-only and creation calldata do not produce a guessed amount. Creation cannot
match a token address. Signed or malformed envelopes are rejected.

CLI success prints JSON and exits 0; invalid input exits 2. The `amount` field
is null when no matched standard token amount exists. Quantities are decimal
strings, decimals is a bounded JSON integer (0–255), and trailing fractional
zeroes are omitted without rounding. The maximum uint256 approval remains
explicitly flagged. Runs from any working directory using committed sibling
imports. No input files, network, environment, wallets, secrets, signing,
transaction submission, payments or public posting are used by the tool.

Checks tried:

```sh
python3 -B line-3/tools/amount-view/test_amount_view.py
```

All 14 new tests passed, including 500 seeded exact integer roundtrips across
0–255 decimals, values above JavaScript's safe integer range, extreme precision,
uint256 boundaries, metadata mismatch, finite/maximum approvals, transfer and
transferFrom, absent or malformed ABI amounts, signed-input refusal and CLI
errors. All 96 inherited Line 3 tests also passed (110 total). No dependency
was installed. These are local checks, not independent certification.

Round 30's mark is a charcoal seed pod containing ochre grains: every smallest
unit counts. The built-in imagegen prompt is recorded in `line-3/IMAGE-PROMPT-30.md`.
The delivered PNG paths are `artifacts/line-3/wall-v11.png` and the identical
continuing `artifacts/line-3/wall.png`; the mandated thumbnail is
`dist/line-3/30.jpg`. Dimensions, formats, pixel preservation and visual review
are recorded in `line-3/round-30-review.json`. The inherited goal, paintings,
older records and tools are preserved.
