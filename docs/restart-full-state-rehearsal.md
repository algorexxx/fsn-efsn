# Full-state recovery bridge rehearsal

The preserved state can execute the eight-block synthetic Candidate A bridge.
Two separate processes, starting from independently checksummed copies, agree on
every block, receipt, ticket map and complete account-trie difference. This is a
test of the recovery mechanism with the full state, not a valid mainnet recovery
sequence or a launch authorization. No production code, real key or original
backup was changed. The mainnet restart anchor remains unset.

## Inputs and isolation

The input is the verified [504 MiB state artifact](restart-state-export.md) at
block 15,130,080, hash
`0xe93ffded087a79097d4309c7831690161db6ed136f4b1a22c4c83a99db80f99f`.
Its 230-file manifest was checked again before copying. Every file in both new
C: copies was reread against the same SHA-256 manifest. Neither original state
nor the preserved WSL historical database is a rehearsal writer target.

A separate Linux reader exported 256 contiguous headers, 15,129,825 through
15,130,080, plus the final block body, receipts and stored total difficulty
63,370,514,513. The source was mounted read-only in a private mount/network
namespace. The 168,191-byte RLP artifact checks ancestry to the observed head,
transaction/receipt roots, bloom and absence of uncle bodies. This is bounded
context validation, not independent consensus replay of those headers.

The first context attempt failed because the harness applied an Ethereum uncle
hash check. Fusion stores a PoS commitment in that header field; its body has no
uncles. The corrected harness checks absence of uncle bodies and preserves the
original committed header. Both the failure and successful extraction are saved.

Windows performs the state-copy execution and cold traversal natively to avoid
the measured WSL/NTFS traversal overhead. These are direct core execution tests,
without node services or peers. Linux helper tests run in a network namespace.
There are no RPC listeners, automatic purchases or real-key accesses.

## Exact synthetic substitution

Public test key `1`, address
`0x7e5f4552091a69125d5dfcb7b8c2659029395bdf`, does not exist in the original state.
The fixture makes exactly three account-trie changes:

1. Original owner `0x9fc4c40e50f902b9aa641b4a32ebaafa5c9386a1`: debit all
   `3225543308109480158626` wei of liquid FSN and its complete FSN time-lock
   schedule. Retain nonce 233,427, its three other asset balances, notation,
   code and storage.
2. Public test address: credit exactly that liquid FSN and the same time-lock
   intervals/amounts; initialize its nonce to 233,427. Copying the nonce is an
   explicit fixture setup step, not a mainnet transaction.
3. Ticket store: reassign only the original owner's two tickets to the test
   address, preserving their IDs, heights and time intervals. All other tickets
   and owners remain unchanged. Recompute the compressed ticket commitment.

Both directions of the account-trie difference are enumerated, including account
creation/deletion. RLP field comparisons permit only these changes. Funding is
not duplicated. The complete before/after RLP records, time-lock schedule and
ticket IDs are in `fixture.json`; the key audit also records the original account.
Other native ownership records, including swaps, are unchanged. This substitution
does not simulate moving those ownership rights.

The synthetic parent has hash
`0x5c374b29049a080e62442c3cd9fcf056967b6d4fc07f43ad857349d20f9085c5`, root
`0x5c16feaed0c954346a0979268bf99c6d69975b37b5e1a3c217ed71c65ddcb531`,
and ticket commitment
`0x7ddb42f1edd476fbe4176f6251cb817669320e9bedec051f1487dec5ba06d4b3`.
Its body and receipts come from the preserved block; only root and ticket
commitment are changed in its header. Its old signature consequently no longer
validates. It is deliberately installed as a trusted synthetic fixture boundary.
Genesis/header metadata is installed for core startup, but genesis state and the
intervening complete history are absent. Never expose these databases as a
mainnet bootstrap, archive or genesis-sync source.

## Execution and accounting

The first two blocks advance historical time by 120 seconds each. The third
jumps to the fixed rehearsal time 2026-09-23 00:00:00 UTC. The remaining blocks
advance by 120 seconds. A purchase is included in every block except the first.
Blocks are built using the existing execution/finalization helpers, signed with
the public test key, serialized to RLP and imported through `InsertChain`.
The verifier is another process with its own prepared state; it receives only
the saved block artifacts and compares its results with the producer's ledger.

| Step | Height | Unix timestamp | Remaining tickets | Changed accounts |
| --- | --- | --- | --- | --- |
| 1 | 15,130,081 | 1759826750 | 484 | 7 |
| 2 | 15,130,082 | 1759826870 | 480 | 5 |
| 3 | 15,130,083 | 1790121600 | 475 | 2 |
| 4 | 15,130,084 | 1790121720 | 1 | 2 |
| 5 | 15,130,085 | 1790121840 | 1 | 2 |
| 6 | 15,130,086 | 1790121960 | 1 | 2 |
| 7 | 15,130,087 | 1790122080 | 1 | 2 |
| 8 | 15,130,088 | 1790122200 | 1 | 2 |

The delayed removal of expired tickets follows existing finalization, which
clears expiry against the parent timestamp. The full-state result reproduces
that behavior across the jump.

