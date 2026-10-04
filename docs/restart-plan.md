# Fusion restart launch plan

Updated 4 October 2026. Working branch: `codex/restart-investigation-wip`.
This is the current checklist, not permission to sign or launch. The
[investigation record](restart-investigation-record.md) preserves the previous
plan, rationale and chronology. Linked reports retain their dated findings;
their old next-step lists do not add separate requirements to this checklist.

## Agreed outcome and sequence

Restart from accepted, verifiable Fusion history with the smallest reviewed
client changes. A fixed recovery anchor must prevent an incompatible old
continuation from replacing the accepted restart. Ordinary compatible forks
retain existing fork choice and ticket economics.

Peter initially operates the backup and donation nodes. Backup wallet
`0x9fc4c40e50f902b9aa641b4a32ebaafa5c9386a1` signs one historical recovery block,
including the donation wallet's first funded ticket purchase, and buys no new
ticket. Donation wallet `0xa3ce60d2dbf51afa0ab106df1c44a2e48853817a` completes
the reviewed time bridge and continues mining/replenishment. Our backup signer
is cleanly stopped and its key returned after verified handover.

The public dashboard and independent-producer onboarding are included in the
launch programme. Independent owners may join after bootstrap using their own
keys and ordinary funded tickets; they do not need to sign the initial block.
The first historical block is only part of recovery: finish and verify the
controlled recovery sequence and publish its fixed anchor before inviting
ordinary public transactions or independent production. Do not insert an
unreviewed entrant transaction into the controlled bridge.

Prepare and test the entrant procedure before launch. Record actual independent
participation after recovery as a separate milestone; an unavailable volunteer
does not invalidate a completed test or require Peter to simulate independence
with another wallet. The backup owner may later join through this same procedure.

## Completion rules

Eight gates below define the remaining work. Each unchecked item needs linked
evidence or a named, reviewed disposition before its stated boundary. Passing a
test closes that case, not every related failure mode. Tests need explicit
workload bounds and pass conditions before execution; extend them only for a
new failure, changed implementation or an uncovered supported use case.

The release supports full block sync from a verified restored state, with
`--syncmode full`. Fast/light acquisition, arbitrary freezer/pruning layouts and
genesis resync are not advertised as working launch paths. Any reachable path
that can violate the fixed anchor remains a blocker regardless of its label.
Unsupported configurations must be refused or clearly excluded in the operator
release; no silent expansion of the supported matrix.

New findings are assigned to one of these gates. Record their consequence and
whether they block the declared launch, need an operating restriction, or belong
in the later backlog. No unresolved accounting mismatch, reproducible accepted-
history replacement, uncontrolled signing, or unusable supported onboarding path
can be waived merely to meet a date.

## Gate summary

| Gate | Evidence already available | Remaining boundary |
| --- | --- | --- |
| G1 History and preservation | Complete structural/current-state checks; baseline replay to 3,300,000; complete local package/restore | Accepted history and trust record before final construction |
| G2 Client and supported operation | P1–P17 candidates; anchor, crash, discovery and purchase regressions | Reviewed release candidate |
| G3 Recovery and custody | Complete-state test-key bridge, separate imports, signing journal and command interruption checks | Approved real artifacts before public activation |
| G4 Supervised launch and response | SSH and self-hosted fsn-stats selected; optional observer diagnostics available | Rehearsed manual checks and operator response before public use |
| G5 Release infrastructure and data | Network profile, DNS recovery and local restore/service checks | Real download/restore/connect path before public use |
| G6 Public dashboard | [Toolchain acceptance](restart-dashboard-toolchain.md) passes; frontend and backend audits now report zero known advisories, with maintenance and public deployment controls open | Working public dashboard before public-use announcement |
| G7 Independent producers | Funded test-key entrant already buys and mines with donation node | Tested entry kit before release; actual independent entry after recovery |
| G8 Review, final rehearsal and activation | Extensive retained evidence; final release not selected | Explicit go/no-go and recorded launch |

