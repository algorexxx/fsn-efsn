# Dashboard registration and ping bounds

3 October 2026. Registration now stores only native efsn metadata, limited to
2 KiB of serialized UTF-8 JSON. Telemetry ping timestamps are limited to 128
serialized bytes. The actual efsn → collector → PostgreSQL → HTTP API → browser
check passes with unchanged efsn and frontend code. G6 remains open.

The dashboard work remains isolated on `codex/dashboard-telemetry-auth` at
`tmp/fsn-stats-auth`; the original dashboard checkout is preserved. The
[evidence bundle](evidence/restart-dashboard-admission-2026-10-03/README.md)
contains the local commit patch, exact source hashes, failures and successful
runs. There are three production-file changes: the registration projection,
the existing report validator's ping case and collector wiring.

## Interface and behavior

`hello.info` retains `node`, `net`, `protocol`, `api`, `os`, `os_v`, `client`,
`port` and `canUpdateHistory`. The seven text fields must be nonempty strings;
port must be an integer from 0 through 65535 and the history flag a boolean.
The authenticated credential ID supplies `name`. Reported names, IPs and unknown
metadata extensions are discarded. The resulting object, including its field
names, credential ID, punctuation and JSON escaping, may occupy at most 2048
UTF-8 bytes. Invalid registration closes before identity reservation or collection
mutation, allowing a later corrected connection to register normally.

`node-ping.clientTime` must be a nonempty string occupying at most 128 serialized
UTF-8 JSON bytes, including its quotes. Accepted strings are echoed unchanged;
invalid values close the authenticated session without being echoed. No ping
refreshes block, stats or pending-report timestamps. This accepts the native
efsn timestamp string without trusting or parsing its reported time.

These fixed dashboard interface bounds comfortably cover the observed native
metadata (201 bytes) and ping values (57–58 bytes). They are not new chain rules.
Current-head hashes, ticket behavior, history validation and compact storage,
snapshot persistence, APIs and frontend are unchanged. Custom telemetry clients
must follow the documented native field contract; no arbitrary extension storage
or numeric ping compatibility is promised.

## Evidence and limits

- Five new regressions fail on the previous production source. One ordinary-ping
  case already passes. The first sandbox attempt could not load Node modules
  (`EPERM`); only the subsequent complete six-test run is baseline evidence.
- **167 contracts and 13 socket tests pass**, including exact byte boundaries,
  UTF-8/escaping, metadata projection, invalid-input rejection before state
  changes, reconnects and unchanged report receipts.
- The output-budget regression still proves bounded queued writes and session
  recovery, using multiple 126-character pings that satisfy the new contract.
- Actual efsn metadata and timestamps pass the new checks. The current head and
  fifty history blocks match direct RPC; API transaction hashes, ticket/peer/
  pending values and all forty transaction-count chart entries remain correct.
- All four compiled-browser checkpoints pass: actual head, pinning, writer-loss
  expiry and writer recovery. The final writer reports **zero errors**.
- All three disposable PostgreSQL clusters are stopped, password files removed,
  and matching Windows/WSL test processes absent. No bulk restore, real key,
  backup data or public network was used. The unchanged frontend build was reused.

The first two actual-node attempts completed the browser checks but failed the
zero-writer-error assertion. The second attempt's transport record identifies
two initial `ECONNREFUSED` errors on the Windows-to-WSL collector port, followed
by a successful connection about 0.5 seconds later. A further close diagnostic
occurred only during failure cleanup, when the fixture stopped the server first.

The test now waits for bounded Windows-side TCP readiness before starting the
writer and stops the writer before its server during cleanup. In the successful
run four probes were refused, then the port became reachable after 441 ms; both
writer connections opened and closed normally. Error assertions, production
retries, payload limits and snapshot freshness deadlines were not relaxed.
Transport diagnostics remain in the fixture. This identifies this startup issue,
not the cause of the older retention-run freshness assertion failure.

## Remaining admission work

The 2 KiB limit applies to projected registration fields before the collector
adds its IP. That IP is derived by Primus forwarding middleware, which accepts
multiple forwarding-header names; it must not be described as authenticated
peer identity. Header normalization and the additional address/geo fields belong
in the proxy and aggregate-budget checks.

Current heads still retain unknown extensions and complete transaction hashes.
The 4 MiB input cap alone does not ensure eight accepted heads fit the 1 MiB
snapshot/output candidate. Persistence enforces its node count after receipt,
and the credential file can enroll more identities than the concurrent TCP cap.
Inactive rows remain for up to four hours. These are still open admission limits.

Next, choose and verify an explicit complete-head/extension policy preserving
required hashes, then coordinate total enrollment and inactive retention against
inventory, chart, queued-output and snapshot budgets. Include the appended IP
and geo data. Only then can the measured eight-node profile support deployment
sizing. Proxy/TLS, runtime/dependency review, supervision, external alert delivery
and collector loss during mining remain in the consolidated plan.
