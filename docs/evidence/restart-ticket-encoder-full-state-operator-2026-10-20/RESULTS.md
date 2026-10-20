# Candidate complete-state recovery command and handover

Passed on 20 October 2026 at 05:14:46 UTC. The separate
[record/artifact review](verification.json) passes. Preparation and dispatch
records retain their original pending status; this result supersedes it.

The retained, unselected encoder candidate with Go 1.27.1 ran the actual
`fsn-recovery` command through three approved recovery stages on complete account
state. Review, prepare, journal initialization, public-test-key signing and
export passed. Wrong passwords left no reservation; repeats returned identical
completed bytes without key access. Twelve fresh import/cold processes checked
the working and verifier copies across all three stages. The race-enabled test
passed without skips or race reports.

All eleven independent reference artifacts are byte-identical to the sealed
September legacy-encoder results. The owner-by-owner ledger audit passes across
future FSN rights, rewards, fees and retreat penalties. Other assets, code,
storage and notation remain preserved; the retired account is unchanged in
stages two and three.

| Height | Block hash | Tickets |
| --- | --- | --- |
| 15,130,081 | `7e16c5dabebb465314f9d48ba24bbb2cb836768a5264d5193329b46fd69af3da` | 485 |
| 15,130,082 | `9aaa779dad8d3883bff738d99f6a3c360812f658ccffd4778a6a4aa0c9ec862a` | 480 |
| 15,130,083 | `94ed041a999c47e4a3797f3f33067e3cdf011add53b786832f3ad334d9727345` | 1 |

The command SHA-256 is
`4bab0ee66536876b92e3d7ce9526c9a96c874601a766349089c41152850da623`.
The harness SHA-256 is
`43dce92bbf1922bb490b5e74bbf80a359b6ede432daca80c50a97caa04352b28`.
The retained 1,225-file source inventory, exact harness extracts, compiler,
command inputs and binaries were checked before and after execution.

Three disposable copies each matched the sealed compact export: 230 files /
528,817,080 bytes. That export contains complete account state and the 256-header
context needed by this test, not the full historical database. The source was
read-only and stayed unchanged. All writers exited before the 764-file closed
fixture inventory; 45 non-database artifacts are archived here. Databases,
journals and build outputs remain under the matching `tmp/` job directory.

All fifteen resource samples pass. Minimum free capacity was 21.47 GiB Linux,
50.95 GiB D: and 244.12 GiB C:, above the 20/50/40 GiB running reserves.
Peak sampled logical job size was 1.70 GiB against its 12 GiB limit.
All three commands and the outer job finished within their finite limits.
Worker time was 480.073 monotonic seconds versus 495.248 wall seconds; the clock
difference remains recorded without an inferred cause.

Private network and mount namespaces, loopback down, exclusive investigation
ownership and public scalars 1/2 confined this run. Original backup, local
fallback, separate recovery and both detached W: image metadata remain unchanged.
Cleanup unmounted the source view; the 05:53 UTC check found no test process,
matching mount, test loop or held investigation lock.

`host-post-state.json` preserves a false supplemental image comparison:
PowerShell parsed the expected timestamp into a DateTime, while the observation
was compared as a string. `host-image-comparison.json` records the types, lengths
and UTC ticks and confirms both images unchanged. The job's original host and
worker preservation checks passed; no acceptance gate or artifact was altered.

This is offline candidate qualification with synthetic public-key ownership and
funding substitutions. It does not select a release, authorize real signing,
establish canonical history or complete independent human review. The next narrow
test is approved-signing process interruption, refusal and credential-lock
behavior under this candidate/toolchain; the current success path does not cover
those cuts. Historical replay, the complete-backup copy/startup and unchanged
guard refusals need no blanket rerun.
