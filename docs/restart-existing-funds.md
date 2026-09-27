# Recovery using the remaining existing funds

27 September 2026, baseline `26b416c`. Tests and evidence only; production
candidates remain P1–P15.

The [genuine-history experiment](restart-partition-history.md) ended with a
correct-nonce funding failure on its heavier canonical branch. The donation
test account had no tickets, 2,021.665544264 liquid FSN and no free time locks
covering its saved purchase. Both saved and canonical nonces were 7. This
follow-up separates that condition from missing-nonce repair.

## Bounded funding choice

The original backup test account has only 1,205.752763845480158626 liquid FSN
after the hypothetical entrant funding; its mature 10,000-FSN rights have
already been spent. It cannot supply a further 5,000-FSN reserve alone.

This experiment instead combines **1,200 FSN from the backup test account and
1,800 FSN from the entrant**. It preserves the exact starting state and uses
ordinary signed transfers. No balance is manufactured, no ticket is injected,
and no further account ownership is substituted. The combined 3,000 FSN raises
the donation account's liquid balance to 5,021.665544264 FSN before its saved
purchase. This is a specific sufficient contribution for this recorded state,
not a universal reserve requirement or the mathematically smallest transfer.

These are public synthetic keys and hypothetical contributions. The result
does not authorize use of either real owner's money, require keeping the backup
key after handover, or change the selected single-producer launch arrangement.
An actual recovery contribution needs an authorized source and current checks.

## Controlled execution

Two fresh copies of the stopped, synchronized failure databases start at block
15,130,096, hash
`0x48212779e0851316084461094494cffcbb2c380362d1877a450c874913034291`.
All 592 copied files are hashed; the originals are rechecked unchanged. The
copies total 1,147,561,591 bytes, use C:, and retain the 50-GiB host reserve.
No additional original-backup copy or W:/D: data workload is needed.

Before funding, the actual transaction pool rejects the donation's exact saved
purchase for insufficient balance and accepts the entrant's saved purchase.
Both saved records and canonical nonces must match the retained failure.

| Height | Producer | Ordered transactions |
| --- | --- | --- |
| 15,130,097 | Entrant test key | Entrant's exact saved purchase at nonce 11; backup's 1,200-FSN transfer at nonce 233,429; entrant's 1,800-FSN transfer at nonce 12 |
| 15,130,098 | Entrant test key | Donation's exact saved purchase at nonce 7 |

The entrant's pending purchase executes before its contribution consumes the
next nonce. Neither saved purchase is replaced or rewritten. After the first
block the real pool accepts the donation purchase; the second block creates
its expected native ticket and advances its nonce to 8.

The race-instrumented controlled test **passes in 9.15 seconds**. Both databases
independently execute the blocks, close, reopen, and agree on all eighteen suffix
blocks, receipts, tickets and account differences. The first sixteen blocks
match the previous committed canonical evidence byte for byte. Independent
accounting checks every future interval, all gas/native fees, rewards, the two
earlier retreat losses and unrelated account fields. The only two additional
transfers are allowed by exact signed transaction hash and block height.

After controlled recovery:

| Test account | Liquid FSN | Tickets | Free time-lock rights |
| --- | --- | --- | --- |
| Donation | 21.665501816 | 1 | Future rights begin after the current purchase interval starts |
| Entrant | 223.852084448 | 0 | 10,000 FSN from time 1,790,459,600 through forever |
| Backup | 5.752721845480158626 | 0 | None |

The backup signs a funding transaction, but no additional block or ticket
purchase. The controlled test does not start a live miner or exercise a nonce
rollback, and one recovered purchase alone does not prove continued operation.

## Live continuation

A separate actual-service test reopens the same controlled result with the
original saved records intact. It first starts the entrant's worker and buyer:
the entrant has no ticket to sign with, but can place a funded replacement in
the transaction pool. Only after automatic nonce 13 is pending does it enable
the donation worker, which holds the sole remaining ticket.

That first live test **fails after 154.51 seconds**. Both heads remain at
15,130,098 during the 150-second progress gate. The entrant keeps nonce 13
pending; the donation buyer reconciles its successfully included nonce 7 and
cannot fund a fresh purchase. The donation worker reports `Next block doesn't
have ticket, wait buy ticket`. This is the finalization guard against consuming
the last ticket without replenishment, not failure to select the donation's
ticket. The complete controlled result therefore does not by itself establish
live recovery.

