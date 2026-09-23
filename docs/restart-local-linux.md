# Local Linux rehearsal environment

Status, 23 September 2026: reboot completed; Ubuntu 24.04 is running under WSL 2
with its virtual disk on D:. Linux/CGO synthetic tests have run, including a
newly reproduced miner race. The 109.12 GiB disposable chaindata copy is complete
and every file has passed SHA-256 verification.
No networked node has been started. See [Linux findings](restart-linux-investigation.md).

The isolated read-only database probe also passed: the recorded head, complete
ticket set/commitment, account observations and eight sampled block/receipt
commitments match. Several sampled older state roots are unavailable; this is
not a demonstrated archive-state or fully replayed backup.

## Machine and storage observations

| Resource | Observed |
| --- | --- |
| Windows | Windows 11 Pro 25H2, build 26200.9457 |
| CPU | Intel i9-12900K; firmware virtualization and SLAT available |
| RAM | 31.8 GiB total; 18.3 GiB free after reboot; WSL limited to 6 GB |
| D: | NTFS, 465.7 GiB total, 266.6 GiB free |
| W: | Network share, about 3.29 TiB free; operator describes a ZFS array of slower HDDs |
| Preserved chaindata | 56,107 files, 117,170,022,674 bytes (109.12 GiB) |
| Installed WSL | 2.7.14.0; bundled kernel 6.18.33.2-2 |

These are point-in-time observations, not capacity reservations. The inventory
read only file metadata in `fusion-node/data/efsn/chaindata`; it did not open the
keystore or rehash the entire backup.

Use D: for the Linux ext4 virtual disk, build cache, and one active database.
Use W: for checksummed preservation copies, closed rehearsal exports, and other
cold artifacts. Keeping active random database I/O on local storage is the
working performance choice; no network-array benchmark has been performed.
Do not put a running WSL virtual disk on the network share as an untested shortcut.

Two 109.12 GiB copies on D: would leave only about 48 GiB before the OS, build
caches, swap, and replay growth. Start with one active copy; additional replay
databases require a measured capacity decision. W:'s capacity does not remove
that local active-working-set limit. ZFS snapshots must be arranged on the
storage host; access to a mapped drive does not itself give snapshot control.

## Changes already made

- Created `D:\FusionRehearsal` and its `swap` subdirectory.
- Created the previously absent `C:\Users\Peter\.wslconfig`:

  ```ini
  [wsl2]
  memory=6GB
  processors=4
  swap=2GB
  swapFile=D:\\FusionRehearsal\\swap\\swap.vhdx
  guiApplications=false
  defaultVhdSize=200GB
  ```

- Ran Microsoft's `wsl --install --no-distribution --web-download` from an
  elevated, hidden PowerShell process using the reviewed
  [platform installer script](../tests/restart/install-wsl-platform.ps1).
- Installer exit code: 0. `VirtualMachinePlatform` reports enabled; installer
  explicitly reports that the changes require reboot to take effect.
- After the operator's reboot, verified the hypervisor is active and installed
  Ubuntu 24.04 under the dedicated distribution name `FusionRehearsal`.
- Verified the registered base path is `D:\FusionRehearsal\Ubuntu`; the virtual
  disk is `ext4.vhdx` there. Linux reports Ubuntu 24.04.5 LTS, kernel
  `6.18.33.2-microsoft-standard-WSL2`, four CPUs, about 5.8 GiB RAM and 2 GiB swap.
- Created the non-root Linux user `rehearsal`. `/etc/wsl.conf` retains systemd
  and sets this default user; use `-u rehearsal` explicitly in current sessions.
