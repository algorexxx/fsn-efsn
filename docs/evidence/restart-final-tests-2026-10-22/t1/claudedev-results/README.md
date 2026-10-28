# T1 result, 28 October 2026

**Pass.** The final release source (`efsn-final` 5c40e6c, the union of the mergeable branches) built with Go
1.27.3 replayed blocks 7,170,976 → 15,130,080 from the fallback database and ended on the preserved backup's
tip:

| Field at 15,130,080 | Value (equal to the backup) |
| --- | --- |
| Hash | `0xe93ffded087a79097d4309c7831690161db6ed136f4b1a22c4c83a99db80f99f` |
| State root | `0x1526799d6f10f4a4467e4dd4f3b1f81ca1479822bb2c24aa541ac66f889ccffc` |
| Ticket commitment (`MixDigest`) | `0xe4e079c525c189eb30ca22ba57bbd4af8b44050e2fc1618c2157107b00820e2c` |
| Receipt root | `0x25404575e27a7090c3b4cc474357b85f69a33901f443daf80190b275a919deb7` |
| Tickets | 491 |

Every block went through normal import, which verifies each block's state root, receipts and ticket
commitment, and the run logged no mismatch, panic or bad block.

The run started on the PC (WSL) on 22 October, stopped cleanly at 7,376,672 to move to claudedev, and resumed
there on 23 October from the same image and the same test binary (`replay.test` sha256 9405f27f…). It was
stopped once more at 7,384,352 to raise the timeout, and finished on 28 October 09:27Z after 108 h 53 min of
replay. On claudedev it ran at 10–40 blocks/s, bound by random reads of `replay.ext4` over NFS. The `FAIL`
lines in `run.log` before the final `PASS` are the two deliberate STOPs and two start-up path errors in the
first claudedev resume script, fixed before any block was replayed.

`run.log` is the complete log of all runs.
