# Observer against isolated node services

27 September 2026, baseline `8da6ce7`. The external observer passes eight
observations against two actual `node`/`eth` services using the normal RPC
implementations over IPC and HTTP. The observer and service processes were
built with Go 1.21.3 race detection; the successful service test took 13.93
seconds and reported no race. Both services shut down cleanly afterward.

This adds a Linux integration test and an opt-in HTTP listener to the existing
test harness. **No observer or node runtime source changes were needed.** The
candidate node patch list remains P1–P15. This closes a bounded service-interface
check, not the continuous monitoring or launch-readiness gates.

## Setup and independent expectations

[TestObserverNodeServices](../tests/restart/observer_services_linux_test.go)
uses the existing dense synthetic fixture. It independently executes the same
24-block history in two small disposable LevelDB databases, with a synthetic
devnet genesis and public test keys 1 and 2. No large backup is opened, restored
or copied. The fixture's large balances are artificial test funding and do not
establish any real operator's reserves.

Both nodes enforce the same synthetic anchor at block 24. Above it:

- The local branch includes a BuyTicket at wallet-one nonce 24 in block 25.
- The alternate branch includes a zero-value self-transfer at the same nonce in
  its different block 25, then an empty block 26. It has greater total difficulty.
- The observer tracks a common-prefix purchase at nonce 23, both conflicting
  nonce-24 transactions, and an initially unsubmitted signed purchase at nonce 26.

Before starting either service, the harness records the independently executed
headers, difficulty, canonical nonce, liquid balance, raw time locks and tickets.
The observer's IPC and HTTP outputs must match those records exactly. The HTTP
listener is bound only to loopback on an allocated port, with explicit
`eth,fsn,net,web3,txpool` modules. The child processes use the existing rehearsal
network ID `99032659`; this is not a production configuration.

Both services begin with ordinary mining and automatic buying disabled. The
initial observer role is maintenance and both endpoints monitor wallet one;
the second service's own coinbase remains public test wallet two. Zero peers is
expected initially. The harness then connects the services and explicitly asks
the existing downloader to synchronize the local node to the heavier branch.
It subsequently submits the public-test-key nonce-26 bytes to create a real
queued nonce gap. These are test-controller actions, separate from observer
invocations; this is not a new unattended mining or spontaneous convergence test.

## Observed results

| Observation | Result |
| --- | --- |
| IPC, initially separated branches | Stable identities/state; divergent hashes at common height 25, despite different tip heights 25/26. The purchase is canonical native success only on its branch; the alternate self-transfer is ordinary success only on its branch. |
| HTTP, same initial services | Same headers, difficulty, balances, raw locks, tickets and transaction diagnoses as IPC. Normal service responses required no adapter or observer correction. |
| IPC, after controlled synchronization | Both nodes agree at block 26. The formerly confirmed purchase is now absent; its nonce is consumed by the canonical self-transfer. The shared older purchase remains native success. |
| IPC, queued gap | Canonical nonce is 25; exact signed purchase 26 is queued on the receiving node, absent from receipts and diagnosed as ahead. Funding is available in this artificial fixture. Pool visibility is local and is not assumed to match the other node. |
| IPC, expected producer role | Disabled mining/auto-buy flags produce `disabled_observed`; configuring an expected role does not start anything. |
| IPC, intentionally wrong expected network ID | Identity mismatch makes comparison unavailable and tracked inclusion diagnoses unknown. |
| IPC, second service stopped | Unavailable endpoint and unknown state; no false agreement or zero-state diagnosis. |
| IPC, stopped service marked retired | No endpoint fault for the retired role, but comparison remains unavailable. |

For every invocation, the harness compares before/after head hashes and roots,
head markers, difficulty, mining/auto-buy flags, signature count, canonical
wallet nonce, durable saved purchase and transaction pool. All remained equal.
The observer's existing read-method allowlist is unchanged. Harness-only `lab_*`
calls provide the independent state check; the observer never uses them.

The current head after convergence is
`0x6e9010ff667835bc89ed8fb88352622e7381e4c809a02a0b5b61b5174dff36c8`
at block 26. Exact branch bytes, configuration, state comparisons and reports
are retained in [attempt 4](evidence/restart-observer-services-2026-09-27/attempt-4/services/).
The fixed expected identity in each config comes from the prepared fixture,
not from trusting the node being checked. The config paths and ports are
temporary test endpoints, not reusable launch instructions.

## Evidence and limits

The [evidence index](evidence/restart-observer-services-2026-09-27/README.md)
records commands, source/build identities, attempts and verification. Earlier
attempts retain a WSL Git ownership preflight stop, an unused test import and a
test-configuration rewrite error. None was an observer/runtime failure; the
first attempt reaching the actual services passed. No test failure was hidden
by changing its expected chain/account values.

The successful run used a private network namespace with only loopback. The
temporary databases and test keystores were cleaned by the existing fixture
cleanup, and a subsequent process check found no remaining service/observer
process. D: free bytes were unchanged across the passing run; no W: workload
was required. Build cache and evidence still consume a modest amount of space.

This test checks real RPC serialization, historical receipt/ticket access,
explicit branch synchronization, queued transactions and endpoint lifecycle.
It does not exercise the full recovered database, a public endpoint, ordinary
mining during collection, pruning, sustained load, a reorganization in the
middle of an RPC sample, or notifications. The existing retained-data fault
tests remain the evidence for a sample invalidated during collection.

The next monitoring work is durable observation/history coverage and incident
transitions, including reopening an incident when a receipt disappears.
Selecting delivery destinations/timings and demonstrating notification,
acknowledgement and loss of the collector remain separate requirements in the
[response policy](restart-monitoring-response.md). The observer still reports
saved intent as unknown and does not close incidents or recover the node.
