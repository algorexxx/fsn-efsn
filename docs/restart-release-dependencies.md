# Selected efsn dependency review

4 October 2026. F10 remains a **release hold**. The first audit of the exact
[P1–P17+B1 selection](restart-release-selection.md) is complete; remediation and
independent acceptance are not. No runtime source, module version or consensus
rule changed during this audit. The two discovery fixture repairs are separate
test-only work recorded in the same [evidence bundle](evidence/restart-release-followup-2026-10-04).

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

No upgrade is selected by this report. The next technical work is the bounded
dependency remediation above alongside the separate baseline history replay.
