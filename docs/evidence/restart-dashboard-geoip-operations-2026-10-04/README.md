# GeoIP operations evidence

Read [the investigation report](../../restart-dashboard-geoip-operations.md)
before using this evidence. These are isolated synthetic fixtures, not production
update scripts or a live provider test.

`source-baseline.json` captures the clean dashboard commit and source hashes.
`run-3` is the accepted ten-case updater run; `switch-1` is the accepted lookup,
selection and rollback run. `verification.json` independently checks their
outcomes, preserved code/package bytes, original checkout and stopped processes.

Early harness attempts are retained and are not counted as acceptance:

- Attempt 1 stopped before launching the updater because Linux Git could not
  resolve the Windows worktree's absolute Git-directory reference. Git metadata
  is now captured with Windows Git in `capture-baseline.py`.
- Attempt 2 used incorrect CSV filenames inside the synthetic ZIP. It stopped
  at the City-failure case because conversion could not find its Country input;
  the expected filenames were corrected to those read by the pinned updater.
  All launched child processes had stopped. `run-2` retains the outputs.

To reproduce in the existing local fixture layout, capture the baseline before
editing any dashboard files, then run `run.py` with a new numeric attempt ID
under WSL `FusionRehearsal` as `rehearsal`. It requires the cached Linux Node
24.21.0 runtime and installed dashboard packages. Each output/scratch directory
must be new; it refuses reuse. `switch.py` explicitly targets the accepted
attempt 3 and a new `switch-1` output directory, so adapt those fixture paths for
another run. No real account key or public connection is needed.

The preload mock blocks connections and serves tiny generated ZIP/checksum
responses. Python produces the expected binary data independently using stated
synthetic locations and documentation address ranges. The scripts never select
the installed package data as a write target. `verify.py` runs from Windows and
uses WSL only for a read-only process check.

`lookup.cjs` gained its optional long-running mode after the updater run, for the
switch test; its one-shot path performs the same lookups and mapping. No product
source was edited. Dataset files and archives remain only in ignored scratch;
the committed inputs record generation code, hashes and expected binary bytes.
