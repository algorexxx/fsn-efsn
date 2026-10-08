# F12 affected regressions and bounded encoding cost

Declared before execution, 8 October 2026. No production selection changes.

Use fresh copies of the frozen D1 node and recovery selections. Apply exactly
the unselected patch from restart-ticket-encoder-candidate-v2-2026-10-08 to
the modern-compiler copies. Compare Go 1.21.3 with unchanged D1 to Go 1.27.1
with that patch. Check all prior manifests and inventories before execution.
No F11 patch, dependency experiment, backup access, public networking or real
wallet keys. Enforce a private network namespace with only loopback down,
offline Go modules, two build workers and existing caches. Require 30 GiB
Linux and 60 GiB D: free. Never overwrite an evidence/run directory.

## Existing regressions

Copy existing fixture and test files unchanged from investigation commit
94113b0b. Preserve their independent literal expectations and assertions.
Copy five existing helper function bodies exactly, recording source file,
line range and SHA256, into one temporary helper file to avoid pulling in
unrelated auto-buy/anchor test suites merely for their helpers. Record the
complete resulting source inventories. The advancePurchaseFixture helper
retains its existing wall-clock-relative timestamp: its two consumers are
behavioral regressions, not cross-run historical/hash vectors.

Build race-enabled binaries and run each named top-level test in a fresh
process, with a 90-second outer / 75-second Go timeout. Exact list is in
run.py. Node scope: expiry rejection, eight-block bridge import, last-ticket
replacement, missing-state reconstruction and expiry boundaries, unstored
header batch and concurrent-parent finalization, one-backup-block handover
and short-ticket rejection, and three purchase admission cases. Recovery
scope: guarded construction, refusals, insufficient replacement, and journal
handover/concurrent signing with existing public scalar-1/scalar-2 test keys.
Also run the three existing snapshot framing tests on both node selections.

Pass means every specified test and subtest passes with no skip or race.
This is affected regression coverage, not go test ./..., actual recovery
signing, a network rehearsal or historical replay. The fixtures install a
synthetic parent at backup height using preserved RPC observations; they do
not replay the path from genesis. Existing same-implementation differential
assertions remain described as such, not independent historical commitments.

## Bounded cost measurement

Non-race benchmark binaries for old-standard, modern-standard and modern-
candidate encoders. Use preserved RLP at heights 0, 15,130,080 and 12,000,000;
read inputs outside the measured loop. Each iteration creates a writer,
makes one Write and Close, and retains the output, matching the encoder
call pattern. Measure compression alone, not RLP, hashing, database or block
throughput. Validate output independently outside timing: old and candidate
must equal the existing preserved gzip bytes; modern is a representation
control and must decompress to the same payload.

Five interleaved rounds (old, modern, candidate), 100 iterations per input,
GOMAXPROCS=1, one CPU in the Go harness, benchmem enabled. Report all raw
samples and per-input median ns/op, B/op and allocs/op with candidate/old
ratios. No invented performance acceptance threshold. Shared-host timing is
descriptive; an apparent improvement is not a throughput guarantee. Do not
repeat until a preferred result appears.

## Next historical work

Prepare a separate, identity-bound candidate replay from genesis with a
small declared endpoint and cold commitment verification. Do not resume the
old baseline replay with a different executable or relax its identity check.
No historical replay is launched by this run. Independent codec/maintenance
review and F12 restored-identity refusal remain open.
