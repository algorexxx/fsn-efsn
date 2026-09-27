# Local snapshot framing evidence

Baseline `96ff3b4`. The [report](../../restart-snapshot-framing.md) records the
three-line P16 candidate, local reproduction, scope reduction and remaining
proof gaps. No signed malformed-header, process-crash or peer-network test was
run. The unexecuted integration-test draft was removed before compilation.

`before-snapshot.go.txt` retains the original decoder. `before-windows.txt`
records `go test -count=1 -mod=readonly -v -timeout=1m -run '^TestSnapshot'
./consensus/datong` before correction, with Go 1.21.3 and the same offline
Windows environment as `run-windows.ps1`. Eight truncated-count cases fail with
recovered slice-bounds panics; valid encodings and existing error cases pass.
`before-exit.txt` is 1. The test file is unchanged between before/after runs.

After the guard, `run-windows.ps1` passes the entire parser package, including
the fuzz seed corpus. Its subsequent existing header/import suite cannot start:
the offline Windows cache lacks modules, including `github.com/peterh/liner`.
The retained `after-windows/exit.txt` is 1 and `compatibility.txt` records setup
failure. No dependency downloads were enabled or attempted outside the offline
Go environment. This is partial Windows validation, not a fully passing run.

`run-linux.sh` was invoked using
`wsl -d FusionRehearsal -u root -- unshare --net -- bash <absolute-script>`.
Only loopback is enabled. Offline Go 1.21.3 runs the parser package and the
existing `TestHeaderBatchUsesUnstoredParents`,
`TestFinalizeParentIsolatedFromConcurrentImport` and
`TestColdHeaderValidationBoundaries` tests with race detection. These use known
fixtures and temporary small databases; no full backup, external peer, real key
or deployment is involved. All pass, including valid full import and cold reopen.

The parser fuzz check is in-memory and bounded to a requested ten seconds, with
two workers and race detection. It passes 5,151 executions; the total package
time is 13.033 seconds. It is not an exhaustive parser proof. Logs, source/input
identities and toolchain identities remain in `after-linux`. Both runner scripts
refuse to overwrite their result directories.

`verify.py` checks original-source identity, the exact three-line change, eight
original failures, after-test results, the Windows setup limitation, shared
source/input hashes, loopback isolation and fuzz completion. It writes
[checks.json](checks.json). Historical source comparison requires the local
baseline commit to remain available.
