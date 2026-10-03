# Dashboard browser freshness and build investigation

3 October 2026. Dashboard commit `c74d6036a080d17b9ac371dd23635b282c5f3edc` follows snapshot/storage commit `a2e9f1b`.
**110 contracts and six React DOM tests pass. The production build remains
blocked by inherited webpack 4.41.0 on Node 22.11.0.** This is a dashboard-only
change; no node consensus, recovery sequence or P1–P16 patch changed.

## Confirmed problems and correction

The inherited UI stopped polling after an HTTP error or empty response. Node and
geographic data accumulated through mutable arrays, summary values survived
replacement snapshots, software-version strings influenced the highest block,
and an average block time of 12.99 was hardcoded. A failed API request could leave
old values displayed indefinitely.

The replacement polling helper has one pending request, a request deadline and
one scheduled retry. Failure or expiry clears current rows, map points and
summary values. Late callbacks from canceled requests cannot replace newer data.
Unmounting cancels work; returning to a visible tab invalidates its old view and
requests a new snapshot. Successful responses replace the complete displayed
snapshot, including legitimate empty results, instead of merging old nodes.

The API adds `X-Dashboard-Valid-For-Ms` alongside its existing observation timestamp
and no-store header. The browser subtracts elapsed request time from this server
freshness budget and schedules expiry independently of the next poll. It does
not require the user's wall clock to match the server. API and browser must be
released together, and the proxy must retain these headers and avoid caching.

Two explicit public build settings control polling interval and request timeout.
Both require positive integer milliseconds, with no production defaults. The
existing same-origin API path remains required. The checked local profile uses
100 ms between requests and a 50 ms deadline; these are test values only.

The UI distinguishes loading, empty, received and unavailable/expired data. The
last successfully displayed observation remains labeled **Last snapshot** after
failure. Valid zero values stay zero, including height zero. Unknown receive
times show a dash instead of a permanent spinner. The hardcoded average is gone;
no calculated average is claimed yet.

Summaries use a connected node reporting the highest height, with ID ordering for
ties. Disconnected higher reports do not drive those summaries. The count shows
connected versus total reported nodes. Full hashes remain intact and are only
shortened for presentation. These labels do not establish canonical chain
agreement, recent reports from each node or successful staking.

## Validation and limits

- **110 contracts passed:** the retained authentication, configuration, writer
  and API checks plus 11 browser polling/projection scenarios. Coverage includes
  retries, empty replacement, decreasing heights, zeroes, malformed metadata,
  mixed timestamps, timeout cancellation, late callbacks, visibility refresh,
  synchronous adapter failure and expiry while a later request is pending.
- **Six actual React DOM tests passed:** loading to populated to empty; API error
  to automatic recovery; expiry during a pending request and unmount cancellation;
  timeout/malformed response recovery; visible-tab refresh; zero height and
  unavailable receive time. These render the real component in JSDOM with a
  controlled Axios adapter and monotonic clock.
- The API tests exercise the freshness header over real loopback HTTP, including
  the exact server age boundary. A zero remaining budget is conservatively
  unavailable in the browser.

The final React run has no DOM/act warnings; an inherited `punycode` deprecation
remains. Earlier exploratory outputs are retained, including corrected DOM/test
warnings and the version before the final zero-display review. Final source hashes
are matched to the local dashboard commit and portable patch in the evidence.

These are not tests in a compiled browser, against actual efsn telemetry, through
PostgreSQL, or through a TLS proxy. Previous real storage acceptance remains
separate evidence. Browser timer throttling/process suspension can delay UI work;
the visible-tab refresh prevents deliberately retaining the prior snapshot when
the visibility event runs. Per-node report timestamps and stale labels still
need collector work; a fresh collector snapshot alone cannot supply them.

## Reproduced build blocker

The unchanged frontend lock installed 1603 packages with lifecycle scripts
disabled. The local `npm.cmd` wrapper reports 6.14.15; the separately queried
bundled npm CLI is 10.9.0. Final tests/build invoke Node directly. Installed
versions include React/React DOM 16.10.2, react-scripts 3.2.0, webpack 4.41.0,
Axios 0.21.2 and Jest 24.9.0.

Both the inherited and modified production builds fail with
`ERR_OSSL_EVP_UNSUPPORTED` in webpack's hashing path on Node 22.11.0. No dependency
lock changed, `NODE_OPTIONS` was unset, and no crypto compatibility switch,
dependency-file edit or runtime downgrade was applied. The build is **failed**,
not verified or ready to publish. This turn used no database service or large
chain restore/replay workload.

Next, make a separately reviewed build-tool/runtime correction, obtain a full
production build and test the compiled UI in a browser. Then finish collector
input/resource limits and per-node freshness, real efsn/RPC comparisons, runtime
dependency review, supervision and TLS/proxy acceptance. G6 remains open.

See the [evidence bundle](evidence/restart-dashboard-browser-2026-10-03/README.md)
for the exact candidate commit, patch, commands, hashes and saved failures.
Nothing was pushed, deployed or signed.
