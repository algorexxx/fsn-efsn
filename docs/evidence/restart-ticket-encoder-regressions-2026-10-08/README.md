# F12 encoder: affected regressions and cost

8 October 2026. **Passed within this scope; candidate remains unselected.**
The run completed from 15:41:22 to 15:43:05 UTC. All 62 recorded commands
exited zero, with no stderr, failed/skipped tests or reported races. The
[specification](spec.md) and [runner](run.py) preceded execution; the
[verification](verification.json) checks the retained outputs and provenance.

## Integration result

Each selection passed **20 top-level tests and 32 subtests**: unchanged D1
with Go 1.21.3, and D1 plus the exact previously retained encoder patch with
Go 1.27.1. Both validator and recovery source selections were copied and
checked independently. Recovery code was not added to the validator selection.
All four regression binaries used race detection; benchmarks did not.

Coverage includes eight-block bridge import, expired-ticket refusal, required
replacement of the final ticket, missing-state ticket reconstruction, expiry
boundaries, unstored header batches, finalization during concurrent import,
the one-backup-block handover, purchase admission, guarded recovery construction
and refusal, journal handover with concurrent signing, and snapshot framing.

The bridge, single-backup-block handover, recovery builder and recovery journal
also produced identical deterministic logged observations across compilers.
These include the successor state roots and recovered block hashes. The
fixtures use public scalar-1/scalar-2 test keys and synthetic state populated
from the existing preserved RPC observations. They are not real wallet actions
or accepted historical blocks. Assertions comparing two production paths in
one fixture remain differential checks, not independent consensus oracles.

Nine node fixture/test files, two additional recovery test files, the snapshot
test and the existing RPC observations were copied unchanged from investigation
commit 94113b0b. Five existing helper bodies were extracted unchanged with
source hashes and line ranges recorded. This avoids copying unrelated test
suites solely for their helpers. The existing advancePurchaseFixture helper
uses wall-clock-relative time; its header-batch/concurrent-finalization tests
passed behaviorally and are excluded from the cross-run hash comparison.

## Compression cost

Five interleaved rounds per encoder, 100 encodes per input per round, one
Go CPU, Intel i9-12900K under WSL. These medians measure writer creation,
one Write and Close only. Input reading, correctness checks, RLP encoding,
hashing and database work are outside the measured loop.

| Preserved ticket RLP | Bytes | Old standard, microseconds/op | Candidate, microseconds/op | Modern standard control, microseconds/op |
| --- | ---: | ---: | ---: | ---: |
| Genesis | 252 | 100.35 | 80.77 | 91.84 |
| Backup head 15,130,080 | 23,776 | 427.44 | 409.04 | 368.38 |
| Height 12,000,000 | 243,666 | 3,929.44 | 3,773.18 | 2,443.24 |

Candidate allocation medians were 814,528 / 879,088 / 1,337,840 B/op and
20 / 26 / 29 allocations respectively: **176 fewer bytes and one fewer
allocation per call** than the old compiler's standard writer. B/op is total
allocated memory per operation, not retained memory or peak process usage.

The candidate's measured time was 0.80 / 0.96 / 0.96 times the legacy
comparator. This bounded shared-host measurement found no cost increase
against that comparator; it is not a performance guarantee. The modern
standard encoder is faster on the two larger inputs, but its different output
does not satisfy historical commitment compatibility. All benchmark runs
checked decompression before timing; old and candidate also required exact
equality to the previously preserved gzip files. No performance threshold
was invented and no rounds were repeated to improve the result.

## Provenance and limits

The private network namespace had only loopback down; Go downloads were
disabled. No backup database, existing replay database, live peer or real key
was opened. Initial and final selected-source inventories match; candidate
inventories contain only the prior patch and recorded test/benchmark additions.
All **815 files** covered by prior manifests were rechecked. Full command
arguments, timestamps, compiler identities, input/source/binary SHA256 hashes,
helper extraction provenance and raw stdout/stderr are retained in
[qualification/run.json](qualification/run.json). Final space was 43.83 GiB
Linux and 91.60 GiB D:. No large database copy was made.

This completes the declared affected-regression and bounded-cost step. It does
not pass go test ./..., qualify the production CLI recovery workflow, settle
F11, or close F12. Next is the [separate candidate replay](../../restart-ticket-encoder-replay.md)
from genesis through 100,000, followed by further bounded historical work and
independent codec/consensus/maintenance review. The restored-identity startup
safeguard is still missing. Production source selection and activation remain
unchanged.
