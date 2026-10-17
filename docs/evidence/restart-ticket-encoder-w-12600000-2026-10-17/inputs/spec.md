# W-backed continuation from 12,300,000 to 12,600,000

Execute 300,000 new historical blocks by continuing the verified W-backed
checkpoint in place. The preceding range passed seven commands, ten preservation
checks, both cold comparisons, all manifests, outer cleanup and host exit.
Its automatic SHA256SUMS is
16614b3ca880516754083129428060e8c3dd454bb6d9764fc399662dc9179d3d;
its separately reviewed REPORT_SHA256SUMS is
a02c9cf1dcff04164a5f7eb945793c5525aa446e72e6a4a465f2e80769e70dfa.
Both are checked before dispatch. Preserve all prior completed and failed records.

Reuse byte-identical image, replay, monitoring and verification controllers.
Retained replay executable SHA256 remains
b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245.
Only the observer's endpoint literal changes. No runtime, toolchain, identity
manifest or production selection changes; no unchanged test reruns.

Finite limits: fresh 115 GiB sampled database allocation, 30-second samples,
21,600-second cooperative replay stop, 22,500-second Go timeout, 23,400-second
replay outer timeout plus 20-second kill grace. The entire image attachment,
preparation, replay, cold verification and detach have a 28,800-second
(eight-hour) outer cap plus 20-second grace. Never extend a running limit.
Any stop/failure stays incomplete pending review; no automatic next writer.

The completed 300,000-block range took 85.733 wall-clock replay minutes
(80.534 monotonic), plus 237.176 wall-clock minutes outside replay.
Clock differences are recorded and unexplained. It grew 1.324 GiB from actual
startup allocation to 102.813 GiB. Keep the same range: about 157 minutes remained
under the whole-job cap, but recent ranges left as little as 81 minutes and
earlier same-size ranges reached four replay hours. Do not increase the range
or time limits. A 115 GiB ceiling gives 12.187 GiB for net growth, over twice
the largest measured net growth among recent ranges (5.511 GiB). This adds new
historical coverage while amortizing costly cold checks. Later activity may
differ; timing and growth are not guaranteed or an all-history estimate.
A completed range extends F12/G1 evidence without rerunning accepted blocks.

Starting allocation in the preceding run matched its prior closed measurement.
All 52,179 starting file hashes matched before replay and the review independently
compares the saved hash maps. Earlier allocation differences and the failed
supplemental assertion remain preserved, with cause unestablished. Record
allocation separately from the unchanged exact checkpoint hash gate.
The earlier line-ending preflight refusal and WSL monitoring interruption/recovery
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

Require exact 12,600,000 reference commitments, warm/cold ticket agreement,
both cold readers, closed inventory, preservation/evidence verification,
outer filesystem/unmount/detach and host exit. Seal final outer records
separately from the original inner automatic manifest. No full image/live
LevelDB hash, blind retry, key use, public peer contact, activation, cleanup
or D: expansion. Further ranges depend on reviewed completion and capacity.
