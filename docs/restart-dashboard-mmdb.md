# Dashboard MMDB integration

2026-10-04. The [selected reader](restart-dashboard-geoip-reader.md) is now
integrated in the isolated dashboard candidate. Country flags remain visible
without coordinates; only nodes with valid coordinates appear on the map.
No efsn source, chain data or consensus behavior changes.

Dashboard commit: `02c882a1dcd88ee6e5794846a075d6154b233a99` on
`codex/dashboard-telemetry-auth`.

The implementation replaces `geoip-lite` with pinned `mmdb-lib` 3.0.3 and removes
the superseded five-file validator and its 59 tests. Eleven old dependency
entries are removed and one dependency-free package is added; other locked
entries remain unchanged. The original dashboard checkout and old installation
are preserved. No production geography data is bundled or downloaded.

The collector explicitly selects MMDB or disabled geography. An enabled file
requires an absolute path, approved SHA-256 and byte budget. Loading checks file
type, size, stable identity/content timestamps and hash, then accepts supported
IPv4/IPv6 City metadata. Configuration or file failures stop startup before
sockets are created. The collector performs one lookup at registration and
passes its result into the node model; peer-supplied geography is not accepted.

The updated CLI uses the same configuration and loader. Full settings and
limitations are in the dashboard patch's `docs/geoip-mmdb.md`. The old CLI
arguments and `GEODATADIR` are rejected. Disabled mode requires no dataset and
keeps the dashboard functional with unavailable geography. Enabled mode retains
the loaded bytes until restart; live path changes do not mutate its reader.

## Acceptance and corrections

| Check | Result |
| --- | --- |
| Linux Node 24.21.0/npm 10.9.0 clean backend install | Pass; prior installation preserved |
| Backend dependency audit | Zero reported advisories; inherited v1-lock/`yaeti` notices remain |
| Backend contracts | 204 pass: 178 retained, 25 MMDB, one additional snapshot case |
| Loopback sockets | All 14 pass |
| Frontend tests | All 23 pass, including country-only flag rendering |
| Lint and normal deployment build | Pass, no build warnings |
| Compiled browser | Twelve checkpoints pass; no page errors, foreign requests or missing assets |
| Native integration with MMDB enabled | efsn → WSS → snapshot database → HTTPS API → browser passes; four browser checkpoints |

The initial backend invocation did not run tests because npm's child shell
lacked Node on PATH. After fixing the runner, one existing test treated the new
`GEOIP_MODE` as a numeric collector limit. Restricting that test to its collector
settings restores all assertions; GeoIP validation has its own coverage.

The first native run failed while parsing `ready.json`. Its producer creates
and writes the small flat JSON object with `os.WriteFile`; the consumer had
polled for existence only. The test now waits for the object's closing brace
before parsing, within the same existing deadline. Invalid complete JSON still
fails. No production service or Go source was changed to address this fixture
race. The second full native run passes and cleans up its processes and secrets.

The separate staging build succeeded with an output-directory warning. A normal
in-place deployment build then passed without that warning. Its 542 non-source-map
files exactly match the browser-tested staging build; four debug source maps
differ with the output path. Native acceptance uses the final deployment build.
Previous compiled assets remain preserved separately.

These checks use only named synthetic fixtures. File hashes and metadata do not
prove geographic accuracy, freshness or source authorization, and the input
byte budget is not total decoder-memory containment. The loader does not claim
comprehensive validation of every MMDB record. Approval of a production dataset
and release configuration remains separate.

## Remaining work

The reader migration is complete for this candidate. Stop revisiting the old
conversion format; its investigations remain historical evidence.

For geography enabled at launch, finish protected source acquisition, archive
integrity, production-size/freshness budgets, lookup acceptance, immutable
activation/rollback and refresh/deletion procedures. Alternatively, explicitly
select `GEOIP_MODE=disabled` in the launch manifest and leave geography unavailable;
that mode does not require a provider account or refresh job.

Continue G6 service supervision, certificate renewal, retry/log lifecycle and
the common deployment manifest. The [restart plan](restart-plan.md) retains the
other launch gates and UI maintenance decisions. No public deployment, refresh
schedule or data-provider account was created.

Exact source/dependency captures, initial failures, accepted runs, synthetic
fixture provenance and the portable dashboard patch are in
`docs/evidence/restart-dashboard-mmdb-2026-10-04/`.
