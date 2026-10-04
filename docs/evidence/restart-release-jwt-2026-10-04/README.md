# Narrow JWT v4 qualification

4 October 2026. Continue F10 with only the JWT dependency update needed for
GO-2024-3250 and GO-2025-3553. Base inputs are the frozen P1–P17+B1 node and
separate recovery sources from `restart-release-selection-2026-10-04`.
No blockchain data or real keys are opened by this qualification.

## Declared scope and bounds

Download the explicitly named public `github.com/golang-jwt/jwt/v4@v4.5.2`
module using the official Go proxy/checksum service, from an empty work
directory with no project module. Record its authenticated module sums and
upstream source inventory, review all changed runtime files against v4.4.2,
and check that its own dependency manifest adds no transitive modules.

Copy only the two retained small selected source trees into a new results
directory after matching complete inventories and checking at least 30 GiB
Linux / 60 GiB D: free. Preserve the selected source trees and original scan
results. Reproduce the existing local HTTP/WS JWT test before the update.
Apply a separate two-file module patch to the new copies; qualify the affected
node package with race detection. Tests run in a private network namespace with
only loopback up, at most two Go workers and a five-minute test/seven-minute
outer deadline. No public endpoint load or fault injection is part of this work.

Build both commands using the selected Go 1.27.1 compiler and recorded existing
CGO build inputs; each build has a ten-minute deadline. Check executable version
and help, compare linked-module inventories, and perform offline binary/source
scans with the already pinned govulncheck v1.8.0 and complete local database.
Each scan has a ten-minute deadline, downloads disabled and no enabled network
interface. JSON exit zero alone is not acceptance. Require both JWT advisory
IDs to be absent; keep all other findings visible.

Do not update unrelated modules, select a new consensus rule, rewrite original
evidence or infer full release approval. Independent review, other F10 findings,
final artifact/host acceptance and historical compatibility remain separate.

Primary references: [v4.5.2 release](https://github.com/golang-jwt/jwt/releases/tag/v4.5.2),
[allocation advisory](https://github.com/golang-jwt/jwt/security/advisories/GHSA-mh63-6h87-95cp)
and [error-handling advisory](https://github.com/golang-jwt/jwt/security/advisories/GHSA-29wx-vh33-7x7r).

## Qualified D1 change

`08-jwt-dependency.patch` changes exactly one version in `go.mod` and its two
existing checksum lines in `go.sum`: v4.4.2 to v4.5.2. The module is pinned to
upstream commit `2f0e9add62078527821828c76865661aa7718a84`. Its authenticated
module sum is `h1:YtQM7lnr8iZ+j5q71MGKkNw9Mn7AjHM68uc9g5fXeUI=`; its own
`go.mod` is byte-for-byte unchanged and has no required modules. No efsn Go file
or other selected module version changed.

Review of changed upstream files found these runtime differences: signature
failure returns before claim validation; token splitting has a fixed three-part
allocation instead of unbounded segment allocation; strict base64 decoding is
optional and defaults off; an unused request helper is added; an issuer check
is simplified without changing its boolean result. The upstream JWT command
change is comment formatting. Fusion's production import is in
`node/jwt_handler.go`; it still restricts HS256, rejects all errors and performs
its existing time checks. No block execution or ticket rule changes are selected.
`upstream-inventories.json` and `upstream-changed-files.json` pin this review.

The initial offline baseline failed before compiling because testify v1.7.2
was not cached. After its exact download, a second attempt identified missing
go-difflib v1.0.0 and yaml.v3 v3.0.1. Those existing versions were downloaded
through the same official proxy/checksum service from the empty download
directory. All three already occur in the project manifests; none was upgraded.
Both failed setup logs and prior runner versions are retained. The successful
runner revalidated unchanged source copies before applying D1.

## Results and limits

| Check | Result |
| --- | --- |
| Existing JWT HTTP/WS baseline, v4.4.2, race enabled | Pass, 1.063 s |
| Complete `node` package after D1, race enabled | Pass, 1.257 s; no skips |
| Upstream `TestSplitToken`, `TestParser_Parse`, `TestSetPadding`, race enabled | Pass, 1.034 s; no skips |
| Selected node and separate recovery builds | Both pass; logs empty |
| Node version/help and recovery help | Pass; inherited version remains 5.0.3-stable |
| Linked module comparison | Node changes JWT only; recovery changes none |
| Offline binary and source scans | Both JWT IDs absent; all other finding IDs retained, no new IDs |

The upstream regex also named nonexistent `TestParser_ParseWithClaims`; that
alternative matched nothing and is not counted as another pass. Actual
`TestParser_Parse` explicitly calls `ParseWithClaims` for its claim types.
The first evidence-verifier attempt rejected the mistaken fourth-test count;
verification now requires the three tests that actually exist and passed.

The node package run includes the existing valid and invalid authentication
cases over real local HTTP/WS connections, plus RPC startup and lifecycle tests.
The upstream split test includes extra delimiters and malformed shapes. These
are bounded existing fixtures, not an allocation benchmark, public service test
or proof of every possible authentication input. No new regression tests were
needed and no tests were weakened.

Node SHA-256:
`ecfb0c6333b2ae2963f021ce77acfbf74fcdd38dbdc135b6ec5794cccf164017`.
Recovery SHA-256:
`655c0882b68e7cb5b97caf168c1b7a9bac8af3cb03802a0559a28b384dd88407`;
this is identical to the pre-D1 executable. The earlier same-host clean-cache
repeatability test predates D1 and is not a new reproducibility claim for D1.

Node scans retain GO-2026-5970 and GO-2026-6278 symbol findings. Recovery retains
the WebSocket binary symbol finding, with no source call finding. Lower-level
module/package findings are unchanged. Scanner/database inputs are the retained
v1.8.0 scanner and 1 October 2026 database snapshot from the preceding audit.
The complete database is local; neither scan mode has networking enabled.

`selection-addendum.json` selects D1 as an explicit addition to the frozen
candidate for independent review, preserving the original selection manifest.
`acceptance.json` records actual test names, binary hashes, linked-module delta
and finding IDs. `verify.py --check` validates it against the retained source
copies and original streams without rewriting it. `SHA256SUMS` covers the whole
bundle except itself. The fixed workload scripts preserve their completed
destinations; new reproduction needs new paths and the same declared bounds.

F10 remains open for the other dependency findings and independent review.
This qualifies a narrow dependency change; it does not approve final CI,
production endpoint configuration, history acceptance or a public launch.
