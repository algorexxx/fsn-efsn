# Automatic purchases: storage errors and peer reorganizations

25 September 2026, baseline `c62d8cd`. This extends the
[purchase controller](restart-purchase-controller.md) and
[process-interruption rehearsal](restart-purchase-crash-rehearsal.md).
The additions are tests, documentation and evidence. Production code and the
eight-item [node patch inventory](restart-node-patch-review.md) are unchanged.

## Storage errors

Eight child-process cases use the real controller, LevelDB, transaction pool,
gas estimator and an encrypted public-scalar-1 keystore. A test database wrapper
returns errors only for that account's local automatic-purchase record.

| Injected failure | Required behavior |
| --- | --- |
| New record `Put`, before writing | No record or submission. Persistent failure prevents submission across a retry interval; recovery buys at the still-unconsumed canonical nonce. |
| New record `Put`, after writing | Report the error without submitting in that attempt. With the wallet subsequently locked, recover the exact saved bytes. |
| Adopting an existing pool purchase, before/after `Put` | Preserve the existing pool transaction; finish adoption with the wallet locked, without another submission. |
| Retiring a confirmed purchase, before `Delete` | Keep its record and stop before signing/submitting its successor. When storage recovers, retire it and submit at the canonical next nonce. |
| Retiring a confirmed purchase, after `Delete` | The record is already absent despite the error. Recovery proceeds at the canonical next nonce without resubmitting the consumed transaction. |
| Record `Has` / `Get` | Stop on read failure. When reads recover, submit the exact previously retained purchase with the wallet locked. |

Each case checks the record immediately after the failed attempt, then the
recovered nonce, bytes and exactly one pool entry. Persistent pre-operation/read
faults remain enabled through another retry interval. Recovery is observed for
a further interval without additional submission or canonical-head movement.

All eight cases pass on Windows (80.12 seconds) and Linux with race detection
(97.61 seconds). The initial Windows run exposed a test warning queue left over
from fixture preparation; consuming that expected setup warning fixed the test.
No controller defect was reproduced by these cases.

The post-delete-error case also demonstrates a monitoring limitation: the
confirmation log is emitted after a successful return from `Delete`. If deletion
takes effect but returns an error, the next attempt sees no record, and that
confirmation line is never emitted. Canonical receipts remain authoritative.
The test expects zero such lines in this case and one after a pre-delete failure
is resolved. This is not a loss of the canonical transaction or ticket.

These are errors at the database interface, including uncertain write outcomes.
They do not emulate a full disk, a permanently poisoned LevelDB instance, a torn
write, or loss of machine power. Normal record writes still lack an additional
synchronous-flush guarantee. Failed pre-write attempts may sign again after
recovery because no intent was saved or submitted; retained intents must keep
their exact bytes.

## Compatible forks arriving from a peer

The Linux harness uses separate actual node services, LevelDB databases, devp2p
connections and the full downloader inside a network namespace containing only
loopback. Both nodes enforce the same synthetic anchor. The heavier branch
diverges strictly after that anchor, where ordinary fork choice is intended to
remain available.

The starting local database contains a canonical purchase and its saved signed
record, explicitly seeded by the fixture. The actual controller retires that
record and creates its next-nonce purchase. The peer then supplies a heavier
branch in one of two arrangements:

1. The original purchase appears in a different block; its receipt must move to
   that canonical block. Another peer purchase consumes the pending successor's
   nonce.
2. A transfer replaces the original purchase at its nonce. Subsequent native
   purchases keep the peer chain producing and consume the successor's nonce.
   Neither displaced local transaction may retain a canonical receipt.

The controller must reconcile canonical nonce consumption without falsely
confirming its displaced successor, then retain one current-nonce purchase.
The checks compare canonical and persisted heads, state/ticket roots, receipt
lookups, pool contents, saved bytes and confirmation/submission logs. A clean
process restart with pool journaling disabled must restore the exact saved
purchase into an initially empty pool. Both the first recovery and cold restart
are observed across a complete retry interval.

Both final peer cases pass with race detection (44.81 seconds together). The
initial peer attempt stopped before IPC startup because the mounted Windows
temporary path exceeded Linux's Unix-socket path limit. The passing run uses
short, disposable Linux temporary paths and adds explicit log-count and
initially-empty-pool assertions.

The production miner is enabled so the real controller's mining gate applies.
A test-only block signer deliberately refuses signatures to prevent local
block production from racing the controlled fork. Transaction signing uses the
real encrypted test keystore. This exercises actual network fork import and
purchase reconciliation, not competing live block producers. The fixture is
sparse and gives other owners perpetual test-ticket intervals; missing historical
bodies cause an expected bloom-index warning. No original backup or real key is
used.
Both constructed branches deliberately use the same public fixture signer;
the resulting multiple-mining report messages are expected test behavior, not
permission to run competing real-key copies.

## Remaining boundaries

This does not introduce ongoing finality. A prior confirmation can still be
invalidated by a compatible post-anchor reorganization. The fixed anchor's
protection against incompatible old history has separate
[peer evidence](restart-node-rehearsal.md).

The later [nonce rollback and competing-miner investigation](restart-purchase-nonce-rollback.md)
adds a two-purchase rollback through an actual peer, cold/manual nonce repair,
and distinct real miners rejoining and continuing. It confirms that a nonce gap
can require operator intervention. More fork depths and reinjection orders,
exact concurrent receipt-read/record-retirement cuts, expired or underpriced
retained purchases, broader storage corruption and real key custody still need
their own review or explicit operational decisions.

Commands and raw results are retained in
[`restart-purchase-storage-2026-09-25`](evidence/restart-purchase-storage-2026-09-25).
Independent review of P4 remains a release requirement.