## G1 — History and preservation

- [ ] Confirm immutable preservation and a separate verified recoverable copy;
  record provenance, hashes, storage health and restore ownership. Resolve the
  earlier ESXi storage-controller concern before making it a launch dependency.
- [ ] Continue bounded baseline replay from 3,300,000 through the accepted
  historical parent (backup head 15,130,080 unless better verified history is
  selected). Check capacity before each range. Record legacy checkpoint
  shortcuts explicitly and compare cold state/ticket/receipt commitments.
- [ ] Verify historical compatibility of the selected candidate changes; do not
  cite the unchanged baseline replay as proof of the patched executable.
- [ ] Close the surviving-operator evidence window and accept the exact parent
  and verification/trust limits before construction. Investigate any mismatch.

Evidence: [integrity/replay](restart-integrity-investigation.md),
[snapshot restore](restart-snapshot-restore.md),
[surviving-node contact](restart-surviving-node.md).
W: remains available for capacity; no new bulk workload starts without fresh
space/path checks. On 4 October the unchanged baseline completed 3,000,000 through
3,300,000 on a verified separate D:-backed ext4 copy. Replay and the independent
exact-height cold check passed; the closed target occupies 6,527,746,048 allocated
bytes. See the [final evidence](evidence/restart-replay-3300000-2026-10-04).
No further range is running; candidate-patch historical compatibility remains open.

## G2 — Client and supported operation

- [x] Assemble the [proposed source patches](restart-release-extraction.md) from
  pinned upstream: P1–P17 node changes, optional O1 and separate recovery tooling.
  All 109 node hunks have review IDs; observer and gateway changes are excluded.
  This prepares the review input, not approval of the release selection below.
- [ ] Select every production hunk against upstream from the
  [P1–P17 inventory](restart-node-patch-review.md); separate node changes,
  recovery tooling, observer, packaging and inherited explorer settings.
- [x] Freeze the [ten-group release matrix and reviewer handoff](restart-release-matrix.md)
  for the supported Linux restored full-sync path. It links retained evidence,
  exact test entry points, inherited failures and final acceptance criteria.
- [ ] Complete those groups against the selected release and hosts, including
  the clean-machine operator kit and final handover rehearsal. Reuse existing
  passing evidence; do not rerun unchanged investigations by default.
- [x] Close the bounded [unknown-heavier automatic-sync gap](restart-automatic-sync.md):
  complete ancestry, compatible catch-up, explicit anchored refusal and an
  unanchored control all pass with cold heads/lookups intact. Final release/host
  acceptance remains open; the fixture adds no ongoing finality.
- [x] Measure [anchor startup cost](restart-anchor-startup.md) through one million
  synthetic descendants: all 12 cases pass, including split heads and damaged
  canonical indexes. The two largest successful startup checks take about 26 s
  aligned / 37 s split locally. Final release/host service timing remains open;
  this does not establish full historical execution or large-reorg batch cost.
- [x] Measure [compatible-reorganization storage](restart-reorg-cost.md) through
  4,096 displaced blocks with 32 transactions/logs per block, including shorter
  heavier replacement and before/after canonical-batch process exits. All six
  corrected-fixture cases pass; no runtime change. Maximum-gas workloads,
  arbitrary depth and production resource sizing are not established.
- [ ] Record inherited failing tests and disposition native-call decode and
  other audit findings. Select the release toolchain/dependencies, establish CI,
  build reproducibly and rerun affected compatibility checks after changes.
- [ ] State operating limits: equal-weight forks may require intervention;
  purchase nonce gaps and retreat losses can require manual repair and funding.
  Demonstrate the selected restore/storage path without promising power-loss
  safety or unsupported sync modes from process-exit tests.

Evidence: [anchor](restart-anchor-implementation.md),
[patch review](restart-node-patch-review.md),
[operator recovery](restart-operator-recovery.md),
[native decode finding](native-call-decode-errors.md).

## G3 — Recovery and custody

