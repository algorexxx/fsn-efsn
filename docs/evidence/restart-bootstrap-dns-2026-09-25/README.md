# Bootstrap DNS candidate evidence

Baseline `d7fa207`; see [report](../../restart-bootstrap-dns.md).

- `dns-race.txt`: initial DNS/CLI-TOML/UDP-only/address-move rehearsal, PASS
  44.48 seconds. This predates explicit blocked-lookup shutdown and P13 cache fixes.
- `full-race.txt`: intermediate combined run, before P13; failed with a DNS test
  fixture race although the cold-cache case passed. Its source/binary
  identities are in `initial-live-identities.json`; it must not stand in for the
  final candidate.
- `cache-before.txt`: a strengthened cache-refresh check finds duplicate identities
  with old and newly resolved IPs. The first draft checked only the nearest result
  and passed, missing the duplicate; the retained failure checks the whole result.
- `cache-current.txt`: same test passes after restoring decoded routing hashes
  and preserving existing table entries during cached seed insertion.
- `final-race.txt`: P12/P13 run before the DNS fixture correction; the same test
  fixture race remains. `pre-fixture-identities.json` pins that version.
- `verified-race.txt`: P12/P13 combined rehearsal after the fixture correction,
  including actual `efsn dumpconfig`, live DNS recovery/move/cancellation and
  genuine cold peer-cache restart with NXDOMAIN still configured.
  PASS: DNS group 44.47 seconds, discovery/cache group 404.24 seconds, seventeen
  live leaf cases total. `current-identities.json` pins sources and executables.
- `units-race.txt`: final focused Linux race regressions, including resolver
  deadline/cancellation, cache refresh, parser/encoding, prior P10/P11 cases,
  dial scheduling, server behavior and explicit empty bootstrap configuration.
- `broad-race.txt` / `broad-exit.txt`: the complete affected networking packages
  retain exactly the three previously documented failures: `TestParseNode`,
  `TestForwardCompatibility` and `TestProtocolHandshake`. No additional failures
  or race reports appeared; exit status remains one.
- `windows-build.txt` / `windows-tests.txt`: CGO-disabled Windows discovery test
  executable cross-build and actual native execution. Parser/TOML, RLP encoding,
  cache refresh and deadline/cancellation checks pass. Reproduce with
  `check-windows-build.sh`, then `check-windows.ps1` on Windows. This is not a
  Windows live DNS/P2P rehearsal or race-detector run.
- `initial-units-failure.txt`: retained first development failure. Filtering inside
  the general dial scheduler broke its synthetic incomplete-node fixtures; the
  final implementation filters server bootstrap configuration instead and leaves
  the scheduler unchanged. The same first run could not compile `cmd/efsn` tests
  because two test-only dependencies were absent from the offline module cache.
  Actual command builds and subprocess `dumpconfig` tests are exercised instead;
  this does not claim the command package's complete test suite passed.

The test fixture's cancellation case exposed a late internal DNS dial reading
`net.DefaultResolver` while cleanup restored that global pointer. Its dialer now
uses an explicitly captured resolver. This is a fixture change; node runtime
sources are identical between the `final` and `verified` runs. The failed logs
are retained and are not counted as successful combined runs.

`check-final.sh` builds separate final executables and runs with Linux race
detection in a network namespace containing only enabled loopback. The earlier
runner uses different executable paths, so its child processes cannot accidentally
switch to a later build. `check-verified.sh` rebuilds the corrected test executable
and reuses the unchanged final node command. Run `check-final.sh` first when
reproducing from scratch. `check-units.sh` runs focused checks. `check-cache.sh`
selects the cache version. For `before`, first run `prepare-cache-before.py` to
reconstruct and verify the two pre-P13 source files against their captured blob
identities, then use its overlay. Current mode uses working-tree sources.

No preserved chain state or real keys are used. The maturity wait is real; the
small synthetic cache regression uses controlled records and a test transport.
Scripts overwrite their named outputs: preserve this evidence before rerunning.
`.gitattributes` retains raw bytes, and `SHA256SUMS` excludes itself.
