# Dashboard runtime and dependency review

2026-10-03. G6 now has a passing Node 24 runtime candidate and an evidence-based
dependency worklist. The current dashboard dependencies are **not approved for
public hosting**. In particular, the collector resolves an affected WebSocket
parser on the intended public telemetry route. The earlier application limits
and successful availability tests do not close that finding.

This review changes no dashboard application code, dependency lock, efsn source,
chain rule or database schema. It uses the existing isolated dashboard branch at
`d70014342f1995807bccd26370a7b86379c89099`, read-only registry/advisory requests and
bounded local compatibility tests. It does not run advisory exploit examples.

## Runtime candidate

| Component | Observed candidate | Disposition |
| --- | --- | --- |
| Dashboard services | Linux Node 24.21.0 | Existing contracts, sockets and actual WSS/database/browser pipeline pass |
| Existing test controller | Windows Node 22.11.0, npm 10.9.0 | Retained for comparison/audit; this old patch is not the public deployment selection |
| Database | PostgreSQL 16.15, Ubuntu revision `16.15-0ubuntu0.24.04.1` | Keep this tested major as the candidate; refresh minor/package review at release |
| Reverse proxy | Ubuntu nginx `1.24.0-2ubuntu7.18` | Retain the distribution revision in the manifest; assess its backports and host libraries |
| Driver | `pg` 8.23.1 | Resolves from the root install and passes the real database pipeline |

