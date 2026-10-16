# W-backed continuation from 11,700,000 to 12,000,000

Execute 300,000 new historical blocks by continuing the verified W-backed
checkpoint in place. The preceding range passed seven commands, ten preservation
checks, both cold comparisons, all manifests, outer cleanup and host exit.
Its automatic SHA256SUMS is
452f08a0f41a05b25d0356e9c8ade16bf00c4010f589b5abd9dcbbf971a1318a;
its separately reviewed REPORT_SHA256SUMS is
0e4a37a161a9b6c5fddb652cc0b2fd27137e11ea2698756b3770a92cdb8a915d.
Both are checked before dispatch. Preserve all prior completed and failed records.

Reuse byte-identical image, replay, monitoring and verification controllers.
Retained replay executable SHA256 remains
b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245.
Only the observer's endpoint literal changes. No runtime, toolchain, identity
manifest or production selection changes; no unchanged test reruns.

Finite limits: fresh 112 GiB sampled database allocation, 30-second samples,
21,600-second cooperative replay stop, 22,500-second Go timeout, 23,400-second
replay outer timeout plus 20-second kill grace. The entire image attachment,
preparation, replay, cold verification and detach have a 28,800-second
(eight-hour) outer cap plus 20-second grace. Never extend a running limit.
Any stop/failure stays incomplete pending review; no automatic next writer.

The completed 300,000-block range took 189.514 wall-clock replay minutes
(184.380 monotonic), plus 183.622 wall-clock minutes outside replay.
Clock differences are recorded and unexplained. It grew 4.461 GiB from actual
startup allocation to 99.830 GiB. Keep the same range: about 107 minutes remained
under the whole-job cap, versus 81 in the preceding range; earlier same-size
ranges reached four replay hours. Do not increase the range or time limits.
A 112 GiB ceiling gives 12.170 GiB for net growth, over twice the largest
measured net growth among recent ranges (5.511 GiB). This adds new historical
coverage while amortizing costly cold checks. Later activity may differ;
timing and growth are not guaranteed or an all-history estimate. A completed
range extends F12/G1 historical evidence without rerunning accepted blocks.
All prior failed/refused attempts stay sealed.

Starting allocation in the preceding run matched its prior closed measurement.
All 49,313 starting file hashes matched before replay and the review independently
compares the saved hash maps. Earlier allocation differences and the failed
supplemental assertion remain preserved, with cause unestablished. Record
allocation separately from the unchanged exact checkpoint hash gate.
The preceding preflight refusal caught observer line-ending changes before any
attachment or writer; byte-preserving correction and repeated preflight passed.
Its 18 preserved refusal files remain in the prior automatic manifest. This
observer and patch are prepared with exact bytes, preserving original newlines.
The earlier WSL monitoring interruption and recovered access remain sealed;
no forced restart occurred, final verification passed and cause is unestablished.

Use the same W: image/UUID, one attachment owner, private mount/network
namespaces, loopback down, GOMAXPROCS=2 and protected read-only views.
Preserve the local 7,170,976 fallback, independent 2,400,000 recovery, original
backup, baselines and archives. Running reserves stay 20 GiB Linux/image,
50 GiB D: and 100 GiB W:. Starting floors stay Linux >21 GiB, D: >51 GiB,
W: >101 GiB plus declared growth, image >21 GiB plus declared growth.
Actual mounted capacity, exact cold inventory and identity must pass before
writing. Refuse wrong mount/UUID or fallback to an ordinary local directory.

Require exact 12,000,000 reference commitments, warm/cold ticket agreement,
both cold readers, closed inventory, preservation/evidence verification,
outer filesystem/unmount/detach and host exit. Seal final outer records
separately from the original inner automatic manifest. No full image/live
LevelDB hash, blind retry, key use, public peer contact, activation, cleanup
or D: expansion. Further ranges depend on reviewed completion and capacity.
