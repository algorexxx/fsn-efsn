# Operator kit: fresh restore and console-driven entry

4 October 2026. The [draft operator kit](restart-operator-kit.md) consolidates
release/data verification, fresh restore, identity checks, static fallback,
funding, first purchase, mining/buying, cold restart and supervised operation.
This investigation adds tests and documentation only. Production source,
consensus rules and the unset compiled mainnet anchor are unchanged.

## What the local rehearsal exercises

The existing complete synthetic-history helper builds 24 shared blocks with
public keys 1/2 and a two-ticket reserve. Ordinary key-2 successors establish
the test anchor at 25 and consume/retreat all key-1 tickets. No key-1 node process
is started. Key 2 represents donation production and key 3 a later entrant.
Genesis gives the entrant 50,000 synthetic liquid FSN; this is neither real
funding authorization nor a proposed universal reserve.

The old height-24 database is closed, reopened read-only under a database lock,
and packaged with the existing `snapshot_package.py`. Its trusted test manifest
is supplied to a restore into a fresh datadir. The package contains only flat
LevelDB files. The completion marker and a fresh distinct P2P identity are
required before proceeding. The prepared donation database already has the
accepted successors; ordinary automatic full sync brings the entrant across
the anchor without `lab_sync` or manual post-connection block insertion.

Operator actions use the actual, separately built `efsn attach --exec` console
over IPC: read `admin.nodeInfo`, add the peer, check genesis/anchor/sync/mining/
buyer status and exact liquid balance/nonce, start donation production, buy the
entrant's first ticket, inspect its receipt, enable entrant production and
buying, then stop both. The harness checks the successful native BuyTicket log,
both producers' canonical blocks and subsequent automatic purchases.

After stop, the existing settling check requires a common head unchanged for
35 seconds. Final acceptance rechecks the first purchase, both producers and
replenishers in that settled canonical history, rather than relying on earlier
live observations. Every suffix transaction/receipt and native purchase result
is checked again after each service starts in a new process, together with all
three head markers, state/ticket commitments and each owner's exact nonce/saved
automatic-purchase bytes. Pool contents need not survive a stopped process.

## Retained attempts

| Attempt | Result |
| --- | --- |
| 1 | Seed construction stopped in 0.24 seconds: a one-ticket limit can leave an owner with zero after the last seed block. The existing helper requires positive reserves. |
| 2 | The existing two-ticket setup passed; packaging then stopped because the earlier Go-source extraction omitted the Python snapshot helper. |
| 3 | Passed in 127.86 seconds: five database files, 66,233 restored bytes, anchor 25, first entrant purchase at 30, common final head 35 and both cold services. |
| 4 | Passed in **117.07 seconds**, including the stricter settled/cold native-purchase, producer and saved-record assertions. Five files / 65,563 restored bytes; anchor 25, first purchase 30, both replenished through 32, settled and cold head 34. All original limits retained; no skipped selected case or race report. |

All failed logs, source inputs and executable identities remain in the
[evidence bundle](evidence/restart-operator-kit-2026-10-04). The final result is
recorded in its `acceptance.json`; no setup failure is counted as a passing run.
Builds use the existing offline Go 1.21.3 Linux amd64 toolchain with CGO and race
detection for the services. The console executable is the verified node-only
build from the [source extraction](restart-release-extraction.md).

Entry point: `TestRestartNodeRehearsal/operator_kit`, with
`FUSION_RESTART_NODE_REHEARSAL=1` and an absolute `FUSION_RESTART_EFSN_COMMAND`.
The [runner](evidence/restart-operator-kit-2026-10-04/run-linux.sh) pins inputs,
refuses existing result directories and runs under an ordinary account inside
a network namespace containing only enabled loopback. Synthetic data is capped
at 64 MiB, with a 5 GiB free-space reserve; preparation permits at most twelve
successors and the live suffix at most 64 blocks. Sync is bounded to 90 seconds,
first purchase to 60 seconds, replenishment to 120 seconds and the full test to
eight minutes. No historical database or real signing key is opened or copied.

## Remaining release acceptance

This is a fresh datadir on the existing WSL host. The node services are real
`node.Node`/`eth.Ethereum` instances embedded in the test executable; the harness
supplies their synthetic genesis, anchor and unlocked public test keys. The
console is the real CLI, but node startup is not the final CLI/service package.
The profile, account-creation/unlock and public download instructions remain
source-reviewed templates requiring the selected release/host rehearsal.

R6/R9 therefore remain open for: authenticated public download/restore of the
final recovery dataset; final executable and compiled anchor; actual key custody,
funding intervals and unattended credentials; supported host/storage/service
configuration and reboot; the combined complete-state ledger and SSH/dashboard
handover. This test compares executed commitments and native receipts, not an
independent full-account accounting implementation. Existing complete-state
entrant/accounting results remain separate evidence.

The [unknown-heavier automatic-sync test](restart-automatic-sync.md) separately
covers incompatible-history refusal. This kit does not add ongoing finality,
economic changes, observer/dashboard features or an external monitoring provider.
Historical baseline execution remains verified through 3,300,000.
