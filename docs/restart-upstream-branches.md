# Fusion-Community/efsn restart branches

22 October 2026. Branches against `develop` (`c5f0174d`, v5.0.3), after two
review rounds and a necessity review. Each branch is reviewed as a PR into the
branch it sits on, so every review diff contains only that branch's own commits.
No branch contains a merge commit.

```
develop
├─ fix/ticket-encoding-compat ─ fix/fsn-log-json-compat ─ build/go-toolchain
├─ fix/jwt-and-test-fixtures            (optional)
├─ fix/p2p-discovery
├─ fix/restart-double-seal
└─ fix/chain-consistency ─┬─ feature/restart-checkpoints
                          ├─ feature/autobuy-retry
                          └─ tools/restart-recovery   (never merged; tag at signing)
```

| Branch | PR base | Commits | Runtime diff (excl. tests and vendored Go files) | Importance |
| --- | --- | ---: | --- | --- |
| `fix/ticket-encoding-compat` | develop | 1 | +32 / −10, plus 2,240 lines copied unchanged from Go 1.21.3 | Critical before any compiler change |
| `fix/fsn-log-json-compat` | fix/ticket-encoding-compat | 1 | +11 / −4, plus 2,371 lines copied unchanged from Go 1.21.3 | Critical before any compiler change |
| `build/go-toolchain` | fix/fsn-log-json-compat | 2 | +6 / −14 | High |
| `fix/jwt-and-test-fixtures` | develop | 2 | +3 / −3 | Optional (scanner hygiene) |
| `fix/p2p-discovery` | develop | 5 | +12 / −3 | High for the restart |
| `fix/chain-consistency` | develop | 8 | +94 / −99 | High |
| `feature/restart-checkpoints` | fix/chain-consistency | 3 | +48 / −27 | Critical for the restart |
| `feature/autobuy-retry` | fix/chain-consistency | 3 | +51 / −34 | High |
| `fix/restart-double-seal` | develop | 1 | +32 | High for the restart |
| `tools/restart-recovery` | fix/chain-consistency | 4 | +1,506 (separate binary) | Critical for the restart operation, never merged |

The restart node changes (excluding the copied Go encoders and tests) total
about 230 lines, down from about 1,800 in the first version.

**Rating scale:**
- **Critical:** the restart cannot be done safely without it.
- **High:** a demonstrated failure that is likely to hit a small restarted network.
- **Optional:** no reachable failure.

### Verification
- **Combined build on Go 1.27.3:** all mergeable branches together, built with `make all`.
- **Package tests:** every touched package passes with `-race`: `internal/ticketgzip`, `internal/logjson`, `core/types`, `consensus/datong`, `ethdb`, `p2p`, `cmd/utils`, `params` and `internal/ethapi`.
- **Restart suite:** all 8 `tests/restart` integration tests pass with `-race`.
- **`p2p/discover`:** fails only `TestParseNode` and `TestForwardCompatibility`, both failing identically on develop.
- **Tools branch:** its 10 recovery tests pass with `-race`.
- **Regression tests are real:** every regression test was also run against the code without its fix and fails there. The exception is `TestHeaderBatchUsesUnstoredParents`, which guards the changed code path rather than a reproduced bug.
- **History:** the unchanged node fixes, ticket encoder and recovery tool are the ones Codex replayed and rehearsed: mainnet 1–15,130,080 with matching roots, receipts and ticket commitments. The JSON encoder, checkpoint pinning, autobuy rewrite and p2p reductions are new since that replay. The JSON encoder is byte-identical to Go 1.21.3's on 70 hostile payloads. The others are covered by the tests above.

---

## 1. `fix/ticket-encoding-compat`

**Summary.** Fusion stores `gzip(RLP(tickets))` in the ticket account and commits
its hash in every header's `MixDigest`. Go 1.27 rewrote the DEFLATE encoder, so a
node built with it computes a different mainnet genesis. This branch freezes the
ticket writer:
- five unchanged Go 1.21.3 `compress/flate` writer files;
- two shared definitions;
- a fixed gzip header and trailer.

Decoding still uses the standard library.

