# Complete-backup startup preflight passed

Verified pass, 9 October 2026, 19:29:58 UTC. The existing unselected
`core.CheckRestoredState` accepts the complete preserved backup under its explicit
in-process test profile. It validates the expected genesis and stored configuration,
anchor/head structure, available head state, stored ticket commitment and
candidate ticket re-encoding at height 15,130,080.

- Head: `0xe93ffded087a79097d4309c7831690161db6ed136f4b1a22c4c83a99db80f99f`
- State: `0x1526799d6f10f4a4467e4dd4f3b1f81ca1479822bb2c24aa541ac66f889ccffc`
- Tickets: `0xe4e079c525c189eb30ca22ba57bbd4af8b44050e2fc1618c2157107b00820e2c`

Both commands exited zero. The observer checked the read-only mount and used
read-only LevelDB; a shared lock on the actual database LOCK excluded ordinary
writers, with the separate replay run lock held. Execution used isolated mount
and network namespaces, loopback down, offline dependencies and one Go worker.
All 56,107 backup metadata entries / 117,170,022,674 logical bytes remain equal
to the sealed replay inventory before and after. No backup copy, full backup
rehash, writable startup, production profile change or real-key signing occurred.
Candidate runtime/source and observer identity checks pass.

The [first refusal](../restart-restored-backup-preflight-2026-10-09/RESULTS.md)
is preserved: the initial test supplied the anchor on a caller configuration
copy, but the mainnet path intentionally trusts the global mainnet profile.
The fresh test installs and restores that test-only global profile, as the
earlier CLI shim does. No runtime repair was needed.

The backup head is a test anchor here, not a selected recovery anchor. This
direct check closes the complete-backup **read-only preflight** case only.
Writable restored CLI startup, recovery/handover acceptance for the final chosen
executable, independent review, historical replay and release decisions remain
open. Existing small passing fixtures need no repetition.
