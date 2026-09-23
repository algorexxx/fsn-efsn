# Synthetic historical bridge experiment — 23 September 2026

## Outcome

Candidate A in [the restart plan](restart-plan.md) now has executable evidence:
the unchanged client imports an eight-block synthetic bridge with ordinary ticket
purchases and refunds. A separate test reproduces the suspected missing-state
ticket reconstruction defect at its large timestamp jump. Candidate A is not yet
approved for launch or proven against the full recovered database.

The tests and reproducibility notes are in [tests/restart](../tests/restart/README.md).
No production Go code, dependency versions, live node settings, balances, or
private keys were changed. A checksum-verified portable Go 1.21.3 runtime was
placed in the ignored workspace temporary directory. The run used Windows amd64
and `CGO_ENABLED=0`; Linux/CGO behavior remains to be checked.

## What the fixture represents

It loads the saved RPC evidence, substitutes a public synthetic signer for the
investigated ticket owner, and creates a synthetic state at height 15,130,080.
The owner has the recorded two tickets, liquid balance, and time-lock intervals;
the other recorded tickets are included. Other owners' complete account states
and prior chain history are not reproduced. Ticket map ordering is made
deterministic for the fixture, not claimed to be the original storage ordering.

Consequently, these are tests of the mechanism under observed conditions. The
synthetic signer's selection rank and retreat counts are not predictions for the
real owner. The seed is deliberately not a mainnet-valid parent, so the public
test key's signatures cannot be used as real-parent double-signing evidence.

The producer and verifier use separate in-memory databases within one process.
Both import RLP-decoded blocks through `InsertChain`. This clears header selection
caches and executes validation/replay rather than trusting a miner's direct state
write. It is still not an independent implementation or separate-node rehearsal;
the runtime and the global ticket cache are shared. The fallback tests explicitly
evict that ticket cache.

## Observed sequence

The fixed jump timestamp is 23 September 2026 00:00:00 UTC. The initial long-lived
ticket end is 23 October 2026 00:00:00 UTC; subsequent purchases extend it as
necessary to preserve the minimum 30-day lifetime.

| Step | Synthetic height | Behavior | Tickets after block |
| ---: | ---: | --- | ---: |
| 1 | 15,130,081 | Historical timestamp; consume one old ticket; ordinary refund | 484 |
| 2 | 15,130,082 | Historical timestamp; consume the other old ticket; buy long-lived ticket | 480 |
| 3 | 15,130,083 | Jump to current time; consume long-lived ticket and buy replacement | 475 |
| 4 | 15,130,084 | First cleanup using a present-day parent timestamp | 1 |
| 5–8 | 15,130,085–88 | Ordinary replacement purchase, selection, and refund | 1 each |

After step 1, the executed time-lock balance provides exactly 5,000 FSN of
continuous coverage through the sampled long-ticket end. This matches the
previous independent interval arithmetic. Each block is accepted in both
databases, with the same committed state root.

The late cleanup is expected from current code: `Finalize` clears expired tickets
using **parent time**, so step 3 still retains other expired tickets. Step 4 has a
present-day parent and removes them. Selection/retreat also removes tickets along
the way. No expiry extension or free ticket allocation was added.

A replacement is necessary after cleanup: with a single parent ticket and no
purchase, `Finalize` rejects the block before consuming that last ticket. The
funding cycle works in these eight blocks, but no pool admission, purchase RPC,
auto-buy service, outage, or multi-operator behavior was established by that
initial run. The expanded purchase tests below now cover construction/admission.

## Confirmed reconstruction defect

With step 3's state root made unavailable through a test database wrapper and its
cached tickets evicted, the real `getAllTickets` fallback reconstructs tickets
from the previous available state, receipts, and snapshots. Its final cleanup
uses **step 3's own timestamp**, unlike the parent timestamp used when that
block's ticket commitment was created. The reconstructed list therefore loses
the other expired tickets too soon.

