# Dashboard backend cleanup and Lodash compatibility

Local evidence date: 2026-10-03. This completes the unused root dependency and
Lodash portion of G6's runtime work. It does not close backend dependency or
public deployment acceptance. The efsn node and consensus code are unchanged.

## Change and removal evidence

The isolated dashboard removes twelve direct dependencies: `auto-bind`,
`body-parser`, `debug`, `grunt`, `grunt-contrib-clean`, `grunt-contrib-concat`,
`grunt-contrib-copy`, `grunt-contrib-cssmin`, `grunt-contrib-jade`,
`grunt-contrib-uglify`, `http2` and `jade`. No tracked Gruntfile or legacy
Jade views remain. The current frontend has its own unchanged package/lock.

The removed `lib/express.js` configured those absent legacy views and assets.
`server.js` required it only outside production and discarded the returned app:
both branches called `http.createServer()` without a request handler. Startup
now creates that same bare server directly. The actual snapshot API remains
in `api-server/app.js`; its Express dependency is retained. `body-parser` and
`debug` still exist transitively, so removing their direct declarations does
not clear their audit findings. The obsolete adapter and the unneeded package
directories were checked absent after the clean install.

Root Lodash is pinned from 3.10.1 to 4.18.1. The manifest otherwise changes only
by those twelve removals. Lock format remains v1: 333 package entries become
156, with 177 removed entries and just one retained version change, root
Lodash. Other retained package versions and archive identities remain fixed.
Resolution used npm 10.9.0 in scratch; the installation used `npm ci` with
lifecycle scripts disabled. The fetched Lodash archive matches npm's SHA-512
integrity value, and the selected installed source files match the inspected
archive. This is an integrity check, not independent publisher attestation.

## Compatibility details

The application migration follows the [Lodash API](https://lodash.com/docs/4.18.1):
`pluck` becomes `map`, descending `sortByOrder` becomes explicit `orderBy`,
and object extrema use `maxBy`/`minBy`. Empty history still reports height zero.
The old three-argument `find` shorthand becomes an explicit node predicate,
preserving each node's own propagation timing. The propagation loop now uses
the sorted array directly; Lodash 4's implicitly chained `forEach` unwraps
its result, so the old trailing chain was incompatible.

Five added characterization tests passed with Lodash 3 before the migration:
empty history, numeric extrema, two nodes' distinct propagation with a missing
height, empty collection and highest reported node head. Expected propagation
values follow the injected receipt times: 1250 - 1000 = 250 ms and
2700 - 2000 = 700 ms. They are unchanged under Lodash 4. The existing suite
also checks chart alignment, history ranges, forks, ticket values, reports,
freshness, limits and identity handling.

The first upgraded run caught the `forEach` chain incompatibility: nine
contract and three socket tests failed. Those raw results are retained. After
removing the unused trailing chain, the complete Node 24.21.0 suites pass:
178 contract tests and 14 ordinary loopback socket tests. Tests and expected
values were not weakened to make the migration pass.

## End-to-end evidence

The actual efsn reporter passes the existing native WSS fixture through nginx,
PostgreSQL 16.15, the HTTPS API and compiled Edge browser. Direct RPC comparison,
the fifty-block history and all four browser checkpoints pass, including
writer expiry and recovery. The stationary run records no writer errors,
browser exceptions or foreign-origin requests.

The synthetic mining-outage drill also passes on the final source and lock.
Height/nonce advance from 61 to 73 while the
collector is absent, then reach 75 after recovery. Mining and
automatic ticket buying remain enabled, with two tickets and zero peers.
All 14 intervening purchases have successful receipts,
linked canonical blocks, sequential nonces and the expected ticket owner.
Collector absence lasts 137.459 seconds; recovery takes 14.369
seconds. The restored forty-point chart agrees with the produced history.
The writer logs 530 expected connection errors
during the outage and none after recovery. Retry pacing/log volume remains
an existing operational follow-up, not a new launch waiver.

All 1,007 efsn Go/module source hashes and all 547 compiled frontend file
hashes match the preceding transport evidence. Test processes are stopped,
temporary credentials are removed, and the two small disposable PostgreSQL
data directories remain stopped. The original dashboard checkout is preserved.
No chain restore, public deployment, push or real signing took place.

## Remaining findings and next work

The root lock audit falls from 41 to 18 affected package names: two critical,
eleven high, two moderate and three low. Lodash and 22 other previously flagged
names disappear; no new names appear. These counts include inherited findings,
not eighteen distinct demonstrated runtime vulnerabilities. The separate
legacy API and frontend locks have not been changed or re-cleared.

| Remaining names | Owning path and next action |
| --- | --- |
| `express`, `body-parser`, `cookie`, `debug`, `ms`, `path-to-regexp`, `qs`, `send`, `serve-static` | Update the active Express 4 stack with compatible fixes and consolidate the separate API install. Review route/query parsing and preserve the four JSON endpoints and freshness/error contract. Unused body/static/redirect helpers do not clear the entire installed stack. |
| `geoip-lite`, `async`, `unzip`, `fstream`, `mkdirp`, `minimist`, `minimatch`, `brace-expansion` | Update or replace GeoIP after checking lookup compatibility, data licensing and maintenance. `async` is imported by the lookup module; archive/glob tools belong to its updater dependencies. No updater was executed. These paths remain open until a reviewed change or specific disposition. |
| `color-string` | Review the compatible transitive update under Primus diagnostics/colorspace/color. The preceding transport update preserved these older versions. |

After backend acceptance, address browser Axios and the build/deployment
workflow, freeze the Node/npm matrix and validate a fresh Linux install.
Continue service supervision, certificate renewal, retries/log retention and
the common deployment manifest. The eight-reporter proxy acceptance from the
preceding transport slice was not rerun here; this slice retains ordinary
socket tests and the actual WSS/mining paths affected by the history migration.

The accompanying efsn investigation retains both failed and passing runs under
`docs/evidence/restart-dashboard-backend-2026-10-03/`. It includes the baseline,
exact package inputs, lock diff, archive integrity, installed versions, audit,
remaining dependency paths, source hashes, RPC/receipt comparisons, process
cleanup and a portable dashboard patch. The consolidated launch gates remain
in [the restart plan](restart-plan.md).
