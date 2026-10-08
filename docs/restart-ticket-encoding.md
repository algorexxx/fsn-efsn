# Historical ticket encoding compatibility

8 October 2026. F12 remains a release hold. This narrows the next technical
work under G1/G2; it does not change the agreed restart or ticket economics.

Fusion hashes compressed ticket bytes in both the ticket account's code and
the header MixDigest. Its current encoder uses the compiler's default gzip
writer. [Genesis/startup evidence](evidence/restart-genesis-startup-v2-2026-10-08/README.md)
establishes the differing genesis cause. The subsequent
[historical comparison](evidence/restart-ticket-compression-2026-10-08/README.md)
finds the same representation mismatch in all seven available samples spanning
genesis through backup height 15,130,080.

Go 1.21.3 reproduces those bytes. Go 1.27.1 with a temporary overlay of the old
flate code also reproduces them, including the complete historical genesis
header and actual ticket-cache hash checks. Unchanged Go 1.27.1 does neither.
The test isolates a viable algorithm-preservation direction without requiring
the entire node to remain on an old compiler. It does not prove all-history
compatibility or qualify a production implementation.

## Proposed implementation boundary

Prepare an isolated candidate that freezes only the writer used for ticket
commitments, with exact source provenance and the upstream license. Keep
decompression on the maintained standard library. Route calcTicketsStorageData
through that encoder so normal updates and AddCachedTickets use the same bytes.
Preserve existing RLP, ordering, expiry logic, error handling and one-Write/Close
behavior. Specify the default gzip envelope explicitly rather than relying on
future standard-library encoder defaults.

The conservative writer boundary in the inspected Go 1.21.3 source is five
files: deflate.go, deflatefast.go, huffman_bit_writer.go, huffman_code.go and
token.go, plus required shared definitions and a small gzip envelope. Those
five files contain 62,796 bytes / 2,198 lines before any packaging adjustments.
This is a small Fusion integration change with a meaningful amount of copied
upstream encoder code. Keep algorithm code mechanically traceable; do not
hand-simplify it merely to reduce line count. Confirm the precise dependency
boundary by building the candidate. Preserve copyright and license notices.

Do not distribute the diagnostic GOROOT overlay or silently replace the general
gzip implementation. Changing compression level, copying modern output hashes
into genesis, or recomputing stored commitments does not meet the historical
byte-preservation requirement. Returning to Go 1.21.3 remains only the existing
replay comparator, not an accepted production solution.

## Finite qualification work

1. Build the encoder-only candidate on the selected modern toolchain. Compare
   it against all seven retained historical byte vectors and the full genesis
   header, with the existing encoder kept as a negative control. Preserve the
   candidate patch and its exact source/license provenance separately from the
   frozen production selection.
2. Specify a bounded matrix for the wrapper and ticket use: deterministic
   output, empty/small inputs, compressor window/block boundaries and ticket
   expiry transitions. For derived cases use the old encoder as a differential
   comparator and independently check the intended surviving ticket set. Label
   derived vectors as synthetic; they are not accepted historical roots.
3. Exercise the real state update/cache and genesis/startup paths, then the
   affected node/recovery builds and selected regressions. Measure the affected
   encoding cost without extending into unrelated performance work.
4. Resume bounded candidate-history qualification with the reviewed encoding
   candidate and compare cold state/ticket/receipt commitments to preserved
   history. Missing sampled blobs and seven passing byte vectors cannot replace
   this requirement. Keep baseline replay and candidate replay results distinct.
5. Obtain independent codec/consensus and maintenance review before selection.
   If a historical mismatch is found, stop and resolve its cause; do not add an
   activation boundary by assumption. A byte-compatible implementation should
   preserve existing rules, not create a new encoding fork.

No production correction or activation height is selected. F11's distinct
rollback disposition and F12's empty/mispointed-datadir startup safeguard remain
open in the [launch plan](restart-plan.md) and [findings ledger](restart-release-findings.md).
