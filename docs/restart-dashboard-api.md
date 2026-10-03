# Dashboard API dependency upgrade

Local evidence date: 2026-10-03. Express is pinned from 4.17.1 to 4.22.3 and
the API now shares the root backend installation. No application JavaScript,
efsn source, schema or compiled frontend changes are needed for this slice.
The nine Express-related root audit findings clear; nine other names remain.
G6 remains open for those dependencies and public deployment acceptance.

## Version and lock review

[Express supports the latest release in both its 4.x and 5.x lines](https://expressjs.com/en/support/).
The captured npm registry lists 4.22.3, published 2026-09-14, as the latest
stable 4.x version. Retaining the supported 4.x API keeps this change bounded.
The [Express security update history](https://expressjs.com/en/advanced/security-updates/)
and the selected archive's `History.md` were reviewed. The application retains
four literal GET routes, JSON responses, freshness headers and its existing
read-error handling. It does not add middleware or new route behavior.

Resolution uses npm 10.9.0 and preserves lock format v1. The lock grows from
156 to 167 installed paths: 18 additions, seven removals and 37 updated entries.
An updated entry may be metadata rather than a changed version. The selected
tree includes body-parser 1.20.8, qs 6.16.0, path-to-regexp 0.1.13, send 0.19.2
and serve-static 1.16.3. These are locked transitive versions, not new direct
dependencies. Every other direct dependency declaration remains unchanged.

All changed paths are accounted for by Express's old/new tree and one shared
dependency removal: `websocket` accepts debug `^2.2.0`, and now reuses Express's
debug 2.6.9. Its previous private ms 0.7.1 is removed. This shared effect is
included in the ordinary socket acceptance rather than assumed harmless.

The Express archive matches npm's SHA-512 integrity value; selected installed
files match the inspected archive. This verifies integrity, not independent
publisher attestation. Installation uses `npm ci --ignore-scripts --no-audit
--no-fund` only in the isolated dashboard checkout. All 167 installed versions
match the new lock; the manifest and lock remain unchanged by installation.
Existing old-lock and deprecated dependency warnings are retained in evidence.

## One backend installation

The removed `api-server/package.json` and `api-server/package-lock.json` defined
an independent Express installation that could shadow the tested root version.
The root package now provides `npm run start:api`, executing
`node api-server/server.js`. The collector still uses `npm start`.
The frontend retains its separate build installation.

Node 24.21.0 confirms that resolving Express from the API entrypoint and the
root package yields the same root `node_modules/express/index.js`, version
4.22.3. Both old API package files and `api-server/node_modules` are absent.
Deployment must use a fresh release directory so old nested dependencies cannot
silently shadow the new lock. Required environment and least-privilege database
settings are unchanged. The snapshot guide owns the installation/start commands.

## Acceptance and limits

All existing tests pass on Linux Node 24.21.0: 178 contract and 14 loopback
socket tests. The contracts cover all four JSON endpoints, exact freshness
boundaries, missing/stale/future/failed reads, response headers and separate
per-node report expiry. No tests or expected values were changed.

The real efsn reporter passes through WSS, nginx, PostgreSQL 16.15, the HTTPS API
and the compiled Edge browser. RPC/head and fifty-block history comparisons
agree. All four browser checkpoints pass, including writer expiry and recovery,
with no writer errors, browser exceptions or foreign-origin requests.

The existing eight-reporter proxy fixture also passes: certificate trust and
hostname checks, compiled assets, route isolation, stale-snapshot refusal,
reporter admission and authentication. It carries the normal 3,276,956-byte
history payload and verifies normalized forwarding headers for all reporters.
These are bounded loopback acceptance runs, not public traffic or exploit tests.

All 1,007 efsn Go/module files and 547 compiled frontend files retain their prior
hashes. The original dashboard checkout is preserved. Test processes are stopped,
temporary credentials are removed and the disposable PostgreSQL directory
remains stopped. No large chain restore, deployment, push or real signing occurs.
The previous mining-outage result remains the evidence for continued production;
it was not rerun for this package-only API change. Final combined acceptance
still needs the complete selected deployment package.

## Remaining work

The root audit falls from 18 to nine affected package names. Cleared names are
`express`, `body-parser`, `cookie`, `debug`, `ms`, `path-to-regexp`, `qs`, `send`
and `serve-static`; no new names appear. Remaining counts are two critical,
six high and one moderate. These are dependency findings, not demonstrated
reachable vulnerability counts. The removed API lock is superseded by the
audited root installation, and the frontend lock has not been re-cleared.

| Remaining path | Next action |
| --- | --- |
| GeoIP: `geoip-lite`, `async`, `unzip`, `fstream`, `mkdirp`, `minimist`, `minimatch`, `brace-expansion` | Review a supported replacement/update, lookup compatibility, data licensing and updater behavior. `async` is imported by the lookup module; do not label the entire path build-only. No updater ran in this slice. |
| Primus diagnostics/colorspace/color: `color-string` | Review and lock a compatible transitive correction, then re-audit the remaining backend tree. |

Then address browser Axios, build-only dependencies and the obsolete deployment
workflow; select the final Node/npm matrix and validate a clean Linux install.
Finish supervision, public certificate renewal, retries/log retention and the
coordinated deployment manifest before public use.

The accompanying efsn investigation retains exact inputs, metadata, archive
integrity, lock scope, installed package versions, module resolution, audits,
test results, RPC/browser/proxy captures, cleanup and the portable dashboard
patch under `docs/evidence/restart-dashboard-api-2026-10-03/`.
The launch gates remain in [the restart plan](restart-plan.md).
