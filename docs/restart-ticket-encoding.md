# Historical ticket encoding compatibility

9 October 2026. F12 remains a release hold. This narrows the next technical
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

## Unselected implementation candidate

The [isolated candidate](evidence/restart-ticket-encoder-candidate-v2-2026-10-08/README.md)
now freezes only the writer used for ticket commitments, with exact source
provenance and the upstream license. It keeps decompression on the maintained
standard library and routes calcTicketsStorageData through the encoder, covering
normal updates and AddCachedTickets. RLP, ordering, expiry logic, compression
error text and one-Write/Close behavior are preserved. The default gzip envelope
is explicit. It changes one existing runtime file and adds the isolated codec.

The conservative writer boundary in the inspected Go 1.21.3 source is five
files: deflate.go, deflatefast.go, huffman_bit_writer.go, huffman_code.go and
token.go, plus required shared definitions and a small gzip envelope. Those
five files contain 62,796 bytes / 2,198 lines and are copied unchanged.
This is a small Fusion integration change with a meaningful amount of copied
upstream encoder code. Keep algorithm code mechanically traceable; do not
hand-simplify it merely to reduce line count. Successful node and recovery builds
confirm this dependency boundary. Copyright and
license notices are preserved. No old decoder or GOROOT overlay is included.

Do not distribute the diagnostic GOROOT overlay or silently replace the general
gzip implementation. Changing compression level, copying modern output hashes
into genesis, or recomputing stored commitments does not meet the historical
byte-preservation requirement. Returning to Go 1.21.3 remains only the existing
replay comparator, not an accepted production solution.

## Finite qualification work

1. **Bounded candidate comparison complete.** The modern candidate reproduces
   all seven historical ticket byte vectors and the complete genesis header.
   The unchanged modern encoder remains a failing compatibility control. The
   candidate patch and source/license provenance are separate from the frozen
   production selection.
2. **Bounded encoding/expiry matrix complete.** All 55 synthetic payloads match
   the old encoder, including repeated/concurrent calls with race detection.
   Six expiry cases meet independently constructed survivor-RLP expectations.
   These derived cases remain synthetic, not accepted historical roots.
3. **Bounded integration and cost checks complete.** Real decoder/update/cache
   paths, initial/restarted genesis and builds pass. The [affected regressions](evidence/restart-ticket-encoder-regressions-2026-10-08/README.md)
   add 20 top-level tests and 32 subtests per selection, with race detection,
   including synthetic guarded recovery and journal handover. Three preserved
   RLP inputs show no encoding-cost increase against the legacy comparator in
   five bounded rounds. This does not qualify the production CLI recovery
   workflow or the full suite.
4. **Candidate history is cold-verified through 2,356,032.** The [attempt toward
   2,400,000](evidence/restart-ticket-encoder-replay-2400000-2026-10-09/README.md)
   hit its unchanged 30-minute allowance and remains incomplete. A separate
   [cold inspection](evidence/restart-ticket-encoder-stopped-2356032-2026-10-09/README.md)
   matches preserved header, state/ticket/receipt commitments and TD at the
   stopped height. Legacy checkpoint shortcuts still apply. Free capacity is
   35.98 GiB Linux / 66.97 GiB D: after the earlier verified W: archival.
   Next is only the [remaining 43,968 blocks to 2,400,000](restart-ticket-encoder-replay.md),
   using a verified copy, unchanged executable and unchanged stop limits.
   Further history remains open; these results do not replace all-history
   qualification or recover the 17 missing exported samples. Keep baseline,
   completed-range and stopped-inspection results distinct.
5. Obtain independent codec/consensus and maintenance review before selection.
   If a historical mismatch is found, stop and resolve its cause; do not add an
   activation boundary by assumption. A byte-compatible implementation should
   preserve existing rules, not create a new encoding fork.

No production correction or activation height is selected. F11's distinct
rollback disposition and F12's empty/mispointed-datadir startup safeguard remain
open in the [launch plan](restart-plan.md) and [findings ledger](restart-release-findings.md).
