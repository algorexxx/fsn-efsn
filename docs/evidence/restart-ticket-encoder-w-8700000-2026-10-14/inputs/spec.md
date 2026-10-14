# W-backed continuation from 8,400,000 to 8,700,000

Execute 300,000 new historical blocks by continuing the verified W-backed
checkpoint in place. The preceding range passed seven commands, ten preservation
checks, both cold comparisons, all manifests, outer cleanup and host exit.
Its automatic SHA256SUMS is
14f9837374482bd21410fa50ffaabbda3fb8ca19d4b88d0c313b42d415122df4;
its separately reviewed REPORT_SHA256SUMS is
e8934c138fa24ff20f9595fd6e3e155878354096c290d4824ce7d2b83244b91d.
Both are checked before dispatch. Preserve all prior completed and failed records.

Reuse byte-identical image, replay, monitoring and verification controllers.
Retained replay executable SHA256 remains
b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245.
Only the observer's endpoint literal changes. No runtime, toolchain, identity
manifest or production selection changes; no unchanged test reruns.

Finite limits: fresh 75 GiB sampled database allocation, 30-second samples,
21,600-second cooperative replay stop, 22,500-second Go timeout, 23,400-second
replay outer timeout plus 20-second kill grace. The entire image attachment,
preparation, replay, cold verification and detach have a 28,800-second
(eight-hour) outer cap plus 20-second grace. Never extend a running limit.
Any stop/failure stays incomplete pending review; no automatic next writer.

The completed 300,000-block range took 184.764 wall-clock replay minutes
(172.659 monotonic), plus 132.485 wall-clock minutes outside replay.
Clock differences are recorded and unexplained. It grew 4.245 GiB to
63.361 GiB. Keep the same range to retain time margin for varying activity;
recent same-size ranges took up to about four replay hours. A 75 GiB ceiling gives
11.639 GiB for net growth, over twice the largest of the last three measured ranges
(5.511 GiB). This amortizes verification cost while bounding the next workload.
Later activity may differ; these are not guarantees or an all-history estimate.
A completed range extends F12/G1 historical evidence without rerunning accepted
blocks. All prior failed/refused attempts stay sealed.

Use the same W: image/UUID, one attachment owner, private mount/network
namespaces, loopback down, GOMAXPROCS=2 and protected read-only views.
Preserve the local 7,170,976 fallback, independent 2,400,000 recovery, original
backup, baselines and archives. Running reserves stay 20 GiB Linux/image,
50 GiB D: and 100 GiB W:. Starting floors stay Linux >21 GiB, D: >51 GiB,
W: >101 GiB plus declared growth, image >21 GiB plus declared growth.
Actual mounted capacity, exact cold inventory and identity must pass before
writing. Refuse wrong mount/UUID or fallback to an ordinary local directory.

Require exact 8,700,000 reference commitments, warm/cold ticket agreement,
both cold readers, closed inventory, preservation/evidence verification,
outer filesystem/unmount/detach and host exit. Seal final outer records
separately from the original inner automatic manifest. No full image/live
LevelDB hash, blind retry, key use, public peer contact, activation, cleanup
or D: expansion. Further ranges depend on reviewed completion and capacity.
