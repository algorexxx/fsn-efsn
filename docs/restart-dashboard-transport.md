# Dashboard collector transport upgrade

2026-10-03. The isolated dashboard branch now pins **Primus 8.0.9 and ws 8.22.0**.
This corrects the transport dependency findings identified in the
[runtime review](restart-dashboard-runtime.md). All 173 contract tests, 14 socket
tests, the local TLS proxy scenario, actual efsn WSS/database/browser acceptance
and the collector-loss mining drill pass on Linux Node 24.21.0.

There is no dashboard application-source or efsn-source change in this slice.
The production change is the root package manifest and lock; fixture changes
check actual parser settings and the documented byte boundary. The existing
Primus event and latency plugins retain their versions. The original dashboard
checkout, frontend build/lock, separate API lock and database schema are intact.

## Scope and dependency evidence

The two npm archives were inspected after matching their published SHA-512
integrity values. Primus 8's adapter consumes the current ws upgrade-request and
text-frame interfaces. It continues to use JSON event envelopes and the existing
Primus ping/pong protocol. Native efsn framing and authentication need no change.

Only these direct dependency versions change. The v1 lock has 17 changed package
paths, including removals and relocations, and grows from 331 to 333 entries.
Those paths belong to the transport dependency update, including diagnostics,
forwarded-for, eventemitter3, setheader and their dependencies. A clean backend
install with npm 10.9.0 and lifecycle scripts disabled leaves both input files
unchanged; all 333 installed versions match the lock. The final production
Linux/Node/npm installation matrix remains a separate release check.

The fresh root audit no longer flags ws, Primus or setheader. Its package findings
decrease from 44 to 41: 12 critical, 18 high, six moderate and five low. Other
runtime and legacy-tool findings remain; this is not a complete dependency
clearance. The old `http2` engine warning and dependency deprecations are retained
in the install logs. No audit fix, force option, peer-check bypass or global
runtime installation was used.

The installed ws version is outside the affected ranges of the upstream
[parser-memory advisory](https://github.com/websockets/ws/security/advisories/GHSA-96hv-2xvq-fx4p).
The added configuration check confirms that the actual servers on all three
collector paths have finite defaults: 16,384 message fragments and 262,144
buffered chunks, alongside the configured payload maximum. Compression remains
disabled and UTF-8 validation enabled. These are parser count caps, not a bound
on total process memory. Advisory exploit examples and exhaustion tests were
not run.

## Explicit compatibility detail

The byte maximum is now inclusive: a setting of 2048 accepts 2048 bytes and
rejects 2049. The old parser rejected a message at the exact threshold too. The
first post-upgrade test run kept that expectation and timed out while waiting
for a valid connection to close; the other twelve socket tests passed.

The corrected test verifies successful delivery at the maximum, refusal above
it and the existing multibyte/fragmented-message cases. This follows the new
receiver's explicit greater-than comparison. The configuration documentation now
states the boundary; production settings themselves are unchanged. The other
existing wire checks pass unchanged, and all 14 socket tests pass. The failed run
and its exact source hashes remain in the evidence.

## Integration results

| Check | Result |
| --- | --- |
| Native efsn WSS → PostgreSQL → HTTPS → browser | RPC comparison, fifty-block history and four browser checkpoints pass, including writer expiry/recovery |
| Eight-reporter TLS proxy | Authentication, normalized forwarding headers, private-route isolation, payload/output limits, connection cap and inactivity deadlines pass |
| Larger normal history reply | 3,276,956 bytes accepted within the existing 4 MiB profile |
| Collector absent during real synthetic mining | Height and nonce advance 61 → 73 with automatic purchases enabled and two tickets maintained |
| Reconnect after collector restoration | Height 74 reaches HTTPS automatically; no efsn or writer restart |
| Recovered chart | All forty heights 35–74 persisted; thirteen new purchases audited against canonical receipts |

The collector was absent for 139.897 seconds. Fresh head recovery took 13.337
seconds after restoration. The telemetry head sequence was 73, 73, 74, 74,
retaining P17's correction for obsolete queued head reports. The snapshot writer
recorded 538 expected connection-loss/failure messages under the test's 250 ms
retry interval, with no new error category or subsequent recovery error. Public
retry pacing and log retention are still deployment work.

The proxy scenario also keeps eight normal reporters active for about 47 seconds
and observes 24 application pings, while testing the established forwarding-header
allowlist. This matters because the Primus update includes forwarded-for. The
proxy template and all proxy expectations pass unchanged.

These remain isolated synthetic tests: public test key 1, in-memory chain,
loopback networking, disposable PostgreSQL and temporary TLS trust. Real backup
data and signing keys were not used. The compiled frontend's 547 files remain
byte-identical; no rebuild was needed for this backend dependency change.
Scratch services are stopped and temporary credentials removed.

## Evidence and next step

The [transport evidence bundle](evidence/restart-dashboard-transport-2026-10-03/)
contains package inspection/integrity, exact lock changes, install and audit logs,
failed and corrected socket runs, all three integration captures, cleanup checks,
dashboard commit/patch and a standalone verifier. Work remains on the existing
temporary branches; nothing is pushed or deployed.

Continue G6 with the remaining active dependencies and unused legacy tools,
then consolidate the API install, browser HTTP client and deployment workflow.
Keep final clean-install, supervision, public certificate renewal, retry/log
lifecycle and hosting acceptance in the [consolidated plan](restart-plan.md).
This transport item is complete locally; G6 is still open.
