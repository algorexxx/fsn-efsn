# Complete-backup restored startup and restart

Completed 20 October 2026 at 04:26:33 UTC; independent record review passed at
04:58:35 UTC. The retained, unselected guard/encoder CLI opened the complete
56,107-file backup copy, shut down with normal pruning, and reopened in a fresh
process. Both observations retain height 15,130,080, hash
`0xe93ffded087a79097d4309c7831690161db6ed136f4b1a22c4c83a99db80f99f`,
state root and ticket commitment. Mining and automatic purchase stayed disabled.

The existing read-only identity guard ran before service initialization. Both
shutdowns wrote the expected head, parent and head-minus-127 states, with no
failed commit, dangling trie or fatal error. First open/query/shutdown took
30.10 wall seconds and the fresh restart took 1.52 seconds. The exact retained
CLI SHA-256 is `07aa74a3f58132e5ff1465152402d5ea3b01738c0017af5dfd5672a75a2550cd`;
all 1,208 source files and pinned inputs remain unchanged.

All 56,107 starting hashes matched the original sealed backup inventory before
any writable attachment. Following shutdown, filesystem check and detach, the
read-only reattachment produced 56,168 closed hashes and both actual cold tests
passed. Complete header RLP, head/state/ticket/body/receipt commitments, bloom,
TD and counts match the preserved endpoint: 491 tickets and one transaction /
receipt. The closed inventory SHA-256 is
`9af3c403a41e439eaf396a620a65f0d3621cc18c6944acc6d76dc0dec1eee7fc`.
The physical database inventory changed by 64 new, 3 removed and 3 changed
retained files; its logical byte total is 116,957,665,789. No unchanged-file claim
is made across writable startup. Cold readers left the post-startup metadata
unchanged.

All 34 exit-bearing records are zero. Both filesystem checks, UUID/attachment
checks and cleanup pass. All 271 recorded resource samples and finite limits
pass; sampled minimum free space is /home/rehearsal: 21.471 GiB, /mnt/d: 52.575 GiB, /mnt/w: 2866.748 GiB, image: 145.422 GiB.
The whole job recorded 7,968.207 monotonic seconds and 8,621.438 host wall seconds.
Host finish precedes Linux completion by about one second. Preserve these
unexplained clock differences without assuming synchronized clocks.

At 04:54 UTC the dispatcher and test processes were absent, and no test/ext4
image loop or matching mount remained. A first supplemental assertion requiring
no loop devices anywhere failed on unrelated read-only autoclear Docker ISO
attachments; its secondary transcription is preserved in
`post-state-refusal.json`. The subsequent raw targeted observation is
`post-state.json`. No loop was modified and the original successful job's
acceptance conditions were not changed.

Original-backup, local fallback and independent recovery metadata remain
unchanged; the protected final replay image's size/mtime remain unchanged and
that image was never attached. Source/executable identities were rechecked in
all three phases. The 17 input and 24 startup-manifest entries still verify.
Private network namespaces had only loopback down, one owner held the image
and source locks, the original backup view was read-only, and the test-only
anchor used the preserved mainnet configuration and tip. The disposable W:
startup image is retained. No real key or public peer was used.

This qualifies complete-backup startup/restart for this unselected Linux
candidate and test anchor. It does not select a release, establish the accepted
parent/trust decision, complete independent codec/consensus review, demonstrate
machine power-loss recovery, or qualify the candidate's recovery command and
handover on complete state. The latter is the next useful bounded acceptance
slice, using the existing compact-state/operator helpers and public test keys.
Do not rerun unchanged small refusal or synthetic pruning tests, or repeat this
117 GB copy. Final package and clean-host acceptance remain separate.