- [ ] Recheck both real wallets' balances, time-lock intervals, gas and ticket
  runway. Publish the exact Candidate A sequence and complete economic ledger,
  including both original tickets' selection/refund/expiry effects. Candidate B
  remains a fallback only if A fails a required condition.
- [ ] Finalize owner approvals, signer proof, offline custody and artifact
  journal; drain/inventory live backup-wallet pools and saved purchases. Prevent
  concurrent signers and verify process shutdown: mining-stop RPC alone is not
  a barrier to already scheduled signed work.
- [ ] Review fresh timing parameters, then produce the authorized artifacts once,
  independently import/cold-check them, freeze the final anchor and preserve
  recovery data and manifests. Return backup-key control after verified handover.

Evidence: [wallet handover](restart-wallet-handover.md),
[guarded construction](restart-recovery-construction.md),
[complete-state command rehearsal](restart-full-state-operator.md),
[signing approval](restart-signing-approval.md).
Passing public-test-key rehearsals does not authorize real signing or use of
the backup owner's funds for another participant.

## G4 — Supervised launch and operator response

4 October scope decision: Peter will use SSH checks during the actively
supervised initial blocks and the self-hosted fsn-stats dashboard for visibility.
A separate hosted monitoring service, heartbeat integration or notification
provider is not a launch prerequisite. The observer/history tools already built
remain optional diagnostics. They add no consensus rule. SSH checks by this
assistant take place during an active work session, not as an unattended service.
If nobody is watching, this arrangement does not promise immediate notification
of a node or dashboard-host outage. Automated alerting can be a later choice.

- [x] Measure the declared longer retained backlog: the
  [4,096-block/64-block replacement fixture](restart-observer-backlog.md) passes
  ticket reconstruction, preserved displaced evidence and closed-copy reopening
  on Windows/Linux and with Linux race detection. This is observer evidence,
  not execution of a consensus-valid 4,096-block chain or production capacity.
- [x] Provide an explicit [capacity-copy procedure](restart-observer-capacity.md)
  that continues a full history in a new directory with a larger reviewed budget,
  preserving all original events, ticket baselines and unresolved review state.
  This adds headroom within the existing 1 GiB ceiling; it does not prune events
  or reduce growing replay cost.
- [ ] For any observer history actually used during launch, select a bounded
  collection/evidence budget and preserve its baselines and unresolved incidents.
  Continuous retention/rotation sizing is conditional on deploying continuous
  collection; it is not a reason to delay the supervised restart work.
- [ ] Capture and preserve both production wallet baselines before activity.
  Historical state is sparse; later RPC acquisition cannot be assumed possible.
- [x] Supply an [external history check](restart-observer-check.md) with tested
  executable exit codes for missing/stale collection, low logical headroom and
  unresolved incidents. Fresh reviews do not mask stopped collection; failed
  history reads return nonzero. This is local detection, not message delivery.
- [ ] Rehearse the supervised SSH checks and fsn-stats visibility for the agreed
  wallet handover. Record the responding operator, evidence and manual response
  to stalled production, failed purchases and unavailable observation. External
  service integration and automated notification delivery are outside this gate.
- [ ] Rehearse the applicable manual detection/response cases in the
  [response guide](restart-monitoring-response.md), accept manual intervention
  limits and verify the actual authorized funding available for supported repair.

Evidence: [observer](restart-observer.md),
[mixed workload](restart-observer-mixed-workload.md),
[opening replay improvement](restart-observer-open-replay.md),
[sparse backup state](restart-observer-preserved-inventory.md).
No ongoing finality or automatic economic repair is added by this gate.

## G5 — Release infrastructure and data

- [ ] Choose organization maintainers, domains, hosts and release ownership;
  preserve upstream ancestry/license notices and review requirements. Produce
  checksummed/signed binaries and source from the exact approved inputs.
- [ ] Deploy the selected DNS discovery contact with distinct stable P2P identity,
  public TCP/UDP reachability and static fallback. Check real NAT/firewall and
  whichever IP families are advertised. Keep signing/admin RPC private.
