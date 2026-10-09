# Candidate in-place replay to 3,600,000

This job advances the verified 2,700,000 working database to 3,600,000 while
preserving the separate 2,400,000 recovery checkpoint. The
[specification](inputs/spec.md) and [configuration](inputs/config.json)
declare the finite interval and resource limits before launch.

Read completion.json for the outcome; a missing record is pending, not success.
Replay must be followed by both cold checks and successful evidence verification.
The launcher seals complete input/output/bundle manifests. Do not edit this
bundle after launch. The [canonical plan](../../restart-ticket-encoder-replay.md)
records current verified assurance and subsequent work.

No release selection, consensus rule or replay executable changes.
