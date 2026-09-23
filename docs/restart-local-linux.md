# Local Linux rehearsal environment

Status, 23 September 2026: WSL platform installed successfully; Windows reboot
required. No Linux distribution is installed, no chain database has been copied,
and no node was started. The existing explorer gateway is unchanged.

## Machine and storage observations

| Resource | Observed |
| --- | --- |
| Windows | Windows 11 Pro 25H2, build 26200.9457 |
| CPU | Intel i9-12900K; firmware virtualization and SLAT available |
| RAM | 31.8 GiB total; only 0.6 GiB free at the initial check |
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
- Verified WSL version and that no distributions are installed.

No reboot was requested by the script. Logs and result JSON are under ignored
`tmp/restart-wsl-install`. These WSL settings apply globally to this Windows
user's WSL 2 environments, including future distributions. The 200 GB setting is
a virtual-disk maximum, not a reservation of physical space. Microsoft documents
the [configuration settings](https://learn.microsoft.com/en-us/windows/wsl/wsl-config)
and [installation commands](https://learn.microsoft.com/en-us/windows/wsl/basic-commands).

The WSL platform itself uses Windows system storage. The planned distribution,
working database, and swap belong on D:. No files have been written to W: yet.

## Resume after Windows reboot

1. Recheck `wsl --version`, `wsl --status`, virtualization state, free RAM, and
   D: free space. Close other memory-heavy work before the node/replay workload.
2. Check `wsl --list --online` and `wsl --list --verbose`; avoid creating a
   duplicate distribution if setup has since continued.
3. Install Ubuntu 24.04 under the dedicated name and location:

   ```powershell
   wsl --install Ubuntu-24.04 --name FusionRehearsal --location D:\FusionRehearsal\Ubuntu --no-launch --web-download
   ```

   The installed WSL help confirms `--name`, `--location`, and `--no-launch`.
   This command has not yet been run. Verify the actual registration/base path
   and virtual disk location before loading any large data.
4. Configure a non-root Linux rehearsal user. Build and keep working data in
   Linux's ext4 filesystem inside the D:-backed disk. Install the chosen pinned
   baseline toolchain and build prerequisites; copy the source and evidence
   without the Windows `tmp` compiler cache or any staking identities.
5. Run the synthetic tests on Linux first, then CGO/race tests as appropriate.
   Record compiler, kernel, build inputs, and results. WSL results do not replace
   the eventual deployment-host and multi-operator rehearsal.
6. Prepare a new, dedicated directory on W: for preservation artifacts. Use the
   existing authenticated mapping; do not put credentials in scripts. Copy only
   the intended public chain database and verify a full checksum manifest. Keep
   the original C: copy intact. Never treat a live database file copy as a
   consistent snapshot.
7. Copy the preserved chaindata into one disposable Linux working datadir,
   verifying checksums before opening it. Do not copy the original keystore,
   node key, or peer database. Make the source mount read-only during copying.
8. Enforce isolated node execution with discovery, peers, mining, and public RPC
   disabled. Prefer an isolated network namespace for full-data probes. Validate
   genesis/head/state/ticket identities against the saved evidence before more
   invasive tests. Do not sign production-parent headers during setup.
9. Before lengthy replay, measure actual working-disk growth and available host
   space. Establish a stop threshold; do not assume free space reported inside a
   dynamically growing Linux disk equals space remaining on D:.

Docker Desktop is not required for this path. Its usual Windows Linux-container
backends also require Windows virtualization; installing it would not remove
the current WSL reboot prerequisite. See
[Docker's Windows requirements](https://docs.docker.com/desktop/setup/install/windows-install/).
Windows-only synthetic investigations can continue before that reboot.
