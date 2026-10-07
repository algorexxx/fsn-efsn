# Selected efsn dependency review

4 October 2026. F10 remains a **release hold**. The first audit of the exact
[P1–P17+B1 selection](restart-release-selection.md) is complete; remediation and
independent acceptance are not. No runtime source, module version or consensus
rule changed during this audit. The two discovery fixture repairs are separate
test-only work recorded in the same [evidence bundle](evidence/restart-release-followup-2026-10-04).

Subsequent qualification on the same date selects **D1: JWT v4.5.2**, documented
below. It removes both JWT findings from new offline scans; the other findings
and independent acceptance remain open. The original audit counts and hashes
below remain the pre-D1 record.

## Inputs and limits

Official `govulncheck v1.8.0`, built with the selected Go 1.27.1 compiler, scanned
both retained executables and their selected command sources. The node SHA-256
is `ab9c8ff071568bc21466e030a7ae3895a3c7a085559df28389248bec24c0632d`;
the separate recovery executable is
`655c0882b68e7cb5b97caf168c1b7a9bac8af3cb03802a0559a28b384dd88407`.
Source inventories, compiler/scanner inputs and unchanged module manifests are
retained. The investigation branch HEAD contains excluded code and was not the
scan target.

The complete public database was downloaded from the official fixed bulk URL;
its last-modified time is **1 October 2026, 20:24:15 UTC**. Both scan modes then
ran against the local `file://` database in a private network namespace with
loopback down, module downloads disabled and ten-minute per-command limits.
No binary-derived module names or project source were sent to the database.
The evidence records the earlier online-scan approval rejection and this safer
offline alternative. See the official [database protocol](https://go.dev/doc/security/vuln/database).

[Scanner documentation](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck)
distinguishes symbol presence in binaries from conservative call analysis in
source. JSON-mode exit zero means analysis completed, not that it found nothing.
Returned advisory records also include unaffected versions; their count is not
a count of affected vulnerabilities. Source analysis can overestimate interface
calls and miss reflection/unsafe paths. It does not audit Fusion's own logic,
native OS libraries, deployment exposure or previously unknown vulnerabilities.

| Target / mode | Unique IDs with symbol findings | Package-only IDs | Module-only IDs |
| --- | ---: | ---: | ---: |
| Node binary | 4 | 0 | 40 |
| Node command source | 4 | 0 | 41 |
| Recovery binary | 1 | 0 | 23 |
| Recovery command source | 0 | 1 | 24 |

Each ID is counted once at its highest reported level. Source and binary module
sets differ, so their totals need not match. Every lower-level finding remains
in the derived [scan summary](evidence/restart-release-followup-2026-10-04/scan-summary.json)
and original streams; absence of a reported call is not blanket acceptance.

## Four node findings requiring disposition

| Advisory / installed module | Actual use and initial disposition | Required next check |
| --- | --- | --- |
| [GO-2024-3250](https://pkg.go.dev/vuln/GO-2024-3250), JWT v4.4.2 | `node/jwt_handler.go` calls `ParseWithClaims`, but rejects every non-nil error before allowing the next handler. The advisory's selective error-acceptance pattern is absent in this inspected handler. This is a code-review observation, not a demonstrated authentication bypass. | Keep the finding visible; qualify the JWT update needed for the next row and rerun token rejection/expiry tests. |
| [GO-2025-3553](https://pkg.go.dev/vuln/GO-2025-3553), JWT v4.4.2 | Parsing can allocate excessively before authentication completes. The JWT wrapper is installed on the authenticated HTTP/WS stack when configured; returning an error afterwards does not avoid parsing cost. Actual launch exposure must be checked. | Qualify the upstream v4 fix, at least v4.5.2, with `node.TestJWT` and local HTTP/WS acceptance. No public endpoint stress test is needed. |
| [GO-2026-5970](https://pkg.go.dev/vuln/GO-2026-5970), x/text v0.12.0 | Reported normalization functions can loop on invalid UTF-8. Goja uses text collation; Fusion includes Goja in its console and JavaScript tracing facilities. The scan is not proof that ordinary block execution can supply a triggering input. | Qualify x/text v0.39.0 or a separately reviewed fix, checking the resulting module graph and console/tracer behavior. Establish applicable input restrictions or remediation before acceptance. |
| [GO-2026-6278](https://pkg.go.dev/vuln/GO-2026-6278), gorilla/websocket v1.5.0 | **UNREVIEWED database entry.** Node WebSocket client use includes `ethstats` and RPC dialing. The reported client mask generator uses `math/rand`; this concerns frame masking, not blockchain signing. Source review found a discrepancy in the listed fixed version. | Resolve the advisory/version discrepancy below before selecting a pin. Retain RPC and dashboard connection/write/recovery checks for any change. |

The JWT maintainer's [error-handling advisory](https://github.com/golang-jwt/jwt/security/advisories/GHSA-29wx-vh33-7x7r)
describes callers accepting a subset of combined errors. Our handler uses
`case err != nil` first. The separate
[allocation advisory](https://github.com/golang-jwt/jwt/security/advisories/GHSA-mh63-6h87-95cp)
lists v4.5.2 as patched. This supports a narrow v4 update investigation, not a
major-version migration or an assumption that every v4 behavior is unchanged.

The Go team's [normalization issue](https://go.dev/issue/80142) confirms the
invalid-UTF-8 loop. The recorded source traces include conservative interface
edges; do not present them as proven remote request paths or consensus defects.
Direct integration points are `internal/jsre/jsre.go` and
`eth/tracers/js/goja.go`. No hostile-input workload was run in this audit.

The WebSocket database entry lists **v1.5.3** as fixed, but the official
[v1.5.3 source](https://github.com/gorilla/websocket/blob/v1.5.3/conn.go#L172-L175)
still calls `rand.Uint32()` in `newMaskKey`. Its referenced upstream
[fix commit](https://github.com/gorilla/websocket/commit/d67f41855da42d7bccd9ef050c49f7e54e783b95)
changes that generator to `crypto/rand`. The advisory originates from a fork;
the Go database labels it unreviewed. Therefore v1.5.3 is **not established as a
code-level fix**, even if upgrading to it would silence this database entry.
An upstream release/commit containing the actual correction must be verified.

The recovery binary reports `httpProxyDialer.Dial` symbol presence for that
WebSocket advisory, while source analysis reports the package without a call
finding. Preserve both results: this does not demonstrate that the offline
recovery workflow opens a WebSocket or that the tool is universally unaffected.

## Bounded remediation sequence

1. Verify the upstream fixed versions/commits and the effect of each proposed
   module update. Start with JWT v4; keep each justified dependency change
   separate from the frozen production patch selection. Do not perform a broad
   `go get -u` or treat scanner suppression as a fix.
2. For each selected update, record the exact `go.mod`/`go.sum` delta, inspect
   transitive changes, build both commands and run affected existing unit/race
   and command-level acceptance. Any consensus-relevant transitive change needs
   explicit historical-compatibility coverage. Retain original failures.
3. Re-scan exact rebuilt artifacts against a pinned database; review remaining
   module/package findings and analysis limitations. Refresh the database near
   final release, since this snapshot cannot cover later disclosures.
4. Record independent dispositions in F10, pin the CI/build image and finish
   affected R1/R7/R8/R10 acceptance. A passing scan alone does not clear F10 or
   approve a public launch.

## D1 — JWT remediation qualified

The [D1 evidence and selection addendum](evidence/restart-release-jwt-2026-10-04)
pin v4.5.2 and a separate two-file patch. Only the JWT version and its two
checksum lines change. Its own module manifest is unchanged and adds no
dependencies; every other linked module is unchanged. The update incorporates
the upstream signature-error handling and bounded token-splitting fixes.
No efsn Go file or consensus rule changed.

The existing v4.4.2 HTTP/WS authentication test passes with race detection in
1.063 s once its missing, already-pinned test libraries are cached. With D1,
the full `node` package passes with race detection in 1.257 s and no skips.
Three upstream parser/splitting/padding tests pass in 1.034 s. Both commands
build and CLI probes pass. The node binary is
`ecfb0c6333b2ae2963f021ce77acfbf74fcdd38dbdc135b6ec5794cccf164017`;
the recovery executable remains byte-for-byte identical to the pre-D1 build.

All four offline scans completed. Both JWT advisory IDs are absent; no new
finding IDs appear, and every other finding ID remains. Node symbol findings
are now GO-2026-5970 and GO-2026-6278. Recovery results are unchanged. The
original failed cache-setup attempts and actual test selectors are preserved;
this is not a full-project test pass or new clean-cache reproducibility result.

The two JWT entries are technically remediated by D1, pending independent
review. Next: qualify the text-normalization fix, resolve the WebSocket
fixed-version discrepancy, and finish lower-level findings/CI acceptance.
The existing F10 release hold remains in force.

## Text correction experiment — not selected

The [bounded text experiment](evidence/restart-release-text-2026-10-04)
verified that authenticated x/text v0.39.0 includes all four files of the
upstream correction. Both experimental commands build, the JS runtime and
upstream text tests pass with their recorded skips, and actual console Unicode
checks pass before and after. GO-2026-5970 disappears from both node scans;
no new finding IDs appear. The WebSocket finding and lower-level review remain.

This is broader than D1: it requires x/sync v0.21.0 and raises the main
module's `go` directive from 1.18 to 1.25.0. Only text/sync change in the node's
linked-module list, but both commands change compatibility defaults. The
recovery binary changes even though its linked modules do not. A newer language
directive can also alter existing loop-variable behavior. Do not equate a
two-file manifest patch with unchanged execution semantics.

Existing console/JS-tracer suites fail to compile identically before and after;
RPC `TestServer` fails because its testdata directory is absent, also reproduced
on D1. Node/NAT/errgroup checks pass; optional upstream text and real-router
tests are explicitly skipped. These gaps belong to F1 and cannot be called
full regression acceptance.

Keep P1–P17+B1+D1 selected. No backport, D2 selection or workspace module
change is made by this experiment. The x/text finding remains open on the
selected candidate; F10 is not cleared by the experimental scans.

## Language/default follow-up — 7 October

The [bounded review](evidence/restart-release-go-defaults-2026-10-07) covers
25 compiler-diagnosed node loops, 14 recovery loops and all 22 changed legacy
compatibility overrides. Inspected ticket scoring and storage callees consume
or copy loop values before reuse; no specific consensus-output change was
identified. This does not establish historical compatibility. DNS, HTTP/TLS
and CPU scheduling defaults have concrete operational effects recorded in the
report. Do not globally restore old defaults: that also removes newer request
limits and does not preserve the old language semantics.

Common/RLP race tests pass before and after. Two minimal test-only repairs
restore the complete core/types suite, also passing on both versions. State
tests still have identical inherited compilation failures after their pinned
test dependencies are cached. Original failures and exact overlay/patch inputs
are retained; no production source or selected manifest changed.

Prefer continuing qualification of the upstream update over maintaining a
private dependency backport without an identified compatibility blocker.
Next, complete the F11 state rollback disposition below, repair or precisely
replace the relevant console/tracer/RPC test coverage and verify patched
historical/recovery behavior. Actual service
DNS/TLS checks remain part of existing host acceptance. The update stays
unselected until that evidence is accepted; other F10 findings remain open.

## State coverage follow-up - 7 October

The [state test repairs](evidence/restart-state-tests-2026-10-07) remove the
inherited compilation barrier without changing runtime code. Each build has
15 passing top-level tests and three failing snapshot restoration tests.
The relevant runtime code matches upstream; these failures are not introduced
by x/text or the newer language directive. F11 now records their required
runtime disposition. The separate EVM follow-up has unfinished assertions and
is preserved as incomplete after recurring product content restrictions.
Neither identical failures nor the passing subset clears F1/F10/F11 or selects
the text update. No production manifests, binary artifacts or historical data
were changed by this follow-up.