- [ ] Publish the verified recovery package with trust assumptions and a recovery
  download route; demonstrate clean-machine download, hash verification, restore,
  full-sync catch-up and matching anchor/head/state/tickets using release commands.
- [ ] Check production storage growth, clean shutdown/backup/restore and public
  read-RPC/explorer behavior across the transition, including native events and
  reorganizations. Retain the historical gateway as a reference.

Evidence: [network profile](restart-network-profile.md),
[DNS resilience](restart-bootstrap-dns.md),
[complete local restore](restart-snapshot-restore.md).
More discovery operators/domains can be added as participation grows.

## G6 — Public dashboard

Target repository: `C:/Users/Peter/Documents/CODING/fsn-stats`, branch
`codex/recovery-readiness`. See the [repository handoff](restart-dashboard-handoff.md).
Further dashboard implementation is parked while the chain investigation resumes.
The dashboard is included in public-launch readiness, while block production
must continue if it is unavailable.

- [ ] Establish a pinned, tested dashboard build and deployment. Replace legacy
  endpoints/default credentials with validated deployment configuration; use
  private least-privilege database access and TLS/WSS.
- [ ] Verify telemetry authentication and session/identity ownership, bounded
  inputs, credential rotation, reconnects and stale/disconnected reporting.
  Publish a usable enrollment procedure for independent operators without
  distributing validator keys or making telemetry enrollment a consensus rule.
- [ ] Demonstrate efsn telemetry through ingestion, storage, API and browser;
  compare displayed heads against direct RPC, and drill dashboard/collector loss.
  Label self-reported and stale values. Legacy uptime/sync flags do not establish
  chain agreement, ticket funding or purchase health.
- [ ] Publish the actual dashboard and operating runbook before announcing public
  economic use. Record maintenance ownership, access, retention and recovery.

