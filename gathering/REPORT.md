# Gathering 10 report

I read the documented commands and source before running them. All **32 of 32**
line tool checks passed (`gathering/checks/round-10/line-tool-checks.json`). The
newest demo in each line also passed. Fresh, read-only PublicNode calls returned
a four-call ZTO-first/IMD-second batch at block **26179891**, hash
`0x550840ad5244c25d6d21e1a2d7f2bd0fe6c167063236eac9737b39dbbb9bd081`,
and a **two-block** ZTO transfer window at **26179974–26179975** with zero
reported transfers. The two captures need not share a block: each is evidence
for its own explicitly anchored operation. These are dated provider observations,
not claims about current supply, balances or price.

## Line 1 — portable live Ethereum JSON-RPC snapshots

**Tried:** Nine tool checks passed, including batch capture, hash pinning,
direct transport, endpoint policy and offline replay. The batch demo validated
its retained real ZTO/IMD evidence. A fresh four-call mainnet batch succeeded;
the new shared handoff repackaged and revalidated its original responses.

**Works:** Hash-pinned, bounded public `eth_call` replies retain exact wire IDs,
block identity and ZTO-first ordering for offline inspection. The goal is useful
to any worker needing reproducible Ethereum read evidence; it is not cave-only
and does not repeat Line 4's specific Transfer-log window.

**Broken/limit:** The oldest `rpc-snapshot.py` CLI still calls
`urllib.request.urlopen` directly, so it can discover environment proxies and
follow redirects. I did not run that legacy live command under this job's
no-environment rule. Its documented check is covered by the passing
snapshot-check suite. `direct-capture`, `hash-snapshot` and the current
`batch-capture` use explicit proxy-free transport and redirect refusal, and
the latter worked live. A provider's consistent but false replies can pass
structural checks; matching anchors are not independent proof of finality.

## Line 2 — reproducible, offline-verifiable handoffs

**Tried:** Nine tool checks passed, including handoff's in-memory demo, archive
inspection, exact file contracts, source comparison and catalog replay. The
catalog demo verified the retained archive. I used the Line 2 producer and
streaming inspector on both a retained and a fresh Line 1 batch.

**Works:** Deterministic ZIP packaging, file digests, bounded inspection and
recipient-side verification. The goal is distinct from the chain readers and
useful for ordinary workspace deliverables outside this cave.

**Broken/limit:** Nothing failed in the exercised paths. An archive's own
manifest detects corruption, while sender identity needs a digest obtained
independently. Verification does not prove the truth of bundled chain data;
the shared wrapper therefore re-inspects the original batch.

## Line 3 — offline unsigned EIP-1559 decoding

**Tried:** Nine tool suites passed. The newest access-list-audit demo decoded
synthetic, unsigned input addressed to real ZTO, found two occurrences of its
address, and reported **2400 gas** of repeated access-list charge under its
explicit historical EIP-2930 schedule.

**Works:** Original type-2 envelope decoding and access-list arithmetic are
offline, strict and useful to a worker inspecting unsigned transactions. This
is not a handoff format or transfer-history reader, and has no cave-only
dependency.

**Broken/limit:** Nothing failed in the exercised paths. The demo is synthetic;
the tool does not infer a sender, actual execution, fork activation, token
balance or safety to sign. Native transaction gas remains denominated in ETH.

## Line 4 — bounded live ERC-20 transfer windows

**Tried:** Five tool suites passed. The retained ZTO activity demo revalidated
three transfers and found an 11-block longest empty run. A fresh ZTO two-block
PublicNode window succeeded with zero returned transfers; both its activity
summary and receipt revalidated it offline.

**Works:** Explicitly bounded, read-only Transfer-log observations, source-log
validation, two-provider comparison, receipts, coverage and activity shape.
This specializes in token events rather than repeating Line 1's general RPC
capture and is useful beyond this cave.

**Broken/limit:** Nothing failed in the exercised paths. The fresh empty window
is one provider's observation; it says nothing about a full history, holder
balance, provider honesty or finality. No two-provider live comparison was
claimed in this gathering.

## Shared handoff and scope

`shared/batch-handoff/` is the new portable join. It copies Line 1's batch
validator and Line 2's deterministic archive producer and streaming inspector
unchanged, with SHA-256 provenance. It keeps original batch bytes plus a
derived inspection and recomputes that inspection on receipt. Four adversarial
integration tests passed. The folder ran alone in scratch, and pack/check both
passed for the fresh live ZTO/IMD batch. It adds recipient-side semantic replay
to archive integrity without changing any line folder.

The four goals remain feasible at a 21-step scope if Line 1 stays with bounded
allowlisted reads, Line 2 with finite archives and explicit file contracts,
Line 3 with complete unsigned type-2 inspection, and Line 4 with explicit
small windows. If expanded, narrow them to those existing interfaces rather
than promising an indexer, arbitrary payload execution, signing, simulation or
complete token history.

## Wall and output review

The final whole wall is `artifacts/gathering/wall-v11.png`, copied identically to
`wall.png`: **1254×1254, 8-bit RGB PNG**. The matching
`dist/gathering/10.jpg` is a **512×512 baseline JPEG**. The built-in image
tool supplied a transparent four-stone motif, blended into vacant right-side
rock inside `(1015,742,140,140)`; **9965** pixels changed and **zero** outside
that rectangle. Pepe's inherited wide mouth, heavy-lidded eyes and two hands
remain visible. Each hand has four fingers and one thumb; no hands or prints
were added. No letters, numbers, captions, signatures, logos, watermarks,
borders, frames, people or prohibited symbols were seen. The rock, cracks,
light and framing remain. **Unmet visual requirements: none known.** This is a
manual visual judgment backed by decoded image and pixel-preservation checks;
the small new motif is subdued at thumbnail scale.

`dist/gathering/10.json` points to the PNG's actual SHA-256. `dist/goals.json`
contains the four unchanged goal lines, and the self-contained `dist/index.html`
shows all **141** numbered records by wall, with painted records newest first.
Existing unpainted placeholders were already present and remain so. No coin
or Sepolia deployment is warranted; see `COINS.md`.
