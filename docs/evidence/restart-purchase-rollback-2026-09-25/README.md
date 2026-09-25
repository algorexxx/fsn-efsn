# Nonce rollback and competing-miner evidence

25 September 2026, production baseline `bcbd1ce`. See the
[investigation](../../restart-purchase-nonce-rollback.md) for the manual-repair
boundary and synthetic-fixture limitations.

Final results:

- `linux-competing-race.txt`: real workers for two distinct public wallets
  produce competing branches, converge and continue buying; PASS, 98.37 seconds,
  after the P9 parent-context correction. `run-competing-linux.sh` rebuilds and
  runs this case with Linux race detection.
- `../restart-parent-isolation-2026-09-25/linux-node-regressions-race.txt`:
  post-P9 two-purchase rollback, cold nonce-gap pause and explicit original-byte
  repair; PASS, 49.95 seconds within the five-case actual-node group.

Earlier results are retained rather than represented as final evidence:

- `initial-passing-competing.txt`: PASS, 77.65 seconds. A later repetition
  exposed a race, so this initial pass did not establish isolation.
- `pre-fix-competing-race.txt`: FAIL, 84.37 seconds, including two `DATA RACE`
  reports from the shared DaTong parent context despite successful convergence.
- `initial-passing-rollback.txt`, `linux-rollback-race.txt` and
  `pre-fix-rollback-race.txt`: earlier rollback passes before P9.
- `initial-*-failure.txt` and `initial-competing-start-timeout.txt`: fixture
  preparation, sparse-history ancestor-search and miner-readiness failures
  described in the report. They are not production-chain failures.

`check-linux.sh` is the earlier build/rollback command. The historical
`check-final-rollback-linux.sh` wrote `linux-rollback-final-race.txt`, subsequently
retained as `pre-fix-rollback-race.txt`; despite its original name, that run was
before P9. The final rollback result is the cross-linked actual-node group.

Final source and binary identities, automated log checks and checksum generation
are in `../restart-parent-isolation-2026-09-25/identities.json` and
`write-identities.py`. Each folder's `SHA256SUMS` preserves all retained evidence
bytes. Build outputs can be empty on success. Initial preparation failures are
kept for transparency, not claimed to match the final fixture source exactly.

Both owners receive one million synthetic FSN and explicit public-key tickets;
this isolates nonce/concurrency behavior and is not real launch funding proof.
Real peer sockets stay inside a loopback-only Linux network namespace. The test
requires another eligible producer to mine nonce repairs and does not prove
recovery when every available wallet lacks tickets. No original backup, real
key, public peer, complete-state dataset or network-drive restore was accessed.
