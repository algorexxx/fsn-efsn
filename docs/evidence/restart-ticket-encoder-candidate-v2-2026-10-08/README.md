# Encoder-only compatibility candidate

8 October 2026. **The bounded candidate checks pass; the patch remains
unselected.** All 27 preparation/build/probe/CLI commands exited zero between
07:03:28 and 07:04:51 UTC. The [specification](spec.md),
[candidate patch](candidate.patch), [source provenance](preparation.json),
[command record](qualification/run.json), and [verified results](verification.json)
are retained for review. This is a patch against P1–P17+B1+D1, not investigation
HEAD and not the separate F11 rollback candidate.

## Actual patch boundary

One existing runtime file changes: core/state/statedb.go imports ticketgzip and
delegates its existing RLP payload to Encode. The new 30-line wrapper fixes the
default gzip header and CRC32/length trailer and calls the frozen DEFLATE writer
once followed by Close. Existing compression-error text is retained. RLP,
ordering, expiry, cache consumers, genesis constants and fork configuration are
unchanged. Normal ticket updates and AddCachedTickets share this call site.

Five writer files are byte-identical to the pinned Go 1.21.3 source (62,796
bytes). shared.go extracts its maxNumLit and InternalError definitions; the
upstream BSD license and a provenance/maintenance note accompany them. In total
the patch covers eight Go files, one license and one note. No old decoder,
GOROOT overlay or dependency change is included. The installed modern gzip
reader still handles ticket decoding. Both isolated node and recovery trees
build with Go 1.27.1.

## Results and limits

| Check | Old compiler comparator | Unchanged modern control | Modern candidate |
| --- | --- | --- | --- |
| Seven preserved ticket blobs, exact bytes and cache commitment acceptance | 7/7 | 0/7 | 7/7 |
| Fifty-five synthetic payloads, exact legacy bytes | 55/55 | 0/55 | 55/55 |
| Full in-memory historical genesis header | Exact | Different | Exact |
| Six independent expiry/survivor expectations | Pass | Pass | Pass |
| Actual node initial/restarted genesis | Prior evidence | Prior evidence differs | Exact historical header |

Historical inputs are the seven available blobs in the preceding 24-height
sample; the other 17 are still unavailable. Each hash starts with an empty
ticket cache, so AllTickets reads the saved blob through the real decoder.
UpdateTickets at timestamp zero preserves all those tickets. Candidate bytes,
commitments and full observations equal the old-mode results. Synthetic
ticket-account roots match between those modes; they are not historical block
roots because the rest of account state is absent.

The 55 payloads cover empty/small inputs and compressor window/block boundaries
with zeros, repetition and a SHA-256 counter stream. Each is encoded twice
sequentially and four times concurrently. All three helper builds use race
detection, with no reported races. Python independently checks decompression,
the fixed gzip header, CRC32 and uncompressed length. These are deterministic
fixtures, not a fuzz campaign or a resource-limit benchmark.

All six expiry cases preserve the independently specified ticket owners, order
and fields. At timestamps 200 and 201 no ticket survives: the existing error is
returned, the original in-memory ticket list remains, and no compressed blob
is written. Successful candidate expiry bytes and complete observations match
the old comparator. This does not add a new expiry rule.

Actual candidate efsn starts and restarts a disposable empty datadir with
historical genesis 0xc2422b1d9d16331be2a5b207c0783027d4419498003f729f4b9e9c5c1838623a,
head zero, mining/purchase disabled and network ID 32659. Two stopped read-only
inspections confirm the complete header and configuration and leave database
file hashes unchanged. fsn-recovery builds and its help command succeeds;
recovery execution and signing are not exercised here.

**The empty-datadir safeguard is still missing.** Correct genesis construction
does not turn an empty directory into the required verified restored history.
The candidate still starts without a restore marker. This part of F12 remains
open independently of encoding compatibility.

## Preservation and corrections

The network namespace has only loopback DOWN, with module downloads disabled.
No backup was opened; historical bytes came from the already retained evidence.
Original node/recovery source inventories remain exactly pinned, and only the
declared files differ in disposable candidate copies. Installed toolchains are
unchanged. Disk reserves remain above the required floors. Verification checks
463 files in preceding manifests, copied writer/license provenance, complete
source inventories, helper/runtime identities and all result comparisons.
Generated logs retain their original spacing; only those logs and raw patch
files are exempted from Git whitespace checks. Binary payload fixtures retain
their exact bytes.

The [first attempt](../restart-ticket-encoder-candidate-2026-10-08/README.md)
stopped at patch checking because additions lacked Git's new-file metadata.
Its inputs and failure remain unchanged. The
[attempt correction](attempt-correction.patch) only repairs metadata, chooses a
fresh result path and adds the earlier manifest; all ten candidate input files
are identical between attempts.

The first result verifier also applied the independent legacy empty-stream
literal to the modern negative control. Modern Go emits an empty fixed-Huffman
block (03 00), while the old encoder/candidate use an empty final stored block
(01 00 00 ff ff). Both decode to empty bytes. The
[failed verifier](verify-attempt-1.py), [failure record](verification-run.json),
[one-line scope correction](verifier-correction.patch), and
[successful verification](verification-v2-run.json) retain this distinction.
The literal expected legacy bytes, candidate checks and all experiment outputs
are unchanged; no experiment was rerun to accommodate the control difference.

Remaining work: affected integration regressions and bounded encoding-cost
measurement, candidate historical replay, independent consensus/maintenance
review, and the restore-identity startup safeguard. No full-project test pass,
full-history proof, final release selection or activation approval is claimed.
