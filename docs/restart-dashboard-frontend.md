# Dashboard frontend dependencies and validation workflow

Local evidence date: 2026-10-03. Axios moves from 0.21.2 to an exact 0.34.0 pin,
thirteen unused frontend dependencies are removed, and the inherited Foundation
deployment workflow is replaced by validation only. Application JavaScript,
test expectations, backend dependencies and all efsn Go/module sources remain
unchanged. The rebuilt frontend passes both synthetic and native efsn browser
acceptance. G6 remains open for build-tool dependencies and deployment controls.

## Dependency selection and scope

[Axios's support policy](https://github.com/axios/axios/security/policy) covers
both 0.x and 1.x. The captured registry and [0.34.0 release](https://github.com/axios/axios/releases/tag/v0.34.0)
identify 0.34.0, published 2026-09-13, as the current stable 0.x release.
Retaining this supported line preserves the existing CommonJS/browser setup.
The application still makes one same-origin GET request through Axios's XHR
adapter; its own polling controller owns deadlines, retry scheduling and expiry.
Its existing CancelToken integration remains functional, although Axios
[deprecates that API](https://axios-http.com/docs/cancellation). A future major
migration should use AbortController and repeat cancellation acceptance.

The selected archive matches npm's SHA-512 integrity value and all 78 archive
files match installation. A separate installation containing this exact Axios
version passes `npm audit signatures`: 23 registry signatures and one provenance
attestation verify. This checks package provenance, not absence of defects.
No install lifecycle scripts are enabled.

The removed direct declarations are `highcharts`, `highcharts-react-official`,
`react-countdown-now`, `react-countup`, `react-custom-scrollbars`,
`react-fontawesome`, `react-lazyload`, `react-loading-skeleton`, `react-reveal`,
`react-toastify`, `react-tooltip`, `recharts` and `websocket`. Source imports and
the previous production source maps reference none of them. Active map, flag,
number-formatting, Bootstrap, Material UI, React and time-display packages are
retained. Backend WebSockets use their separate unchanged installation.

The frontend v1 lock goes from 1515 to 1445 paths: 72 removed, two added and one
updated. Every changed path belongs to Axios's dependency tree or a removed
package's tree. Axios gains private form-data 4.0.6 and proxy-from-env 1.1.0;
only Axios changes version among retained paths. No blanket update, override or
automatic audit fix is used. A clean Linux Node 24.21.0/npm 10.9.0 `npm ci`
passes with engine checks enforced and lifecycle scripts disabled. The frontend
now declares Node >=24. All 1425 installed packages match their locked versions;
20 platform-specific optional paths are omitted on Linux x64. All 72 removed
paths are absent. Root backend manifest and lock retain their accepted hashes.

## Remaining advisory and maintenance work

The frontend audit drops from 76 to 73 affected package names, clearing Axios,
d3-color and Highcharts. No new names appear. The remaining counts are 66 high,
four moderate and three low, with react-scripts the sole directly flagged
dependency. Full details and dependency paths are retained in `audit-after.json`.
These are package-level findings, not counts of demonstrated reachable exploits.

Tracing every audited installed path finds one outside react-scripts:
`node_modules/falafel/node_modules/acorn`, version 5.7.3, belongs to the legacy
map package's Node/build dependency tree. The browser uses TopoJSON's packaged
browser entrypoint. Acorn is absent from the compiled source maps, but a CRA
replacement alone must not be assumed to remove that installed path. Retain
its separate correction/review item with the map-library maintenance work.

None of those 73 names appears in the rebuilt production JavaScript source
maps. The maps confirm Axios's XHR adapter is included and its Node HTTP adapter
is absent. This is evidence about the current bundle, not a general finding that
the development/build environment is safe. Treat the remaining toolchain review
as open; do not run its development server as the public dashboard or publish
the installed frontend node_modules. Only the static build is served.

The clean install also records deprecations, including the inherited Material
UI v4, Popper v1 and build tools. A zero reported advisory is not a maintenance
guarantee. Review the [deprecated Create React App toolchain](https://react.dev/blog/2025/02/14/sunsetting-create-react-app)
next, choosing supported tooling while preserving the UI and explicit settings.
Keep used UI-library maintenance decisions separate and record their disposition.
The unchanged backend's last audit remains at zero known advisories.

## Validation workflow

`.github/workflows/deploy.yml` is gone. It previously ran Node 16, unlocked
`npm install`, AWS credential configuration and an S3 sync to the Foundation
bucket. `.github/workflows/validate.yml` has only pull-request and manual
triggers, read-only contents permission, no retained checkout credentials and
no deployment step or secret references.

The new workflow selects Ubuntu 24.04, Node 24.21.0 and npm 10.9.0, pins checkout
7.0.1 and setup-node 7.0.0 by full commit SHA, and disables automatic package
caching. It runs locked installations, backend contracts/socket tests, frontend
DOM tests and a production build. Its explicit API/timing values are local
validation settings, not a chosen production profile. It parses successfully;
the referenced action definitions and release pins are captured. No GitHub
workflow has been run, no artifact published and no deployment target selected.
Local Linux execution verifies the test/build commands, not hosted Actions setup.

## Build and browser acceptance

All 178 backend contract tests, 14 socket tests and eight existing React DOM
tests pass. The production build passes with `CI=true`, without lint/preflight
bypasses or legacy crypto options. The inherited `DEP0176` build warning is
retained. The build still has 547 files: 542 are byte-identical; the main
JavaScript bundle, its licence/source-map files, index and asset manifest change.
The prior build is preserved in scratch; the rebuilt files are the active local
browser fixture. Generated assets remain outside the Git patch and must be
rebuilt from the exact source, lock, runtime and settings for a release.

The compiled Edge browser passes nine checkpoints: populated rows, keyboard
pinning, accessible map/two markers, empty data, storage failure, recovery,
expired storage, request timeout and timeout recovery. There are no page errors,
missing assets or foreign-origin requests. One aborted API request is expected
from the deliberate deadline case. The map screenshot was also inspected.

The real local efsn reporter then passes WSS -> nginx -> PostgreSQL -> HTTPS API
-> the rebuilt browser, with matching head/fifty-block history. All four browser
checkpoints pass, including writer expiry and recovery, with no writer/browser
errors. The existing eight-reporter proxy and mining-outage results are retained
for their unchanged code; those separate workloads were not repeated here.
The original dashboard checkout and all 1007 efsn source/module hashes are
preserved. Fixture processes are stopped and disposable credentials removed.

## Next step and retained evidence

Resolve the remaining build-tool findings and supported build/test matrix,
then repeat clean installation and combined acceptance for that final package.
Finish GeoIP dataset operations, service supervision, retry/log lifecycle,
public TLS renewal and the common deployment manifest before public use.
The replacement validation workflow is not deployment approval.

The efsn investigation retains baseline inputs, registry/provenance records,
dependency changes, audits, build hashes, browser captures, workflow checks,
native telemetry evidence and the portable dashboard patch under
`docs/evidence/restart-dashboard-frontend-2026-10-03/`.
The [restart plan](restart-plan.md) owns the launch gates.