**Importance: Critical before any compiler change.** **If skipped:** release
builds must stay on Go 1.21.3, which receives no security fixes. Anyone building
with Go ≥ 1.27 gets a node that rejects the real chain at genesis.

**Consensus / existing nodes.** No change. The output is byte-identical to Go
1.21.3, the compiler v5.0.3 images were built with. It was checked against 7
historical blobs, 55 synthetic payloads, the genesis header and a full mainnet
import.

**PR message.**

> **core/state: freeze the ticket gzip writer to Go 1.21.3**
>
> Ticket commitments (`MixDigest`) hash the gzip-compressed ticket list. Go 1.27
> changed the DEFLATE output, so a node built with it computes a different
> mainnet genesis. This vendors the unchanged Go 1.21.3 DEFLATE writer under
> `internal/ticketgzip` (BSD license included) and uses it only for ticket
> encoding.
>
> Testing: `TestMainnetGenesisHash` fails on Go 1.27 without this change and passes
> with it. A Go 1.27.1 build imported mainnet 1–15,130,080 with matching roots and
> ticket commitments.
>
> 🤖 Generated with [Claude Code](https://claude.com/claude-code)

---

## 2. `fix/fsn-log-json-compat` (on `fix/ticket-encoding-compat`)

**Summary.** FSN native calls write their parameters and outcome as JSON into
`Log.Data`, which is hashed into the receipt root. Go 1.22 changed `\b`/`\f`
escaping and Go 1.27 changed invalid-UTF-8 output. Both log writers now use an
unchanged copy of the Go 1.21.3 encoder: six files plus the `Number` type.

**Importance: Critical before any compiler change.** **If skipped:** one GenAsset,
MakeSwap or AssetValueChange transaction containing such bytes would split nodes
built with different compilers.

**Consensus / existing nodes.** No change. Output is byte-identical to Go 1.21.3 on
70 addLog-shaped payloads with hostile strings, while Go 1.27.3's own encoder
differs on 21 of them. It is stacked on the encoder branch only because the
toolchain branch needs both.

**PR message.**

> **core: freeze the FSN log JSON encoder to Go 1.21.3**
>
> FSN call logs are JSON in `Log.Data` and are hashed into receipt roots.
> `encoding/json` output changed after Go 1.21 (`\b`/`\f` in Go 1.22, invalid
> UTF-8 in Go 1.27). This vendors the unchanged Go 1.21.3 encoder under
> `internal/logjson` and uses it for the two log writers.
>
> Testing: `TestLegacyEscaping` (fails with the Go 1.27 standard library); 70 hostile
> payloads byte-identical between Go 1.21.3 `encoding/json` and Go 1.27.3 with this
> encoder.
>
> 🤖 Generated with [Claude Code](https://claude.com/claude-code)

---

## 3. `build/go-toolchain` (on `fix/fsn-log-json-compat`)

**Summary.**
- Removes the `memsize` profiler, which Go 1.23+ refuses to link.
- Moves CI and the three Dockerfiles to Go 1.27.3.
- CI also runs the two frozen encoders' tests with `-race`.

**Importance: High.** It ships a supported compiler. It isn't needed to run the
restart itself. **If skipped:** releases stay on Go 1.21.3.

**Consensus / existing nodes.** None, given the two encoder branches. An audit of
`core`, `core/state`, `core/vm`, `core/types`, `consensus/datong`, `common`,
`params`, `rlp` and `trie` against Go 1.22–1.27 found no other standard-library
output that reaches consensus data.
- Error strings written into logs are efsn's own text.
- Datong only decodes JSON the node itself wrote.
- Go 1.24's sort change only reorders equal elements.

Operators rebuilding the image lose the `/memsize/` pprof page.

**PR message.**

> **build: move to Go 1.27.3**
>
> Depends on the ticket encoder and FSN log JSON PRs, which freeze the only two
> places where compiler output reached consensus data.
>
> - Remove the memsize profiler, which Go 1.23+ cannot link.
> - CI and Dockerfiles on Go 1.27.3; CI runs the frozen encoders' tests so a
>   toolchain update that changes their output fails.
>
> 🤖 Generated with [Claude Code](https://claude.com/claude-code)

---

## 4. `fix/jwt-and-test-fixtures` (optional)

**Summary.**
- golang-jwt/jwt v4.4.2 → v4.5.2.
- Repairs the `TestProtocolHandshake` and core/types test fixtures.

**Importance: Optional.** The JWT handler is only installed for APIs registered as
authenticated, and efsn registers none, so the advisories (GO-2024-3250,
GO-2025-3553) are not reachable. This only clears vulnerability scanners.
Nothing in CI runs the repaired tests. **If skipped:** scanners keep reporting
the advisories.

**Consensus / existing nodes.** None.

---

## 5. `fix/p2p-discovery`

**Summary.** Five discovery fixes for a small network:
1. Start the table loop after the UDP transport is attached (a startup race).
2. Accept `findnode` replies with fewer than 16 neighbours. Before, every reply in a network of fewer than 16 nodes counted as a failure, and healthy peers were deleted after 5 of them.
3. Never add the local node to its own table, where it suppressed the refresh that re-contacts bootnodes.
4. Restore the routing hash of seeds loaded from the database.
5. Skip an unparsable bootstrap entry with an error log instead of exiting, as the v5 bootstrap path already does.

On the last one: all four default mainnet bootnodes (`bn1`–`bn4.fusionnetwork.io`)
no longer resolve, so a default-config v5.0.3 node currently exits at startup.

**Importance: High for the restart.** **If skipped:** a restarted network of a few
nodes keeps deleting its own peers, and default-config nodes don't start.

**Consensus / existing nodes.** None. No wire, record or schema change.

**Dropped after review:**
- the `addedAt` change: its premise was wrong, since early peer persistence is harmless;
- the address-reservation rework: it stopped counting dead peers' failures;
- the 400-line DNS bootstrap feature: the 2-line skip above replaces it;
- the forward-compatibility test vectors: they fix a pre-existing test failure unrelated to the restart.

**PR message.**

> **p2p/discover, cmd/utils: discovery fixes for small networks**
>
> Five fixes, one per commit with the reproduced failure: table loop start race,
> sparse findnode replies counted as failures, self-admission, seed routing hash,
> and skipping unresolvable bootnodes instead of exiting (the default mainnet
> bootnode hostnames no longer resolve). New tests fail on develop and pass here.
>
> 🤖 Generated with [Claude Code](https://claude.com/claude-code)

---

## 6. `fix/chain-consistency`

| Commit | Fix |
| --- | --- |
| Parent isolation | Removes the package-global DaTong parent list that concurrent imports and the miner shared ("unknown ancestor" on valid blocks, plus a data race). |
| Reconstruction timestamp | Ticket reconstruction cleared expiries at the header time instead of the parent time used by execution. It failed across expiry boundaries and time jumps, which is exactly what the restart's jump block does. Also fixes a nil dereference on a missing ancestor. |
| Atomic reorg | Canonical hashes, lookups and head markers are written in one batch, so a crash can't leave a half-switched chain. |
| Atomic SetHead | Deletions and head markers are written in one batch; state repair stops on a missing ancestor instead of panicking. |
| Receipt log copy | The miner's sealing task gets its own `Log` structs, fixing a data race. |
| Snapshot length | Rejects 1–4 byte snapshot data. Any validly signed header (any key) could otherwise crash nodes, so this is a likely remote crash on current nodes. |
| Coinbase lock | Both of the miner's coinbase reads take the worker lock (a data race in 3 of 4 `-race` runs). |
| Tests | Parent isolation and reconstruction regression tests on a synthetic chain from the 15,130,080 state. The operator address is replaced by the synthetic test owner. |

**Importance: High.** **If skipped:** two producers can reject each other's valid
blocks; restored nodes can fail to verify the restart's jump block; a crash during
a reorg or rewind can leave an inconsistent database; and a peer can crash nodes.

**Consensus / existing nodes.** No validity change; replayed against mainnet
history. Unpatched nodes agree on every block.

**Dropped after review:**
- rollback without a freezer: `Rollback` has no caller outside tests;
- ethstats head reporting: a follow-up;
- the read-only LevelDB fix: moved to the tools branch, its only user.

**PR message.**

> **core, consensus/datong, miner: persistence, race and parser fixes**
>
> Seven independent fixes, one per commit with the reproduced failure, plus
> regression tests that fail on develop. No block validity change; replayed
> against mainnet 1–15,130,080.
>
> 🤖 Generated with [Claude Code](https://claude.com/claude-code)

---

## 7. `feature/restart-checkpoints` (on `fix/chain-consistency`)

**Summary.** Uses the existing hard-coded checkpoint table instead of a new
anchor mechanism:
- Hashes listed above `LastCheckPoint` are now enforced on header verification, block and header imports, reorgs, head writes and startup. At startup the node rewinds below any mismatch.
- `LastCheckPoint` stays at 2,680,000, because heights up to it skip seal verification.
- Pins the backup tip 15,130,080.
- A reorg may not move the head back below a checkpoint the node has already passed.
- The recovery block hashes are added in the restart release, once they exist.

**Importance: Critical for the restart.** **If skipped:** anyone holding the old,
now-expired tickets could seal a private continuation timestamped before they
expired. At about 490 tickets' difficulty per block, against a handful after the
restart, it would replace the restarted chain under ordinary fork choice.

**Consensus / existing nodes.** This is a fork-choice restriction, not a validity
change. Upgraded nodes refuse a chain that conflicts with a pinned block; v5.0.3
nodes would follow it if it were heavier. All producers and services must upgrade.
Compatible descendants keep ordinary fork choice.

**Tests:**
- A unit test of the checkpoint lookups and the reorg guard.
- An integration test: a heavier rival branch is refused at the pinned height on block and header import, and a node on the rival branch rewinds at startup. Without this branch the rival is imported.

**Third commit (28 October), `cmd/efsn: load the check points before opening the chain`.** The
startup rewind never ran in the real binary: efsn filled in the check point table in `startNode`,
after `makeFullNode` had already opened the chain and run the check against an empty table. The
integration test missed it because it initialises the table itself. The T2 rival test showed it: a
rival node restarted on the pinned build stayed on its chain until fork choice moved it. The commit
moves the network selection and `InitCheckPoints` to the start of `makeFullNode`; the restarted rival
node then rewinds as it opens the chain. The chain subcommands (`import` and others) now enforce the
table too.

**PR message.**

> **consensus/datong: enforce pinned check points above LastCheckPoint**
>
> Lets the existing check point table pin hashes above the legacy range (which
> keeps skipping seal verification) and refuses reorganisations back below a
> pinned height, so an older chain with more total difficulty cannot replace the
> restarted one. Pins block 15,130,080; the recovery blocks are pinned in the
> restart release.
>
> 🤖 Generated with [Claude Code](https://claude.com/claude-code)

---

## 8. `feature/autobuy-retry` (on `fix/chain-consistency`)

**Summary.** Every block consumes the ticket that sealed it, so a producer has to
buy about one ticket per block. Changes to the existing buyer loop:
- It wakes every 5 s as well as on new blocks.
- The per-block "already submitted" cache is replaced by a pool check, which still allows an explicit same-nonce replacement.
- On the timer it resends the account's own pending purchase to all peers, fixing the two-producer "rejected while behind, never re-sent" failure Codex reproduced.

**Importance: High.** **If skipped:** after a restart nothing is bought until a new
block arrives, and failed purchases aren't retried. A sole producer with few
tickets stalls the chain again.

**Consensus / existing nodes.** None. Peers receive the producer's own pending
purchase again at most every 5 s.

**Tests:**
- A unit test for the pool check.
- A real-miner integration test: a sole producer with one ticket and a failed first submission mines the retry and the next purchase in consecutive blocks. It fails on the old buyer with "no submission".
- An explicit-replacement test that the old per-block cache refused.

**Third commit (28 October), `internal/ethapi: log why an automatic ticket purchase fails`.** The
buyer discarded the purchase error, so a producer without spendable funds stopped buying with nothing
in its log (T2 soak, producer A). It now logs a warning whenever the reason changes. A producer that
can buy only right after its own blocks logs it each time it runs dry again.

**PR message.**

> **internal/ethapi: retry automatic ticket purchases between blocks**
>
> The buyer acted only on new blocks and tried once, so a sole producer could run
> out of tickets. Adds a 5-second retry, replaces the per-block cache with a pool
> check, and resends the pending purchase to peers. No price, selection or
> validation change.
>
> 🤖 Generated with [Claude Code](https://claude.com/claude-code)

---

## 8b. `fix/restart-double-seal` (on develop)

**Summary.** A producer killed with `kill -9` restarts on the last head whose state reached disk,
which with the default GC mode can be far behind (T2: 1,668 blocks). It then begins sealing at once
and, if that seal is delivered before the sync starts, signs a second block on a parent it already
signed on; nodes report that with `ReportIllegal`, which deletes the miner's tickets. DaTong now
records the highest block number it hands to the miner and refuses to seal at or below it, so the
restarted producer syncs first.

**Importance: High for the restart.** **If skipped:** a crashed producer can lose its tickets by
double-signing after restart, and with few producers the chain depends on it.

**Consensus / existing nodes.** None: only the local miner's behaviour changes. A sole node that
lost its newest blocks cannot seal below its recorded height again.

**Tests:** a unit test that a restarted engine refuses heights it sealed before (it seals without
the change). The T2 crash test (`t2-crash-restart-claudedev.sh`): on restart the guard refused
block 15,130,084 ten seconds before the sync started, and no node logged a double block.

---

## 9. `tools/restart-recovery` (on `fix/chain-consistency`, never merged)

**Contents:**
- the read-only LevelDB fix;
- the rehearsed `fsn-recovery` tool with `datong.SigningPayload`;
- the selected-ticket expiry guard;
- the recovery integration tests, including the opt-in full-state rehearsals.

It stays on Fusion-Community as the public record of how the restart blocks were
built. Tag the exact commit used for signing. The full-state rehearsal fixtures
still name the operator address, which the recovery blocks' coinbase makes public
anyway.

Build the tool only after rebasing it onto the release commit. The branch itself
lacks the frozen ticket gzip writer and log JSON encoder, so a Go 1.27.3 build of
the bare branch computes different ticket commitments (and receipt hashes for the
purchase) than every node, and the network would reject the signed blocks.

Why the full tool rather than a cut-down version: the network re-validates its
output, but signing with real keys happens once. Fusion also deletes a ticket
from a miner reported for signing two different blocks on the same parent, so
the rehearsed journal that prevents exactly that is kept.

---

## Merge order

1. Any order: `fix/ticket-encoding-compat`, `fix/p2p-discovery`, `fix/chain-consistency`.
2. After its parent: `fix/fsn-log-json-compat` → `build/go-toolchain`. Coordinate the CI change with the historical-tracing PR.
3. After `fix/chain-consistency`: `feature/restart-checkpoints` and `feature/autobuy-retry`, in either order.
4. `fix/restart-double-seal`, any time.
5. `fix/jwt-and-test-fixtures` is optional.
6. Restart release:
   1. Rebase `tools/restart-recovery` onto the release commit, build the recovery blocks and tag the tool.
   2. Add the recovery block hashes to `mainnetCheckPoints`.
   3. Replace the default bootnodes.
   4. Bump the version.

## Still open

- **Bootnodes (decided 22 October):** two slots in the restart release, each defined by a DNS name plus a dedicated node key that can later be moved to another machine:
  - `bn1.fsnex.net`: a discovery-only `bootnode` on a small VPS (Contabo).
  - `bn2.fsnex.net`: the FSNEX explorer's full node.

  The producers peer with each other through static nodes and do not depend on these entries. Still needed: both enode public keys and the VPS IP. Slots can later be handed to community operators by moving the key file and the DNS record; retire one only once the current release lists 2–3 other reliably run entries.
- **Recovery hashes:** the recovery block hashes for the checkpoint table, available only after signing.
- **F5 and F11:** native-call RLP decode errors are ignored (F5), and there are state rollback defects (F11). Both are preserved as historical behaviour; a fix needs an activation height.
- **Wall-clock check:** `core/state_transition.go` (TimeLockToAsset) compares the start time with the wall clock (`time.Now()`) inside a state transition. This is pre-existing and non-deterministic input to consensus.
- **Follow-ups:** ethstats current-head reporting; re-resolving bootnode hostnames periodically; the inherited `TestParseNode`/`TestForwardCompatibility` failures.
