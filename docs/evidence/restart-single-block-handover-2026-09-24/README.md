# Single-backup-block handover evidence

See the [selected startup sequence](../../restart-wallet-handover.md).

Source baseline: `56b31c9`, plus `tests/restart/single_block_handover_test.go`
identified in `identities.json`. Production code is unchanged. All signatures
use public test keys 1 and 2; synthetic successor funding is 12,020.102 FSN.
Neither original data nor either real wallet key is opened by these tests.

The positive case imports one original-signer block at 15,130,081, with no
original-wallet purchase and a long-lived successor purchase built through the
RPC argument builder. It then imports five successor-only blocks independently
into a second database. The first successor block jumps to 23 September 2026.
The original selected ticket returns 5,000 FSN of its remaining time-lock
interval. Its other ticket, expiring at timestamp 1762415390, is retreated during
the jump in this fixture without another account credit. The original account
is byte-identical throughout successor-only production. At 15,130,083 only one
successor ticket remains, and replacement purchases continue. Final height is
15,130,086, with synthetic state root
`0x2f9d8a080152645d98fd444143e74bb91ae91dc6f62a0d80860b0cc1fe8f55bd`.
These dates, ordering and roots are not a proposed production identity.

The negative case makes the first successor ticket last only 30 days from the
historical timestamp. Validation rejects its attempted present-day jump with
`checkTicketInfo ticket ExpireTime mismatch`, leaving the head unchanged.
Linux logs include the expected rejected-block diagnostic for this negative
case; the test passes by asserting that rejection.

`windows-handover.txt` contains both new cases, the earlier three funding cases
and the existing sole-ticket/no-replacement rejection. The native executable
was built offline with Go, `CGO_ENABLED=0`, `GOMAXPROCS=2`, `GOTOOLCHAIN=local`,
`GOPROXY=off`, the cached runtime under `tmp/restart-runtime`, and:

```text
go test -p=2 -mod=readonly -c -o tmp/single-block-handover-final-tests.exe ./tests/restart
```

Run from `tests/restart` with `-test.v -test.timeout=2m` and:

```text
-test.run=^Test(SingleBackupBlockHandover|SingleBackupBlockRejectsShortSuccessorTicket|LastTicketHandover|SingleRemainingTicketRequiresReplacement)$
```

`check-linux.sh` records the Linux build and two race-detector runs in a private
network namespace, using an isolated source checkout. `linux-race.txt` records
both passes; `linux-identity.txt` identifies the retained executable and tests.
`identities.json` also identifies the Windows binary and baseline archive.
The archived baseline uses Git's LF line endings; the existing Windows
`handover_test.go` has CRLF, so its raw file hash differs between platforms.
The added test has the same raw source hash on both platforms.
`SHA256SUMS` covers the evidence files except itself.

This proves a sparse core transition and RPC argument construction. It does
not prove full-state accounting, actual worker timestamps, transaction-pool
admission/propagation, two running node processes, automatic purchase startup,
restart behavior or key custody. The original first ticket and its jump-block
replacement need explicit intervals spanning the recovery jump. The next
rehearsal must verify those runtime steps with copies of the complete state and
synthetic substitutions, followed by review of the real-address sequence.
