# Dashboard build-tool replacement

Local evidence: 2026-10-03 through 2026-10-04. The dashboard frontend now builds
with Rsbuild instead of Create React App. The final frontend npm audit reports
zero known advisories, down from 73; the unchanged backend's accepted audit is
also zero. This closes the recorded advisory list, not the public-dashboard
launch gate. No efsn source, consensus rule, ticket behavior or wallet changes.

## Exact application impact

- Replace `react-scripts` with pinned build, test and lint tools. Preserve React
  and React DOM 16.10.2 and every other active direct application-library version.
- Retain classic JSX, CommonJS helpers, the three explicit `REACT_APP_STATS_*`
  settings, same-origin requests and the `build` output directory. The build now
  calls the existing configuration validator before compilation, so missing or
  invalid deployment settings fail immediately. Development binds to loopback.
- Adapt the HTML asset placeholder. Remove one orphan Flow type import and type
  annotation from the localization file; all strings and runtime expressions
  remain unchanged. No test expectations, polling or display logic change.
- Run the existing Jest tests directly. CSS/image mocks replace CRA's test-only
  import handling. Run lint before every production build.
- Correct the map dependency's Acorn path within its allowed range and update
  compatible YAML paths. Convert the frontend lock to npm 10's v3 format, which
  records modern package aliases without the old lock's metadata warnings.

The selected direct tools are Rsbuild 2.2.11, its React plugin 2.1.1, SWC core
1.16.13 / Jest adapter 0.2.39, Jest and jsdom environment 30.5.2, Oxlint 1.86.0,
ESLint 10.12.0 and globals 17.13.0. All are development dependencies. No blanket
override, force audit fix, peer bypass or install lifecycle script is used.
The final lock has 904 package paths, with 821 installed on Linux and 83 optional
platform-specific paths omitted. The previous lock had 1445 paths. The original
dashboard checkout and the prior compiled build are preserved.

[Rsbuild's CRA migration guide](https://rsbuild.rs/guide/migration/cra) describes
the HTML, environment and output-directory compatibility options. Its
[React plugin](https://rsbuild.rs/plugins/list/plugin-react) supports the classic
JSX runtime used here. These let the build change stay separate from a React/UI
upgrade. [SWC's Jest adapter](https://swc.rs/docs/usage/jest) provides the test
transform without CRA's Babel preset.

## Lint coverage and the discovered gap

ESLint 9 reached end of support on 2026-08-06 according to its
[version-support policy](https://eslint.org/version-support/). The inherited
React/import/accessibility plugins' published peer ranges do not accept ESLint
10. Oxlint supplies the relevant native rules without those plugin dependencies.
The old 116-rule configuration and license are captured; 99 rules are retained,
including four renamed equivalents. The copied rule configuration retains its
MIT notice in `react-frontend/LINT-LICENSE.txt`.

This is not exact lint parity. Five formatting/parenthesization rules and the
redundant-strict-directive style check are omitted. Three Flow checks are no
longer relevant; JSX variable tracking is built in. Four syntax restrictions
are covered by module parsing. `react/forbid-foreign-prop-types` and
`react/no-typos` have no direct replacement and remain documented review
limitations. The full mapping is in `lint-migration.json`. Oxlint's
[migration documentation](https://oxc.rs/docs/guide/usage/linter/migrate-from-eslint.html)
also distinguishes compatible rules from exact implementation parity.

A negative check found that Oxlint 1.86.0 misses `export default missingNode;`,
although its ordinary undefined-variable checks work. The final lint command
therefore also runs maintained ESLint 10's `no-undef` rule. The same fixture now
fails through ESLint; missing image alt text and duplicate parameters also fail.
Do not remove that second check merely because Oxlint includes a rule with the
same name. No upstream message or issue was sent.

Lint covers all twelve application/test JavaScript files. The eighteen inherited,
unimported `src/js` theme/demo files remain outside scope, as with CRA's imported
module linting. Source imports and both compiled source-map inventories show
they are not in the application. The old unused-catch-variable setting is
explicitly retained. No existing application warning was suppressed to pass.

## Acceptance and its limits

The final clean Linux Node 24.21.0 / npm 10.9.0 installation uses engine and peer
checks, with lifecycle scripts disabled. Every installed manifest version
matches the lock. npm's normal archive-integrity checks apply; this is not a
claim of independently verified provenance for every transitive package.

Passing checks:

- 178 backend contracts and 14 socket tests.
- Eight unchanged React DOM tests, lint with zero warnings/errors, and the normal
  production build with `CI=true` and no build warnings.
- Nine build-configuration/lint gate checks, covering valid settings, missing or
  foreign API paths, missing polling, zero timeout and representative lint errors.
- Nine compiled Edge checkpoints: rows, pinning, map, empty data, failure,
  recovery, expiry, timeout and timeout recovery. No page errors, missing assets
  or foreign-origin requests; one expected aborted request in the timeout case.
- Native local efsn -> WSS/nginx -> PostgreSQL -> HTTPS API -> browser, with the
  actual head and fifty-block history matching. Writer expiry/recovery and all
  four browser checkpoints pass over TLS 1.3.

The final 546-file build is byte-identical before and after the lint-only gap
correction. Browser/native acceptance therefore applies to the final assets.
Compared with CRA, 520 output files retain identical bytes; bundle names,
splitting, CSS and font paths change. Axios still includes its browser XHR
adapter and excludes its Node HTTP adapter. The map screenshot was inspected.
The native fixture is stationary; the existing mining-outage result applies to
unchanged reporter/backend code and was not repeated here.

All 1007 efsn source/module hashes and the original dashboard checkout are
preserved. Test processes are stopped and disposable credentials removed.
The validation workflow's commands remain valid; it has not run on GitHub.
Linux/Edge acceptance does not establish every OS/browser combination.

## Remaining release work

Zero advisories is a dated registry result, not proof that dependencies are
safe or maintained. Installation still reports deprecations for legacy UI/map
packages and some Jest transitives. Review the used UI libraries, the two lint
coverage limitations and the intended browser matrix separately. Recheck the
exact release lock and repeat acceptance if production assets/runtime change.

G6 still needs GeoIP dataset/update operations, service supervision, retry/log
lifecycle, public certificate renewal and the coordinated deployment manifest.
Serve only the static build, not the development server or installed packages.
Source maps are retained for local review; decide their public serving policy
in the deployment manifest. The [restart plan](restart-plan.md) owns the gates.

Evidence and the portable dashboard patch are under
`docs/evidence/restart-dashboard-toolchain-2026-10-03/`. Preliminary failures
are retained alongside final passing records, including the npm harness path
correction, lint-scope correction and reproduced undefined-export gap.
