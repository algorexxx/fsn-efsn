# Peer-cache and cold-restart evidence

25 September 2026, baseline `31433ca`. See the
[report](../../restart-discovery-cache.md) for behavior, scope and limits.

| Evidence | Result |
| --- | --- |
| `baseline-persistence-race.txt` | Pre-P11 live cache/restart scenario passes, 370.82 seconds. |
| `boundaries-baseline.txt` | One-minute contact loses its timestamp on refresh and is prematurely persisted. The maturity and aging controls pass. |
| `boundaries-current.txt` | All three boundary tests pass with P11 and race detection. |
| `timestamp-only-race.txt` | Timestamp correction alone fails the live cache check after 340 seconds of connection; mature endpoint is absent. |
| `timestamp-only-regressions.txt` | Initial focused checks passed in 13.232 seconds despite that live regression. |
| `timestamp-only-sparse.txt` / `sparse-baseline.txt` | Valid partial replies produce timeouts and penalize a healthy responding peer, both with the timestamp-only patch and with the exact pre-P11 overlay. |
| `sparse-current.txt` | Combined P11 passes five sparse-reply cases with race detection, including missing/invalid reply controls, 3.602 seconds. |
| `current-race.txt` | Combined P11 passes live persistence/cold restart (370.31 seconds) and the prior DNS/outage matrix (400.69 seconds total), with race detection and wrapper exit zero. |
| `regressions-race.txt` | Combined P11 discovery table, bucket, UDP, node-database, age and sparse-reply regressions pass with race detection, 17.066 seconds. |

The baseline live run completed and printed PASS before its wrapper failed while
reading its final output-tail command: the wrapper script had been edited while
the shell was waiting on the test. The shell reported an unexpected EOF caused
by an unmatched quote. That post-test wrapper exit is not a failure of
the retained Go test result. The current run uses an unchanged script throughout;
do not edit runner files during execution. The baseline binary is retained as
`tmp/discovery-cache-linux-tests`; the intermediate binary has `-timestamp-only-`
and the combined current binary has `-current-` in its name.

`check-linux.sh current` compiles and runs the entire opt-in discovery rehearsal
in a loopback-only network namespace, allowing eleven minutes. Actual maturation
uses 340 seconds; child cold starts are separate processes with no seed/static
addresses. The peer caches are small temporary Linux databases removed by test
cleanup. No preserved chain state, W: restore or real keys are accessed.

`check-boundaries.sh current` runs the three synthetic age/persistence tests.
`check-sparse.sh current` runs the sparse-reply tests; `check-regressions.sh` runs
the combined focused checks. For runners accepting `baseline` mode, first run
`prepare-baseline.py`; pre-P11 `table.go` and `udp.go` are overlaid, preserving P10
and current tests. A new baseline live reproduction also
runs the previous DNS/outage cases, whereas the retained baseline log selected
only the persistence case. Baseline boundary and sparse-reply failures are expected.
The retained boundary logs were captured before the second hunk was added; these
tests exercise table/database behavior and do not make UDP requests.

Scripts overwrite their named outputs, so preserve this evidence before rerunning.
The earlier frozen evidence runner had a four-minute timeout; use the new runner
for the expanded suite. `write-identities.py` validates outcomes, the two-file
runtime delta (six added/one removed lines) and source/binary identities, and
writes `SHA256SUMS`. That manifest
excludes its own checksum. `.gitattributes` preserves raw evidence bytes.

The broader P2P suites have the three inherited failures documented in the prior
discovery report. They were not silently fixed or treated as passing here.
