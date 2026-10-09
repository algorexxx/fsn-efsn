# Prepared candidate replay to 4,500,000 — not launched

The [configuration](inputs/config.json) and [specification](inputs/spec.md) define
the next justified 900,000-block interval, with the identical replay executable,
unchanged controller and separate recovery checkpoint. Only the endpoint observer
literal and declared target-size allowance change. No writer is running for this
job. A prepared input manifest is not runtime evidence.

The [capacity preflight](preflight-refused-2026-10-09.json) records why dispatch was
refused: D: is below the unchanged 60 GiB starting floor. Previous completion and
endpoint verification pass; no node/replay/observer process is active. The check
only measures closed-target allocation and free space; it does not open or hash
a live database, remove data, compact disks or launch a process that writes history.

The user must resolve host capacity or explicitly approve a concrete alternate
storage procedure. W: can preserve verified cold copies, but copying alone does
not free host D: space; do not infer approval for deletion or disk compaction.
Freeing at least 10 GiB on D: would give useful margin over the observed floor
deficit, subject to a fresh check. Preserve this refused preflight.

After capacity changes, rerun capacity_preflight.py with a new output filename.
Fresh success is required before dispatch; the launch repeats capacity, prior
result, executable/source identity and complete cold-inventory checks. Use the
existing hidden Windows dispatcher only after those prerequisites are met.
Never launch a duplicate writer or change the release selection to make it run.
