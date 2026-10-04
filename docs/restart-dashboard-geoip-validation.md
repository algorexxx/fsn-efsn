# Dashboard GeoIP dataset validator and IPv6 compatibility finding

Local evidence date: 2026-10-04. A read-only dataset validator is implemented in
the isolated dashboard candidate. It checks the five binary files before any
future activation step. Fifty-nine new tests pass, along with all 178 existing
backend contracts and all 14 socket tests. No collector behavior, frontend,
dependency version, efsn source or chain rule changes.

The full data review also finds an unresolved reader compatibility problem:
`geoip-lite` 2.0.3 compares only the upper 64 bits of IPv6 addresses. The bundled
dataset contains ranges that this reader cannot distinguish correctly. The
validator rejects that dataset; this is a failed data acceptance result, not a
waived check. It is not wired into collector startup in this slice.

## Read-only validation command

From the dashboard checkout, under the tested Linux Node 24 runtime:

```sh
node deploy/validate-geoip.cjs /absolute/path/to/staged-data 134217728
```

Both arguments are required. The second is a maximum aggregate byte size for
the five files. The example is the explicit 128 MiB ceiling used for the local
bundled-data check, not a selected production budget. No download, file write,
symlink switch, service restart or network lookup occurs.

Success writes JSON containing the resolved directory and each file's byte
count, record count and SHA-256. Failure writes a diagnostic to stderr, leaves
stdout empty and exits nonzero. A generated output hash identifies inspected
bytes; it is **not** an independently trusted provider checksum, proof of
freshness, geographic accuracy or licensing approval.

The validator requires an absolute dataset directory and a positive safe integer
byte budget. It opens all five files read-only, rejects symlinks/nonregular files,
empty files and partial records, and scans bounded record chunks. It validates:

- Ordered, disjoint address ranges and readable location references.
- IPv6 bounds that the pinned reader can represent: whole /64 units, without
  overlaps in that reader's upper-64-bit comparison.
- Country code encoding, location UTF-8 fields, EU/metro metadata, coordinate
  bounds and nonnegative accuracy radii.
- Stable directory selection, file identities, sizes and change timestamps
  across the scan. Files are closed on either success or failure.

The record sizes remain 88 bytes for names, 10/34 for Country IPv4/IPv6 and
24/48 for City IPv4/IPv6. Empty location countries and the defined `0xffffffff`
no-location reference remain structurally legal. Structural validity does not
establish correct missing-location display behavior; the earlier Country-only
fallback/map issue and sentinel presentation remain part of lookup acceptance.

This is a conservative compatibility gate for the current reader. It rejects
narrow IPv6 ranges even where neighboring records happen to return identical
geography; it does not merge, round, drop or reinterpret provider ranges. Do not
weaken the gate or discard those records to obtain a passing dataset.

The filesystem checks detect ordinary concurrent changes; they are not a lock
against another writer, nor a guarantee about later bytes. Run after conversion
has stopped in private staging, then retain immutable data for activation. Source
archive verification and a supervised fresh-process lookup remain separate steps.

## IPv6 evidence

An independent Python scan reads every record in the installed dataset:
115,343,066 bytes and 4,239,118 total records. The sampled field/reference checks
from the earlier dependency review are extended to a full scan here. Location
encoding, references and coordinate bounds pass. IPv4 ranges are ordered and
disjoint. IPv6 does not satisfy the same assumptions:

| Installed file | Records | Adjacent full-address overlap/out-of-order pairs | Adjacent pairs overlapping under the reader's upper-64-bit comparison |
| --- | ---: | ---: | ---: |
| `geoip-country6.dat` | 95,027 | 751 | 11,480 |
| `geoip-city6.dat` | 393,146 | 3,557 | 95,168 |

These are adjacent-pair counts from the independent scan, not counts of affected
IPs or all possible intersections. Some neighbors have identical outputs; others
do not. The captured examples and counts avoid inferring today's geographic
truth from the old packaged data.

A separate tiny synthetic dataset encodes two distinct records in the same
`2001:db8::/64`: `2001:db8::1` has country `NO`, and `2001:db8::2` has country
`SE`. Both ranges are single addresses and have independent location records.
The actual dashboard node model returns `NO` for both. These invented records
prove loss of distinction relative to the supplied bytes, without contacting
either address or relying on a claim about real-world IP ownership.

The new validator rejects this fixture and the installed bundled dataset. The
bundled rejection occurs at Country IPv6 record 0 because its bounds require
more precision than the reader uses. A complete synthetic fixture with supported
IPv6 bounds passes, with all five output hashes matching the independently
encoded expected bytes. All inspected datasets retain their original hashes.

## Tests and one existing fixture correction

`npm test` includes the new validator tests. Its 237 tests pass: 178 existing
contracts plus 59 new cases covering byte budgets, required files, alignment,
file types, record fields/references, IPv6 precision, range ordering across chunk
boundaries, changes during validation, hashes and CLI results. The final validator
test file also passes independently after a test-title-only correction.

The first socket run passes 13 of 14 tests. The existing output-buffer test
returned early: it waited for a count of socket writes as though each write were
a whole WebSocket reply. The observed queue was 4,925 bytes while the assertion
expected 8,077. The fixture exposes low-level writes, and a frame can use separate
header/payload writes. The premature wait is fixed to wait for the expected
queued bytes, returning early on destruction so the existing assertions can
report it. The initial payload thresholds exceed the respective frame headers.
All exact queue, buffer-limit, disconnect, isolation and reconnect assertions
remain unchanged. The subsequent complete socket run passes all 14 tests.
No collector or WebSocket implementation is modified to make this test pass.

Module/CLI syntax checks pass. These changes do not alter the frontend or the
live collector paths, so native mining, full WSS/database/browser, frontend build
and dependency audit runs were not repeated. Their earlier results are retained,
not presented as new tests. The installed package/lock files and compiled assets,
all 1007 efsn source/module files and the original dashboard checkout are preserved.

## Next decision and remaining work

The subsequent [reader comparison](restart-dashboard-geoip-reader.md) selects
standard MMDB with `mmdb-lib` 3.0.3 for implementation. It passes 3,007 independently
expected raw lookups and isolated node/snapshot mapping checks. The precision
patch also works on a tiny fixture but leaves the bundled-data ordering and
custom-converter maintenance unresolved. Implement the bounded MMDB loader and
preserve country-only flags before accepting a production dataset; the dashboard
still uses the original reader at this evidence point. Retire this five-file
validator from the active deployment path when the format replacement lands.

Then complete the protected MMDB download job, independent archive
integrity checks, source metadata, immutable activation/rollback, service
supervision and refresh/deletion policy from the [operations design](restart-dashboard-geoip-operations.md).
No provider account or live download was used, and no scheduler or public
deployment was created. The validator closes one implementation item, not G6.

The [restart plan](restart-plan.md) owns release decisions. Exact fixtures, scans,
successful checks, the initial socket-test failure and the portable dashboard
patch are in `docs/evidence/restart-dashboard-geoip-validation-2026-10-04/`.
