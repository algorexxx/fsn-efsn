# Guarded recovery construction

Status: isolated investigation, 24 September 2026. The command prepares an
unsigned candidate. Real-key signing, publication and the production anchor
remain separate launch gates.

The [full-state handover](restart-full-state-handover.md) demonstrated that a
jump block without its replacement purchase can be accepted with only expired
tickets left. `internal/recovery.Build` now executes a reviewed purchase and
checks its outcome before returning a candidate for subsequent signing.
This is an operator construction policy; consensus and ordinary mining rules
are unchanged.

## Checks before a candidate is returned

- The genesis, chain ID, current parent height/hash and explicit signer match
  the plan. The read-only database adapter also requires full, header, fast and
  canonical head markers to agree.
- Exactly one transaction is allowed. Its hash, protected chain ID, recovered
  sender, nonce, zero transfer value, native BuyTicket destination/function and
  decoded ticket interval must match the plan.
- Both block timestamps advance by at least the consensus minimum. The purchase
  lasts at least 30 days and extends strictly beyond `NextTimestamp`. Consensus
  may not silently adjust the requested block timestamp.
- Real transaction execution succeeds. The receipt and native log must confirm
  the expected ticket ID and owner. A native `Error` is rejected even when the
  receipt reports success.
- Ordinary DaTong finalization succeeds, and the purchased ticket survives with
  the expected owner, height and interval. State read errors fail construction.

The purchase transaction hash commits its gas limit, fee and signature as well
as its other fields. The parent hash commits the parent state and ticket roots.
The report includes the chain configuration for review. Review that configuration
against the chosen release; matching a chain ID alone does not authenticate every
configuration field.

`NextTimestamp` is an explicit eligibility horizon, not a promise of indefinite
production. For the first historical block it must cover the intended jump;
for the jump it must cover cleanup; for cleanup it must cover actual unattended
startup plus a reviewed operating margin. Replenishment, adequate funding and
uptime remain necessary afterward. A delayed launch needs a fresh interval review.

## Read-only command

Build `./cmd/fsn-recovery`, then use a stopped database and a new output filename:

```powershell
fsn-recovery.exe -chaindata C:\rehearsal\chaindata `
  -plan C:\rehearsal\recovery-plan.json `
  -purchase C:\rehearsal\purchase.rlp `
  -out C:\rehearsal\unsigned-report.json