The [authentication correction](restart-dashboard-auth.md) now addresses the
five baseline failures in a separate dashboard branch: 71 contracts and one
real loopback collector test passed with unchanged locked dependencies. The
[deployment configuration follow-up](restart-dashboard-config.md) expands this
to 86 passing contracts and one real collector wire test, including a real HTTP
API check with stubbed storage. Endpoints, loopback listeners and database
credentials now require explicit configuration. Inherited persistence, timer,
SQL and schema problems were recorded as the next blockers. A
[real PostgreSQL compatibility check](restart-dashboard-postgres.md) then exposed
and corrected the old driver's connection failure on Node 22.11.0. The pinned
replacement and explicit database timeouts pass five real database scenarios.
The [snapshot persistence replacement](restart-dashboard-snapshots.md) now passes
99 contracts and real collector/PostgreSQL/HTTP checks with two synthetic nodes,
including reconnects and stale API responses. The [browser freshness correction](restart-dashboard-browser.md)
now passes 110 contracts and six React DOM scenarios, clearing old values on
failure/expiry and recovering automatically. Its inherited webpack production
build initially failed on Node 22.11.0. The [build correction and compiled-browser
acceptance](restart-dashboard-build.md) now pass: 110 contracts, seven React DOM
tests and nine Edge checkpoints, including outage recovery and accessible map
closure. [Collector input limits](restart-dashboard-input.md) now pass 120 contracts
and eight real socket tests, including byte/connection/message caps, login expiry
and bounded history replies. [Per-node freshness](restart-dashboard-node-freshness.md)
now separates collector connection state from accepted block/stats/pending reports:
132 contracts, nine socket tests, eight DOM tests, the real database pipeline,
strict build and 13 compiled-browser checkpoints pass. [Chart cache corrections](restart-dashboard-history.md)
now admit advancing heads, display the latest forty cached heights, backfill
only missing heights and reclaim abandoned forks within the 2,000-height window.
145 contracts, 10 socket tests and six database pipeline scenarios pass.
Retained forks are bounded by configured node identities plus the existing
representative; this remains diagnostic
telemetry, not chain selection. [Output limits](restart-dashboard-output.md) now
bound pending collector socket writes across telemetry, viewer and control
replies: 151 contracts, 12 socket tests and six database scenarios pass.
The [actual efsn comparison](restart-dashboard-telemetry.md) now passes through
the unchanged collector, PostgreSQL and HTTP API: 51 distinct synthetic blocks
match direct RPC, as do ticket, peer, pending and mining values. It confirms a
legacy sync-flag/RPC mismatch and literal reported uptime. A fifty-block reply
with only ten transactions per block can exceed the 64 KiB test input limit.
The [presentation and busier telemetry follow-up](restart-dashboard-presentation.md)
removes the ambiguous sync/uptime columns and passes eight DOM tests, the strict
build and four compiled Edge checkpoints through the actual node/database/API
pipeline, including snapshot-writer loss and recovery. Sixty blocks with ten
transactions each produce a measured 66,076-byte history reply, accepted with an
explicit 128 KiB fixture limit. An offline model and source review identify
transaction-hash retention as the next memory issue; those test limits are not
deployment defaults. The [validation and retention follow-up](restart-dashboard-retention.md)
now validates known block/stats/pending fields and retains only scalar chart
records and transaction/uncle counts. Current-head hashes remain in both API
routes and match direct RPC. All 159 contracts, 12 socket tests, six database
scenarios and four actual-node/browser checkpoints pass. An offline eight-identity,
2,000-height, 18,000-variant run measures about 13–14 MiB retained heap growth
for both one and 714 transactions per block; this is not concurrent load or peak
RAM. An earlier freshness assertion failure is preserved with its cause unproven;
the successful run adds complete-report readiness and receipt diagnostics without
widening limits. Metadata/ping field review, production payload/resource sizing,
collector loss during mining, runtime review and proxy/TLS/deployment controls
remain open.
The [larger-report/multiple-node profile](restart-dashboard-profile.md) now
passes with eight simulated reporters, 714 hashes per block, two batches of
fifty-block history replies and four saved advancing heads. It independently
demonstrates 64 KiB snapshot and 256 KiB output failures. A 4 MiB input / 1 MiB
pending-output / 1 MiB snapshot candidate succeeds; highest sampled collector
RSS is 238.5 MiB, not a continuous peak or deployment allocation. The small
writer correction reports previously silent transport closes/errors; 161
contracts, 12 socket tests and six database scenarios pass. Registration/ping
fields and current-head extensions still need explicit admission bounds before
the measured profile can become a supported public deployment envelope.
The [registration and ping follow-up](restart-dashboard-admission.md) now
projects native registration fields into at most 2 KiB of UTF-8 JSON and accepts
only timestamp strings occupying at most 128 serialized bytes. Five new
regressions fail on prior source; 167 contracts, 13 socket tests and the actual
efsn/database/API/browser check pass. Two initial integration failures exposed
a Windows-to-WSL reachability delay; the fixture now checks bounded port readiness
while retaining zero-writer-error assertions and transport diagnostics. Current
heads, total enrollment/inactive rows and the Primus-derived IP still need
aggregate bounds. Forwarded-header normalization belongs in proxy acceptance.
The [head/enrollment follow-up](restart-dashboard-enrollment.md) now adds explicit
complete-head and credential-roster limits, projects native head fields without
truncating hashes, and bounds appended IP literals. Six new regressions fail on
prior source; 173 contracts, 13 socket tests, eight maximum-size inactive rows,
rotated reconnect, concurrent reporters and actual efsn/database/browser pass.
The boundary snapshot reaches 554,917 bytes under the tested 1 MiB budget.
The 8-node / 64 KiB-head / 4/1/1 MiB configuration is a coordinated deployment
candidate; process settings must match and output queues can still fill.
The [local TLS proxy follow-up](restart-dashboard-proxy.md) now tests an nginx
candidate with certificate/hostname verification, private-route refusal and
normalized forwarding headers. Eight bounded WSS reporters, complete heads,
a 3,276,956-byte history message, API freshness, connection caps and inactivity
timeouts pass. Synthetic pings follow the actual fifteen-second efsn cadence.
All thirteen socket tests pass on Linux and Windows after correcting an
OS-dependent close-code assertion. No application/consensus code changed.
This proxy slice uses an in-memory store and byte-compares compiled assets;
actual efsn WSS/database/browser and collector loss during mining remain open.
The [actual WSS follow-up](restart-dashboard-wss.md) now passes with the real
node reporter, PostgreSQL, HTTPS API and four compiled-browser checkpoints.
RPC comparisons and writer-loss expiry/recovery pass. A mixed Windows/WSL
timestamp-ordering failure led to placing collector, writer and API together
on Linux, preserving strict freshness rules. Browser trust is pinned only to
the temporary test certificate; public PKI and renewal remain open. All 173
contracts, 13 socket tests and the original plain-loopback integration pass.
Only fixtures changed. That chain is stationary. The subsequent
[collector-loss mining drill](restart-dashboard-mining-outage.md) now passes:
twelve ordinary blocks and ticket purchases while the collector process is
absent, stale API refusal, automatic WSS recovery and verified outage-block
history. The investigation also exposed a queued old-head report after reconnect;
P17 changes two reporter lines to read the current canonical tip. It changes
telemetry only and needs its own release review. The stationary browser regression
and 173 contract / 13 socket tests also pass. This closes the bounded local
process-loss item. The [runtime/dependency review](restart-dashboard-runtime.md)
now passes the same contracts, sockets, WSS/database/browser scenario and strict
frontend build on Linux Node 24.21.0 with unchanged dependencies. It identifies
ws 1.1.5 on the public collector path as a concrete launch blocker and records
separate work for Primus, Lodash, Express, GeoIP, browser Axios, unused tools and
the obsolete deployment workflow. Audit counts distinguish package findings from
proven reachable issues. Update the transport pair first, then re-audit and
validate the final pinned installation; runtime compatibility alone does not
close dependency acceptance. Supervision, public certificates and log lifecycle
acceptance also remain open. The [transport correction](restart-dashboard-transport.md)
now pins Primus 8.0.9 and ws 8.22.0 with no application or efsn source change.
All 173 contracts, 14 socket tests, native WSS/database/browser, eight-reporter
proxy and the mining-outage drill pass on Node 24. The byte maximum is explicitly
inclusive after the upgrade. A fresh audit clears the three targeted package
findings; 41 other root findings remain for disposition. Continue the remaining
dependency work before public deployment acceptance.

