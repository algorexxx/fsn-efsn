# Complete-state offline interruption rehearsal

25 September 2026, based on `45ad8af` plus the two test files pinned in
`identities.json`. Production signing, consensus and journal code are unchanged.
Public private scalars 1 and 2 are the only signing keys.

The reference builder creates the three controlled handover blocks and audits
complete changed-account ledgers. Independent working/verifier copies exercise
nine completed signing/export/import cuts and two unfinished signing cuts on
each platform. The small-state process/refusal tests also run after harness
reuse. Read [the report](../../restart-offline-signing.md) for results and limits.

Windows passes in 35.91 seconds; Linux with race detection passes in 294.60
seconds. Both small-state regression runs also pass. All eleven retained
reference artifacts (three plans, three RLPs, three ledgers and two substitution
records) match byte for byte between platforms.

## Reproduction

These commands require the existing Go 1.21.3 toolchains, offline module caches,
immutable compact source and its pinned manifest. They refuse existing copy
roots; preserve prior evidence and choose fresh dated roots/output directories
when repeating. Preparation consumes 4,759,353,720 bytes of source data for each
platform's nine copies, plus filesystem and subsequent database overhead. All
new databases are on C:; no W: copy, D: database copy or cleanup is performed.

From the repository root, in PowerShell:

```powershell
& ./docs/evidence/restart-full-state-offline-2026-09-25/build-windows.ps1
& ./docs/evidence/restart-full-state-offline-2026-09-25/prepare-copies.ps1 -Platform windows > ./docs/evidence/restart-full-state-offline-2026-09-25/windows-copies.txt
& ./docs/evidence/restart-full-state-offline-2026-09-25/run-windows.ps1
& ./docs/evidence/restart-full-state-offline-2026-09-25/prepare-copies.ps1 -Platform linux > ./docs/evidence/restart-full-state-offline-2026-09-25/linux-copies.txt
wsl.exe --distribution FusionRehearsal --user root --exec bash /mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-full-state-offline-2026-09-25/check-linux.sh
```

The original Windows build used the exact environment and compiler command
subsequently recorded in `build-windows.ps1`; the script was saved afterward.
Windows tests run outside the Codex filesystem sandbox because it blocks their
path-resolution checks. Linux builds/tests run as `rehearsal`; test processes
use an isolated network namespace and race detection. Each forcibly killed child
holds a stopped chain and authoritative synthetic journal, with no public peers.

After both platforms pass, run `write-identities.py` with Python. It checks both
logs, requires byte-identical cross-platform plans, RLPs and account ledgers,
copies those small artifacts into this directory, and records source Git blobs,
binary hashes and evidence checksums. It refuses to overwrite existing outputs.
The source/binary record is not a reproducible release-build attestation.

The compact source was previously fully traversed. This run verifies every
initial copy file and all affected account differences; it does not repeat the
entire trie traversal, extend historical execution, or test machine power loss.
Its synthetic block identities are not production restart anchors.
