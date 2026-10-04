# Bounded compatible-reorganization storage measurement

4 October 2026. Declared before execution. No node-runtime changes, real keys,
public networking or backup/replay database access.

## Cases and limits

| Old suffix | Replacement suffix | Replacement difficulty per block | Completion cases |
| --- | --- | --- | --- |
| 1,024 | 1,025 | 1 | Clean switch and fresh-process verification |
| 1,024 | 512 | 3 | Clean shorter/heavier switch and fresh-process verification |
| 4,096 | 4,097 | 1 | Clean switch and fresh-process verification |
| 4,096 | 2,048 | 3 | Clean switch, process exit before canonical batch, process exit after canonical batch; separate verification for each |

The old branch has difficulty 1 per block; both branches share the same fixed
test anchor and initial cumulative difficulty. Every block contains 32 unsigned
synthetic transactions with 256-byte data, each with one 64-byte receipt log.
Eight transactions per overlapping height are shared between branches. This
exercises both removal of orphaned lookups and retention of shared lookups. All
stored transaction/receipt commitments are constructed coherently. State is
reused: no seal validity, native execution or economic accounting is claimed.

The preparation process stores both candidate suffixes and closes LevelDB.
A fresh writer opens the original canonical branch with P1 enabled, checks that
the replacement is strictly heavier, then invokes the production
`WriteBlockWithState` path. The measurement covers the resulting ordinary P5
canonical switch and its surrounding write, not consensus validation or branch
execution. No test-only production hook or reorganization limit is introduced.

Declared resource acceptance:

- At most 512 MiB of closed fixture files per case.
- At most 120 seconds for the measured write/switch, or to reach its requested
  interruption boundary. Each complete child has a separate 200-second timeout.
- At the canonical batch write, at most 64 MiB summed key/value payload,
  1 GiB Go live heap and 1.5 GiB Go-accounted system memory.
- Exactly one batch containing the multi-block canonical replacement and all
  three head markers. This also covers canonical suffix deletions for the
  shorter replacement and old-only transaction lookup deletion.

The wrapper reports both summed key/value bytes and the database `ValueSize`
counter: the latter excludes keys for puts and includes keys for deletes, so it
is not encoded batch size. Neither includes all backend overhead. Heap is
sampled with the complete batch staged, not a continuous peak. External command
resource accounting and cumulative allocation are retained separately.

## Required integrity result

The interruption exits only with code 86 at the requested actual LevelDB batch
API boundary, skipping defers. A fresh process must see the complete old branch
before the batch, or the complete new branch after it, with all three persisted
and loaded heads agreeing and no startup rewind. This does not simulate torn
LevelDB writes, power loss or fsync durability.

Verification walks both stored branches back to the anchor, checks every
canonical index and obsolete suffix entry, every transaction's canonical lookup,
and every stored transaction/receipt commitment, bloom, receipt identity and log
removal flag. Shared and branch-specific transaction/receipt resolution is also
checked at the first/last positions of each canonical block. Available state and
anchor readiness must survive reopening. This is a storage oracle, not an
independent execution oracle for the synthetic bodies.

The tests reuse the existing fixture, key classifier, state-export JSON helper
and error assertions. Their efficient verifier decodes receipts once per block
for complete commitments/index checks; per-transaction body/receipt resolution
in the earlier small-chain helper would repeat a full block decode 32 times.

## Execution

```text
wsl.exe -d FusionRehearsal -u root -- unshare --net bash /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-reorg-cost-2026-10-04/run-linux.sh attempt-1
```

The runner uses the existing offline Linux Go toolchain, with disposable ext4
fixtures and a private network namespace. The test skips without
`FUSION_RESTART_REORG_COST=1`. Each attempt captures its exact test sources as
`.go.txt`, source/binary identities, declared scope, logs, exits and capacity.
Existing attempt paths are refused. Results remain pending until verified.
