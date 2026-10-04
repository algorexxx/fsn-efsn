# Selected candidate for release review

4 October 2026. This freezes the proposed source and build direction for the
minimal Linux restart. It is a pre-activation candidate, not a deployable release:
the real recovery anchor, historical compatibility, dependency review, final
acceptance and independent approval remain open. See the
[findings ledger](restart-release-findings.md) for explicit decisions and holds.

## Source decisions

| Component | Selection | Reason |
| --- | --- | --- |
| Upstream | `c5f0174d88ab2b9c3086c6a9cc9ccf38a072992f` | Existing pinned Fusion baseline, retaining license and module identity. |
| Node fixes | All P1–P17 in the existing `01-node.patch`, extracted from `6ecc753f00f6c6ec9ee7ad3855f2f8ff71f1f711` | Covers the agreed fixed anchor, demonstrated persistence/mining/purchase defects, DNS discovery and accurate existing telemetry. All 109 mapped hunks are selected together; shared hunks are not independent cherry-picks. |
| O1 bootstrap-list trimming | Exclude `02-optional-bootstrap-trim.patch` | Optional input convenience. Use the already-tested explicit TOML list or correctly formatted CLI list. DNS support remains in P12. |
| Recovery executable | Separate build with `03-recovery-tool.patch` after the node selection | Includes the existing signing accessor and guarded command. Do not include observer code or automatically ship a signer in the validator package. |
| Build compatibility B1 | Remove the obsolete memory-size profiler integration and its sole module/checksum entries | The unmodified candidate fails to link with the selected compiler. This is a four-file, eight-line deletion, separate from P1–P17. |
| Observer, explorer gateway and dashboard | Exclude from node patches and executable dependencies | Existing diagnostics/deployment work has separate scope and release ownership. |
| Consensus additions | No native-decode activation, ongoing finality, token confiscation or new ticket economics | Preserve the agreed restart scope. The native-decode finding still needs a release disposition; excluding a fix is not accepting its risk. |

The [selection manifest](evidence/restart-release-selection-2026-10-04/selection.json)
pins patch hashes, source inventories and every selected review ID. Use the
[existing hunk map](evidence/restart-release-extraction-2026-10-04/hunk-map.json)
with it. The investigation branch also contains excluded code, so building its
HEAD does not reproduce this selected source.

B1 removes `debug.Memsize.Add`, the exported memsize handler, its `/memsize/`
registration and import, and the unused dependency from `go.mod`/`go.sum`.
Ordinary Go CPU/heap profiling and metrics remain. Nothing in transaction
execution, ticket accounting, header validation or fork choice is changed by B1.
Its [standalone patch](evidence/restart-release-selection-2026-10-04/05-build-compatibility.patch)
applies after patch 01; it must accompany the selected compiler.

## Build direction and observations

Select **Go 1.27.1, Linux amd64 v1, CGO enabled** for candidate qualification.
The compiler archive is verified against its official SHA-256 and size before
use. On 4 October the [official download metadata](https://go.dev/dl/?mode=json)
lists it as stable. Go's [support policy](https://go.dev/doc/devel/release)
covers a major release until two newer major releases exist; Go 1.21.3 remains
an investigation/replay toolchain, not the release compiler.

Build inputs: `GOTOOLCHAIN=local`, `GOFLAGS=-mod=readonly`, `GOAMD64=v1`,
`CGO_ENABLED=1`, `go build -p=2 -trimpath -buildvcs=false`. Candidate probes use
the retained module cache with networking disabled. The evidence records the
compiler archive, module manifests, actual linked modules, GCC/libc package
versions, shared libraries, source inventories, environment and output hashes.
The installed Ubuntu/GCC environment is a measured build input; pinning the
clean CI/production image is still required.

The first exact P1–P17 build failed at link time:

```text
link: github.com/fjl/memsize: invalid reference to runtime.stopTheWorld
```

With B1, the node builds and its version/help commands run. A second build from
a fresh upstream export and empty build cache produces identical node bytes.
This establishes repeatability on this host with these recorded inputs; it does
not establish cross-host reproducibility or final release acceptance. The
binary still reports inherited version `5.0.3-stable`; a distinct release version
and approved compiled mainnet anchor must be set before publication.

The second runner stopped after the successful binary comparison because
`go list -m all` requested metadata missing from the offline cache. That failure
is retained. A separate continuation records it and resumes the independent
recovery build/test probes. Linked-module build information is available; a
complete dependency/security review is still outstanding. No automatic module
upgrades or linker safety bypass was used.

The separate recovery executable also builds with Go 1.27.1 without O1. The
parser and discovery-vector failures reproduce. The disconnect fixture is
corrected separately as test-only patch 06; it passes with race detection after
reproducing the original size mismatch. The initial loopback-down timeout remains
in the evidence. These results do not represent a full regression-suite pass.

Detailed logs and exact hashes are in the
[selection evidence](evidence/restart-release-selection-2026-10-04).

## Remaining release boundary

1. Complete G1 history acceptance and patched historical compatibility. Current
   baseline replay remains a separate unchanged executable.
2. Close the blocking entries in the findings ledger, including dependency
   review and the native-call decision. Repair stale tests or explicitly map
   excluded checks to reviewed replacement coverage.
3. Pin CI/build-image inputs, set the distinct version and approved mainnet
   anchor, then run the affected finite R1–R10 acceptance against those exact
   artifacts. Existing local results are not final-source passes.
4. Fill the real network/host/download values in the operator kit and perform
   its clean-machine rehearsal. Complete independent review before real signing
   and public activation.

Changes to this selection need a stated reason and affected acceptance rows.
The separate recovery build, fixed anchor and test-only overlays must remain
visible in the reviewer packet.
