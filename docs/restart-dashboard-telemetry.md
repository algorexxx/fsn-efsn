# Actual efsn telemetry comparison

3 October 2026. The unchanged efsn reporter now has a passing integration check
through the real dashboard collector, PostgreSQL 18.6 and HTTP API. This advances
G6; production sizing and browser acceptance of this actual-node flow remain
open. The [evidence bundle](evidence/restart-dashboard-telemetry-2026-10-03/README.md)
contains the raw messages, direct RPC responses, source hashes and reusable test.

## Scope and result

The fixture starts the real `eth.Ethereum` and `ethstats` services against an
in-memory synthetic devnet chain. Existing block-building helpers execute and
import 60 blocks containing one native ticket purchase each, using public test
key 1. It then holds the head stationary: no mining worker, auto-buy service,
P2P listener, outbound peer dialing, discovery, real key or backup database.

The normal telemetry login, reports, automatic history request and reply pass
through the current authenticated collector. Its normal snapshot writer stores
the data in a new SCRAM-authenticated loopback PostgreSQL cluster. The normal
HTTP API reads that stored snapshot. Independent direct node RPC calls confirm:

- Head 60, hash, parent, timestamp, producer, state and transaction roots,
  difficulty, total difficulty, gas limit/usage, transaction hashes and uncles.
- The same block fields for every historical height 10 through 59, returned by
  efsn in descending order. The dashboard chart shows heights 21 through 60.
- Two total tickets and two owned tickets; zero peers and pending transactions;
  mining stopped. All three report groups have positive freshness budgets.
- The head hash is unchanged after the comparisons. The node verifies it is
  still at height 60, not mining and has no peers before its clean shutdown.

The accepted run is `attempt-3`: one integration test, 58 successful direct RPC
requests, 51 distinct compared blocks, no snapshot collection errors and clean
node/collector/database shutdown. This test uses the database administrator in
its disposable cluster; it does not replace the earlier least-privilege role
tests or prove production database configuration.

## Confirmed legacy semantics

At this caught-up, zero-peer stationary head, `eth_syncing` returns `false`, while
the reporter sends `stats.syncing: true`. The reporter's full/light branches
compare the current header with the downloader's highest known block using
`>=`; the RPC method reports syncing while its current block is **below** the
highest known block. Header and fully executed block progress may also differ.

The browser labels this field **Syncing**, but gives `true` a green indicator.
It therefore cannot be presented as the RPC syncing boolean. The inherited
reporter also sends a literal `uptime: 100`. This is not measured availability.
No reporter or consensus change was made to address these semantics in this
step. Before public browser acceptance, choose an explicit compatible label or
an unknown/unsupported display policy, including mixed client versions. Never
use either flag to establish agreement with peers, chain progress or funding.

## Measured payloads and sizing implication

These are UTF-8 application-message bytes, including the efsn JSON encoder's
trailing newline, before WebSocket/TCP framing. Hello contains a synthetic
credential of the same captured length; saved evidence removes its value.

| Message | Bytes |
| --- | ---: |
| Hello | 298 |
| Head block, one transaction | 661 |
| Stats | 183 |
| Pending | 59 |
| Latency | 51 |
| History, 50 blocks / 50 transactions | 30,926 |

The run uses the existing **65,536-byte input**, **262,144-byte pending output**
and **100 application messages/second** fixture limits. The largest captured
outgoing application message is 4,784 bytes. The stored snapshot payload's
compact JSON representation is 6,175 bytes. The instrumented collector's one
memory observation is 140,058,624 RSS bytes, including 9,889,520 heap-used bytes
and 83,381,670 external bytes. These are observations, not peaks, production
capacity, per-node costs or proposed deployment defaults.

Each additional transaction-hash object in this wire format adds 78 bytes
including its separating comma. Holding other fields at the measured lengths,
50 blocks with ten transactions each would require
`30,926 + (500 - 50) * 78 = 66,026` bytes, already over the 64 KiB fixture limit.
This is an offline byte calculation, not a generated workload. For perspective,
the fixture's 15,000,000 gas limit and 21,000 minimum transaction gas permit a
loose bound of 714 transactions per block; the analogous hash-list calculation
alone reaches 2,811,626 bytes for a fifty-block reply. Different field lengths,
gas limits, forks, identities and snapshot consumers change the requirements.

Do not promote the small test limits into deployment defaults. Select a declared
supported payload envelope and coordinate report validation, history handling,
input/output/snapshot budgets, retained chart memory and proxy limits. Rehearse
ordinary larger reports within that envelope. Raising one transport limit alone
does not establish a bounded production memory budget.

## Changes and limits

Only test fixtures and documentation were added. The dashboard has a separate
local commit with a preserved patch; efsn adds one opt-in Linux test that reuses
existing chain helpers. Production reporter, consensus, collector, storage,
frontend and dependency locks are unchanged. No original dashboard checkout
files, user branding documents or backup data were changed. Nothing was pushed
or deployed.

The reporter imports a light-client package needing C support. The existing
Windows no-C test toolchain cannot compile that import, so the actual service
runs with the established Linux Go 1.21.3/C toolchain. A portable official
Linux Node 22.11.0 archive was checksum-verified for the collector. The Windows
writer/API use WSL's localhost forwarding. No firewall or machine networking
configuration was changed. All service listeners are loopback.

This is one full node with a stationary synthetic head and small reports. It
does not exercise live production, light sync, a loaded pool, missing historical
blocks/state, collector loss during mining, TLS, multiple reporting nodes or a
compiled browser consuming this actual-node pipeline. Earlier synthetic browser,
freshness and outage evidence remains applicable within its recorded scope.
The new fixture was run without Go's race detector; earlier observer race runs
do not cover this reporter test.

Next: settle the browser semantics above and the supported payload envelope,
then complete report validation, actual browser/outage acceptance and runtime,
dependency, supervision and proxy/TLS review. G6 remains open.
