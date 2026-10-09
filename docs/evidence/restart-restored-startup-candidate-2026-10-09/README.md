# Restored startup candidate — first run, 9 October 2026

**Incomplete: fifteen refusal cases pass; the positive fixture fails at shutdown.**
Keep this run and its failure. It is not a passing service acceptance result.

The unselected patch in [qualification/candidate.patch](qualification/candidate.patch)
adds a read-only preflight before `eth.New` opens writable chain data. It runs
when the expected network has a configured restart anchor, reuses existing
anchor validation and requires restored full-sync state. It adds no anchor value,
CLI flag, signing rule, fork-choice change or release selection. The candidate
is layered on the retained encoder-corrected node source, not F11.

The fifteen actual CLI refusals cover absent/empty chain data, wrong genesis,
chain ID and fork schedule, missing DaTong configuration, missing header/body/
state, ticket-commitment mismatch, genesis-only full head, incorrect anchor,
invalid anchor identity, missing canonical head and fast sync. Each exits 1 with
its expected reason. All chain-database file names and hashes stay unchanged;
the absent chain directory stays absent. Node construction can still create
its ordinary instance lock/keystore directories before this service preflight.
This does not claim that refusal performs no filesystem writes anywhere.

The valid synthetic snapshot passes preflight, starts and prints the expected
head with mining and auto-buy disabled. Shutdown then exits 2 with a nil-block
panic in `core.(*BlockChain).Stop`, at its `HEAD-1`/`HEAD-127` pruning flush.
The reused fixture has a late parent and state but no contiguous preceding
history. The default pruning configuration therefore does not match its storage
setup. The bloom indexer also reports the absent early history. These are real
limitations of this fixture, not proof of a complete supported restore path.

The next run must use a fresh positive fixture with explicit archive mode,
matching its original `TrieDirtyDisabled` setup. Reuse the exact binaries and
candidate source; retain all fifteen passing refusals without rerunning them.
Exercise normal import via the running service's local `admin.importChain`
console API and a fresh-process restart. The planned standalone `import`
subcommand was never reached here; source inspection finds that it opens another
chain after `makeFullNode`, so it is not used as the service import test.
No conclusion about that subcommand's runtime behavior is claimed.

The CLI's [test-only profile](profile.go) registers the synthetic genesis and
anchor for each fresh process. It is separate from the runtime patch and must
never ship. The seeder uses existing public test key 1, independently imports
the generated child in memory and retains exact expected parent/child hashes.
Those blocks and numbers are synthetic evidence, not additional historical replay.

All commands are bounded: five-minute builds, 60-second Go seed tests with
90-second external limits, and 45-second CLI processes; ten-second kill grace.
The run uses one Go worker at niceness 10, offline module settings and a private
network namespace with only loopback down. No original backup or live replay
database is opened. [run.json](qualification/run.json) preserves source/toolchain/
binary identities, commands, exit codes, capacity records and the failure.
The [verification](verification.json) checks the fifteen negative observations
and explicitly retains `verified_pass: false` for the overall run.
