# Snapshot framing correction

27 September 2026, baseline `96ff3b4`. Local parser tests confirm the length-check
concern recorded in the [observer investigation](restart-observer-mining.md).
The candidate correction adds three lines to `snapshot.SetBytes` in
[snapshot.go](../consensus/datong/snapshot.go), rejecting inputs shorter than
the four-byte ticket count plus one checksum byte. It is recorded separately
as **P16** in the [node patch inventory](restart-node-patch-review.md).

## Finding and behavior

The inherited decoder rejected empty input, then checked its checksum before
reading four count bytes. Nonempty, truncated input could reach a slice operation
without having all four bytes. Eight in-memory cases failed before correction:
payload lengths 1–4, each with either exact capacity or spare backing capacity.
Each produced a recovered slice-bounds panic in the test. The valid-encoding
and existing error controls passed on that same source.

The correction rejects these inputs with the existing `data length error`
message. The original empty-input error remains unchanged. Inputs of at least
five bytes follow the original implementation exactly, including checksum,
record framing, count conversion and record interpretation. This neither changes
valid snapshot bytes nor adds stricter record-type/order rules. It does not
change ticket price, expiry, returns, rewards, fork weight or recovery ancestry.

The validation below supports including this small parser correction. It does
not establish every input is safe, a remotely reachable exploit, or a complete
security audit. Any node correction still requires independent review before
release.

## Validation scope

The user reported a Codex notice saying content could not be shown and Daybreak
was unavailable for Astra. The exact classifier reason and account eligibility
were not available. No shell action in this investigation had received an
automatic approval rejection.

In response, this investigation was narrowed to local in-memory parser tests,
the bounds-check patch, and the existing valid-header/import compatibility
suite. An unexecuted draft for signed malformed-header and child-process testing
was removed before any build or run. No crafted signed header, malicious peer
traffic, public endpoint, real key or full chain backup was used for this finding.
This is a substantive testing-scope limit, not a renamed or retried blocked action.

OpenAI's [published guidance](https://learn.chatgpt.com/docs/cyber-safety) describes
authorized defensive work and notes that legitimate activity can trigger a
safeguard; suspected Codex false positives can be reported through `/feedback`.
Its [defensive workflow guidance](https://developers.openai.com/blog/scaling-cyber-defenders-with-daybreak)
includes focused patches and regression verification. These sources do not
guarantee acceptance of any particular request or grant access to an approved
cybersecurity offering. Retain the actual scope and authorization when seeking
support; do not disable safeguards or disguise the work to bypass a restriction.

Source inspection finds decoder use in seal validation, historical ticket
reconstruction, and snapshot RPC/tool readers. Header checks call the decoder
through seal validation after signature checks. This call-path inspection is
not a dynamic end-to-end network test. Network delivery, process-level effects,
and conditions under which a peer can reach those paths remain unverified.
The local guard covers the decoder shared by those callers without adding a
consensus exception.

## Evidence and remaining work

See the [evidence directory](evidence/restart-snapshot-framing-2026-09-27/) for
before/after source, logs, runner scripts and verified source identities.
Windows parser tests pass after correction. Windows header/import compatibility
tests could not start because several modules were absent from its offline cache;
the retained setup failure is not a test pass or a demonstrated runtime defect.
Linux parser and existing header/import tests pass with race detection, including
the eight-case cold-header matrix and valid full import/cold reopen. The bounded
parser fuzz run also passes: 5,151 executions with a requested ten-second budget
(13.03 seconds including runner overhead). Only the stated cases and execution
budget are covered.

Next review P16 and continue the external native ticket timeline with explicit
anchor inventory, native outcomes, report deletion and reorganization-aware
derivation. Keep network-level impact unverified unless it is separately tested
within an appropriately authorized and supported workflow. The restart's other
release gates remain in the [main plan](restart-plan.md).
