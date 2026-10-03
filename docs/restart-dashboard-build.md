# Dashboard production build and compiled browser acceptance

3 October 2026. Dashboard commit `a5bee3fd70cc2670f3fad890fd878ec7c14d23cc` follows browser-freshness commit
`c74d603` in the isolated worktree. **The strict production build now passes, along with 110
contracts, seven React DOM tests and nine compiled Edge browser checkpoints.**
The dashboard is still awaiting real-node, resource-limit and deployment review.

## Explicit change list

1. Pin `react-scripts` 5.0.1 and update the frontend lock. The inherited 3.2.0
   release pins webpack 4.41.0; replacing webpack alone would conflict with that
   release's dependency checks. The new lock uses webpack 5.111.1 and resolves
   the reproduced Node 22 hashing failure.
2. Replace two pin/unpin links without destinations with labeled buttons. The
   strict build exposed these accessibility warnings; keyboard pinning is now
   exercised in the compiled app.
3. Pin React Bootstrap 1.6.8 after browser testing found the old beta's map dialog
   marked itself `aria-hidden`. Its react-overlays 5.2.1 replacement fixes that
   behavior. Label the dialog with its title and cancel the map's delayed-render
   timer when it unmounts. A regression test checks accessible closure without
   a late update to an unmounted component.

React and React DOM remain 16.10.2. Dependency resolution also moves `prop-types`
from 15.7.2 to 15.8.1 within its existing manifest range. Other direct application
dependencies retain their installed versions. Backend dependency locks, collector,
storage/API code and node consensus/recovery code are unchanged. Tests, a local
synthetic browser fixture and documentation accompany the frontend correction.

The wider dependency review is not complete. Create React App is in
[maintenance mode](https://react.dev/blog/2025/02/14/sunsetting-create-react-app).
Its [5.x release](https://github.com/react/create-react-app/releases/tag/v5.0.1)
provides the bounded compatibility step here; it is not a claim that this old UI
stack is the final long-term hosting choice. The registry metadata and exact
resolved dependency delta are retained for review.

## Build and local tests

The tested toolchain is Node 22.11.0, npm CLI 10.9.0, react-scripts 5.0.1,
webpack 5.111.1, Jest 27.5.1, React Bootstrap 1.6.8 and react-overlays 5.2.1.
The npm CLI was invoked directly because this Windows machine's `npm.cmd`
wrapper selects npm 6.14.15. Resolution/installation used normal dependency
checks with lifecycle scripts disabled; lockfile format 1 is retained.

The final build uses `CI=true` and reports **Compiled successfully**. No legacy
crypto option, edited dependency file or lint suppression is used. The generated
JavaScript is about 196.79 kB gzip and CSS 37.24 kB gzip. Asset hashes are recorded
against the exact tested source. These sizes describe this local build only.

The first upgraded build failed on the two pin-link warnings. The next strict
build passed, but compiled-browser testing exposed the modal fault. After the
modal update, its new test exposed the uncanceled delayed-render callback. All
those outputs and intermediate sources are retained; the final run has no React
rendering warnings. The inherited test-runner `punycode` deprecation remains.

## Compiled-browser evidence

The in-app browser tool failed twice during initialization with a missing kernel
asset path. The fallback uses bundled Playwright 1.62.1 and installed Edge
154.0.4258.48 in a separate headless profile. It runs the actual optimized bundle,
real Axios/XHR and the existing HTTP API on an ephemeral IPv4 loopback listener,
with synthetic in-memory storage. No normal user browser profile is accessed.

Nine checkpoints pass: populated reports, keyboard pinning, accessible map with
two node markers, an empty snapshot, storage failure, recovery, expired storage,
a hanging request reaching its cancellation deadline, and recovery afterward.
The unavailable state removes old rows and summary values and retains an
explicitly labeled last-observation time. Screenshots were visually inspected.

There are no page exceptions, missing assets or foreign-origin requests. The
deliberately hung API request produces one expected `net::ERR_ABORTED`. Both map
close controls are outside hidden accessibility subtrees. The first exploratory
browser assertion was corrected for the existing CSS uppercase transformation;
that assertion failure and the actual modal failures remain in the evidence.

This is a desktop viewport test with synthetic reports, not actual efsn telemetry,
a production PostgreSQL database, TLS proxy or an independent producer. It does
not close per-node freshness, chain-agreement or ticket-health requirements.
The headless browsers and local fixture are stopped; no signing keys were used.

## Next work

Continue with collector input/resource limits and trustworthy per-node report
freshness, then actual efsn/RPC comparison. Finish production dependencies/runtime,
supervision and combined storage/browser/TLS acceptance before public use. G6
remains open. No historical replay or large restore was started in this step.

The [evidence bundle](evidence/restart-dashboard-build-2026-10-03/README.md) contains
the exact local candidate, portable patch, source/build hashes, test outputs,
browser traces and screenshots. Nothing was pushed, deployed or signed.
