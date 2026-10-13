# W-backed continuation from 7,800,000 to 8,100,000

Execute 300,000 new historical blocks by continuing the verified W-backed
checkpoint in place. The preceding range passed seven commands, ten preservation
checks, both cold comparisons, all manifests, outer cleanup and host exit.
Its automatic SHA256SUMS is
740dfd239f8bb5da62f2d77816992275f7c7e88432189e76943612419f200ef1;
its separately reviewed REPORT_SHA256SUMS is
1290ed422b2bfd8b2f8a5d0cd3772e1ad7daa32f3cab1e7db456c140e7aa671a.
Both are checked before dispatch. Preserve all prior completed and failed records.

Reuse byte-identical image, replay, monitoring and verification controllers.
Retained replay executable SHA256 remains
b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245.
Only the observer's endpoint literal changes. No runtime, toolchain, identity
manifest or production selection changes; no unchanged test reruns.

Finite limits: fresh 67 GiB sampled database allocation, 30-second samples,
21,600-second cooperative replay stop, 22,500-second Go timeout, 23,400-second
replay outer timeout plus 20-second kill grace. The entire image attachment,
preparation, replay, cold verification and detach have a 28,800-second
(eight-hour) outer cap plus 20-second grace. Never extend a running limit.
Any stop/failure stays incomplete pending review; no automatic next writer.

The completed 300,000-block range took 242.953 wall-clock replay minutes
(235.471 monotonic), plus 98.846 wall-clock minutes outside replay. The clock
difference is recorded but not explained. It grew 5.511 GiB to 55.023 GiB.
Keeping the same range leaves margin under the six-hour replay cap; a 67 GiB
ceiling gives 11.977 GiB for net growth, over twice the observed net growth.
This amortizes verification cost while bounding the next workload. Later
activity may differ; these are not guarantees or an estimate for all remaining
history. A completed range extends F12/G1 historical transition evidence
without rerunning accepted blocks. All prior failed/refused attempts stay sealed.

Use the same W: image/UUID, one attachment owner, private mount/network
namespaces, loopback down, GOMAXPROCS=2 and protected read-only views.
Preserve the local 7,170,976 fallback, independent 2,400,000 recovery, original
backup, baselines and archives. Running reserves stay 20 GiB Linux/image,
50 GiB D: and 100 GiB W:. Starting floors stay Linux >21 GiB, D: >51 GiB,
W: >101 GiB plus declared growth, image >21 GiB plus declared growth.
Actual mounted capacity, exact cold inventory and identity must pass before
writing. Refuse wrong mount/UUID or fallback to an ordinary local directory.

Require exact 8,100,000 reference commitments, warm/cold ticket agreement,
both cold readers, closed inventory, preservation/evidence verification,
outer filesystem/unmount/detach and host exit. Seal final outer records
separately from the original inner automatic manifest. No full image/live
LevelDB hash, blind retry, key use, public peer contact, activation, cleanup
or D: expansion. Further ranges depend on reviewed completion and capacity.
