# Dashboard collector loss during mining

2026-10-03. G6's bounded collector-loss-during-mining check passes locally.
An actual efsn process continued ordinary production and funded automatic ticket
purchases while its collector was absent, then reconnected over WSS without a
node restart or operator command. The investigation also found and corrected an
obsolete queued-head report after reconnect. P17 changes two lines in efsn's
telemetry loop; consensus, mining and dashboard application code are unchanged.

## Reporter correction

The retained baseline sends current height 73 after reconnect, then height 62
from the first head event queued while disconnected. Captured collector snapshots
confirm it briefly presents 62 before the next report restores the current tip.
The baseline liveness test passed, but the subsequent evidence audit identified
this reporting defect. It is not a chain rollback: direct RPC and mined receipts
continue on the original canonical chain.

The correction handles head notifications by calling the existing
`reportBlock(conn, nil)` path, which reads the current canonical head. It neither
changes chain state nor imposes monotonic heights; a genuine reorganization still
reports the actual current tip. History requests retain their existing behavior.
The strengthened test rejects any obsolete pre-outage head after reconnect and
waits for a persisted, contiguous forty-block chart. P17 is listed separately in
the [permanent patch inventory](restart-node-patch-review.md) for release review.
The corrected wire sequence is 73, 73, 74, 74; every captured nonempty collector
snapshot also stays at or above 73. The recovered PostgreSQL chart contains all
forty heights from 35 through 74 with one transaction per block.

## Evidence

| Observation | Before loss | Collector absent | After recovery |
| --- | --- | --- | --- |
| Canonical height | 61 | 73 | 74 |
| Account nonce | 61 | 73 | 74 |
| Account tickets | 2 | 2 | 2 |
| Mining / automatic purchases | Enabled | Enabled | Enabled |
| Peers | 0 | 0 | 0 |
| HTTPS API | Current | HTTP 503 after expiry | Current |

The collector alone was terminated and its port confirmed unavailable. Nginx,
PostgreSQL, the snapshot writer and API remained alive. Twelve new blocks were
mined during 141.949 seconds of collector absence, exceeding the reporter's
ten-event input buffer. Account nonces and successful native ticket receipts
prove replenishment continued alongside production. The test audits the linked
canonical blocks and all thirteen purchases from height 62 through 74.

A new collector process on the same endpoint accepted the reporter's existing
synthetic credential. Fresh authenticated telemetry for the next mined block
reached HTTPS 12.267 seconds after restoration in the corrected run. Fifty requested
history blocks and the individual head reports together cover all twelve outage
blocks. Their hashes and transaction hashes match direct RPC. The node and writer were never
restarted or manually reconnected.

While the collector was absent, the stored snapshot remained unchanged. All four
API views returned `snapshot_unavailable` after the ten-second freshness budget.
The Linux node, collector, writer and API shared a clock; WSS and HTTPS both
validated a temporary CA normally. This avoids the cross-host timestamp ordering
problem recorded in the preceding WSS investigation.

The corrected run saved 27 snapshots, each at most 6,166 bytes. Its test-only 250 ms
reconnect interval generated 544 expected connection-loss/failure messages during
the outage, with no other error category or subsequent recovery errors. Public
retry pacing and diagnostic log volume still belong in the deployment review.

## Fixture and verification

The Go fixture gains an opt-in mining mode using public test key 1, a recent
synthetic genesis and existing miner/ticket-buyer services. It seeds sixty blocks
before mining starts, uses an in-memory chain and rejects backup input. It does
not import constructed blocks during the measured outage, hold the signer or
shorten the consensus period. This is a small synthetic availability check;
the preserved mainnet backup and real signing keys are not used.

The dashboard gains the Linux outage controller and a collector-test termination
helper. The existing stationary WSS/PostgreSQL/Edge scenario still passes all
four browser checkpoints, and all 173 contract plus 13 socket tests pass. Browser
expiry/recovery was checked in that separate stationary regression, rather than
simultaneously with live mining. The compiled frontend's 547 files remain intact.

The first live attempt reached height 74 with successful head recovery, then
failed a test assertion that expected history immediately. Source inspection
confirmed history is requested on a later latency report. The final test waits
for that normal cycle with a fixed deadline. The next attempt passed liveness
but retained the queued-head defect described above. Both source/binary versions,
all attempts and their clean shutdowns are retained alongside the corrected run.

Evidence: [mining-outage bundle](evidence/restart-dashboard-mining-outage-2026-10-03/).
It includes the dashboard commit/patch, exact runtime and source hashes, receipt
audit, failed attempt, baseline regression, corrected run and a standalone verifier. Five
scratch PostgreSQL databases are stopped, temporary certificate keys/passwords
are removed and final Linux/Windows process checks are clear. The original
`fsn-stats` checkout remains unchanged. Work stays on the existing temporary
branches; nothing is pushed or deployed.

## Next

This closes the bounded local collector-process-loss item, not all of G6.
Continue with supported runtime/dependency review, service supervision,
certificate acceptance/renewal, log lifecycle and a coordinated deployment
manifest. Public hosting and public economic use remain unapproved. See the
[consolidated plan](restart-plan.md) and [prior WSS result](restart-dashboard-wss.md).