Independent ledger accounting checks seven successful native purchase logs,
their owners/IDs and resulting live 5,000-FSN tickets. Checking receipt status
alone would not suffice for Fusion native calls, which can also report an error
in their log payload. Each block's aggregate liquid-FSN increase is exactly
312,500,000,000,000,000 wei, the 0.3125-FSN reward at this height: 2.5 FSN total.
The sender is also the miner in this fixture. These results do not demonstrate
fee distribution between different operators.

Only the synthetic signer, five other historical ticket owners and the ticket
store change during execution. All changed accounts' complete decoded records
are retained in `accounting.json`; raw differences and full ticket maps are in
each block ledger. Other assets, notation, code, storage and non-signer nonces
are checked unchanged. Other ticket owners' changes are FSN time-lock changes
under the existing refund/retreat rules. The historical blocks can retreat
other owners' tickets, including existing non-refund cases; their exact economic
effects require review in the eventual real-signer ledger.

Final block hash:
`0x61ae0d3df609505cde0fb1677eb03947914e61a03e6e143ee17315d22776e27d`.
Final root:
`0x5673917f18b7c70e5362764bf6eb11d6e7c383ff8fed81b6c9ed283475790e25`.
Final ticket commitment:
`0xfd0679ac2766e30f8c7a14797b7091ac103d39a272a70cb78d7efb45e1c195e6`.

The final ticket is
`0x8075c5fe368d6eed4d264da76b197830f89daf92a54aa32f7238f60188e3cfc9`,
owned by the test signer, with interval 1790122080–1792714080. Its existence
does not establish launch resilience: with one ticket, another replacement
purchase is needed to keep producing blocks. A deliberate ticket runway and
tested operator/failover setup remain to be resolved. One team may initially
operate the producers; independent organizations are a decentralization goal,
not a consensus requirement or a fixed initial launch minimum.

## Cold verification and limits

Each writer closes before a fresh process opens its copy. Cold checks compare
all eight canonical blocks and complete ledgers, all head markers and the EVM
ancestor hashes for the preceding 256 heights. Parent time and the ten-block
sealing-delay header context are present. The helper signs directly, so this
does not exercise the actual mining worker or sealing-delay timer.

With all eight suffix state roots made unavailable through the test database
wrapper and the global ticket cache evicted, DaTong reconstructs tickets back
to the retained synthetic parent. The next prepared header, selected ticket and
retreat list equal direct-state preparation. Hiding that parent state and its
historical fallback header instead produces `ErrUnknownAncestor`. This models
unavailable roots/context; it is not a physical pruning or crash test.

Each final state is traversed, all account/storage roots rebuilt and all
code/native blobs hashed. Both checks passed: 360.90 seconds for the producer
and 246.71 seconds for the verifier. The resulting inventory is 801,356 accounts,
2,886,305 storage leaves, 33,437 code/data references and 262,347,430 referenced
bytes. The account increase is the public test address. Storage and reference
counts match the original; referenced bytes change with the ticket-store blob.
These checks do not promise power-loss durability or support for missing older
state/history beyond the explicit reconstruction boundary.

Twenty focused cases cover correct accounting/context, duplicated funding,
changed other assets/storage/code/nonce, false ledger funding/locks, account
deletion/insertion, and damaged historical headers/body/receipts. They pass on
Windows and twice under the Linux race detector. Linux also independently
decodes and validates the actual bridge accounting; its JSON output is
byte-identical to Windows. The ordinary Windows restart suite also passes, with
its log recorded separately. Opt-in peer-service and process-crash suites are not part of this
test-only change; their previous evidence remains separately scoped.

Initial execution uses retained `tmp/full-state-tests.exe`; final helper tests
and stronger independent accounting use `tmp/full-state-final-tests.exe` and
`tmp/full-state-final-linux-tests`. Their identities and source hashes are saved.
The initial execution log formats hash values as raw bytes; use the JSON/RLP
artifacts and accounting log for readable exact identities. Final source fixes
that log formatting and adds the independent accounting assertions.

## Next gates

- Exercise actual full-state mining and automatic replenishment, including a
  missed purchase, restart and funding/wallet failures. Decide and demonstrate
  the initial operator/key layout and ticket runway before selecting launch
  timing; a team-operated bootstrap is an option.
- Review the historical bridge's refunds, retreats and time-lock changes; compare
  Candidate A with the explicit current-time alternative. Synthetic owner/parent
  changes alter sorting, transaction IDs and ticket IDs, so the real-signer
  sequence still needs separate construction and review.
- Validate supported full-state acquisition, anchor enforcement and peer behavior
  together. This fixture does not implement peer state download, complete
  history/genesis resync or general sparse-history operation.
- Continue the separately bounded historical replay beyond 2,700,000 when its
  next range and storage capacity are selected. This rehearsal does not advance
  that replay or remove earlier checkpoint limitations.

Evidence: [restart-full-state-2026-09-24](evidence/restart-full-state-2026-09-24).
Disposable copies: `tmp/full-state-producer` and `tmp/full-state-verifier`.
Block artifacts: `tmp/full-state-bridge`, also archived with the evidence.
The original `tmp/preserved-head-state` remains the exact verified state artifact.
