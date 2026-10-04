# Observer history-check acceptance

Declared before execution. Add a service-neutral offline check for durable
collection freshness, logical headroom and unresolved incidents. Use existing
history status and the existing external observer command. No alert provider,
new daemon, persisted health cache, automatic response or node change.

Required checks:

- No report, expiry at the configured age, low logical headroom and future
  history timestamps require attention. Exact headroom equality is accepted;
  age equality is expired. No production thresholds are supplied.
- Fresh review/backfill activity must not refresh the last collection time.
  Acknowledged, no-longer-observed or unknown unresolved incidents remain open
  for this check. Resolved incidents do not trigger that condition.
- A failed oversized append does not advance collection freshness; checking
  the old history raises attention and leaves the evidence unchanged.
- The CLI writes JSON and returns nonzero for a triggered check, zero only
  when these specific checks are clear, and nonzero for invalid/unavailable
  input or output failure. Existing history-status success semantics stay intact.
- A real built command is exercised against missing, fresh, expired and locked
  local histories. No endpoint is contacted by the check. Repeated checks do not
  append events or change exported evidence.
- Windows observer/CLI suites and build, plus Linux race suites and build,
  pass against recorded source hashes with cached dependencies only.

The user's preference is to reuse an existing monitoring service if available.
This bundle does not select or configure that service and sends no messages.
Actual delivery, external check/host-loss detection, notification acknowledgement,
production sizing/thresholds and end-to-end response drills remain open.

## Results

Baseline: `b83786ebd7ad561f7081546eda5160d52f70651b`.
Both platforms passed on attempt 1, using Go 1.21.3 and cached dependencies
with downloads disabled. Windows ran outside the restricted sandbox because
the existing capacity-copy tests require source-path resolution unavailable
inside that sandbox. Linux ran in a namespace with loopback as its only link.

| Check | Result |
| --- | --- |
| Windows observer / CLI suites | Pass, 10.337 s / 5.784 s |
| Linux race observer / CLI suites | Pass, 23.501 s / 2.403 s |
| Windows / Linux standalone command builds | Both pass; binary hashes retained |
| Command invocations retained per platform | 24 in-process plus 24 through the real executable |
| Fixed-clock boundary, unresolved-state and invalid-bound cases | Pass |
| Oversized append followed by a fresh review | Old collection remains stale, incident remains unresolved; pass |
| Missing, locked and stale history; invalid combinations; output failure | Nonzero; pass |
| Exports before/after checks | Byte-identical |

The existing Windows directory-symlink case is skipped for unavailable OS
privilege; its Linux counterpart passes. Optional larger history measurement
tests are not rerun for this change; the history storage/copy implementation
did not change. No node database, key, large restore or live notification route
is used by these checks. The command fixture has a retired synthetic node, not
a live producer; a zero exit only establishes the declared history conditions.

`verify.py` verifies tested source hashes, suite/build exits, required passes,
the loopback-only namespace and all captured command results. Only
`cmd/fsn-observe/main.go` changed among 1,011 pre-existing source/module files;
the remaining 1,010 are byte-identical. The new evaluator and tests are confined
to the observer packages. `verification.json` records those results and the
remaining external-delivery limits.
