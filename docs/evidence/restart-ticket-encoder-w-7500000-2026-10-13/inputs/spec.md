# W-backed continuation from 7,200,000 to 7,500,000

Execute 300,000 new historical blocks, continuing the verified W-backed target
in place. The prior trial passed all seven commands, both cold comparisons,
eleven preservation checks, outer filesystem/detach completion and host exit.
Its automatic SHA256SUMS is
65f8f2630a4d028f979e5a8ec30fb51f0f3774691dbe4389f1236a7602077128;
its separately reviewed REPORT_SHA256SUMS is
903ea8add6ec0e636407b297ee226e916cd820d5eb1aedadd715df53f0fac179.
Both are checked before dispatch. Keep all prior failed/sealed records.

Reuse byte-identical image, replay, monitoring and verification controllers.
Retained replay executable SHA256 remains
b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245.
Only the observer's endpoint literal changes. No node runtime, toolchain,
identity manifest or production selection changes; no unchanged test reruns.

Finite limits: 54 GiB sampled database allocation, 30-second samples, 21,600
seconds cooperative replay stop, 22,500 seconds Go timeout and 23,400 seconds
replay outer timeout plus 20-second kill grace. The host wraps the complete
image attachment, preparation, replay, cold checks and detach in 28,800 seconds
(eight hours), plus 20-second grace. This budgets slow W: verification around
the previously used six-hour replay envelope. Never extend a running limit.
A stop/failure remains incomplete and needs review; no automatic next writer.

The prior 29,024-block trial took about 22.1 wall-clock minutes (20.3 monotonic),
with about 65 minutes preparation/verification, and 0.589 GiB live DB growth.
The 54 GiB ceiling leaves about 9.38 GiB growth above 44.622 GiB, compared with
about 6.09 GiB from a linear short-trial illustration. Neither the size nor
rate illustration predicts later workloads. A larger finite range amortizes
measured verification cost without weakening acceptance.

Use the same W: image/UUID, one attachment owner, private mount and network
namespaces, loopback down, GOMAXPROCS=2 and protected read-only views. Preserve
local 7,170,976 fallback and independent 2,400,000 recovery; original backup,
baselines and archives remain intact. Native per-batch image/D: checks and
sampled Linux/W: checks retain 20/50/100 GiB running reserves. Starting floors
stay Linux >21 GiB, D: >51 GiB, W: >101 GiB + declared remaining growth, image
filesystem >21 GiB + growth. Actual mounted capacity and exact cold starting
inventory are writer gates; refuse wrong mount, UUID or fallback directory.

On success require exact 7,500,000 reference commitments, matching warm/cold
tickets, both cold readers, closed byte inventory, preservation/evidence verifier,
outer filesystem/unmount/detach and host exit. Outer completion records occur
after the inner manifest and are separately sealed, never rewritten into it.
No full image/live LevelDB hash, blind retry, key use, public peer contact,
activation, cleanup or D: expansion. Future ranges depend on actual results.
