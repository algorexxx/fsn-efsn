# State extraction and storage continuation evidence

Source baseline: `94b695f` on `codex/restart-investigation-wip`, plus the new
state-export test files. Production code is unchanged. `build-linux.sh` exports
that baseline and overlays the three extraction files; `linux-identity.txt`
records their byte hashes and both retained binaries. A later, separate binary
adds only the read-only closed-replay inspection file; its identity is recorded
separately. `windows-source-identity.json` permits byte comparison with the
working files. `writer-state_export_linux_test.go.txt` preserves the original
writer's Linux test file byte for byte, before its verifier was moved into a
portable file. `build-linux.sh` uses that preserved file to reproduce the original
layout; `build-portable-linux.sh` builds the final layout in a separate checkout.
The original Git archive and binaries remain in the ignored
workspace scratch directory and the WSL results directory respectively.

`focused-windows.txt` is the initial synthetic test run, before storage-corruption
and post-fetch-stop cases were added. `full-windows.txt` is the ordinary
Windows restart suite before the portable split, passing in 97.600 seconds. The Linux focused race run
repeats the expanded extraction suite twice on ext4; `c-filesystem-race` repeats
it twice with temporary LevelDB files on the workspace's C: mount. The separate
46-cut consensus-crash and real-service tests were not re-enabled in these runs.
After the portable split, focused Windows and Linux race tests pass again.
`windows-verify-wrong-writer.txt` is an expected rejection before database open.
`windows-verify.txt` is the successful complete native state/ticket verification,
reporting 230.38 seconds. `windows-reader-identity.json` records its executable.
`portable-initial-argument-error.txt` retains an initial launcher quoting error
before tests ran; the corrected launcher quotes each native executable flag.

The first actual export to D:-backed ext4 stopped at the unchanged 50 GiB host
reserve. Its logs, nonzero exit code, size and capacity records are retained with
the `linux-` prefix. The incomplete artifact is not reused and has no verification
marker. The fresh C: export uses the same executable and is recorded with the
`c-` prefix. It uses its own actual host drive for the same reserve check.
The C: Linux reader was intentionally stopped after the native verifier passed;
`c-verify-exit-code.txt` records 143 and its partial scan is not a completed
verification. The explicit stop reason is retained separately. The full native
scan, not that interrupted reader, produced the verification marker.

The original D: replay stopped through its existing stop file at 2,613,376;
`replay-replay.txt` retains the intentional nonzero exit rather than disguising
it as a completed 2,700,000 phase. `linux-replay-cold-check.txt` independently
verifies its exact closed head with both databases mounted read-only.

`copy-replay.sh`/`copy-replay.py` created a new C: copy from that read-only D:
checkpoint, verified all 1,694 files (3,736,629,446 bytes), and retained a complete
copy manifest. `run-replay-c.sh` resumes only the C: copy, using the original
retained replay executable and its ordinary identity/source preflight. The
original D: database and stop file are preserved. The runner was launched by
Windows `Start-Process wsl.exe -WindowStyle Hidden`; its stdout/stderr are in
`tmp/replay-mainnet-c-runner-output.txt` and `tmp/replay-mainnet-c-runner-error.txt`.
This phase completed at 2,700,000 with exit 0; `replay-c-cold-head-check.txt`
then verifies the closed exact head with no writable database handle.

`archive-results.sh` requires successful export and native cold-verification exit codes
before retaining the completed C: artifact evidence. It hashes every closed
artifact file and rereads the files to verify that manifest. The data itself
stays in the ignored `tmp/preserved-head-state` directory; it is not committed.
The artifact manifest paths are relative to that directory. Directory sizes are
logical bytes, not a prediction of NTFS/WSL allocation or future replay growth.
`verify-identities.py` additionally checks the complete stored configuration
against the earlier replay identity, genesis/head, the retained export executable
and all three extraction source files. The replay identity is archived alongside
the artifact identity for later comparison. The original writer-file hashes are
checked against preserved source where the final portable layout differs.

Successful extraction does not establish network state download, full historical
execution, production filesystem durability or readiness to restart the chain.
No real signing key, public node, production anchor or recovery block is involved.
See [the report](../../restart-state-export.md) and
[the replay record](../../restart-integrity-investigation.md) for final status.
