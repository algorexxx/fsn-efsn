# Complete-state operator evidence

25 September 2026, baseline `04a676c` plus the two test files pinned in
`identities.json`. No production source changes. The command binaries are
checked against their previously recorded hashes before use.

Windows complete-state checks pass in 11.72 seconds, Linux with race detection
in 120.23 seconds. Both small-state regressions also pass. All three command
blocks and twelve separate import/cold processes per platform agree with the
reference. Only public encrypted scalars 1 and 2 are used.

From PowerShell in the repository root:

```powershell
& ./docs/evidence/restart-full-state-operator-2026-09-25/prepare-copies.ps1 -Platform windows > ./docs/evidence/restart-full-state-operator-2026-09-25/windows-copies.txt
& ./docs/evidence/restart-full-state-operator-2026-09-25/check-windows.ps1
& ./docs/evidence/restart-full-state-operator-2026-09-25/prepare-copies.ps1 -Platform linux > ./docs/evidence/restart-full-state-operator-2026-09-25/linux-copies.txt
wsl.exe --distribution FusionRehearsal --user root --exec bash /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-full-state-operator-2026-09-25/check-linux.sh
```

Preparation refuses existing targets and uses three compact copies per platform,
3,172,902,480 initial copied bytes across both platforms, plus database overhead.
It requires 40 GiB free on C: before starting each group, retaining at least
35 GiB before each copy. D: and W: are not used. Reproduction needs new output
directories, the retained commands, pinned compact source and cached Go 1.21.3
toolchains. Preserve these evidence files rather than overwriting them.

Windows executes outside the Codex filesystem sandbox for path-resolution
checks. Linux tests, commands and import children run as `rehearsal`, with race
detection, inside an isolated network namespace. No forced process cuts are
added in this round.

`write-identities.py` verifies logs, unchanged command binaries, cross-platform
artifacts and all 230 original source files. It retains 18 small command
artifacts, references eleven identical earlier ledgers/blocks by checksum, and
records source Git blobs, four binary hashes and all evidence checksums.
Encrypted public-test key files stay in the disposable fixture directories.
This is not a reproducible release-build or independent-implementation audit.

Read [the report](../../restart-full-state-operator.md) for results and limits.
