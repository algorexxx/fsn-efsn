# Native calls with undecodable input run as GenNotation

Found on 23 September 2026 while reconciling block fees in the fsnex explorer against a genesis
import of mainnet through block 1,900,049. It describes behaviour of this source tree; the
chain has replayed with it since genesis, so it is consensus, not a node-local quirk.

## What happens

A transaction sent to `FSNCallAddress` (`0xffff…ffff`) carries an RLP `FSNCallParam`
(`{Func FSNCallFunc; Data []byte}`, `FSNCallFunc` is a `uint8`). `TransitionDb` decodes it
and ignores the error:

```go
// core/state_transition.go, TransitionDb
fsnCallParam = &common.FSNCallParam{}
rlp.DecodeBytes(msg.Data(), fsnCallParam)
st.fee = common.GetFsnCallFee(msg.To(), fsnCallParam.Func)
```

`rlp` decodes field by field into the struct, so a failure leaves whatever was assigned before
it. Input that is not an RLP list — empty input, a string, hex digits sent as text, an ERC-20
call — never assigns `Func`, which stays `0`: `GenNotationFunc`. Then:

1. `GetFsnCallFee` prices it at 0.1 FSN, which `buyGas` debits with the gas.
2. `handleFsnCall` runs GenNotation for the sender. If they hold no notation, they get one. If
   they do, it fails with an error log.
3. A node mining under this code leaves out a transaction whose `handleFsnCall` fails
   (`isInMining`). A block that already contains one is replayed with the error only logged,
   and the fee is paid to the coinbase whether the call succeeded or not.

Input that decodes `Func` and fails later keeps that function: trailing bytes after the list,
too few or too many fields, or a malformed `Data` all execute `Func` and pay its fee.

The transaction pool rejects undecodable input (`decode FSNCallParam error`, `core/tx_pool.go`),
but that check only arrived in `cf2293b` on 2020-02-26. Before it the pool ignored the error
too, and block processing has never checked.

## Where it happened on mainnet

Found in blocks 0 to 1,900,049:

| Block | Transaction | Input | Outcome |
|---:|---|---|---|
| 310,077 | `0xb6d35f2ab98e0d8816abea50b6ddd8e893cd2a25dfeea0044b55d75d8099172d` | The JSON `{"AssetID":"0xff…ff","To":"0xf9b9064a1d379f0239334d1bdb251f635cc1b46b","Value":100000000000000000}`, hex-encoded and sent as text (`0x7b22…`): an intended SendAsset of 0.1 FSN | Notation 10,119,879 created, 0.1 FSN charged, no FSN sent |
| 422,106 | `0x9cfad4cbcc1018384a3f9b2874ac74896167f514201c85ac02badfa56ce5acb8` | ERC-20 `transfer(0x27214edf63950ce22f1551924a5553f7a821b946, 10^16)` | Notation 10,122,809 created, 0.1 FSN charged |

Both receipts log `{"Base":{"Func":0,"Data":null},"notation":…}`. Neither sender asked for a
notation, and the first lost the transfer they meant to make. Blocks above 1,900,049 have not
been checked.

## Related places that ignore the same error

- `handleFsnCall` decodes every operation's `Data` with `rlp.DecodeBytes(param.Data, &x)` and
  ignores the error, then validates and executes the zero-valued or partly decoded parameters.
- `BlockValidator.ValidateRawTransaction` decodes **every** transaction's data, whatever its
  recipient, ignoring the error. It then applies the one-ticket-per-block rule to anything
  whose data decodes as `BuyTicketFunc`, even a transaction that was not sent to the native
  address.

## Fixing it

The behaviour decides balances and fees, so a fix changes consensus. It must activate at a
fork height, with the old path kept below it so history still replays to the same state
roots. Fusion is halted at block 15,130,080, so any restart would apply it from the first new
block.

At and above the fork:

1. In `TransitionDb`, treat a native call whose input fails `rlp.DecodeBytes`, including
   `ErrMoreThanOneValue` from trailing bytes, as invalid: return an error so the transaction
   cannot be included. That matches what the pool has done since 2020. A softer option is to
   treat it as failed: charge gas only, skip `GetFsnCallFee` and `handleFsnCall`, and log the
   error. Either way, never execute a function the input did not state.
2. In `handleFsnCall`, check each operation's `rlp.DecodeBytes(param.Data, …)` and reject the
   call with an error log instead of acting on zero values.
3. In `ValidateRawTransaction`, skip transactions not sent to `FSNCallAddress` before looking
   at their data, and check the decoding error.

Tests to add alongside:

- A native call with empty input and with non-list input, below the fork (charged as
  GenNotation, today's result) and above it (rejected or failed, with no notation and no fee).
- A native call with trailing bytes after a valid envelope, on both sides of the fork.
- A block holding a non-native transaction whose data happens to decode as `BuyTicketFunc`.

## How the explorer handles it

fsnex mirrors the rule for the chain's existing history. It reads the function as
`rlp.DecodeBytes` would have left it (`FusionNativeCallDecoder.DecodeExecutedFunction`),
and charges that function's fee. Checked against every native call through block 1,900,049
(2,272,556): the function it reads matches the receipt's native log for all of them, except
MakeSwapExt and TakeSwapExt, which `handleFsnCall` logs as MakeSwap and TakeSwap at the same
fee.
