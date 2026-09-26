# Complete-state single-producer outage evidence

Baseline: `fb4039ba08891bf44d389b0f560b01f5d6eadb06`. The new test uses the
existing isolated Linux node and packet-loss helpers. No production source,
dependency, network rule or consensus policy is changed.

`prepare-copies.py` verifies all 230 preserved-state artifact files against the
original manifest, requires a 50-GiB free-space reserve plus the two copies, and
refuses an existing target. It writes only fresh workspace directories under
`tmp/full-state-outage-2026-09-26`. `copy-capacity.json` records actual bytes.
The source is the verified compact complete-state export, not the full historical
node backup. D: and W: are not used for these copies.

Run `check-linux.sh build`, then `check-linux.sh run`, through the existing WSL
`FusionRehearsal` environment. The build uses the cached Go 1.21.3 toolchain,
offline dependencies, two workers and race instrumentation. The run requires
root only inside a fresh loopback-only network namespace for `tc` packet loss.
The source-level namespace guard refuses the initial host network namespace.
No public peer is contacted and no real signing key is used.

Each copy receives the existing audited public-key substitutions and executes
the three retained Windows recovery blocks. The live phase has one donation-key
producer and one non-producing backup-key verifier. It drops loopback IP traffic
for 90 seconds, kills the sole producer after observing a persisted pending
purchase, waits 20 seconds, then reopens it with its saved endpoint and automatic
buyer configuration. The normal miner-start action begins recovery; there is no
manual raw submission, external transfer or forced downloader synchronization.

Acceptance requires the same saved transaction bytes at the same canonical nonce
in an empty pool before mining resumes, automatic execution of that intent and
two new successor purchases, normal peer catch-up, and both cold databases'
matching blocks, receipts, tickets and complete account differences. The existing
independent full-state ledger checks the entire recovery suffix. Process logs,
exit status and block artifacts are retained on completion.

This tests an accidental crash and network outage in the selected launch topology.
It does not simulate competing producers, a reorganization, missing nonce repair,
power loss, full historical replay or public-network discovery. Its short saved
history retains the complete account/storage state but is not a general full-sync
distribution artifact.