The [backend cleanup](restart-dashboard-backend.md) subsequently removes twelve
unused direct dependencies and the unserved legacy adapter, and migrates Lodash
to 4.18.1. All 178 contract/14 socket tests and actual WSS/mining checks pass.
That reduced the root audit to 18 affected names. The subsequent
[API update](restart-dashboard-api.md) pins Express 4.22.3 and removes the
separate API install, clearing all nine Express-related findings. The current
178 contract/14 socket tests and native WSS/browser/proxy checks pass. The
[GeoIP/diagnostics update](restart-dashboard-geoip.md) subsequently clears the
remaining nine backend findings, with all 144 installed paths matching the lock.
It requires Node >=24 and passes a clean Linux install plus the same integration
checks. No application JavaScript or node sources change in these two slices.
The [frontend update](restart-dashboard-frontend.md) pins supported Axios 0.34.0,
removes thirteen unused direct packages and replaces the Foundation deployment
workflow with validation only. Eight React tests, the production build, nine
compiled-browser checkpoints and native WSS/browser acceptance pass. The frontend
audit drops from 76 to 73; remaining findings are absent from the production
source maps but still require build-tool review. Application JavaScript and node
sources remain unchanged. The subsequent [toolchain replacement](restart-dashboard-toolchain.md)
removes CRA and clears the remaining 73 frontend advisories, including the map
Acorn path. Clean Linux Node 24/npm 10 installation, DOM/build/lint checks,
compiled-browser and native telemetry acceptance pass. A reproduced linter gap
is covered by maintained ESLint's undefined-name check; the report records the
remaining lint coverage differences. All active application-library versions
and efsn sources are preserved. UI maintenance, GeoIP operations and hosting
controls stay open. The [UI maintenance review](restart-dashboard-ui-maintenance.md)
then identifies the map wrapper's React 16 peer limit and the separate
tooltip/theme migration choices. It fixes reproduced saved-pin failures without
changing dependencies: malformed or blocked browser storage no longer prevents
live reports. Twenty-two frontend tests, seven storage browser scenarios, the
existing nine browser checkpoints and native telemetry acceptance pass.
The [GeoIP operations investigation](restart-dashboard-geoip-operations.md)
then completes ten offline updater cases and five dataset-switch checkpoints.
The stock updater accepts mismatched archive checksums and missing data, and
failed updates can leave mixed files. Isolated staging preserves active data;
fresh-reader activation and rollback pass. Implement the protected downloader,
complete dataset validation and supervised restart before accepting public updates.
The subsequent [read-only validator](restart-dashboard-geoip-validation.md) passes
59 new tests, with 237 backend contracts and 14 socket tests passing overall.
A full data scan and synthetic lookup expose the reader's loss of IPv6 precision;
the bundled data fails the gate. The [reader comparison](restart-dashboard-geoip-reader.md)
selects standard MMDB. The subsequent [integration](restart-dashboard-mmdb.md)
replaces the old reader/converter dependency and validator, adds checked startup
loading and preserves country-only flags. Its 204 backend contracts, 14 socket
tests, 23 frontend tests, twelve compiled-browser checkpoints and native
WSS/database/browser acceptance pass. Explicitly disabled geography is supported;
production data acquisition/update controls remain conditional on enabling it.
No efsn source or chain behavior changes.
The [service supervision follow-up](restart-dashboard-supervision.md) adds three
systemd service candidates and a private journal profile. Eleven real-process
checkpoints pass, including crash recovery, database outage, pending-write drain,
stale refusal, deliberate stop and startup-rate-limit repair. A separate rotation
drill retains 16 MiB and evicts old logs. The combined run's logging-probe failure
is retained; production rate-limit/log-rate acceptance remains open. Application,
dependency, frontend and efsn code are unchanged.
The [proxy lifecycle follow-up](restart-dashboard-proxy-lifecycle.md) now passes
all eight local checkpoints for supervised HTTPS/WSS, timer-driven file rotation,
archive retention, valid/invalid certificate replacement, worker/master recovery
and deliberate stop. Separate proxy and native efsn/database/browser regressions
also pass. WebSocket clients reconnect after bounded worker retirement on reload;
log size/age settings are retention targets, not a disk quota. Public certificate
issuance/renewal, actual-host reboot, production log and supervised-response
acceptance and the coordinated manifest remain open. No chain or application code changes.

