# Candidate replay job to 2,700,000

This finite background job starts from the cold-verified 2,400,000 checkpoint.
Its [specification](inputs/spec.md) and [configuration](inputs/config.json)
declare the scope and limits before launch. The endpoint crosses the existing
2,680,000 legacy-checkpoint boundary. The replay executable and candidate
selection remain unchanged; this is not approval to launch the chain.

Read completion.json for the eventual outcome. A missing completion file or
live progress is **pending**, not a pass. On a successful process exit the runner
performs both cold checks, captures qualification evidence and runs the evidence
verifier automatically. A true verified_pass is required. Final manifests are
written automatically; this bundle must remain unchanged after launch.

The start status and current assurance are tracked in the
[replay plan](../../restart-ticket-encoder-replay.md).
The preserved recovery database is
/home/rehearsal/replay/candidate-ticket-encoding-2400000-v2;
the working database is /home/rehearsal/replay/candidate-ticket-encoding-working.
Further ranges and in-place resume require a reviewed successful result.
