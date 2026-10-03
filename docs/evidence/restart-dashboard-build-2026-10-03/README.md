# Dashboard build evidence — 3 October 2026

The [report](../../restart-dashboard-build.md) explains the final change and its
limits. `commit.json` identifies the dashboard candidate and parent; the patch
preserves that exact commit. `checks.json` records the verifier's conclusions.

## Exact runs

- `resolve.*`, `install.*`: direct npm CLI 10.9.0 resolution and clean installation
  of react-scripts 5.0.1, with lifecycle scripts disabled and normal peer checks.
- `react-scripts-registry.txt`: raw official registry metadata with the npm update
  notice interleaved; retained as text, not parsed as JSON.
- `react-overlays-versions.json`, `react-bootstrap-versions.json`: registry checks
  used to select the stable Bootstrap 4-family modal correction.
- `modal-install.*`: targeted React Bootstrap 1.6.8 installation and lock update.
- `dependency-delta.json`: direct versions before/after and resolved lock changes.
- `attempt-1`: 110 contracts and six DOM tests pass; strict build fails on the two
  inherited pin-link warnings. Its original `Main.js` is retained.
- `attempt-2`: those controls corrected; 110/six/strict build pass. Manifests,
  lock, Main and DOM test source are retained before the modal update.
- `attempt-3`: stable modal and accessibility regression; 110/seven/strict build
  pass, but test stdout exposes the old delayed-render cleanup warning. The
  affected Delay and DOM test sources are retained.
- **`attempt-4`**: final 110 contracts, seven DOM tests and strict build pass;
  source and built-asset SHA-256 manifests identify the tested result.

`run.py` records commands, settings and outputs. Tests use the existing 100/50 ms
profile; the compiled browser uses 250/1000 ms. All are local test settings.
Do not overwrite this historical bundle when reproducing; use a new directory.

## Browser evidence

`browser-check.cjs` uses bundled Playwright and an isolated headless Edge profile.
`serve.py` starts the committed loopback-only fixture using direct log files;
`set-browser-scenario.py` changes only its synthetic input and records the sequence.
These scripts contain no credentials and require no database or efsn process.

- `browser-result.json` and the three root PNGs describe the final passing run,
  including two actual map marker elements, nine checkpoints and network outcomes.
- `modal-controls.json` records the final accessible button ancestry.
- `browser-process.json` records exit zero; `browser.stdout.txt` confirms fixture
  shutdown and counts all final synthetic storage modes. Its stderr is empty.
- `browser-attempt-1`: harness assertion initially missed CSS uppercasing.
- `browser-attempt-2`: the actual hidden-modal failure and screenshot.
- `browser-attempt-3`: DOM ancestry confirms the visible dialog had
  `aria-hidden=true` before the modal-library correction.
- `browser-attempt-4`: first passing final-build run, before adding the explicit
  two-marker assertion prompted by screenshot review. The last root run repeats
  the same scenarios with that added assertion.
- `browser-server.*`: initial launch/clean stop before browser activity; PowerShell
  buffered the ready line, so subsequent launches used `serve.py` file handles.
- `browser-scenarios.jsonl`: complete synthetic control sequence, including stops.

The in-app browser initialization failure is described in the report. Screenshots
are local synthetic data. The final bundle/build hash comparison, original
checkout checks, source/commit agreement and stopped listener are verified by
`verify.py`. This remains separate from real-node, PostgreSQL/TLS and production
dependency acceptance. No public infrastructure was changed.
