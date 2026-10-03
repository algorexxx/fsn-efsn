# Dashboard validation and chart retention

3 October 2026. The dashboard now keeps compact chart records while preserving
full current-head API reports. G6 remains open, but its long-lived chart data no
longer grows with transaction lists in every retained block variant.

## Small production change

Only four dashboard source files change: `lib/telemetry-report.js` validates the
known block/stats/pending shape; new `lib/chart-block.js` projects fixed scalar
chart fields; `lib/history.js` stores that projection and reads counts; and
`lib/collection.js` preserves head timing metadata and rejects whole invalid
history batches before clearing the request. The existing fifty-block cap also
applies at collection. No production efsn or consensus code changes.

Block hashes, roots, producer, gas, timestamp, difficulties, transaction hash
objects and uncle header fields are checked before acceptance. Gas price and
hashrate must also be valid before a stats report refreshes its receipt.
Unknown report kinds are rejected. Nullable ticket counts still distinguish
unknown from zero. This validates report format, not a node's honesty or the
chain's consensus rules.

The supported dashboard numeric profile uses nonnegative safe integer counters,
timestamps safe in milliseconds, safe numeric difficulties or canonical decimal
text up to 78 digits, and efsn-shaped hexadecimal uncle fields (64 digits for
big integers, 16 for uint64 quantities). These are explicit dashboard limits
for compatibility review, not new chain limits. Source inspection found that
DaTong's `VerifyUncles` returns nil; this change therefore does not assume that
nonempty uncle reports can never occur.

The chart cache retains transaction/uncle counts and only scalar identity/chart
fields. Original report mutation cannot change a cached fork. It preserves the
existing representative choice, propagation comparisons and 2,000-height window.
The current node snapshot and `/blocks` API retain transaction hashes, uncle
headers and timing metadata. Unknown extensions remain only in current-head
reports under the configured message limit. Registration metadata/ping validation
and its budgets remain part of public deployment review.

## Verification and measured scope

The [evidence bundle](evidence/restart-dashboard-retention-2026-10-03/README.md)
contains the exact dashboard patch, source/build identities, failed and passing
attempts, measurements, RPC comparisons, screenshots and cleanup checks.

- Eight new regressions fail on the prior production sources; all **159 contract
  tests** and **12 loopback socket tests** pass on the candidate.
- All **six PostgreSQL pipeline scenarios** pass, including separate writer/reader
  roles, unchanged historical sentinel data, identity preservation and recovery.
- The actual synthetic efsn fixture executes/imports **60 blocks and 600
  transactions**. The latest block plus 50 historical reports match direct RPC.
  Both `/nodes` and `/blocks` keep the head's ten transaction hashes, and all
  forty chart transaction counts are ten.
- The existing compiled frontend passes four Edge checkpoints: normal, pinned,
  snapshot-writer expiry and recovery. The build is unchanged from the preceding
  eight-DOM-test/strict-build evidence and its source/build hashes are checked.

The first wire rerun failed because the shared test fixture changed the history
test's intended zero ticket counts; restoring that fixture resolved it. The
first actual-node attempt failed its freshness assertion before recording the
receipt values. The fixture now waits for all three report kinds and saves
initial API payloads and timestamps; the next run passes unchanged freshness
limits. The first failure's exact cause remains unproven. This is functional
acceptance, not a soak or timing-stability result.

The offline cache experiment uses eight identities over 2,000 heights, retaining
nine variants per height: **18,000 fork records**. Reports are synthetic objects,
not signed blocks, and no network is involved.

| Transactions per block | Full cache JSON bytes | Heap growth after GC | Fill time |
| ---: | ---: | ---: | ---: |
| 1 | 14,195,884 | 14,043,736 bytes | 0.47 s |
| 714 | 14,235,884 | 13,855,080 bytes | 1.03 s |

The 40,000-byte serialized difference comes from longer count values, not retained
hash lists. The generator reuses transaction arrays; the cache retains none.
Advancing beyond the window leaves only the new height and reduces sampled heap
to about 6.3 MB. RSS and garbage-collector behavior differ from serialized size;
these samples do not establish peak memory or production capacity. The preceding
1.01 GB estimate concerned full block variants, not a measured old-process heap.

Current-head and fifty-block wire payloads are unchanged. The actual history
reply remains **66,076 bytes** under the fixture's 128 KiB input budget. Neither
that budget nor the proposed 4 MiB larger-report profile is a deployment default.

Only disposable local services and public synthetic key 1 were used. P2P dialing,
listening, discovery and the mining worker remained disabled; no real backup or
funds were accessed. Test services are stopped and temporary database passwords
removed. The original dashboard checkout, dependency locks and efsn sources are
preserved. All three attempts' stopped scratch database directories remain for
evidence recovery.

## Next

Measure a bounded larger-report/multiple-node collector profile and align input,
pending-output, snapshot, identity-count and proxy budgets. Compact chart storage
does not shrink a busy head or history reply on the wire. Complete metadata/ping
field review with that profile. Collector loss during mining, runtime/dependency
review, supervision, enrollment and proxy/TLS/public deployment remain G6 work.
