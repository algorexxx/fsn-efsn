# Public dashboard readiness baseline

3 October 2026. G6 of the [consolidated launch plan](restart-plan.md#g6--public-dashboard)
now includes a public dashboard before public economic use. The existing
`fsn-stats` collector needs corrections before hosting: seven local contract
tests ran, with **two passing and five failing** against the archived source.
This is baseline failure evidence, not a passing dashboard acceptance run.

The subsequent [authentication correction](restart-dashboard-auth.md) addresses
the five failures with 71 passing contracts and a real loopback collector check.
The original baseline below is preserved; full public dashboard readiness remains open.

## Source and scope

Dashboard checkout:
`C:/Users/Peter/Documents/CODING/fusionfoundation/fsn-stats`, HEAD
`e2049634802d4a49adadf998853ce6ee6b1158d0`. Git reports 558 existing working-tree
entries; all 19 source/configuration files in the captured manifest equal HEAD after CRLF
normalization. Exact working bytes are hashed rather than assuming a clean
checkout. The source and Git status remained unchanged. No dashboard, node or
consensus production code was edited.

The harness executes an exact archived `server.js` with dependency, socket,
collection and timer doubles. It invokes normal event handlers directly and
records whether they dispatch collection operations. All credentials and
identities are synthetic. It does not open a port, connect to a public endpoint,
write a database, load local secrets or install packages. Node v22.11.0 is the
test runner, not an approved dashboard deployment runtime.

The first two launches failed before running tests because the Windows sandbox
blocked Node's path resolution (`EPERM`, `lstat C:\Users\Peter`). Both errors
are retained. The approved local retry ran all seven tests and exited 1 for the
five assertions below; it had no stderr or skipped tests.

## Tested acceptance boundaries

| Required behavior | Baseline result | Consequence / correction |
| --- | --- | --- |
| Ordinary hello followed by same-node stats is dispatched | Pass | Keep this compatibility path |
| Missing secret prevents the listener starting | Fail: listener still starts after logging missing configuration | Validate nonempty credentials before constructing/listening |
| Empty secret prevents the listener starting | Fail: empty environment string enables startup | Reject empty credentials, including empty entries in a rotation list |
| Stats require a successful hello on the same connection | Fail: unregistered session dispatches `updateStats` | Gate every state-changing telemetry handler on authentication |
| Stats identity matches the authenticated connection | Fail: session registered as node A dispatches an update for node B | Bind the accepted identity to the session and validate each update |
| Authentication failure logs omit the supplied secret | Fail: rejection passes the complete hello object to logging | Log a redacted reason/identity, never the credential |
| Disconnect marks that session inactive | Pass | Preserve session-based disconnect handling |

These tests establish behavior inside the collector handler, not a complete
Primus/WebSocket/PostgreSQL/browser test or a demonstrated public-network
incident. Source inspection of `Collection.updateStats` confirms that it looks
up the supplied node ID; it does not receive a session identity to independently
check ownership. The positive/disconnect controls prevent treating a harness
that never registers handlers as a useful passing result.

Session binding alone is insufficient for multiple independent operators:
`hello` currently accepts any configured shared secret with a caller-selected
node ID, and `Collection.add` updates an existing record by that ID. The eventual
enrollment configuration must bind credentials to allowed telemetry identities
and define duplicate connections/rotation. This is dashboard identity ownership,
not a permission system for buying tickets or producing chain blocks. It requires
no validator private keys or new consensus membership rule.

## Other source findings

| Surface | Current behavior | Required before deployment |
| --- | --- | --- |
| Persistence collector | `wsclient/wsclient.js` targets `wss://node.fusionnetwork.io/primus` | Explicit validated deployment endpoint |
| Browser | `Main.js` targets `https://api-stats.fusionnetwork.io` | Build/runtime API configuration for the new deployment |
| PostgreSQL | `db/index.js` uses user `postgres`, default password `postgres`, fixed database/port | Required credentials, configurable connection and least-privilege account |
| Read API | Fixed port 3002; queries return entire node/block/chart tables | Deployment bind/port, bounded reads and retention/access policy |
| Release workflow | Builds with Node 16 using `npm install`, then targets the old S3 site | Reviewed runtime/locks, tests and explicit new deployment ownership |
| Collector/API tests | Both package scripts deliberately exit with “no test specified” | Real maintained acceptance tests |

No `node_modules` was present in the collector, API or frontend directories at
inspection. A full install/build, dependency advisory review and browser render
have not been attempted or passed. Package age alone is not an advisory finding.
The working checkout remains suitable source evidence, not a deployable release.

The existing efsn telemetry sends `hello` with `id`, `info` and `secret`, expects
`ready`, then sends normal reports to `/api`. The field/envelope review is
compatible with this collector but is not a transport test. Configure explicit
`wss://` in the eventual node telemetry URL: an unspecified scheme currently
tries WSS followed by WS. Keep the [monitoring guide](restart-monitoring-response.md)
distinction between reported uptime/syncing and actual purchase/chain health.

## Next bounded work

1. Make a separate dashboard patch for startup validation, per-identity
   authentication, all update handlers, duplicate-session handling and secret
   redaction. Preserve the existing efsn wire envelope and keep credentials out
   of the repository. Extend the failing contracts for the chosen identity map
   and reconnect/rotation behavior before calling that patch complete.
2. Add explicit endpoint/database configuration, then establish a pinned install
   and build with the real dependencies. Reproduce the contracts over isolated
   real WebSockets and verify the database/API/browser path, stale data and
   restart behavior. Keep that deployment change out of node consensus patches.
3. Integrate dashboard enrollment into G7's independent-operator kit and perform
   the G6 public deployment check with the selected hosts and credentials.

The [evidence bundle](evidence/restart-dashboard-readiness-2026-10-03/README.md)
contains the archived collector, exact hashes, failed/passing assertions and
source-preservation checks. This work used no chain database or D:/W: disk job.
