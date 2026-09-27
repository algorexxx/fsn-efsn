# Restart monitoring and operator response

Draft for release review, 27 September 2026. Source examined at
`8c2f139c42750814e69b28457ec1721afdbfdb19`. This consolidates the demonstrated
recovery paths into an operating proposal. It does not deploy a monitor, select
alert destinations or approve production thresholds. P1–P15 are unchanged.

The [external snapshot collector](restart-observer.md) now implements bounded
read-only RPC observations and retained-case classification tests. Optional
[durable snapshot history and incident review](restart-observer-history.md) now
retain incidents across restarts and reopen them on observed recurrence.
[Bounded block/receipt backfill](restart-observer-backfill.md) now preserves
contiguous ranges and displaced branches. The
[offline wallet ticket timeline](restart-observer-tickets.md) now derives native
events from saved anchor inventory and retained blocks. Full financial accounting,
historical baseline acquisition, continuous scheduling and notifications remain open;
the policy below describes the complete intended monitoring behavior, not a
claim that the snapshot command implements it all.
The [actual-service follow-up](restart-observer-services.md) now validates eight
external IPC/HTTP observations against two compact synthetic nodes, including a
controlled reorganization and endpoint loss. No runtime correction was needed.
The [ordinary-mining follow-up](restart-observer-mining.md) also passes collection
across naturally advancing heads, catch-up and cold rechecks. Its native inventory
reconstruction supplied the retained reference data for the external timeline.
Production workload and complete accounting remain open gates.

The proposed minimal policy is **automatic observation and notification, with
manual recovery** through the [operator procedure](restart-operator-recovery.md).
The existing purchase controller continues its ordinary retries. A monitor does
not submit transactions, sign, fund accounts, clear records, choose branches,
restart services or change mining settings.

## Initial operating arrangement

Peter operates the donation producer after the agreed backup-wallet block and
handover. The backup wallet's automatic buying remains disabled, and its key is
returned under the agreed custody procedure. Monitoring must not assume that key
remains available for emergency production. See the [wallet handover](restart-wallet-handover.md).

A non-mining verifier can compare canonical history without a ticket or an
unlocked wallet. If used, it needs a separate process/datadir and the accepted
configuration. Two processes operated by Peter provide a useful comparison;
they are not independent operators or evidence of wider network agreement.
This proposal does not require a second funded producer or a new operator.

Record the expected role of each instance: recovery signer, active producer,
verifier, joining node, planned maintenance or retired. A stopped retired backup
node is expected. Zero peers alone is not a chain-failure alert in the approved
single-producer arrangement. An unavailable optional verifier means comparison
is unavailable, rather than that two nodes agree. Once other producers join,
update the expected-peer and comparison configuration.

Use local/private RPC and service logs for operational observations. IPC access
can confer administrative capabilities even when the collector uses only read
methods; an IPC connection is not a server-enforced read-only account. Keep its
process and host access controlled. No wallet unlock, private key or signing
password is needed by the collector. The public fsn-stats dashboard is optional
visibility and is not part of the block-production dependency chain.

## Source findings that constrain monitoring

