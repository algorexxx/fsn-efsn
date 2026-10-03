# Dashboard GeoIP and diagnostics dependency update

Local evidence date: 2026-10-03. The shared backend lock now reports zero known
npm advisories, down from nine affected package names. GeoIP is pinned from
1.2.1 to 2.0.3; the compatible transitive `color-string` resolution moves from
1.5.3 to 1.9.1. The root manifest requires Node >=24.0.0. No application
JavaScript, efsn source, schema, test expectations or compiled frontend changes
are needed. G6 remains open for frontend and deployment work.

## Package scope and installation

The captured registry identifies GeoIP 2.0.3 as the latest stable release. Its
[upstream documentation](https://github.com/geoip-lite/node-geoip) and selected
archive require Node 24. The locked tree contains 144 installed paths, down
from 167: 32 removed, nine added and two updated. Every change belongs to the
old/new GeoIP or color-string dependency tree. All other direct declarations
remain unchanged; no override, automatic audit fix or new direct dependency
is introduced.

GeoIP's native asynchronous file loading replaces its old `async` dependency;
its explicit updater uses `yauzl` instead of the obsolete `unzip` stack.
The diagnostic path remains Primus -> diagnostics -> colorspace -> color ->
color-string; version 1.9.1 satisfies color's existing `^1.5.2` requirement.
These are dependency corrections, not evidence that an exploit was reachable.

Resolution and a clean `npm ci --ignore-scripts --no-audit --no-fund` run use
Linux Node 24.21.0 and npm 10.9.0 with engine checks enforced. The existing
cross-platform npm CLI is run by the Linux Node binary. The preserved v1 lock
still produces npm's old-lock warning; yaeti 0.0.6 also has a deprecation
warning. Those warnings are retained, despite the zero-advisory result.
The final production Node/npm pairing and host image remain release decisions.

Both selected archives match npm's SHA-512 integrity values. All 21 archive
files, including the GeoIP binary datasets, match the installed files. This
checks integrity, not independent publisher attestation. All 144 installed
versions match the lock. All 32 removed dependency paths and any API-local
installation are absent. Installation leaves the manifest and lock unchanged.

## Lookup and dashboard compatibility

GeoIP is used by `lib/node.js` for country flags and map coordinates. Retain
this functionality. Eight local lookups exercise public IPv4, public IPv6,
IPv4-mapped IPv6, loopback and all three RFC1918 ranges; no connection is made
to those addresses. The public country/region/city/timezone expectations come
from the selected upstream package's `test/tests.js`. They describe that
bundled dataset, not independently verified present-day locations.

The actual node model still normalizes the mapped address and exposes null
for the five private/loopback cases. The actual frontend snapshot mapper
accepts all three public records and produces finite in-range map coordinates.
The largest sampled GeoIP JSON object is 164 bytes. Normal RGB parsing passes
published CSS colour values, and four diagnostic namespace colours match the
pre-upgrade capture.

The existing 1024-byte GeoIP allowance is also reviewed against the 2.0.3
reader, not inferred from those samples. Its five string fields are bounded by
84 source bytes in a fixed 88-byte location record. Allow six JSON/wire bytes
per source byte, plus 24 bytes each for the six numeric values and the fixed
JSON structure. The resulting ceiling is 744 bytes; IPv6's empty
range and country-only/null results are smaller. Recheck this allowance when
the reader's schema changes. Dataset changes within this format do not enlarge
the string fields.

All 178 contract tests and 14 loopback socket tests pass on Linux Node 24.
The native efsn reporter passes WSS -> nginx -> PostgreSQL 16.15 -> HTTPS API ->
compiled Edge browser. All four checkpoints pass, including writer expiry and
recovery, with matching head/fifty-block history and no writer/browser errors.
The eight-reporter proxy fixture passes certificate checks, route isolation,
authentication, normalized forwarding and the normal 3,276,956-byte history
payload. These are bounded local acceptance checks.

All 1007 Go/module files and 547 compiled frontend files retain their prior
hashes. The original dashboard checkout is preserved. Test services are
stopped and temporary credentials removed; one stopped disposable PostgreSQL
directory remains. No chain restore or real signing is involved. The earlier
mining-outage result is retained; this metadata dependency slice does not
repeat that drill or constitute final combined deployment acceptance.

## Dataset licensing and launch requirement

The selected archive's [LICENSE](https://github.com/geoip-lite/node-geoip/blob/main/LICENSE)
separately identifies Apache 2.0 code and bundled GeoLite2 data under CC BY-SA
4.0, with a 2012-2018 MaxMind copyright notice. Preserve both notices. The
package version, tar timestamps and copyright year do not establish dataset
freshness. The package README instructs operators to update the bundled data.

This product includes GeoLite2 data created by MaxMind, available from
[MaxMind](https://www.maxmind.com/).

For newly downloaded GeoLite datasets, [MaxMind's current instructions](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data/)
require an account/license key and describe ongoing update and deletion
obligations. Review the terms attached to the selected download; do not assume
the older bundled CC dataset and a current download have identical terms.
IP geolocation is approximate network location, not operator identity or proof
of validator independence.

The updater was inspected, not run. It is an explicit script, not an install
hook, and accepts a license key through an argument or `LICENSE_KEY`, with
`GEODATADIR`/`GEOTMPDIR` overrides. No account/key was supplied and no MaxMind
download, redistribution or updater network behavior was tested.

Before public deployment, select and record the dataset source, applicable
terms, edition/date and hashes; preserve required notices in documentation and
map-facing attribution. Obtain updates using a protected job without exposing
the license key in arguments, URLs or logs. Stage the complete dataset outside
the serving process, verify lookup compatibility, then switch and restart the
collector with an explicit `GEODATADIR`. Verify update failure/retry behavior,
rollback availability subject to retention terms, and the required refresh and
deletion schedule. This operational acceptance remains open; the package
upgrade does not certify fresh map data.

## Next work

Address browser Axios and build dependencies, replace the inherited deployment
workflow, and finalize the reproducible runtime/build matrix. Complete G6
service supervision, public TLS renewal, retries/log retention, GeoIP dataset
operations and the coordinated deployment manifest. Repeat advisory review
and combined acceptance on that final release. A zero backend audit is a
point-in-time result, not a security guarantee or a cleared frontend audit.

Exact inputs, package metadata/integrity, lock changes, lookup captures, audits,
test results, cleanup and the portable dashboard patch are retained under
`docs/evidence/restart-dashboard-geoip-2026-10-03/` in the efsn investigation.
The [restart plan](restart-plan.md) owns the launch gates.
