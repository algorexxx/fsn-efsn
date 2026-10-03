# Preserved historical inventory evidence — 3 October 2026

Baseline `c4255a21`. Only the Linux investigation test and documentation changed.
The source is the previously verified, closed LevelDB copy at
`/home/rehearsal/data/efsn/chaindata` in `FusionRehearsal` on D:.

`attempt-1` contains nine fresh-process probes. `attempt-2` adds three heights
between the shutdown checkpoints after source inspection showed that successful
head/head−1/head−127 reads do not establish a complete recent-state window.
All twelve tests passed. Both attempts retain their exact shell runner, binary
digest, source digests, compiler diagnostics, per-height results, timings,
resource measurements, isolation records and source metadata comparison.

The existing Fusion API method is exercised with an explicit-height read-only
test backend. There is no running node or RPC transport. The probe verifies the
ticket blob against its header commitment and the head against the saved gateway
response. The first ticket lookup runs with an empty process ticket cache;
operating-system disk caches are not cleared. Each process measures backup-wallet,
donation-wallet and repeated backup-wallet reads in that order.

`verify.py` checks all results and source hashes, compares the saved head fields
and inventories, checks error-versus-empty behavior, and produces `checks.json`.
Its initial header assertion compared a header to the entire saved block response;
the four extra block fields (`size`, `totalDifficulty`, `transactions`, `uncles`)
made that assertion fail. Every actual header field already matched. The verifier
now compares the saved header projection; neither the probe nor its result changed.

Repeat only with an unused attempt name; the runner refuses existing outputs and
retains the executable in Linux `/tmp`. Optional trailing arguments select up to
16 explicit preserved heights. Dependency downloads are disabled.

```powershell
wsl -d FusionRehearsal -u root -- unshare --mount --net --propagation private -- bash /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-observer-preserved-inventory-2026-10-03/run-linux.sh attempt-3
```

The backup mount is read-only and the network namespace has only a down loopback
interface. No keys, mining, restore, replay or full content rehash are involved.
Source metadata covers names, sizes and modification times, using the existing
snapshot packager's inventory helper. The successful read timings exclude startup
and serialization; peak RSS is for the whole process. See the
[report](../../restart-observer-preserved-inventory.md) for the availability table,
launch baseline-preservation procedure and limits.
