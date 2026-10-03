# Dashboard telemetry identity and session correction

3 October 2026. Dashboard commit
`497b0831a148d67624974748c0ee609b4e815a08`, branch
`codex/dashboard-telemetry-auth`, based on upstream dashboard HEAD `e204963`.
The five failing [readiness contracts](restart-dashboard-readiness.md) now have
passing coverage in an expanded 71-test suite. A separate real loopback
WebSocket test also passes with the existing locked collector dependencies.

## Change and ownership

The only dashboard runtime files changed are `server.js` and the new
`lib/telemetry-credentials.js`. The patch also adds tests, enrollment instructions,
credential-file ignore rules and working test commands. The dependency lock is
unchanged. No efsn node, consensus, observer or P1–P16 source changed.

Work lives in an isolated dashboard Git worktree at
`C:/Users/Peter/Documents/CODING/fsn-efsn/tmp/fsn-stats-auth`.
The original `fusionfoundation/fsn-stats` checkout remains on master with its
previous source bytes and existing status. The dashboard branch is committed
in that repository; a [portable Git patch](evidence/restart-dashboard-auth-2026-10-03/dashboard-auth.patch)
is retained here for review and eventual organization migration. Nothing was
pushed or deployed.

## Authentication contract

`WS_CREDENTIALS_FILE` names an absolute private UTF-8 JSON file mapping a
dashboard node name to its unique credential. It is required before listening.
The old global `WS_SECRET` and implicit `ws_secret.json` behavior are deliberately
unsupported; configuration must migrate rather than silently retaining shared
identity access.

Names are 1–64 letters/digits/dots/underscores/hyphens, starting with a letter or
digit. Tokens are 32–256 URL-safe characters and must be unique across all
configured identities. Operators should generate high-entropy tokens, such as
32 random bytes encoded as hex. Length validation is not proof of entropy.
Configuration errors omit credential contents; loaded tokens are converted to
digests for comparison. The efsn `hello` / `ready` envelope and telemetry URL
format remain unchanged.

Each name can have one live session. Authentication reserves that identity;
reports are accepted only after collection registration succeeds. Every existing
telemetry handler checks that its envelope names the authenticated owner.
Rejected, closed or superseded sessions cannot update another owner or reactivate
themselves through a delayed callback. A duplicate connection is rejected while
the original remains usable. Registration failure releases the reservation.

Hello credentials are omitted from collection registration, and rejection logs
no longer print the supplied payload. The public display name is the accepted
identity. Basic envelope/body shape checks cover null/array misuse; this is not
a complete schema or resource-limit implementation.

For rotation, one node can temporarily have two credentials. Reload requires a
collector restart: enable the new credential, reconnect the node, then remove
the old credential and restart again. No live reload or multi-collector shared
session registry is implemented. Dashboard credentials do not authorize ticket
purchases or consensus membership; independent operators keep their signing keys.

## Validation

The retained Windows run uses Node 22.11.0. Syntax checks and **71 contracts pass**
with zero skipped tests. Coverage includes ordinary reporting, all seven report
handlers before login/after disconnect/under the wrong identity, invalid
configuration, credential separation, rotation, duplicate/repeated login,
registration failure, delayed callbacks, disconnect cleanup and log redaction.
These carry forward the original seven desired behaviors with the new explicit
credential configuration; they are not the original harness run unchanged.

The real transport test uses Primus 6.1.0, primus-emit 1.0.0,
primus-spark-latency 0.1.1, ws 1.1.5, lodash 3.10.1 and geoip-lite 1.2.1 from the
unchanged lock. Dependencies were installed with `npm ci --ignore-scripts
--no-audit --no-fund`; no lifecycle scripts or deployment ran. Install and test
deprecation warnings are retained and do not constitute an advisory review.

A disposable collector process runs its real collection and socket plugins.
The test wrapper forces an ephemeral `127.0.0.1` listener. Synthetic clients use
the efsn message envelope: normal stats reach the viewer, unauthenticated and
cross-identity updates do not change the owner's reported stats, wrong-identity
credentials and duplicate sessions are rejected, and disconnect/reconnect with
the next credential succeeds. The child exits cleanly with status zero and its
captured logs contain none of the synthetic credentials.

The initial syntax launch hit the already observed Windows path-resolution
`EPERM` before checking source. Approved local execution passed; the normalized
failure record and exact final run are retained. There is no Linux deployment
result, TLS test, actual efsn telemetry process, PostgreSQL persistence, HTTP read
API or browser claim in this result.

## Remaining G6 work

The authentication correction closes the reproduced collector failures within
the tested scope. Public hosting still requires endpoint/database configuration,
a reviewed runtime/dependency build, private backend access and TLS, input/size/
rate/connection limits, login deadlines, stale-data behavior and the complete
storage/API/browser acceptance path. Finish the operator credential-delivery
procedure with the selected deployment, without putting secrets in the release.

The [launch plan](restart-plan.md#g6--public-dashboard) retains these requirements
and G7's independent-producer enrollment work. The
[evidence bundle](evidence/restart-dashboard-auth-2026-10-03/README.md) contains
source identities, exact commands, results and the portable patch.