- Installed build-essential, GCC 13.3.0 and the required transfer/build tools.
- Installed Go 1.21.3 at `/opt/fusion-toolchain/go`. The Linux archive SHA-256
  `1241381b2843fae5a9707eec1f8fb2ef94d827990582c7c7c32f5bdfbfd420c8`
  matches the [official Go release metadata](https://go.dev/dl/?mode=json&include=all).
  This is a historical reproduction compiler, not a production-toolchain choice.

No reboot was requested by the script. Logs and result JSON are under ignored
`tmp/restart-wsl-install`. These WSL settings apply globally to this Windows
user's WSL 2 environments, including future distributions. The 200 GB setting is
a virtual-disk maximum, not a reservation of physical space. Microsoft documents
the [configuration settings](https://learn.microsoft.com/en-us/windows/wsl/wsl-config)
and [installation commands](https://learn.microsoft.com/en-us/windows/wsl/basic-commands).

The WSL platform itself uses Windows system storage. The distribution, working
database, and swap are on D:. No files have been written to W: yet.

## Working locations and commands

The completed distribution installation command was:

```powershell
wsl --install Ubuntu-24.04 --name FusionRehearsal --location D:\FusionRehearsal\Ubuntu --no-launch --web-download
```

Do not reinstall it. Enter the existing environment with:

```powershell
wsl -d FusionRehearsal -u rehearsal
```

| Location inside Linux | Purpose |
| --- | --- |
| `/home/rehearsal/fsn-efsn` | Source export, initially commit `a93f45b`, plus recorded investigation-only test changes |
| `/opt/fusion-toolchain/go` | Verified baseline compiler |
| `/home/rehearsal/data/efsn/chaindata` | Verified disposable database copy |
| `/home/rehearsal/results` | Test logs, copy manifests and inspection output |

The Linux source is an exported snapshot, not another Git checkout. Edits in the
Windows repository do not automatically update it. Copy explicitly selected
files or export a new commit, record their hashes, and retain evidence of the
tested inputs. Go/module/build caches remain inside the D:-backed Linux disk.

```bash
cd /home/rehearsal/fsn-efsn
export PATH=/opt/fusion-toolchain/go/bin:$PATH
export GOTOOLCHAIN=local GOMAXPROCS=4 CGO_ENABLED=1
export GOFLAGS='-p=2 -mod=readonly'
go test ./tests/restart -v -count=1 -timeout=90s
python3 tests/restart/run-parent-time-experiment.py --go /opt/fusion-toolchain/go/bin/go
python3 tests/restart/run-receipt-copy-experiment.py --go /opt/fusion-toolchain/go/bin/go
```

The unchanged production miner fails the race scenario. The last command tests
a temporary compiler overlay; it does not fix production source. See the linked
Linux report for separate baseline/overlay results and test limitations.

An unchanged-production baseline binary is retained at
`/home/rehearsal/bin/efsn-a93f45b`, built with `CGO_ENABLED=1`, `-trimpath`, and
pinned modules. `efsn version` reports `5.0.3-stable`; `go mod verify` passed.
Its digest and module inputs are in the Linux evidence. This binary is for
comparison and investigation; it includes the known unfixed defects.

## Verified database copy

On 23 September at 20:04:30 UTC, all 56,107 files totaling 117,170,022,674 bytes
passed destination SHA-256 verification. Source and destination filename/size/
modification-time inventories match; source inventory remained unchanged after
copying. The source was bind-mounted read-only in the copy process's private
mount namespace. No keystore, node key, or peer database was included.

The full manifest is
`/home/rehearsal/results/backup-copy-2026-09-23/sha256sum.txt`, SHA-256
`a41ebd5f4f250cbb22b7c0d9ac484b7b1a503d6bc6ff7ff57cec97915cbe88c6`.
Keep that file with preservation artifacts; its digest alone cannot verify an
individual database file.
An identical second manifest copy is retained in the Windows workspace at
`tmp/restart-linux/backup-copy-2026-09-23/sha256sum.txt` (ignored by Git).
The [copy metadata](evidence/restart-linux-2026-09-23/backup-copy-metadata.json)
records the paths, inventories and checksums.

To repeat only the offline inspection, compile the probe in the source directory
as `rehearsal` with the Go environment above:

```bash
go test -c -o /home/rehearsal/restart-tests ./tests/restart
```

Enter a separate root shell using `wsl -d FusionRehearsal -u root`, then run:

```bash
unshare --mount --net --propagation private bash <<'PROBE'
set -eu
test -f /home/rehearsal/results/backup-copy-2026-09-23/verified.txt
mkdir -p /mnt/fusion-rehearsal-probe
mount --bind /home/rehearsal/data/efsn/chaindata /mnt/fusion-rehearsal-probe
mount -o remount,bind,ro /mnt/fusion-rehearsal-probe
cd /home/rehearsal/fsn-efsn/tests/restart
runuser -u rehearsal -- env FUSION_RESTART_CHAINDATA=/mnt/fusion-rehearsal-probe GOMAXPROCS=4 /home/rehearsal/restart-tests '-test.run=^TestPreservedBackupReadOnly$' -test.v -test.timeout=180s
PROBE
```

The mount and network namespace end with that command. It starts no node or
signer and opens only the disposable database in read-only mode.

The initial fast-copy pass stopped with `sendfile` error `ENOMEM`. A resumed
pass used eight workers with 1 MiB userspace buffers, skipped existing files
only after their checksums matched, and verified every destination file again.
The 6 GB WSL memory limit was retained. Do not infer disk damage from that
transport/copy error; the completed checksum pass found no mismatches.

After copying/building, D: had about 147.3 GiB free and Linux ext4 about
73.5 GiB available. The Linux disk's configured capacity remains about 200 GB.
Neither value is a reservation. A second complete database or fresh replay
requires a new capacity decision. The transfer enforced reserves of 50 GiB on
D: and 20 GiB inside Linux; set appropriate measured limits for future workloads.

## Remaining data and rehearsal work

1. Prepare a new, dedicated directory on W: for preservation artifacts. Use the
   existing authenticated mapping; do not put credentials in scripts. Copy only
   the intended public chain database and verify a full checksum manifest. Keep
   the original C: copy intact. Never treat a live database file copy as a
   consistent snapshot.
2. Retain the completed copy manifest and offline-inspection evidence. Complete
   historical replay and state completeness checks before treating the backup
   as a validated restart baseline. Restore fresh disposable copies for any
   experiment whose mutations would otherwise contaminate later comparisons.
3. Enforce isolated node execution with discovery, peers, mining, and public RPC
   disabled. Prefer an isolated network namespace for full-data probes. Validate
   genesis/head/state/ticket identities against the saved evidence before more
   invasive tests. Do not sign production-parent headers during setup.
4. Before lengthy replay, measure actual working-disk growth and available host
   space. Establish a stop threshold; do not assume free space reported inside a
   dynamically growing Linux disk equals space remaining on D:.

Docker Desktop is not required for this path. Its usual Windows Linux-container
backends also require Windows virtualization; installing it would not remove
the WSL reboot prerequisite encountered during setup. See
[Docker's Windows requirements](https://docs.docker.com/desktop/setup/install/windows-install/).
WSL results do not replace the eventual deployment-host and multi-operator rehearsal.
