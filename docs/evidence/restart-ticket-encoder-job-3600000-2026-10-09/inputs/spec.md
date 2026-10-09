# In-place candidate replay: 2,700,000 to 3,600,000

Declared 9 October 2026 under the user's authorization to continue useful
testing without repeated prompts. This 900,000-block interval extends verified
candidate history toward the retained baseline's 3,600,000 milestone.
The baseline is a comparator, not a substitute for candidate execution.

The preceding job passed replay, both cold checks, its evidence verifier and
all manifests. Reuse its closed working database only after the prior completion
and verification succeed, start height matches and every cold-file hash matches.
The writable working target and checkpoint path are intentionally the same.
Keep the separate 2,400,000 recovery checkpoint read-only and unchanged.
This run qualifies in-place continuation on real data; no such pass is claimed
before completion. If interrupted, the working target is partial and requires
a separate cold inspection and disposition, never a blind retry.

The replay executable remains SHA256
b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245.
Candidate and selected source inventories, toolchain and history identities
remain fixed. Only the separate observer endpoint changes. The controller
delta is recorded in controller-change.patch. It adds remaining-growth capacity
accounting and rejects a prior job that did not pass evidence verification.

Config.json declares a six-hour replay clean-stop budget, 6h15m Go timeout and
6h30m outer timeout plus 20-second kill grace. Preparation and cold checks add
time. The sampled target threshold remains 8 GiB with 30-second sampling and
three bounded measurement attempts. Actual allocation can overshoot between
samples; this is a stop threshold, not a hard storage quota. All 128-block
batches retain the original 20 GiB Linux / 50 GiB D: free-space checks.

The 2,700,000 closed target occupies 4,004,995,072 bytes. It is already allocated.
Before launch measure it again and require Linux free bytes greater than
20 GiB reserve + remaining growth to the 8 GiB target threshold + 1 GiB margin.
D: must exceed both 60 GiB and 50 GiB reserve + remaining growth + 1 GiB margin.
Thus Linux needs about 25.27 GiB for this resume, not the copy-mode minimum
30 GiB. Fresh capacity is recorded in preflight.json and checked again at launch.
No deletion, new full database copy or W: workload is needed. Future capacity
limits must be reviewed from actual growth, never bypassed to force progress.

The original backup, recovery checkpoint and baseline metadata remain preserved.
The prior working checkpoint bytes are intentionally advanced; its sealed
inventory records the starting evidence. Execution uses rehearsal inside a
private mount/network namespace with read-only backup/checkpoint/recovery views.
The checkpoint view aliases the mutable working target, so it is read only
before execution and must not be claimed byte-preserved afterward.
No peers, real keys, mining, public services or release selection are involved.

The controller records progress and errors, performs both cold endpoint checks,
checks full header/state/tickets/receipts/TD against the pre-replay reference,
runs evidence verification and writes completion plus full manifests.
Do not modify this bundle after launch. A missing completion file is pending;
verified_pass must be true for success. Prior sealed inputs/results are unchanged.

The job is finite and does not launch another job itself. The separate hourly
chat follow-up reviews the result, value and resources before continuing.
Ask the user when a substantive decision, unresolved blocker or unnecessary
work is identified. Keep Windows awake and the app running for scheduled
follow-up. The hidden dispatcher holds WSL open; shutdown/reboot interrupts it.
Host logs are under repo tmp/replay-job-3600000-2026-10-09 and runtime status is
/home/rehearsal/results/restart-ticket-encoder-job-3600000-2026-10-09/status.json.
An operator can request normal cleanup by exclusively creating its STOP file.
Preserve the stop marker and failed result.
