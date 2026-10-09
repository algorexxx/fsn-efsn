# Candidate continuation from 1,600,000 through 1,800,000

Declared before execution, 9 October 2026, investigation commit 0ae38f11.
Continue the exact encoder-candidate replay already qualified through 1,600,000.
No runtime patch, compiler setting, source configuration, replay executable or
accepted-history decision changes. Production selection remains frozen.

Preserve /home/rehearsal/replay/candidate-ticket-encoding-1600000. Hold its run
lock and mount it read-only in a private mount/network namespace alongside the
backup. Verify all 802 checkpoint file hashes against the previous cold-check
inventory and run the retained exact-height cold helper at 1,600,000. Copy this
closed checkpoint to a new candidate-ticket-encoding-1800000 directory, verify
all copied bytes and leave the identity manifest unchanged. Refuse existing
targets/results. No baseline database is opened or copied.

Copy the exact retained replay-tests executable; require SHA256
b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245.
Its existing validated-resume path must accept the unchanged executable,
source history and configurations, start at 1,600,000 and stop at 1,800,000.
Reuse the sealed first-range runner's recorded command execution, environment, monitor,
replay and preservation helpers without editing that sealed evidence. Record
the imported runner hash. Its initial-range label does not change the boundary.

Build a separate observer using Go 1.27.1 and an overlay changing only the
prior details_test.go's literal endpoint from 1600000 to 1800000. Retain the
one-line diff, overlay and full build inputs. The original replay binary and
its source remain unchanged. The observer's replay test is never invoked.
Capture the preserved source endpoint before replay. After clean shutdown,
run the original cold-head test and the separate observer's cold-details test
in fresh processes on the read-only target mount. Compare full endpoint
header/commitments/TD to the source reference and ticket count to the replay
observation; do not invent an expected ticket count.

Use the same bounds: at least 30 GiB Linux and 60 GiB D: before work;
per-batch reserves of 20/50 GiB; sampled 4 GiB target stop; three bounded
size-measurement attempts; clean stop requested at 30 minutes; one-hour outer
timeout. GOMAXPROCS=2, no public peers, offline Go modules. A stopped, short or
failed run is incomplete. No automatic extension or retry with changed inputs.

Verify backup metadata and both baseline metadata inventories before/after;
hash the preserved candidate checkpoint before/after; hash all stopped-target
files before/after cold inspection. Verify selected source, prior candidate
source, copied source, replay binaries, observer and overlay remain unchanged.
Retain commands, errors, identities, hashes, timestamps and manifests. No
large source-backup copy, real keys, signing, mining or W: storage is needed.

The range remains below legacy checkpoint end 2,680,000. Actual transaction
execution and state/receipt comparisons run, while documented ticket-seal and
raw-transaction shortcuts remain. Passing this range does not close F12 or
qualify the remainder of history, F11 or independent consensus review.

This range remains 200,000 blocks. The preceding same-sized command took
18 minutes 46 seconds. Retain the same 30-minute allowance and other stop
thresholds; earlier duration does not guarantee this range's runtime.
