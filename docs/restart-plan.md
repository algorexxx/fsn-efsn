# Fusion restart launch plan

Updated 3 October 2026. Working branch: `codex/restart-investigation-wip`.
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
| G1 History and preservation | Complete structural/current-state checks; baseline replay to 3,000,000; complete local package/restore | Accepted history and trust record before final construction |
| G2 Client and supported operation | P1–P16 candidates; anchor, crash, discovery and purchase regressions | Reviewed release candidate |
| G3 Recovery and custody | Complete-state test-key bridge, separate imports, signing journal and command interruption checks | Approved real artifacts before public activation |
| G4 Monitoring and response | Read-only collector, durable history, ticket timelines, live reorg and budget checks | Usable operator coverage before public use |
| G5 Release infrastructure and data | Network profile, DNS recovery and local restore/service checks | Real download/restore/connect path before public use |
| G6 Public dashboard | [Source baseline and local contracts](restart-dashboard-readiness.md): two pass, five fail; remediation required | Working public dashboard before public-use announcement |
| G7 Independent producers | Funded test-key entrant already buys and mines with donation node | Tested entry kit before release; actual independent entry after recovery |
| G8 Review, final rehearsal and activation | Extensive retained evidence; final release not selected | Explicit go/no-go and recorded launch |

## G1 — History and preservation

- [ ] Confirm immutable preservation and a separate verified recoverable copy;
  record provenance, hashes, storage health and restore ownership. Resolve the
  earlier ESXi storage-controller concern before making it a launch dependency.
- [ ] Continue bounded baseline replay from 3,000,000 through the accepted
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
space/path checks. Full execution beyond 3,000,000 is not currently running.

## G2 — Client and supported operation

- [ ] Select every production hunk against upstream from the
  [P1–P16 inventory](restart-node-patch-review.md); separate node changes,
  recovery tooling, observer, packaging and inherited explorer settings.
- [ ] Freeze a bounded final regression matrix for supported Linux deployment:
  anchor/startup/import/rewind, ordinary purchase/mining/restart, compatible
  reorganization, interrupted writes, discovery and returning incompatible
  history. Measure long post-anchor startup and larger reorganization batches
  against declared resource limits; link earlier passing cases instead of
  repeating unchanged tests indefinitely.
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

## G4 — Monitoring and response

- [ ] Measure a declared longer block/receipt backlog and ticket timeline,
  including a bounded competing branch. Select collection cadence, budget and
  retention that preserve anchor baselines, unresolved incidents, review identity
  and displaced evidence; verify reopening and continuity across retention.
- [ ] Capture and preserve both production wallet baselines before activity.
  Historical state is sparse; later RPC acquisition cannot be assumed possible.
- [ ] Implement and demonstrate alert delivery, acknowledgement and collector-
  loss detection, including collection failure when history rejects an append.
  Choose destinations, response timings and operator coverage before deployment.
- [ ] Rehearse the finite detection/response cases in the
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

Target repository: `C:/Users/Peter/Documents/CODING/fusionfoundation/fsn-stats`.
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

The [readiness baseline](restart-dashboard-readiness.md) now records five failing
collector contracts (secret configuration, session ownership and redaction) and
unchanged source. Full dependency/build/browser integration is still unverified.
This gate is separate from G4's operational alerts. A visible node list alone
does not close either gate.

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
| Monitor limits, delivery and coverage | Measured bounded observer; no deployed alert route | G4 |
| Public dashboard and hosting | Included; fsn-stats requires readiness work | G6 before public use |
| Independent participation | Kit ready before release, real operators join after recovery | G7 |
| Domains/organization/hosts/toolchain | Final choices unselected | G2/G5 |
| Accepted residual risks | Written, case-specific review; no implicit waivers | G8 |

Current technical order:

1. G6: correct the five locally reproduced collector contract failures, define
   per-identity enrollment and validate all update/reconnect paths. Then establish
   the real dependency build and isolated storage/API/browser integration before
   deployment. See the [dashboard baseline](restart-dashboard-readiness.md).
2. G4: bounded longer-ancestry/backlog measurement, then retention and actual
   notification delivery. Keep each experiment tied to its gate's pass condition.
3. G1: resume bounded historical execution only after fresh capacity/path checks;
   coordinate this larger disk job with the small local work above.
4. G2/G5/G7: select the supported release matrix, complete the public package and
   clean-machine entrant rehearsal, then finish G3/G8 with actual operator choices.

Deliberately outside this launch: disputed-wallet confiscation/burns, new voting
economics, ongoing finality, automatic nonce-gap funding/repair and survival
after the sole remaining participant leaves. Broader platform/sync support and
unbounded stress testing need separate scope. The public dashboard and the
post-bootstrap independent-producer programme are **not** deferred out of scope.
