# Dashboard: actual efsn WSS acceptance

2026-10-03. The next G6 transport slice passes locally. Actual efsn telemetry now
travels through nginx WSS, the collector, PostgreSQL, the HTTPS API and compiled
Edge browser. No production node, consensus, dashboard application, database
schema, frontend, dependency or nginx-template changes were required.

The sole Go edit lets the existing synthetic fixture accept `wss` as well as
`ws`, while retaining its numeric-loopback, public-test-key and no-backup-input
restrictions. Dashboard edits are test orchestration, a shared HTTPS request
helper, certificate checks and cleanup. Changes stay on the existing temporary
branches; nothing is deployed or pushed.

Dashboard commit: `d9dfa96b8323db2621f2d7e41a70304c2f1b7415`, based on
`4ca1f59` on `codex/dashboard-telemetry-auth`.

## What passed

- The explicit WSS endpoint carries one actual reporter, with no plaintext
  fallback. Its unchanged Go dialer validates a temporary test CA. HTTPS API
  checks record authorized TLS 1.3 sessions.
- The head plus fifty history blocks match direct RPC, including transaction
  hashes and supported scalar fields. Each block has ten transactions. Forty
  displayed chart heights retain the expected transaction counts; ticket,
  peer, pending and mining values match RPC.
- Four browser checkpoints pass: actual head, pinned head, expired data after
  writer loss, and automatic recovery. Screenshots confirm stale rows and
  summaries disappear. There are no page errors or foreign page requests.
- An ordinary Edge process rejects the untrusted test certificate. Functional
  navigation uses a separate temporary profile with a trust exception pinned to
  that test leaf's SPKI. No machine trust store is changed. This browser exception
  does not establish public-certificate acceptance or renewal readiness.
- Linux writer/collector/API clocks agree on the receipt ordering. The final TLS
  run records fifteen snapshots, two writer connections with normal closes and
  zero writer errors. The largest snapshot is 6,958 bytes under the coordinated
  4 MiB input / 1 MiB output / 1 MiB snapshot settings.
- All 173 contract tests and 13 socket tests pass. The original actual-node
  plain-loopback/PostgreSQL/browser scenario also passes after the shared fixture
  changes. The frontend build's 547 files remain unchanged.

The chain in this fixture remains at height 60 with zero peers and no ongoing
mining. This is a transport, display and writer-outage check. It does not close
the collector-loss-during-mining requirement or repeat the eight-node size test.

## Findings and preserved attempts

`attempt-1` stops during certificate setup: its `/tmp` directory is absent when
OpenSSL tries to write the key. The runner now places private Linux scratch under
the rehearsal user's home and hashes only relevant Go/module files. No database
was started in that attempt; the reason the directory disappeared was not proven.

`attempt-2` reaches actual WSS, PostgreSQL and HTTPS, then fails the strict
freshness assertion. The Linux collector receipt is 637 ms later than the Windows
writer's snapshot observation. The fixture had spread timestamp-producing
components across Windows and WSL. The API correctly refuses to call this timing
known. The corrected layout keeps collector, writer and API together on Linux;
no limits or freshness rules are relaxed. This evidence does not retrospectively
prove the cause of the older retained freshness failure.

`attempt-3` passes the data and all browser checks, then fails a cleanup hook that
issues a second stop command after its child has exited. The fixture now makes
writer stop idempotent and explicitly stops the writer and node before the
collector/proxy. `attempt-4` passes the complete WSS test and cleanup.
`attempt-5` passes the original plain-loopback scenario. All failed results remain
in the evidence bundle, including their distinct failure stages.

## Runtime and remaining work

The TLS run uses Ubuntu PostgreSQL 16.15, extracted into scratch without service
installation, alongside the previously tested nginx 1.24.0-2ubuntu7.18 and Node
22.11.0. Windows runs the controller and Edge 154.0.4258.48. The plain-loopback
regression uses Windows PostgreSQL 18.6. Both use pg 8.23.1 and the existing Go
1.21.3 toolchain. These version choices are test inputs; the supported public
runtime/dependency matrix remains unselected.

Three Linux scratch databases and one Windows scratch database were stopped.
Temporary certificate private keys and database passwords were removed. Final
process checks find no matching node, nginx, PostgreSQL or headless Edge process.
Only disposable database files remain in scratch; the chain backup and original
dashboard checkout were not changed. Inherited Node deprecation messages and
the node's expected connection-close warning during shutdown remain visible.

Next: drill collector loss during actual mining, then finish runtime/dependency
review, service supervision, certificate/log lifecycle checks and the common
deployment manifest. Clock synchronization and the single-host assumption belong
in that manifest. Public hosting and public-certificate acceptance remain open.

See [the plan](restart-plan.md), [prior proxy acceptance](restart-dashboard-proxy.md)
and [the complete evidence bundle](evidence/restart-dashboard-wss-2026-10-03/).
The dashboard branch contains the reproduction notes in
`docs/actual-wss-acceptance.md`.
