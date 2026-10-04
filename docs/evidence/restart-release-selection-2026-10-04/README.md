# Release source selection and compiler check

4 October 2026. This records preparation of the minimum candidate for review.
It is not release approval, a full regression pass or permission to activate.

## Declared bounds before execution

Use the existing hash-pinned upstream archive and `01-node.patch` without O1,
recovery or observer additions. Reuse the extraction verifier for the complete
821-Go-file tree and require unchanged module manifests before/after building.
The downloaded Go 1.27.1 Linux amd64 compiler must match the official HTTPS
metadata, pinned size and SHA-256 before extraction. The existing Go 1.21.3
toolchain and historical replay executable remain unchanged.

Preparation needs over 30 GiB Linux / 60 GiB D: available. Only the official
compiler metadata and archive are downloaded. Build inside a private network
namespace as the unprivileged rehearsal user, using the existing module cache,
read-only dependency resolution, a separate build cache, two workers and a
12-minute deadline. No module upgrades, source compatibility edits, node startup,
database opens or signing are part of this initial build probe. Its exact failure
will remain evidence if the current dependency graph cannot build.

Commands:

```text
wsl.exe -d FusionRehearsal -u rehearsal -- bash /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-release-selection-2026-10-04/prepare-toolchain.sh
wsl.exe -d FusionRehearsal -u root -- unshare --net -- runuser -u rehearsal -- bash /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-release-selection-2026-10-04/check-build.sh
```

Retained local build tree:
`/home/rehearsal/results/restart-release-selection-2026-10-04`.
Source references: [official download metadata](https://go.dev/dl/?mode=json),
[Go release/support policy](https://go.dev/doc/devel/release).

## Follow-up scope and results

The initial node build fails at the memsize link to `runtime.stopTheWorld`.
`05-build-compatibility.patch` removes only its two Go integrations and unused
module/checksum entries: four files, eight deleted lines. The compatibility
runner keeps the original failure and records the entire selected source tree
before and after building. It runs only version/help commands, not a node.
The build passes; the actual linked dependencies exclude memsize, recovery and
observer packages.

The repeat runner starts from another fresh upstream export and empty build
cache, with the same compiler, two-worker limit and 12-minute build deadline.
The node output is byte-identical:
`ab9c8ff071568bc21466e030a7ae3895a3c7a085559df28389248bec24c0632d`.
The first runner then stops at `go list -m all`: metadata needed for the complete
module graph is absent from the offline cache. `repeat-interruption.json` records
this stage failure. The continuation captures the same metadata error and
continues the already-declared independent checks; no successful build is rerun.

Applying the existing recovery patch without O1 succeeds. The separate recovery
binary builds within its five-minute deadline:
`655c0882b68e7cb5b97caf168c1b7a9bac8af3cb03802a0559a28b384dd88407`.
The two selected source inventories account for 1,192 files / 821 Go files in the
node tree and 1,202 / 831 with the separate recovery addition. All source files
and module manifests are checked, not just modified files.

The declared three existing test probes have 90-second test / five-minute outer
deadlines. ParseNode and ForwardCompatibility reproduce their earlier failures.
The initial ProtocolHandshake probe times out with loopback down in the isolated
namespace; that is retained as a runner error, not a runtime regression. The
separate handshake runner enables only loopback, reproduces `got 2, want 1`, then
applies the one-line test-only patch 06. The expected RLP is a list containing
reason 8 (`c1 08`), whereas a typed uint8 slice represents a byte string. With the
correct expectation the test passes with race detection in 1.022 seconds.
The transport source, 90-second test bound and handshake assertions are unchanged.

`verify-selection.py` rereads the compiler archive, both complete source trees,
three binaries, working B1/test bytes, patch/hunk references and all recorded
exits. It checks source formatting after LF normalization, preserving the
Windows files' existing line endings, and syntax-checks every shell runner.
`acceptance.json` records the passing scoped checks and original failures while
keeping full-suite, historical-compatibility, dependency-security, independent-
review and launch claims false. Final inventories separate the handshake test
overlay from the production build inputs.

The [selection report](../../restart-release-selection.md) explains what is
selected and the [findings ledger](../../restart-release-findings.md) states
remaining holds. The Go 1.21.3 replay executable and all historical data remain
outside these build directories and were not replaced or reopened by this work.
