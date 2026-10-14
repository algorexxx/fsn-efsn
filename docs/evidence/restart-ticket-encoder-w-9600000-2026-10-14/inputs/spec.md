# W-backed continuation from 9,300,000 to 9,600,000

Execute 300,000 new historical blocks by continuing the verified W-backed
checkpoint in place. The preceding range passed seven commands, ten preservation
checks, both cold comparisons, all manifests, outer cleanup and host exit.
Its automatic SHA256SUMS is
abbc96cf259a2b79331a34d59f61da8a08c9a5248185389ee7d84183330e5b5c;
its separately reviewed REPORT_SHA256SUMS is
4f7d9908d2bc3067f9936fb65db7a910a06127db10185c3f42659aa27de4c02f.
Both are checked before dispatch. Preserve all prior completed and failed records.

Reuse byte-identical image, replay, monitoring and verification controllers.
Retained replay executable SHA256 remains
b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245.
Only the observer's endpoint literal changes. No runtime, toolchain, identity
manifest or production selection changes; no unchanged test reruns.

Finite limits: fresh 87 GiB sampled database allocation, 30-second samples,
21,600-second cooperative replay stop, 22,500-second Go timeout, 23,400-second
replay outer timeout plus 20-second kill grace. The entire image attachment,
preparation, replay, cold verification and detach have a 28,800-second
(eight-hour) outer cap plus 20-second grace. Never extend a running limit.
Any stop/failure stays incomplete pending review; no automatic next writer.

The completed 300,000-block range took 163.436 wall-clock replay minutes
(156.306 monotonic), plus 105.468 wall-clock minutes outside replay.
Clock differences are recorded and unexplained. It grew 3.478 GiB from
actual startup allocation to 74.764 GiB. Keep the same range to retain time margin for varying activity;
recent same-size ranges took up to about four replay hours. An 87 GiB ceiling gives
12.236 GiB for net growth, over twice the largest of the last six measured ranges
(5.511 GiB). This amortizes verification cost while bounding the next workload.
Later activity may differ; these are not guarantees or an all-history estimate.
A completed range extends F12/G1 historical evidence without rerunning accepted
blocks. All prior failed/refused attempts stay sealed.

The prior supplemental startup capture recorded 4 KiB more allocated space than
the preceding closed measurement. All 36,557 file hashes nevertheless matched
before replay. Preserve the failed capture and revised observation; the cause of
the allocation difference remains unestablished. Future startup observations
record allocation separately from the unchanged exact checkpoint hash gate.

Use the same W: image/UUID, one attachment owner, private mount/network
namespaces, loopback down, GOMAXPROCS=2 and protected read-only views.
Preserve the local 7,170,976 fallback, independent 2,400,000 recovery, original
backup, baselines and archives. Running reserves stay 20 GiB Linux/image,
50 GiB D: and 100 GiB W:. Starting floors stay Linux >21 GiB, D: >51 GiB,
W: >101 GiB plus declared growth, image >21 GiB plus declared growth.
Actual mounted capacity, exact cold inventory and identity must pass before
writing. Refuse wrong mount/UUID or fallback to an ordinary local directory.

Require exact 9,600,000 reference commitments, warm/cold ticket agreement,
both cold readers, closed inventory, preservation/evidence verification,
outer filesystem/unmount/detach and host exit. Seal final outer records
separately from the original inner automatic manifest. No full image/live
LevelDB hash, blind retry, key use, public peer contact, activation, cleanup
or D: expansion. Further ranges depend on reviewed completion and capacity.