Result: `AddCachedTickets: hash mismatch`.

Repeating the same missing-state test after step 4 succeeds. This isolates a
specific mismatch at the large time jump, rather than a generic inability of the
fixture to reconstruct tickets. The test does not establish the frequency of
this defect on historical mainnet or prove an exploitable consensus split.

## Temporary parent-time experiment

An isolated Go compiler overlay substituted this candidate cleanup reference at
the end of `getAllTickets`, leaving the repository's production source untouched:

```go
cleanupParent, err := getParent(chain, header, nil)
if err != nil {
    return nil, err
}
tickets, err = tickets.ClearExpiredTickets(cleanupParent.Time)
```

For that experimental build only, the time-jump regression expected successful
reconstruction instead of the current error. All five tests passed, including
the eight-block import test and the post-cleanup reconstruction control. The
logged ticket counts and liquid balances were unchanged from the baseline run.

This is a candidate correction to reconstruction of an existing commitment, not
a change to block rewards, ticket purchases, finalization, or ongoing finality.
It remains unmerged. The expanded tests below add deeper missing-state and
synthetic expiry-boundary coverage; historical replay and platform testing remain
outstanding. Candidate B,
if later selected, would need its own explicitly consistent cleanup reference.

## Evidence and interpretation

- [Baseline test output](evidence/restart-2026-09-23/synthetic-bridge-tests.txt):
  five passing characterization tests; one intentionally confirms the defect.
- [Experimental overlay output](evidence/restart-2026-09-23/synthetic-bridge-parent-time-overlay-tests.txt):
  five passing tests with successful reconstruction required at the jump.
- [Original RPC evidence](evidence/restart-2026-09-23/metadata.json).
- [Expanded baseline output](evidence/restart-2026-09-23/synthetic-expanded-baseline-tests.txt).
- [Expanded parent-time overlay output](evidence/restart-2026-09-23/synthetic-expanded-parent-time-tests.txt).
- [Expanded run metadata and file hashes](evidence/restart-2026-09-23/synthetic-expanded-metadata.json).

An earlier test iteration stopped after step 4 because it reused a fixed ticket
end date even as start times advanced. The fixture was corrected to satisfy the
existing minimum lifetime; no production validation was relaxed. This is a useful
operational constraint for the eventual purchase automation.

## Expanded investigation: purchase admission and reconstruction

Both expanded runs passed nine top-level tests covering 21 cases. Some cases
intentionally reproduce defects, including the panic below. These are
characterization results, not a clean bill of health. The expanded run retained
Windows amd64, Go 1.21.3, CGO disabled, and unchanged production sources and
dependency versions. Additional existing pinned dependencies were downloaded
when importing the real purchase API.

### Purchase construction and admission

| Situation | RPC argument builder | Transaction pool | Execution/import |
| --- | --- | --- | --- |
| Long ticket before first historical refund | Rejects insufficient interval coverage | Accepts signed raw purchase | Execution rejects insufficient coverage |
| Same long ticket after first refund | Accepts | Accepts remote purchase | Imports and creates the expected ticket |
| Default purchase after first historical refund | Produces historical start and 30-day end | Rejects even as local: end is already past | Not needed to establish this admission failure |
| Present-day start while head is historical | Rejects start beyond head time + 3 hours | Rejects for the same reason | Not retested here |

The mismatch is explained by the actual checks: the pool measures funding from
`max(start, time.Now())`, whereas the RPC builder and execution use the historical
head/parent time. Future coverage is therefore not proof of continuous historical
coverage. A pool acknowledgement must not be used as proof that the first
purchase can execute.

The default interval after the fixture's first block is
`1759826750..1762418750` (October–November 2025). The long-purchase admission tests
use an explicit `TimeLockForever` end to avoid becoming stale in October 2026.
This does not recommend perpetual tickets for launch; the original eight-block
bridge still uses finite expiries. These tests run the real API argument builder
with an in-memory state backend, not HTTP RPC, account-manager signing, or gas
estimation. The pool's wall clock is unchanged and must be after November 2025.

