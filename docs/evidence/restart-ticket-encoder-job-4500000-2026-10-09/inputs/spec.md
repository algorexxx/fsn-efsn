# Candidate replay: 3,600,000 to 4,500,000

Prepared 9 October 2026 under the authorization for useful autonomous testing.
The preceding 900,000-block range is complete, with both cold checks and evidence
verification. Continue candidate history beyond the retained baseline endpoint;
another baseline pass has no current diagnostic justification.

This job has not launched. Fresh capacity must pass before dispatch. The unchanged
controller requires Linux free space above 20 GiB reserve plus remaining target
growth plus 1 GiB margin; D: must exceed both 60 GiB and 50 GiB reserve plus
remaining growth plus 1 GiB. Per-batch 20/50 GiB free-space stops stay intact.

Reuse the verified working database in place and retain the separate verified
2,400,000 recovery checkpoint. Require preceding completion/verification, exact
start height, every cold working-file hash and unchanged replay identity before
writing. No full database copy, local deletion or compaction is authorized by
this specification. Preserve the original backup, baseline checkpoints, failed
attempts and all sealed evidence.

The 3,600,000 target occupies 7,580,307,456 bytes. The preceding 900,000-block job
grew it by about 3.33 GiB and took 182.972 minutes. Declare an 11 GiB sampled
target ceiling, leaving about 3.94 GiB growth allowance. This is a bounded
experiment, not an estimate guaranteeing the next interval fits. Keep a six-hour
clean-stop limit, 6h15m Go timeout, 6h30m outer timeout and 20-second kill grace.
Sample size every 30 seconds with the existing three bounded attempts. A sampled
threshold can overshoot; preserve and inspect any stop instead of blindly retrying.

Controller code is byte-identical to the tested preceding job. Reuse its fourteen
passing controller tests; only configuration and the separate observer's endpoint
literal change. The retained replay executable remains
b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245.
No startup candidate, F11 patch, source selection or compiler change enters replay.

Run offline in the existing private mount/network isolation, with the backup and
recovery checkpoint read-only. After execution, require fresh-process cold head
and detailed state/ticket/receipt/TD checks, complete preservation checks and
automatic evidence verification before claiming success. Keep the job finite.
The separate chat follow-up reviews value/capacity before any later interval.
No public networking, production activation, real keys or mining is authorized.