Source inspection shows an additional startup concern: `eth/handler.go` ignores
peer transactions until its acceptance flag is enabled. `eth/backend.go` enables
that flag at mining start. The first log places the entrant's broadcast before
the donation's mining start. Losing that initial broadcast is a plausible cause
of the absent replacement, but the flag was not sampled directly. A follow-up
restarts the stopped state and enables both miners before either buyer, preserving
the entrant's exact saved nonce-13 bytes. No additional funding or record rewrite
is used for that follow-up.

Acceptance requires both owners to make at least two fresh automatic purchases,
matching canonical native receipts, clean service shutdown, equal cold account
ledgers and unchanged saved-record bytes across reopening.

The revised startup **also fails the full acceptance test, after 154.62 seconds**,
but restores block production. Both nodes reach 15,130,111 with the same hash,
`0xec993b33d085d74c03256109c866e825b7609a64a1a55a94b70a12daf27e54f9`.
The exact staged entrant purchase is included, followed by repeated entrant
replenishment. The donation nonce stays at 8, with a new correctly numbered
purchase pending in its local pool. The entrant reaches nonce 26. Thus the chain
advances thirteen blocks but both-owner replenishment remains unproven. The
first failure is retained; the changed ordering is not described as a complete fix.

There is a second delivery concern. The donation's nonce-8 submission is logged
at 07:58:03.079; the entrant's import of the first new block follows at
07:58:03.084, in the logs' local timezone. The imported block releases the
donation's selected-ticket rights. A remote pool checking the transaction before
that refund could reject it, after which ordinary peer-known transaction tracking
can prevent a fresh announcement. This is a hypothesis supported by ordering
and source behavior, not a captured remote rejection. The test did not retain
the entrant's pool contents for the donation address or its admission error.
Do not infer that every locally pending transaction reached another miner.

## Cold diagnosis and accounting correction

After both services close, the databases agree on all **31 suffix blocks**,
including all receipts, tickets and complete account differences. Both real
cold pools accept both saved purchases: donation nonce 8 and entrant nonce 26
match their canonical nonces. The donation account has no ticket but has free
5,000-FSN coverage through the earlier interval and 15,000 FSN from that boundary
through forever, plus 21.978023040000021224 liquid FSN. Insufficient current
funds and a missing nonce do not explain this final pending state. Pool
acceptance is still not proof of inclusion or live propagation.

The first independent audit failed after its six cold database/pool checks had
passed. Its old purchase helper required exactly one receipt log. Block
15,130,099 legitimately has a second log: `ProcessMatureFSN` converts 5,000 FSN
of remaining full-lifetime rights to liquid for the entrant after its purchase.
The original failed audit and helper source are retained. The participant audit
now allows this specific additional log only after checking its complete native
shape, sender, parent timestamp, asset and value against independent interval
coverage before the isolated purchase minus its 5,000-FSN cost. The existing
purchase receipt validation and complete account conservation checks still run.

The corrected retained-artifact audit **passes in 0.65 seconds**. The thirteen
new live blocks contain thirteen successful entrant purchases and no retreat.
The first new block is signed by the donation account; the next twelve by the
entrant. The native conversion changes the form of existing rights, not supply.
This test correction does not change production execution or reinterpret either
live acceptance failure as success.

Logs, executable/source identities, exact funding transactions, account
inventories and new block artifacts are retained in
[the evidence directory](evidence/restart-existing-funds-2026-09-27).

## Remaining boundary

This exercise uses nearly all liquid reserves of the three test accounts. It
does not establish resilience to another retreat, an arbitrary fork or a long
outage. Next instrument the recipient's transaction admission and pool, retain
the exact pending bytes, and test their explicit delivery to the surviving
producer without changing nonce or adding money. Funding exhaustion, missing
nonces and a correctly numbered pending transaction are separate conditions.
A new complete-state live rollback/repair rehearsal still needs explicit usable
reserves and pre-fault checks; repeated retries of the small-reserve case are not
a substitute for funding. Equal-weight convergence, real reserve ownership and
the complete live nonce-repair case remain open.
