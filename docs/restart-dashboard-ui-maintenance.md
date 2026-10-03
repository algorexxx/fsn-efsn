# Dashboard UI maintenance and saved-pin recovery

Local evidence date: 2026-10-04. The UI review found and fixed a dashboard
availability defect in saved pin preferences. No dependencies, backend code,
schema or efsn sources change. The legacy UI dependency decisions below remain
separate from this small reliability correction and from launch approval.

## Reproduced defect and correction

The previous component parsed `localStorage.pinnedNodes` during every render,
assumed the result was an array and wrote storage directly in click handlers.
Malformed JSON or a denied storage getter threw during the initial render.
A valid JSON object instead of an array also prevented node rows from rendering.
The old compiled build reproduces all three failures against the same healthy
local API. The object case does not emit a browser `pageerror`; missing rows are
the observed failure, not an inferred error-event count.

The new storage boundary reads once when the component is created. Missing,
unreadable, malformed or non-array data becomes an empty pin list. Mixed arrays
keep unique nonempty string IDs. Existing valid lists and the `pinnedNodes` key
remain compatible. Invalid storage is not rewritten merely by loading the page.

The component keeps pin selection in React state. Pin/unpin changes update the
page even when saving throws, and a status message explains that those changes
will last only until reload. A successful write clears that message. Clearing
the final pin also disables the hide-unpinned filter, preventing an accidentally
empty table. Saved changes survive reload; other open tabs pick up persisted
changes when reloaded. No cross-tab synchronization guarantee is introduced.
Pins are viewing preferences, not node identity, enrollment or consensus state.

## Acceptance

The unchanged eight React DOM tests and fourteen new storage-boundary tests
pass on Linux Node 24.21.0 with the accepted Jest/Rsbuild toolchain. Lint reports
zero warnings/errors. The production build passes; its scratch output location
produces Rsbuild's existing warning that it will not automatically empty a
directory outside the frontend root. That directory was new and the prior
active build was retained before activation.

Seven compiled Edge scenarios pass: malformed JSON, an object in place of the
list, denied storage access, no saved value, mixed/duplicate entries, a full
storage quota and a valid existing pin. All display both expected node rows,
permit pin/unpin and have no page errors or foreign-origin requests. The normal
storage case also verifies reload persistence and clearing the final pin while
the hide-unpinned filter is active. The temporary-save notice was inspected.

The existing nine compiled-browser checkpoints pass, including map, snapshot
expiry, timeout and recovery. Two deliberate hanging API requests correspond
to two aborted requests in the fixture ledger; no other request failure or
missing asset appears. Native efsn -> WSS/nginx -> PostgreSQL -> HTTPS API ->
browser also passes all four checkpoints, with the actual head and fifty-block
history matching, plus writer expiry and recovery over TLS 1.3.

The build still contains 546 files; 540 retain their previous bytes. Source maps
include the new storage helper and exclude its tests. All manifests/locks,
backend code and 1007 efsn source/module hashes are unchanged. The backend
contract/socket suites and advisory audit from the prior accepted slice were
not repeated for this browser-only change. Their results are retained, not
claimed as new runs. Test services are stopped and disposable credentials removed.

## Used-library review

The official npm registry versions, dates, deprecation notices and peer ranges
are captured in `ui-package-review.json`. A latest tag is not proof of support
or security, and a newer version is not automatically a compatible replacement.
The preceding locked-tree audit reports zero known advisories; it does not
resolve these maintenance decisions.

| Used package | Installed | Current latest tag | Disposition for this candidate |
| --- | --- | --- | --- |
| React / React DOM | 16.10.2 | 19.3.0 | Retain for this fix; major migration requires coordinated wrapper/test changes. React 16.14.0 is a possible compatibility step, not a substitute for a maintenance decision. |
| Material UI core | 4.5.1 | 4.12.4 under the old package name | Only Tooltips are imported. The old family is deprecated; upgrading within it does not restore active development. Evaluate a maintained tooltip replacement or the current MUI package as a separate change. |
| React Bootstrap | 1.6.8 | 2.10.10 | Retain the tested modal/layout pairing with the existing Bootstrap 4 theme. The current line targets Bootstrap 5 and needs CSS/modal regression acceptance. |
| React DataMaps | 0.4.1 | 0.4.1 | Its published React peer range ends at 16. This is a concrete blocker for a supported modern React pairing, not something to bypass with forced peer installation. |
| React country flag | 1.1.0 | 3.1.0 | A separately testable major upgrade; preserve the local flag URLs and verify unknown-country behavior. |
| React number format | 4.3.0 | 5.4.5 | A separately testable major upgrade; preserve zero/unavailable values and formatting. |
| React timeago | 4.4.0 | 8.3.0 | A separately testable major upgrade; preserve receipt-based age text and custom formatting. |
| prop-types | 15.8.1 | 15.8.1 | No version gap in the captured latest tag. |
| Axios | 0.34.0 | 1.20.0 | Retain the previously reviewed 0.x choice and tested cancellation contract. A major/API migration is not part of this fix. |

[React's version archive](https://react.dev/versions) distinguishes the current
19.3 documentation from legacy 16 documentation. The
[React Bootstrap migration guide](https://react-bootstrap.github.io/docs/migrating/)
describes its Bootstrap 5 transition. The
[DataMaps wrapper's upstream repository](https://github.com/btmills/react-datamaps)
and published package identify the legacy React pairing. The current
`@mui/material` registry tag is 9.4.0 and requires React 17, 18 or 19; the old
`@material-ui/core` tag must not be mistaken for the maintained successor.

The map's installed transitive versions are DataMaps 0.4.4, D3 3.5.17 and
TopoJSON 1.6.27. The captured latest tags are 0.5.10, 7.9.0 and 3.0.2 respectively;
the existing wrapper's ranges do not provide a drop-in modern map stack.
The map's bubble tooltip constructs HTML from its name. The current name is the
collector-authenticated, character-restricted node ID, not arbitrary node text.
Preserve that boundary or use text-safe rendering when replacing the wrapper.
This source review is not a general security assessment of the map libraries.

Do not label the entire UI stack maintained, or silently waive its release
review. The bounded choices are a coordinated map/tooltip/React migration with
acceptance, or an explicit documented decision about the pinned legacy stack
at the final release review. No such risk acceptance has been granted here.

## Remaining work

Continue GeoIP dataset staging/update failure and recovery checks, then service
supervision, retry/log lifecycle and public certificate renewal. The GeoIP
account/source and actual public host remain unselected. No public download,
update job or deployment was performed.

The browser evidence currently covers desktop Edge. Record the intended support
matrix and test its actual browsers/devices before advertising that coverage;
Browserslist targets are compilation settings, not cross-browser acceptance.
The two remaining lint coverage differences from the toolchain report also
remain named review limitations. The [restart plan](restart-plan.md) owns these
release gates.

Evidence and the portable dashboard patch are retained under
`docs/evidence/restart-dashboard-pins-2026-10-04/`.