Candidate A therefore needs an explicit historical start and a sufficiently
long end for both purchases while the parent is historical: the purchase in
step 2 and the replacement in step 3. Default auto-buy arguments do not provide
that end. The normal worker also obtains new-work timestamps from its wall
clock, so historical block construction still needs dedicated tooling.

### Deeper reconstruction and exact expiry

Ten missing-state cases cover steps 1–4 and every depth back to the seed state.
The unchanged code fails commitment verification at step 3 for depths 1, 2, and
3, and succeeds at steps 1, 2, and 4. The parent-time overlay reconstructs all ten
cases and preserves the prepared header, selected ticket, and retreat list.

Three additional cases alter other owners' lifetimes in synthetic seed state to
expire just before, at, or just after the first historical successor's timestamp.
The unchanged reconstruction fails when expiry is before or equal to that
timestamp, while finalization has correctly retained those tickets using the
earlier parent time. The overlay passes all three. This shows the mismatch can
also occur over a short interval crossing expiry; it does not require a year-long
jump. It does not establish which real historical blocks encountered the defect.

### Missing-ancestor panic

When the current state cannot be opened and the preceding header is unavailable,
`getAllTickets` assigns `nil` to `parent`, then tries to read `parent.Number` and
`parent.ParentHash` while formatting its error. The new test reproduces the
nil-pointer panic. No database was damaged to produce it; the test wrapper
returns the missing-header result.

The parent-time overlay leaves this defect in place. A separate small correction
should preserve the requested parent identity before lookup and return a clear
error if it is unavailable. It must not fabricate tickets or continue with a
different state. This result establishes an error-path defect, not a demonstrated
network-triggerable crash or a claim that the recovered database lacks headers.

### Automatic replenishment still needs an operational test

Follow-up: [the runtime investigation](restart-autobuy-experiment.md) now
reproduces empty-pool startup and submission-failure stalls with the real miner,
then verifies successful explicit retry and subsequent automatic replenishment.
The source analysis below records the concern that motivated that experiment.

Source tracing found one auto-buy notification producer, in the canonical-head
write path. `AutoBuyTicket` waits for notifications, skips work when not mining,
and ignores the returned purchase error. `StartAutoBuyTicket` sets the enable
flag without sending an initial purchase notification. No timer-based retry was
found in that loop. The miner's recommit timer builds work; it does not itself
request ticket purchases.

Together with the tested one-ticket/no-replacement rejection, this creates a
credible stall scenario: a purchase fails, the last available ticket cannot be
consumed without replacement, and no advancing head triggers another attempt.
A cold restart with an empty pool needs the same investigation. This conclusion
is a source-derived risk, not yet a complete running-node reproduction.

Rehearse initial purchase submission and recoverable failures at signing,
estimation, admission, and inclusion. A bounded retry/watchdog may be operational
tooling rather than a consensus edit, but it must observe actual ticket state,
respect nonce and per-owner purchase limits, and report failure. Independent
producers and adequate ticket runway remain necessary launch decisions.

## What this changes in the plan

- Candidate A warrants further investigation before adding ticket-rule exceptions.
- The reconstruction risk is now a reproduced defect, with a narrowly tested
  candidate correction, rather than a source-only suspicion.
- The first present-day block is not sufficient as the end of a verified recovery
  sequence; its cleanup successor and reconstruction behavior must be included.
- Automatic purchase and recovery from purchase failures are essential when only
  one live ticket survives. More independent producers remain a launch decision.

Next work: reproduce and resolve replenishment failure/cold-start behavior;
review the reconstruction correction and missing-ancestor error handling;
exercise real historical reconstruction and the intended Linux toolchain; then
prepare a controlled full-state rehearsal. The separate restart-anchor
implementation and heavier-branch rejection tests are still outstanding.
