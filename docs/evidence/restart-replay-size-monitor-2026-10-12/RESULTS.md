# Live allocation measurement qualification

All 32 controller tests pass with a completed bounded v2 wrapper, private
networking and loopback DOWN. The new metadata-only scanner exactly matches
GNU du on the closed verified working checkpoint: 35,399,045,120 bytes before
and after, under exclusive run/shared database locks. No database content was
read or hashed by this comparison.

The failure evidence shows three consecutive du traversal errors on .ldb files
that disappeared, consistent with concurrent compaction. The live scan now
opens a directory descriptor without following symlinks and sums st_blocks,
deduplicating hard links. It records and tolerates only FileNotFoundError for
recognized numbered LevelDB table/log/temp or manifest names. Unknown missing
entries, permission/I/O errors, symlinks, nested directories, changed roots,
malformed output and timeouts remain failures. Tests cover disappearing tables,
closed agreement including sparse/hard-linked files, refusal cases, bounded
worker retries and restoration of the old closed-measurement function.

Each live measurement keeps its 15-second timeout, two-second kill grace and
three-attempt stop policy. The 30-second sampling interval, 39 GiB job ceiling,
Linux20/D50 GiB reserves and replay time limits are unchanged. This remains a
non-atomic sampled measurement: new allocations between enumeration and stat
can be missed temporarily, just as with du. It is not a hard storage quota.
Closed post-replay allocation still uses the existing du helper, and final
verification checks raw scanner records and the final closed du measurement.
Only test tooling changed; node/replay executable and release selection did not.

Earlier qualification preparation is retained. Linux git diff stalled near the
outer deadline; unit logs eventually show 32 passing tests, but no completed
wrapper record was produced. The initial claim that tests never ran was corrected
in preparation-followup.json. The fresh v2 wrapper uses host-captured, hash-bound
source/patch provenance and completes normally. A first closed-comparison attempt
refused the root-owned lock's append access; v2 locks an existing read-only
descriptor exclusively. Neither failed attempt changed blockchain data.
