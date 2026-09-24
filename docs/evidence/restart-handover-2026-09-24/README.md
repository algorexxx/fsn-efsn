# Two-wallet handover and donation balance

See [the handover report](../../restart-wallet-handover.md).

`donation-wallet.txt` is a read-only native Windows lookup of public address
`0xa3ce60d2dbf51afa0ab106df1c44a2e48853817a` in the verified exported state.
It records source head, exact integer balances, nonce, code hash, time locks,
sampled coverage interval and retained executable SHA-256. It reports
12,020.102 liquid FSN, no time locks and nonce zero. No private key, signing,
transaction submission or fund movement was involved.

The retained query executable is `tmp/handover-wallet-tests.exe`. It was run from
`tests/restart`, with `FUSION_RESTART_FULL_STATE_AUDIT` set to the absolute
`tmp/preserved-head-state` path and `FUSION_RESTART_AUDIT_ADDRESS` set to the
address above, using `-test.run=^TestFullStateKeyAudit$ -test.v -test.timeout=2m`.
`source-preserved.txt` records a subsequent check of all 230 original artifact
files against their retained manifest.

`windows-handover.txt` and `linux-race.txt` cover:

- Public-key-1 final ticket replaced by a purchase signed by public key 2.
- Correct refund to the old signer, zero old tickets, a surviving new ticket,
  four new-signer blocks independently imported and unchanged retired account.
- 10,001-FSN and 12,020.102-FSN synthetic starting balances that fund continuation.
- 5,001-FSN starting balance that funds the first ticket but not its replacement.
- Existing rejection of consuming the sole remaining ticket without replacement.

The Linux test set runs twice with the race detector in a private network
namespace. These are sparse synthetic fixtures with explicitly assigned initial
funding. They are not full-state two-wallet, real miner/auto-buy drain, peer,
cold-restart or custody-cleanup demonstrations. Production code is unchanged.

`check-linux.sh` records the exact Linux build/run procedure. `identities.json`
and `linux-identity.txt` identify retained binaries and current source files.
`SHA256SUMS` covers all evidence except the manifest itself.