```

The plan uses the fields in `recovery.Plan`. `Purchase.Hash` identifies one
already-signed ordinary Fusion purchase transaction, supplied as binary RLP.
The command has no block-signing key input. It opens LevelDB in read-only mode
through a small chain reader, without running node startup repair, committing
state or contacting a network. It rejects unknown plan fields, trailing JSON,
inputs over one MiB and an existing output file.

The output contains the plan, chain configuration, unsigned block RLP/header,
execution receipt, successor ticket, selected ticket and retreat IDs. The header
has a zero block signature. Its hash is **not** the eventual signed block hash
and must never be selected as a production anchor. Receipt block-location fields
are not a mined receipt at this construction stage.

The command currently covers the observed LevelDB-only layout. It is not a
general database repair or freezer reader. Do not launch it against a live node.
The reviewed real sequence still needs complete account-difference/ownership
accounting and independent import verification, as performed for synthetic tests.

## Passing construction evidence

Windows builds the command and prepares three unsigned candidates from fresh
copies of the complete preserved state with the previously audited public-key
funding substitutions. Every database file is hashed before and after each
command invocation: all 232, 233 and 234 files respectively remain unchanged.
The library's sparse test also compares the complete logical database before
and after construction.

The command output matches live-chain construction byte-for-byte. Only then do
the tests call the real DaTong sealing method with public test keys 1 and 2 and
independently import each block. The three signed block hashes match the first
three blocks of the prior full-state handover:

| Step | Height | Signed synthetic block hash | Remaining tickets |
| --- | --- | --- | --- |
| Backup handover | 15,130,081 | `0x7e16c5dabebb465314f9d48ba24bbb2cb836768a5264d5193329b46fd69af3da` | 485 |
| Donation jump | 15,130,082 | `0x9aaa779dad8d3883bff738d99f6a3c360812f658ccffd4778a6a4aa0c9ec862a` | 480 |
| Donation cleanup | 15,130,083 | `0x94ed041a999c47e4a3797f3f33067e3cdf011add53b786832f3ad334d9727345` | 1 |

Focused tests reject omitted/extra/nil transactions, wrong transaction and
parent identities, wrong genesis/chain/signer/owner/nonce/interval, invalid block
times, short-lived tickets and expiry at or before the eligibility horizon.
The 5,001-FSN case buys the first ticket but refuses the unfunded jump replacement
without advancing the head. A separate test rejects a successful receipt with
a native error. These checks pass on Windows and Linux with race detection.

## Full-state two-node result

The final Linux/race run passes the actual `eth.Ethereum` service, local IPC,
devp2p, real worker and registered automatic-buyer lifecycle on two fresh copies
of the complete state. Each service has only its own public test key. Discovery
is disabled and the network namespace contains only loopback. The synthetic
cleanup block is the configured mandatory anchor; it is never installed in
the production mainnet configuration.

The backup service signs the first controlled block. The donation service
independently imports it from its peer, then signs the jump and cleanup. Each
controlled step first submits a deliberately unsafe eligibility horizon and
verifies rejection without a block signature or head change. Both services
agree with the Windows command's reviewed block after every accepted step.

Immediately after cleanup, IPC enables ordinary mining and ticket buying on
the donation service. It mines two blocks, then is killed with SIGKILL. A new
process opens the same data/keystore with automatic purchases enabled, resumes
mining and produces a third ordinary block. The backup service reconnects and
the actual downloader imports that last block. The backup remains non-mining,
with automatic purchases disabled, and signs exactly one controlled block.

Both services are then stopped and independently reopened. All six canonical
blocks, receipts, ticket sets and complete account-RLP differences agree.
The independent ledger audit checks all relevant future time boundaries,
preserves unrelated assets/code/storage/notation and verifies that the retired
backup account is unchanged after its one block. Donation nonces are 0–5;
the final state has one usable donation ticket. Ordinary rewards total
1.875 FSN. Fees for the three constructed purchases are 42,448,000,000,000 wei
each; service-generated purchases pay 21,224,000,021,224 wei each under the
test service's fee configuration. These are observed rehearsal fees, not a
launch fee quote.

Final synthetic height: **15,130,086**. Block hash:
`0xf53717e738f6f5ca16bd806ddd12faa56a991f1fedff639ee81005ad5dce50ac`.
State root:
`0xe06ab26659b2675be6156e2bd86751588accf78688932420f1db2efd7bf45ee9`.

The four existing node/anchor cases also pass with the final shared harness:
readiness/mining/crash, compatible peer sync, heavier incompatible stored-fork
rejection, and incompatible startup refusal without logical database mutation.
This follow-up does not repeat the prior complete trie traversal or extend
historical execution beyond 2,700,000.

## Fixture limitations and retained failures

The compact artifact contains complete preserved state, the synthetic recovery
suffix and 256 recent headers. It omits most historical headers/bodies. The first
test attempted immediate downloader sync with a stale advertised peer head;
ancestor search fell below the available full bodies and failed. The controlled
test constructor now posts the same mined-block event as the ordinary worker,
allowing live peer propagation/import of the three controlled blocks. After
the suffix exists, the final run also demonstrates downloader catch-up across
the donation process restart. This does **not** prove arbitrary sync from this
compact artifact or from genesis.

The service's bloom indexer reports `canonical block #1 unknown` against this
intentionally incomplete historical fixture. Log-index completeness and a
supported downloadable node dataset remain open release requirements. Do not
advertise the compact state export as a complete node backup.

Other retained failed runs exposed test-harness issues: an exclusive-create
JSON helper was incorrectly used to replace restart configuration; the
ephemeral listening port changed after restart; and the peer wait was ten
seconds despite the client's existing 30-second dial-history cooldown. The
final harness retains the donation port and allows 45 seconds for reconnection.
No peer scheduler, consensus or ordinary mining rules were altered. An earlier
run (`v3`) recorded the identical nonce-5 purchase hash before and after the
kill, but failed its later peer-wait assertion. The final passing run proves
resumed purchasing/mining; it does not separately assert journal identity at
every crash boundary or prove power-loss safety.

## Signing and launch gates

The test-only IPC constructor is compiled into the test executable, not `efsn`.
It permits public keys 1 and 2 only. It demonstrates guard-before-sign ordering;
it is not a production signer or an authorization API.

Before any real key signs a block, design and rehearse durable reservation of
the parent and exact payload, refusal to sign a conflicting payload after a
restart, crash-safe artifact custody, and revalidation before publication.
Use DaTong's actual signing encoding; `SealHash` is not interchangeable with
its signature payload. The command intentionally supplies no generic signing
digest or production signing callback.

Inventory the backup node's actual pending/queued transactions and automatic
purchase journal separately. A fresh synthetic keystore and pool do not prove
that old signed backup-wallet purchases have been drained. An operator must
also verify disabled startup configuration and the one-active-signer custody
handover. Real addresses, dates, refunds/retreats and the accepted anchor still
require review before launch.

Evidence and reproduction scripts:
[restart-recovery-guard-2026-09-24](evidence/restart-recovery-guard-2026-09-24).
