# Text dependency review

4 October 2026. Continue F10 after D1 by examining GO-2026-5970 and the
official x/text v0.39.0 release. This is a bounded review of public upstream
source and the selected candidate's dependency graph before choosing a patch.

Download only named public module inputs through the Go proxy and checksum
service from an empty work directory. Keep project source and module names out
of online vulnerability queries. Read the upstream correction and compare it
with the authenticated release, including runtime data and transitive module
requirements. Preserve the existing candidate and all earlier evidence.

Require at least 30 GiB Linux and 60 GiB D: free before creating a small separate
qualification workspace. Any subsequent builds or existing tests must use
offline dependencies, a private network namespace, two Go workers and explicit
deadlines. No blockchain database, real key or public service is a test target.
Do not select a dependency version merely because it silences a scanner.

References: [Go advisory](https://pkg.go.dev/vuln/GO-2026-5970),
[upstream issue](https://go.dev/issue/80142),
[upstream change](https://go.dev/cl/794100),
[v0.39.0 source](https://github.com/golang/text/tree/v0.39.0).

## Qualification bounds

Compare existing `internal/jsre`, `eth/tracers/js` and `console` tests before
and after the update, with race detection, five-minute package and seven-minute
outer deadlines. Retain inherited compilation failures; do not repair unrelated
fixtures as part of this dependency check. Run the updated upstream normalization,
collation and casing tests with the same bounds. Build both selected commands
with ten-minute limits and scan their exact binaries and sources offline with
the previously pinned scanner/database. Inventory actual linked module changes.

The candidate experiment raises `go 1.18` to `go 1.25.0` as required by the new
module and resolves x/sync v0.21.0. A higher main-module language version can
affect existing source semantics and Go compatibility defaults. Successful
focused tests do not authorize selecting that directive change or prove
historical compatibility. Keep the patch separate until its broader impact has
a reviewed disposition.

After the checksum-only setup repair, run existing node, RPC, NAT and upstream
errgroup tests with race detection and the same five/seven-minute deadlines.
Exercise four fixed, ordinary Unicode operations through each real executable's
console, using two new disposable empty datadirs, no mining, no IPC, discovery
disabled, zero peers and isolated loopback. Each invocation has a 45-second
deadline. These CLI checks supplement the inherited broken console suite;
they do not replace its full coverage or test arbitrary malformed input.

## Result: experiment complete; update not selected

All four files from merged upstream fix
`5ae8e578e495731553eddba11b2d0e86c91a00ce` are byte-identical in authenticated
x/text v0.39.0, whose tag resolves to
`b326f3d3c814ab79b3c516f4ac03c2314d8df65f`. The original module comparison
records 231 changed paths, not a claim that each change has been independently
reviewed. The release's checksum and upstream correction are preserved.

The experimental `09-text-experimental.patch` changes only `go.mod` and
`go.sum`: x/text v0.12.0 to v0.39.0, required x/sync v0.3.0 to v0.21.0, and
the main module's Go directive from 1.18 to 1.25.0. Original checksum entries
are retained. No broad module upgrade or `tidy` was performed. Both copied
source trees retain every other file unchanged. The workspace manifests and
previous qualified source inventories still match D1.

Actual linked module changes are x/text and x/sync in the node, and none in
the recovery executable. The command dependency inventories locate text use
in Goja and its parser, and sync use in the UPnP client's `errgroup`.
They do not establish that changing the main module's language has no impact
elsewhere. Both binaries' recorded `DefaultGODEBUG` settings change; the
recovery binary also changes bytes despite its identical linked modules.
The [Go module reference](https://go.dev/ref/mod#go-mod-file-go),
[Go 1.22 language notes](https://go.dev/doc/go1.22#language) and
[compatibility defaults](https://go.dev/doc/godebug) explain why this needs
a separate language/defaults review and historical compatibility evidence.

| Check | Observed result |
| --- | --- |
| Existing JavaScript runtime package, race enabled | Five top-level tests pass before and after, 1.114 s / 1.115 s |
| Existing console and JS tracer suites | Identical compilation failures before/after: stale service, state and tracer APIs |
| Upstream normalization/collation/casing, race enabled | Pass, 54 top-level tests; four optional conformance/data tests explicitly skip to avoid external downloads |
| NAT/node/errgroup packages, race enabled | Pass, 1.535 s / 1.272 s / 1.017 s; optional real-router `TestUPNP_DDWRT` skipped |
| RPC package, race enabled | Fails only `TestServer` because `rpc/testdata` is absent; this reproduces on unchanged D1 in 0.020 s; other executed cases pass |
| Node and separate recovery builds | Both pass with empty build logs |
| Actual executable console | Both pass four known normalization/casing/collation assertions in disposable datadirs |
| Offline binary and source scans | GO-2026-5970 disappears from the two node scans; no new IDs; every other finding ID is retained |

Remaining symbol finding: GO-2026-6278 in both node scans and the recovery
binary scan; the recovery source scan has no symbol findings. The four scans
use the retained v1.8.0 scanner and 1 October database, with only a down loopback
interface. No complete security acceptance or full regression pass is claimed.

Initial failures are retained: missing cached sync metadata, the absent full
sync checksum, and the first baseline-RPC wrapper's malformed status capture.
The checksum continuation and correctly captured RPC reproduction have separate
logs. The console/tracer failures are not setup repairs or waived tests.
The initial Windows upstream-fetch error is also retained; the later WSL fetch
retrieved public upstream material successfully.
Regenerating the report initially tried to overwrite the preserved read-only
module license. It now checks existing license bytes instead. The source-preparation
script is named `prepare_sources.py` to avoid shadowing Python's `inspect` module
in exception reporting. The final read-only verification passes.

`review.json` is derived by `report.py`; `report.py --check` verifies it against
retained source trees, outputs and scans. SHA256SUMS covers the evidence bundle
except itself. Exact binaries and source copies remain in the small Linux
qualification workspace; no historical database was opened or copied.

Disposition: keep the selected release at P1–P17+B1+D1. Before choosing this
update, review the concrete Go-language and compatibility-default changes,
repair or explicitly replace the relevant inherited test gaps, and include
the outcome in patched-history acceptance. A separately maintained upstream
fix backport is an alternative requiring provenance and its own qualification;
none is selected here. F1 and F10 remain open. There is no D2 addendum or launch
approval, and the baseline historical replay remains at 3,600,000.
