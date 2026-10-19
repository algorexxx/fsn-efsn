# W-backed continuation from 15,000,000 to 15,130,080

Execute the final 130,080 historical blocks by continuing the verified W-backed
checkpoint in place. The preceding range passed seven commands, ten preservation
checks, both cold comparisons, all manifests, outer cleanup and host exit.
Its automatic SHA256SUMS is
8fe343559e74fcf02c08aae7d7b3a0ddf1e3539b31c27e9c296b8f7a824aecc1;
its separately reviewed REPORT_SHA256SUMS is
1e0191e75e44cde4de2c1d63de8e8f69f4c61a5318990cde18753f6cddd26f7c.
Both are checked before dispatch. Preserve all prior completed and failed records.

Reuse byte-identical image, replay, monitoring and verification controllers.
Retained replay executable SHA256 remains
b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245.
Only the observer's endpoint literal changes. No runtime, toolchain, identity
manifest or production selection changes; no unchanged test reruns.

Finite limits: fresh 120 GiB sampled database allocation, 30-second samples,
21,600-second cooperative replay stop, 22,500-second Go timeout, 23,400-second
replay outer timeout plus 20-second kill grace. The entire image attachment,
preparation, replay, cold verification and detach have a 28,800-second
(eight-hour) outer cap plus 20-second grace. Never extend a running limit.
Any stop/failure stays incomplete pending review; no automatic next writer.

The preceding 300,000-block range took 15.935 wall-clock replay minutes
(15.596 monotonic), plus 337.758 wall-clock minutes outside replay.
Clock differences are recorded and unexplained. It grew 0.254 GiB from actual
startup allocation to 107.826 GiB. This final 130,080-block range reaches the
preserved backup tip, without going beyond available history. About 126 minutes
remained under the whole-job cap, but recent ranges left as little as 81 minutes.
Keep all time limits. A 120 GiB ceiling gives 12.174 GiB for net growth, over
twice the largest measured recent net growth (5.511 GiB). The smaller final
range adds the remaining historical coverage while retaining costly cold checks.
Timing and growth are not guaranteed. Completion extends F12/G1 evidence;
it does not close restored-startup, recovery, handover or independent review.

Starting allocation in the preceding run matched its prior closed measurement.
All 55,695 starting file hashes matched before replay and the review independently
compares the saved hash maps. Earlier allocation differences and the failed
supplemental assertion remain preserved, with cause unestablished. Record
allocation separately from the unchanged exact checkpoint hash gate.
The earlier filename/line-ending preflight refusals and WSL monitoring interruption/recovery
remain sealed in their original bundles. This observer and patch are prepared
with exact bytes, preserving original newlines. No controller gate is changed.

Use the same W: image/UUID, one attachment owner, private mount/network
namespaces, loopback down, GOMAXPROCS=2 and protected read-only views.
Preserve the local 7,170,976 fallback, independent 2,400,000 recovery, original
backup, baselines and archives. Running reserves stay 20 GiB Linux/image,
50 GiB D: and 100 GiB W:. Starting floors stay Linux >21 GiB, D: >51 GiB,
W: >101 GiB plus declared growth, image >21 GiB plus declared growth.
Actual mounted capacity, exact cold inventory and identity must pass before
writing. Refuse wrong mount/UUID or fallback to an ordinary local directory.

Require exact 15,130,080 reference commitments, warm/cold ticket agreement,
both cold readers, closed inventory, preservation/evidence verification,
outer filesystem/unmount/detach and host exit. Seal final outer records
separately from the original inner automatic manifest. No full image/live
LevelDB hash, blind retry, key use, public peer contact, activation, cleanup
or D: expansion. After verified completion and cleanup, review the remaining
acceptance gaps; no replay range extends beyond the preserved backup tip.