This gate complements G4's supervised checks and response procedure. A visible
node list alone does not close either gate.

## G7 — Independent producers after bootstrap

- [ ] Before release, publish a simple operator kit: release and data verification,
  anchor/network configuration, discovery/static fallback, full-sync readiness,
  funding/interval/gas checks, first ticket purchase, mining/auto-buy and monitoring.
  An existing ticket or exactly 5,000 liquid FSN alone is not a runway guarantee.
- [ ] Rehearse that kit from a fresh node with a distinct test key after recovery:
  synchronize through the fixed anchor, buy an ordinary funded ticket, mine an
  accepted block alongside donation production, replenish and cold-restart.
  Keep the backup signer stopped. Check incompatible old-chain refusal separately.
- [ ] After bootstrap, help a willing independent owner run the released kit with
  their own authorized funds and keys. Record agreement on canonical blocks and
  the owner's successful purchase, production, replenishment and restart. No
  operator allowlist, shared signing key or assumed foundation funding is added.
- [ ] Record that operator's support/alert arrangements and optional independently
  hosted discovery/data contact. Test independence from Peter's infrastructure
  once another real operator can provide the needed services.

Evidence already passed: [complete-state funded entrant](restart-full-state-participant.md)
with public test key 3 and independent account ledgers. It proves the tested
mechanism, not public package usability, a real volunteer or an authorized
funding contribution. Multiple Peter-operated nodes do not count as independence.
The last two items are post-bootstrap milestones; the first two precede release.

