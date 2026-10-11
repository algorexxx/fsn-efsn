# Prepared native storage step

The user has authorized archival and compaction. This step remains pending until
the full before checks pass and their evidence is verified and committed.

The installed WSL help has no compact command; it offers sparse conversion,
relocation and resizing. None of those is selected. Optimize-VHD is unavailable
in the current environment. The Windows token is not elevated. Use the installed
DiskPart for one compaction of the exact detached rehearsal VHD. Windows UAC
approval may be necessary; never bypass it or retry a declined prompt silently.

[Microsoft's compact-vdisk documentation](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/compact-vdisk)
allows compaction of a selected dynamically expanding VHD while detached or
attached read-only. [Its scripting documentation](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/diskpart-scripts-and-examples)
requires at least fifteen seconds between separate DiskPart scripts. The prepared
worker first captures installed `help compact vdisk`, verifies that help, waits
fifteen seconds, and only then runs the frozen select/detail/compact/detail script.
It verifies exit status, native success text, actual geometry and file size.
No `noerr`, shrink, partition operation, automatic repair or deletion is included.

After passing before checks, `trim.py` holds the real database/run locks in private
network/mount namespaces and runs `sync -f /`, then `fstrim --verbose /`. Local
fstrim help confirms that this discards unused blocks of the specified mounted
filesystem. It does not zero-fill free space. Sync is limited to 120 seconds;
trim to 300 seconds with twenty seconds of cleanup grace. Preserve logs and
`trim.json`, verify the result, and freeze `TRIM_OUTPUT_SHA256SUMS` before proceeding.

Then terminate only FusionRehearsal and confirm the VHD detached. If it remains
attached, follow the existing idle-service rule: check no unrelated workload
before stopping Docker/WSL, and restore only services deliberately stopped.
Never stop the before-check worker or start a second database writer.

Run `native-compact.ps1` in a hidden administrator PowerShell using ordinary
Windows elevation. It requires frozen archive/before/trim/input manifests,
the passing preservation records and an unchanged rollback receipt. It opens
the rollback archive read-only at the UNC equivalent of the verified W: path
so elevated drive mappings are unnecessary. It targets only
`D:/FusionRehearsal/Ubuntu/ext4.vhdx` and retains the 220 GiB virtual geometry.

This is one native rewrite, not a retry loop. Never kill it merely because a
tool yields or a monitoring deadline elapses. An overdue native operation needs
diagnosis, with both image states retained. A failed or uncertain operation
blocks further mutation and replay; do not overwrite its records.

Native success alone does not close storage acceptance. Run the unchanged
prepared `after` preservation check, inspect filesystem health and actual
capacity, then review the unchanged next-replay gate. Keep the W: rollback image
through that qualification and assess its continuing recovery value afterward.