Node 24 is LTS and its published end-of-life date is 2028-04-30. Node 22 is also
supported, through 2027-04-30, but the tested 22.11.0 patch is far behind the
observed 22.23.3 release. Prefer the tested 24 line for the dashboard candidate,
then pin the current reviewed patch when assembling the release. This does not
select the efsn Go toolchain. See the [Node release policy](https://nodejs.org/en/about/previous-releases)
and [official schedule](https://raw.githubusercontent.com/nodejs/Release/main/schedule.json).

PostgreSQL lists 16.15 as the current minor for supported major 16, with support
through 2028-11-09. There is no need for a database major upgrade merely to obtain
a supported version. The final host still needs the current distribution package
and backup/restore acceptance. See [PostgreSQL versioning](https://www.postgresql.org/support/versioning/).

The nginx package changelog and [Ubuntu USN-8563-5](https://ubuntu.com/security/notices/USN-8563-5)
identify `1.24.0-2ubuntu7.18` as carrying the CVE-2026-42533 correction. Judging this
package solely by upstream `1.24.0` would miss distribution backports. This one
notice is not a complete host security clearance. The captured linked-library
and installed-package versions must be checked against current Ubuntu notices
when preparing the actual host; no host packages were changed here.

The official Node Linux binary was downloaded to ignored scratch space and
matched its HTTPS-published SHA-256 checksum. The detached release signature was
not checked in this experiment. Release provenance verification remains part of
the release manifest, rather than being inferred from these local tests.

## Audit scope and counts

`npm audit --package-lock-only --ignore-scripts --json` was run against each
existing lock using npm 10.9.0. No install, lifecycle script or automatic fix was
requested. Raw responses, exact input files, package metadata and hashes are in
the [runtime-review evidence](evidence/restart-dashboard-runtime-review-2026-10-03/).

| Lock | Package entries | Critical | High | Moderate | Low | Total flagged entries |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Root/backend | 331 | 12 | 21 | 6 | 5 | 44 |
| React frontend | 1,515 | 0 | 69 | 4 | 3 | 76 |
| Legacy separate API | 50 | 0 | 4 | 0 | 3 | 7 |

These are npm package findings, including inherited dependency findings, not
counts of unique vulnerabilities or demonstrated reachable attacks. They are
not additive across installations. Both main manifests put build tools in
`dependencies`, so `--omit=dev` alone would not distinguish shipped services
from development tools. The audit is a dated inventory, not a durable promise
that an unflagged dependency is secure.

`resolved-packages.json` records resolution from each actual service entry point.
The API currently resolves Express 4.17.1 from the root install. There is no
`api-server/node_modules`; installing its separate legacy lock could silently
shadow the reviewed root dependency. Consolidate that installation path before
documenting the production install.

## Required dependency work

| Area | Finding and relevant path | Next change and acceptance |
| --- | --- | --- |
| Collector WebSocket transport | Primus 6.1.0 resolves root `ws` 1.1.5; Primus also has a `setheader` dependency finding | Review Primus and ws together, including plugins, then rerun authentication, bounded input/output, normal reconnect and native WSS acceptance |
| Collector data processing | Lodash 3.10.1 is actively imported by collector, node and history code | Move to a reviewed fixed release with explicit handling of the old `pluck` and `sortByOrder` calls; preserve chart ordering, identity and report behavior |
| HTTP API | Express 4.17.1 and transitive packages have findings | Prefer a compatible maintained 4.x update if it resolves the reviewed findings; consolidate the separate API lock; rerun freshness, routing and database checks |
| GeoIP | Active `geoip-lite` 1.2.1 has an inherited `unzip` finding | Review lookup versus data-update/install paths and choose a maintained package/data policy; do not infer that an installer finding proves a public lookup exploit |
| Browser HTTP client | Axios 0.21.2 is present in the compiled browser and flagged | Update or replace it with a small compatible client; preserve deadlines, cancellation, same-origin paths, expiry and recovery |
| Legacy tools | Grunt/Jade and other old dependencies contribute many findings; several have no active production entry-point import | Remove unused dependencies and obsolete build paths after reference review; document any retained build-only exposure and isolate the builder |
| Release automation | Legacy workflow uses Node 16, `npm install` and the foundation S3 destination | Replace before enabling Actions or releasing; use reviewed pinned tools, locked installs and an explicitly selected deployment target |

The WebSocket issue is the first concrete public-hosting blocker. The upstream
[ws advisory GHSA-96hv-2xvq-fx4p](https://github.com/websockets/ws/security/advisories/GHSA-96hv-2xvq-fx4p)
includes installed version 1.1.5 and describes parser memory use exceeding what
message-size limits imply. The application sees messages after that parser.
Our inference from that call order is that existing application admission rules
do not establish remediation. The advisory lists reduced payload size as a
mitigation, not a replacement for updating. Keep public exposure blocked pending
the transport update; no resource-exhaustion reproduction is needed.

This is not a one-package blind substitution: the installed Primus transformer
uses `socket.upgradeReq`, an old ws interface. Registry metadata currently names
Primus 8.0.9 and ws 8.22.0 as latest releases; these are candidates to inspect,
not a tested pair. Verify the efsn wire protocol and both Primus plugins before
selecting exact new pins. Native efsn need not change merely because the server's
JavaScript transport implementation changes.

The current compiled JavaScript maps contain 41 package names. Only Axios also
appears in the frontend audit findings. The mapped adapter is its browser XHR
adapter; Node HTTP/proxy-specific advisories do not automatically describe this
browser path. That observation does not dismiss browser-relevant findings or
unmapped assets. Highcharts, Recharts and development-server dependencies are
examples requiring build/reference classification, not reasons to present all
76 findings as public browser vulnerabilities.

Create React App is [deprecated and in maintenance mode](https://react.dev/blog/2025/02/14/sunsetting-create-react-app).
Its 5.0.1 build should therefore have a documented replacement or narrowly
reviewed temporary build-only disposition. A complete React/UI rewrite is not
automatically a launch requirement. Inspect unused direct dependencies first,
then keep any build migration separate from the collector transport fix.

## Compatibility evidence and limits

Node 24.21.0 passes 173 contract and 13 socket tests with unchanged dependencies.
It also runs the actual collector, snapshot writer and API on Linux in the
existing WSS/PostgreSQL fixture. The real efsn reporter, direct RPC comparison,
fifty-block history and four Edge browser checkpoints pass, including writer
loss, expiry and recovery. There are no writer errors, browser exceptions or
foreign-origin requests. Edge reports version 154.0.4258.53 in this run.

A separate `CI=true` production build under Linux Node 24.21.0 also passes with
the same dependencies and explicit browser settings. It writes to new scratch
space, leaving the existing build intact. Of its 547 output files, only the
JavaScript source map differs from the prior build; executable JavaScript, CSS,
HTML and other assets match byte for byte. The build emits the dependency
deprecation warning `DEP0176` about `fs.F_OK`; it was retained, not suppressed.
This build reused installed dependencies, so a clean locked installation with
the final npm version still needs acceptance.

That fixture uses the existing compiled frontend, PostgreSQL 16.15, the extracted
nginx package, P17's existing Go test binary and temporary locally trusted TLS
credentials. The chain is stationary. The separate mining-outage result remains
the evidence for continued production; it was not rerun on Node 24 here. Neither
fixture is acceptance of public certificate renewal, sustained public traffic,
service supervision or a fresh production install.

All 719 non-Markdown dashboard source files, all three package/lock pairs and the
existing 547-file compiled frontend remain unchanged. The efsn Go/module source
inventory also remains unchanged. Scratch services are stopped and temporary
credentials removed. The original dashboard checkout is preserved.

Subsequent [transport](restart-dashboard-transport.md),
[backend cleanup](restart-dashboard-backend.md),
[API dependency](restart-dashboard-api.md) and
[GeoIP/diagnostics](restart-dashboard-geoip.md) work completes the backend
dependency corrections and shared API installation. The latest slice passes
178 contract/14 socket tests, native WSS/browser and eight-reporter proxy
acceptance. All 144 installed backend paths match the lock; the current root
audit reports zero known advisories. Earlier counts describe earlier trees.
The backend requires Node >=24 and passes a clean Linux Node 24.21.0/npm 10.9.0
installation with engine checks enforced and lifecycle scripts disabled.

The [frontend update](restart-dashboard-frontend.md) now pins Axios 0.34.0,
removes thirteen unused direct packages and replaces the Foundation deployment
workflow with validation only. A clean Linux install, eight React DOM tests,
CI build, nine compiled-browser checkpoints and native WSS/browser acceptance
pass. The frontend audit falls from 76 to 73; none of its remaining affected
names appears in the production source maps. The subsequent
[toolchain replacement](restart-dashboard-toolchain.md) removes CRA and clears
all 73 remaining advisory names, including the separate map Acorn path. Clean
installation, DOM/build/lint gates and compiled/native browser acceptance pass.
The final lock retains every active direct application-library version; the
report records lint coverage differences and remaining maintenance work.

## Work order and exit condition

1. Use the [UI maintenance review](restart-dashboard-ui-maintenance.md) for
   the recorded version/peer gaps and the accepted saved-pin recovery fix.
   Decide the coordinated map/tooltip/React migration or explicit legacy-stack
   disposition at release review. Keep lint differences and the intended
   browser matrix explicit. Hosted validation remains unrun; the current
   dependency locks retain the prior zero-advisory results.
2. Use the [GeoIP operations investigation](restart-dashboard-geoip-operations.md)
   for reproduced updater failures and passing isolated switch/rollback checks.
   The [read-only validator](restart-dashboard-geoip-validation.md) implements
   binary checks and exposes incompatible IPv6 data. The subsequent
   [reader comparison](restart-dashboard-geoip-reader.md) selects standard MMDB
   and `mmdb-lib` 3.0.3 after 3,007 passing raw lookups and isolated model checks.
   Implement the bounded loader, preserve country-only flags, retire the custom
   format when replaced, and repeat combined acceptance. Then finish protected
   downloads and supervised immutable-MMDB activation. Source/account selection,
   applicable terms/attribution and refresh/deletion operations remain open.
3. Continue G6 supervision, retry/log lifecycle, public certificates and the
   coordinated deployment manifest. Recheck advisories at release and rerun
   combined acceptance on that exact package. These local compatibility
   results do not constitute release approval.

G6 remains open. The [consolidated plan](restart-plan.md) owns the launch gates;
this report records the initial review and current dependency work order.
