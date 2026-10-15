# W-backed continuation from 10,500,000 to 10,800,000

Execute 300,000 new historical blocks by continuing the verified W-backed
checkpoint in place. The preceding range passed seven commands, ten preservation
checks, both cold comparisons, all manifests, outer cleanup and host exit.
Its automatic SHA256SUMS is
18750a4f084611ae09ad186867c5df4a54a5a93aeff2290324df7815d52cb4e1;
its separately reviewed REPORT_SHA256SUMS is
bea1ceac6fca8244be408670cacfab8f96ed9668c7949d7d68a608745735e0db.
Both are checked before dispatch. Preserve all prior completed and failed records.

Reuse byte-identical image, replay, monitoring and verification controllers.
Retained replay executable SHA256 remains
b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245.
Only the observer's endpoint literal changes. No runtime, toolchain, identity
manifest or production selection changes; no unchanged test reruns.

Finite limits: fresh 98 GiB sampled database allocation, 30-second samples,
21,600-second cooperative replay stop, 22,500-second Go timeout, 23,400-second
replay outer timeout plus 20-second kill grace. The entire image attachment,
preparation, replay, cold verification and detach have a 28,800-second
(eight-hour) outer cap plus 20-second grace. Never extend a running limit.
Any stop/failure stays incomplete pending review; no automatic next writer.

The completed 300,000-block range took 122.386 wall-clock replay minutes
(118.698 monotonic), plus 131.763 wall-clock minutes outside replay.
Clock differences are recorded and unexplained. It grew 3.113 GiB from actual
startup allocation to 85.687 GiB. Keep the same range to retain time margin for
varying activity; recent same-size ranges took up to about four replay hours.
A 98 GiB ceiling gives 12.313 GiB for net growth, over twice the largest measured
net growth among recent ranges (5.511 GiB). This amortizes verification cost while
bounding the next workload. Later activity may differ; these are not guarantees
or an all-history estimate. A completed range extends F12/G1 historical evidence
without rerunning accepted blocks. All prior failed/refused attempts stay sealed.

Starting allocation in the preceding run was 4,096 bytes above its prior closed
measurement, with cause unestablished. All 42,373 starting file hashes matched
before replay and the review independently compares the saved hash maps. The
current supplemental capture passed; the earlier failed allocation assertion
remains preserved. Record allocation separately from the unchanged exact
checkpoint hash gate; allocation equality does not replace content verification.

Use the same W: image/UUID, one attachment owner, private mount/network
namespaces, loopback down, GOMAXPROCS=2 and protected read-only views.
Preserve the local 7,170,976 fallback, independent 2,400,000 recovery, original
backup, baselines and archives. Running reserves stay 20 GiB Linux/image,
50 GiB D: and 100 GiB W:. Starting floors stay Linux >21 GiB, D: >51 GiB,
W: >101 GiB plus declared growth, image >21 GiB plus declared growth.
Actual mounted capacity, exact cold inventory and identity must pass before
writing. Refuse wrong mount/UUID or fallback to an ordinary local directory.

Require exact 10,800,000 reference commitments, warm/cold ticket agreement,
both cold readers, closed inventory, preservation/evidence verification,
outer filesystem/unmount/detach and host exit. Seal final outer records
separately from the original inner automatic manifest. No full image/live
LevelDB hash, blind retry, key use, public peer contact, activation, cleanup
or D: expansion. Further ranges depend on reviewed completion and capacity.