| Finding | Source and evidence | Consequence |
| --- | --- | --- |
| Consecutive identical buyer errors are suppressed after the first warning | `runAutoBuyTicket` in [autobuy.go](../internal/ethapi/autobuy.go) stores `lastError`; retries use a five-second interval | Retain the unresolved incident. Silence is not recovery, and the retry interval is not an approved alert threshold. |
| Enabled flags are not a progress report | The buyer reconciles only while automatic buying **and** mining are enabled; `fsn_isAutoBuyTicket` returns a flag | Check actual canonical purchases, tickets and produced blocks. A normal downloader pause and a permanent stall need different diagnoses. |
| There is no production live saved-intent status endpoint | The durable record is read internally by `loadAutomaticTicket`; [existing retrieval](restart-small-reserve-and-retrieval.md) uses the stopped-database command | Mark saved-intent identity unknown when it cannot be verified. Do not use the test-only `lab_purchaseState` API or open the writer's LevelDB behind its back. |
| Some error-string hashes are raw bytes | Several `fmt.Errorf` calls use `%s` with `common.Hash`; [Hash.Format](../common/types.go) formats the byte slice. Escaped bytes appear in the [live repair log](evidence/restart-live-abandonment-repair-2026-09-27/live-race.txt) | Error text can route diagnosis, but is not a reliable hexadecimal transaction-ID field. Obtain exact hashes/bytes from RPC or the preserved record. A localized formatting correction is a P4 review finding, not implemented by this document. |
| Stats fields do not prove health | [ethstats.go](../ethstats/ethstats.go) sets `active=true`, `uptime=100`, and its `syncing` boolean tests header height `>=` known highest height; [eth_syncing](../internal/ethapi/api.go) returns **false** once sync progress's current block reaches its highest block | Treat these as legacy reporting semantics, not RPC-equivalent health signals. Use direct RPC, observation freshness and measured availability. Ticket counts can also be unavailable; null is not zero. |
| Dashboard telemetry lacks purchase recovery detail | `nodeStats` reports mining, peers and ticket counts, but no canonical wallet nonce, saved intent, purchase error or interval backing | Hosting fsn-stats alone cannot implement this policy. Its separate deployment/hardening work remains in the [main plan](restart-plan.md#11-node-dashboard). |

The stats observations above concern the node's outgoing payload. The dashboard
may calculate its own connection uptime; that still does not establish chain or
wallet health. No dashboard code or node telemetry code is changed here.

## Collect a consistent, bounded observation

1. Record UTC collection time, endpoint/process identity, reviewed executable and
   configuration identity, expected role and configured wallet. Compare
   `web3_clientVersion`, `net_version`, `eth_chainId`, genesis and the accepted
   anchor block with the release manifest. RPC identity strings alone do not
   prove that the reviewed executable or anchor enforcement is running.
2. Read `eth_getBlockByNumber("latest", false)` and retain its height, hash,
   parent, timestamp, state root, ticket commitment and total difficulty. Read
   `eth_syncing`, `eth_mining`, `fsn_isAutoBuyTicket`, `eth_coinbase` and
   `net_peerCount`. A false sync result only describes this node's known target;
   it does not prove the node knows the newest network history.
3. Pin canonical nonce, liquid balance, raw time locks and ticket reads to that
   explicit hexadecimal block number using the [runbook interfaces](restart-operator-recovery.md#observe-a-consistent-state).
   Reread that block's canonical hash afterward. Discard/retry the observation if
   it changed. An RPC error, timeout or unavailable state is **unknown**, not a
   zero balance/ticket count. `fsn_allTicketsByAddress` returning null without an
   error can mean that the owner has no tickets.
4. Capture `txpool_content` and relevant receipts with their collection times.
   Pool contents and enabled flags cannot be pinned to a historical block. Treat
   the observation as a time window, not an atomic database snapshot, and
   resample before any operator action. Preserve amounts as exact integers;
   balances and interval values are decimal wei strings, while Ethereum numeric
   fields are commonly hexadecimal. Do not round through JavaScript `Number`.
5. Compare nodes at a **common height**, rereading both hashes for stability.
   Different latest heights alone can be normal propagation delay. Stable
   differing hashes at the same height identify divergent histories; retain each
   tip and cumulative difficulty as well. Neither a peer connection nor matching
   heights proves agreement. Comparison/confirmation depth is an operator
   setting, not a new consensus finality rule.
6. Follow canonical blocks and native receipts for the monitored owners, including
   every block since the previous observation. Retain old heads, transaction
   locations and relevant signed bytes before replacing an observation after a
   reorganization. Head notifications are a prompt to check; they are not a
   durable complete history feed. If a gap cannot be backfilled, label coverage
   incomplete and alert rather than silently resetting the cursor.

For purchase success, require receipt status, its current canonical block and
the expected native BuyTicket outcome, ticket ID and owner. Confirm the ticket
at the relevant historical state when needed: its absence from the latest state
can result from normal selection. A self-transfer consuming the same nonce is
not a purchase. Keep the signed payload, receipt location and later selection or
retreat evidence distinct. See the [full interval accounting](restart-handover-runway.md).

A state/header hash that remains stable during a sample can still change later.
Recheck tracked receipt locations after a branch change. The accepted restart
anchor protects its ancestry, not finality of every later receipt.

## Decision guide

These are proposed response classes. "Urgent" means notify the responsible
operator once the condition is established; it does not authorize an automatic
mutation. Normal propagation, selection and synchronization need configured
observation windows before being labelled persistent faults.

| Condition | Required distinction | Operator response |
| --- | --- | --- |
| Monitor/endpoint stops reporting | Planned downtime versus lost observation; a collector failure must not be reported as a healthy node | Alert on stale coverage through a separately checked heartbeat. Restore visibility and resample. Do not restart the producer merely because the collector failed. |
| Wrong identity, anchor mismatch or unexplained state/receipt inconsistency | Check the release manifest and stable observations; an unavailable ancestor is not a matching ancestor | Urgent review. Suspend transaction-repair decisions and preserve evidence. No automatic reset, anchor change or head override. |
| No common-chain progress | Check process/sync state, actual eligible producers, tickets, pending replacements and time; equal-weight divergence is a separate case | Urgent if the required producer cannot advance within the agreed stall window. With no eligible producer, a transfer alone cannot create its execution block. Escalate outside the supported routine repair. |
| Compatible producers advance different histories | Compare hashes at a common height and difficulty over time; both can buy tickets successfully on their own forks | Preserve both histories and agree on continuation before considering the [coordinated pause](restart-equal-weight-pause.md). Confirm a funded surviving producer. The monitor must not choose which history loses. |
| Mining or buying unexpectedly disabled | Compare with expected role and sync state; backup/verifier/maintenance instances differ from the active donation producer | Check ordinary resumption after synchronization. A persistent unexpected state needs operator investigation; do not issue unattended repeated start commands. |
| Purchase nonce gap after rollback | Establish the saved intent or label it unknown; check current receipts and pool for automatic reinclusion | Use [sequential repair](restart-operator-recovery.md#check-funding-and-repair-one-nonce-at-a-time) only for missing predecessors. The [live integration](restart-live-abandonment-repair.md) recovered 39–40 automatically and required manual work only for 41–42. |
| Purchase is pending locally but not at the producer | Verify the producer's accepted head/readiness and admissibility of the exact bytes | Distinguish P4's current-nonce automatic intent from a manually repaired predecessor. Review exact-byte delivery through existing RPC if needed; `already known` is not inclusion. See [delivery evidence](restart-manual-purchase-delivery.md). |
| Insufficient usable stake | Distinguish free liquid/raw interval coverage from live-ticket rights, future-only rights and losses | A temporary wait needs a real ticket capable of returning the required rights and another advancing producer. Zero tickets plus inadequate free backing is a funding incident, not a wait for selection. Any transfer needs an authorized source, amount and safe nonce ordering. |
| Original/saved purchase becomes invalid or conflicts | Inspect the exact payload, head-time validity, gas parameters, canonical nonce and competing pool bytes | Stop ordinary replay and follow the specific owner-reviewed procedure. Funding does not repair an expired interval. [Abandonment](restart-operator-recovery.md#explicitly-abandon-an-unsuitable-saved-intent) is a separate signed decision, not record deletion. |
| Nonce consumed without a confirmed purchase | The warning can follow an intentional self-transfer or an unexpected competing transaction | Match the actual canonical transaction to the recorded decision. Unexplained consumption is urgent. Even authorized abandonment stays open as a recovery incident until fresh native purchases and production are observed. |

Ticket count alone is not an eligibility proof, and lack of a recent block from
one wallet is not automatically a fault when multiple wallets compete. Correlate
native purchases, selection opportunities and actual common-chain progress. A
temporary funding warning while a live ticket awaits normal selection is not the
same incident as exhausted backing after a first retreat.

## Alert ownership, timing and closure

The initial responding operator is Peter, consistent with the agreed launch.
An alternate contact, notification destination and acknowledgement/escalation
timings remain unset. The backup key owner is not automatically an on-call
operator or emergency signer. Other operators can own alerts for their own nodes
when they join; the central dashboard should not gain control of their wallets.

| Setting to approve before deployment | Basis for choosing it |
| --- | --- |
| Collection interval and RPC deadline | Measured node/RPC load; bound work and report partial/missing observations |
| Collector/endpoint freshness deadline | Detect lost coverage independently of the collector's own success reports |
| Head-stall and sustained-divergence windows | Production block timing and propagation; distinguish a short same-height race from persistent separation |
| Purchase/selection observation window | Wallet inventory and live-ticket behavior; keep an advancing chain separate from wallet progress |
| Interval-validity lead time | Earliest relevant predecessor/saved `end - 29 days` against the applicable head timestamp, plus operator response time; not a wall-clock substitute |
| Acknowledgement, reminder and escalation schedule | Actual availability of the named responder, particularly with one producer |
| Evidence retention and storage budget | Preserve unresolved incidents, displaced signed bytes and block locations; alert before capacity prevents retention |

The prior ten-second gap check and 60/120/300-second test timeouts are test
controls, not chosen production settings. The controller's five-second retry is
also not a guaranteed purchase/mining deadline. Do not silently convert these
values into deployment defaults.

Each alert should retain: incident ID and condition, expected role/wallet,
first/last observed UTC times, observation coverage/errors, source node and
release identity, both branch observations when available, nonce/pool/receipt
evidence, relevant ticket/interval funding, and the next applicable runbook
section. Keep secrets out of the notification. Store the fuller evidence locally
with controlled access and link it by incident ID.

Deduplicate repeated observations into the same unresolved incident, with
reminders and severity changes under the approved schedule. Acknowledgement is
not resolution. A quiet log, successful RPC response, enabled flag, accepted
submission, advancing unrelated wallet or old confirmation log cannot clear a
purchase incident.

Closure needs current canonical native success for the intended purchase,
fresh automatic successors and observed production under the applicable wallet
and network conditions. The rehearsals require two fresh successors; that is
the proposed recovery acceptance check, not an indefinite liveness guarantee.
If receipts move or disappear, reopen/reclassify the incident. Do not shut down
working nodes solely to satisfy an optional cold audit during a live incident.

## Approval and implementation gates

| Gate | Current state | Concrete remaining work |
| --- | --- | --- |
| Manual recovery behavior | Demonstrated for the linked synthetic cases; unsupported conditions remain | Review and accept the scope and limitations in the operator runbook |
| Observation collector | [External snapshot command implemented](restart-observer.md); retained-case, actual-service and [ordinary-mining checks](restart-observer-mining.md) pass | Validate collection during live competing reorganization and representative deployed workload; select deployment limits |
| Snapshot history and incident state | [Append-only local history and review](restart-observer-history.md) implemented; cross-platform replay, reopening, abrupt-exit and ordinary-mining checks pass | Validate live competing reorganization and representative workload; approve storage/retention procedure |
| Block coverage | [Bounded canonical block/receipt backfill](restart-observer-backfill.md) and explicit gaps implemented; retained-fork, IPC/HTTP and ordinary-mining checks pass. [Offline wallet ticket timelines](restart-observer-tickets.md) match the retained ledger and handle explicit gaps, rewinds and replacements | Acquire historical anchor inventory when monitoring starts later; validate representative backlog and live competing reorganization collection; review P16 separately; deploy collection cadence |
| Routing and operator coverage | Peter is the initial operator; destinations/times unset | Select destinations and timings, then demonstrate notification, acknowledgement and a lost-monitor heartbeat |
| Detection correctness | Retained snapshots, fault cases, actual-service observations, ordinary-mining collection and durable replay/review/recurrence transitions pass; continuous alerts have not been exercised | Extend history mode to live competing reorganization and isolated public-test-key delivery drills for the cases below |
| Real funding and custody | Synthetic contributions are not authorized real reserves | Recheck real-address intervals, gas runway and any explicitly agreed funding source; complete backup-key return |
| Release review | P1–P16 and recovery tool still require independent review | Include observability limits and accepted manual policy in the review record; keep formatting/telemetry findings explicitly dispositioned |

Collector/drill acceptance must cover: healthy single-producer operation with
zero peers; an advancing network with one stalled wallet; equal-weight forks;
automatic reinclusion before manual repair; a funding wait and genuine funding
exhaustion; an expired/conflicting intent; unavailable saved-intent data; receipt
rollback; intended maintenance and key handover; RPC/log/collector loss and
rotation; and correct notifications without any transaction or mining-control
call. Replay of recorded evidence helps classification, but does not replace an
end-to-end alert-delivery drill.

This monitoring work can proceed without another database restore or funded
validator. Public deployment, selected alert delivery and real signing remain
separate steps. The [main plan](restart-plan.md) retains historical replay,
distribution, networking, anchor and release gates.