## G8 — Independent review, final rehearsal and activation

- [ ] Supply reviewers with the selected small production diff, exact artifacts,
  tests and dispositions from G1–G7. Resolve findings; consensus/validation changes
  require independent human review. Additional AI review can support that review.
- [ ] Complete a final rehearsal using the selected release, network profile,
  dashboard, monitoring and operator instructions. Record source/build hashes,
  timing, head/state/ticket agreement and accepted limitations.
- [ ] Approve the launch manifest: history/anchor, sequence/ledger, network and
  transaction-replay policy, artifacts, endpoints, custody, operator duties,
  incident contacts and stale/incompatible-node procedure. Start in the reviewed
  order and verify ordinary production/replenishment before public economic use.
- [ ] After launch, record G7's independent participation milestones and regular
  restore/monitoring checks. Never silently reset publicly used history to the
  old backup in response to a later failure.

## Decisions and work order

| Decision | Default / current position | Due |
| --- | --- | --- |
| Historical parent and evidence deadline | Backup is a candidate; welcome verifiable surviving history | G1, before construction |
| Recovery sequence | Candidate A, one backup block then donation bridge/production | G3, before real signing |
| Chain/network identity and replay policy | Preserve history; no new ID selected | G5/G8 release manifest |
| Launch visibility and response | Supervised SSH plus self-hosted fsn-stats; observer tools optional; no separate alert-service requirement | G4 |
| Public dashboard and hosting | Included; fsn-stats requires readiness work | G6 before public use |
| Independent participation | Kit ready before release, real operators join after recovery | G7 |
| Domains/organization/hosts/toolchain | Final choices unselected | G2/G5 |
| Accepted residual risks | Written, case-specific review; no implicit waivers | G8 |

Current technical order (efsn):

1. G1: resume bounded historical execution after fresh capacity/path checks,
   preserving completed checkpoints and the original backup. Keep baseline and
   candidate-patch validation distinct.
2. G2/G5/G7: use the [frozen release matrix](restart-release-matrix.md) to select
   production hunks/build inputs and disposition findings, close complete-ancestry
   automatic-sync coverage, then complete the public package and clean-machine
   entrant rehearsal. Reuse retained evidence; observer/dashboard expansion is parked.
3. G3/G4/G8: finish real-artifact review, the supervised SSH/dashboard handover
   procedure and final rehearsal. External monitoring-service work is parked.

G6 implementation is parked in the [standalone dashboard repository](restart-dashboard-handoff.md).
Its existing commits, local acceptance and remaining work are preserved there.
When dashboard work resumes, use its `docs/recovery-handoff.md` and the
[runtime/dependency worklist](restart-dashboard-runtime.md). Public host/domain,
certificate renewal, reboot, persistent logs, supervised response, production
retry/log rates, UI maintenance disposition and the coordinated release manifest remain open.
Retain the unresolved journal-probe limitation and same-host clock assumption.
Select disabled geography explicitly or finish the enabled MMDB data workflow.
Recheck advisories and rerun acceptance on the final package. The eight-node,
64 KiB-head and 4/1/1 MiB limits remain a tested candidate requiring sizing review
for growth. G6 is still required before public use; it no longer drives unrelated
dashboard expansion in the chain investigation.

Deliberately outside this launch: disputed-wallet confiscation/burns, new voting
economics, ongoing finality, automatic nonce-gap funding/repair and survival
after the sole remaining participant leaves. Broader platform/sync support and
unbounded stress testing need separate scope. The public dashboard and the
post-bootstrap independent-producer programme are **not** deferred out of scope.
