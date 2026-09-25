# Cold header validation evidence

25 September 2026, baseline `04ad861`. See the
[report](../../restart-cold-header-validation.md) for expected outcomes and limits.
All changes in this investigation are tests, documentation and evidence.

| Run | Eight-case characterization result |
| --- | --- |
| `windows-current.txt` | PASS, 1.69 seconds |
| `windows-pre-p9.txt` | PASS, 1.55 seconds, using pre-P9 runtime overlay |
| `linux-race.txt` | PASS, 16.11 seconds, current candidate with race detection |

Five cases deliberately expect incomplete ticket reconstruction to fail. One
expects an invalid gas-used header to fail. One validates reconstruction from
pre-stored headers/bodies/receipts; one imports full blocks and then reopens in
another process. PASS means the specified behavior was observed, including those
expected refusals. No result establishes headers-only or network fast sync.

`check-windows.ps1` builds and runs the current matrix. For the pre-P9 comparison,
run `prepare-baseline.py`, then pass the printed overlay path with
`-Overlay <path> -Label pre-p9` to the PowerShell script. The overlay replaces
only the three P9 runtime files with bytes from `bcbd1ce`; it does not edit the
working source tree. `baseline-sources.json` pins those earlier bytes. P9 was the
only production Go difference between `bcbd1ce` and `04ad861`.

`check-linux.sh` uses WSL `FusionRehearsal`, the `rehearsal` user, the existing Go
toolchain and an isolated network namespace. There are no peer connections in
these cases. `TMPDIR=/tmp` keeps synthetic data inside the Linux filesystem.
Both platforms use only the repository's existing synthetic fixture and public
test key. Build logs are empty on successful quiet compilation. All scripts
overwrite their named result files; preserve existing evidence separately when
running a new comparison.

`write-identities.py` checks the recorded case counts/outcomes, pins sources and
local test binaries, and writes `SHA256SUMS`. The checksums exclude their own
manifest. `.gitattributes` preserves raw bytes. Ignored executables, temporary
overlay files and disposable databases are not release artifacts.
