# Dashboard GeoIP dataset update and recovery investigation

Local evidence date: 2026-10-04. Ten offline updater cases and five dataset
switch/lookup checkpoints are complete. The installed `geoip-lite` 2.0.3 updater
is unsuitable as an unattended production update job in its current form.
Its successful exit does not establish a complete, verified dataset. Separate
staging, integrity checks, deadlines and activation checks are required.

No dashboard application code, dependency, compiled frontend, efsn source or
chain rule changed. These are synthetic local operational tests, not a MaxMind
download or hosted service restart. G6 remains open.

## Observed updater behavior

The fixture runs the actual installed `scripts/updatedb.js` under Linux Node
24.21.0. A preload replaces only its HTTP boundary with in-memory responses and
blocks network connections. Tiny ZIPs contain invented records for documentation
address ranges `192.0.2.0/24` and `2001:db8::/32`; these are not claims about real
locations. Expected binary bytes are constructed independently with Python's
`struct` and `ipaddress`, rather than copied from the converter's output.

Every attempt has separate absolute `GEODATADIR` and `GEOTMPDIR` paths under a
verified scratch root. The active dataset is never an updater target. This is
essential: the updater recursively removes its temporary directory at startup
and rewrites data files individually. Scratch use for the accepted updater run
is only 7,324 bytes. No large database copy or chain restore was required.

| Case | Actual result | Operational consequence |
| --- | --- | --- |
| Missing license | Exit 1 before any simulated request; dataset unchanged | Treat as configuration failure, without repeated rapid retries |
| Checksum endpoint returns HTTP 503 | Exit 1; dataset unchanged | Keep serving the selected dataset and report failed refresh |
| Empty checksum response | Exit 1; dataset unchanged | Do not use the suggested `force` option to bypass verification |
| Incomplete ZIP | Extraction fails with exit 1; dataset unchanged | Reject the staging directory |
| Country succeeds, City returns 503 | Exit 1 after country files and marker change; City remains old | In-place updates can leave mixed datasets |
| City request stalls | Still running at the fixture's three-second deadline; controller stops it, leaving the same partial update | Supply an external whole-job deadline; the reviewed request path sets none |
| Served checksum differs from ZIP SHA-256 | Exit 0 and converts the ZIP, storing the incorrect checksum | The checksum is used as a change marker, not archive integrity verification |
| Matching markers but no data files | Exit 0, reports both datasets current; a fresh reader fails | Marker equality and exit 0 do not prove dataset existence |
| Complete update | Exit 0; all five binary files equal independently constructed expected bytes | Converter compatibility passes for the tiny complete fixture |
| New attempt after failures | Fresh staging succeeds with the same expected bytes | A later clean attempt can recover without modifying the active data |

No production timeout or retry interval is selected by the three-second test.
The tests do not cover current provider authentication, HTTPS redirects, large
archives, rate limits, archive resource limits or actual conversion duration.
No real license key was supplied. The fixture's request ledger records only
edition and suffix, never credentials.

## Lookup, activation and rollback

The real dashboard `lib/node.js` and frontend snapshot mapper read both synthetic
IPv4/IPv6 records, an IPv4-mapped IPv6 address and a loopback miss. The five
checked transitions are:

1. The selected old directory produces the expected old locations and map points.
2. Rejecting an incomplete candidate leaves the old reader and selection intact.
3. Switching a symlink to the complete new directory leaves the already-running
   reader on its cached old data, even for newly constructed node objects.
4. A fresh reader using the same selected path loads the expected new dataset.
5. Switching back and starting another reader restores the expected old dataset.

Both dataset directories retain their exact bytes. All fixture processes stop;
the final selected path points to the old directory. The symlink replacement
uses one filesystem rename in local WSL/DrvFS scratch. Repeat the selection and
service restart procedure on the actual Linux deployment filesystem and under
its service manager; this is not proof of host-level crash consistency.

A separate incomplete-country-only probe **starts successfully**. Its IPv4
lookup has missing coordinates, while its IPv6 lookup supplies `[0, 0]`. The
current snapshot mapper consequently produces one misleading IPv6 map point at
zero latitude/longitude. This remains an explicitly recorded fallback behavior,
not a renderer fix. Deployment validation must require the complete City data
set and useful lookup probes; silently falling back to Country-only data is not
accepted as a successful City update.

The five required files are `geoip-country.dat`, `geoip-country6.dat`,
`geoip-city-names.dat`, `geoip-city.dat` and `geoip-city6.dat`. Their fixed record
sizes in this pinned reader are 10, 34, 88, 24 and 48 bytes respectively. The
fixture rejects missing, empty or misaligned files before activation. These
basic checks alone cannot detect same-size corruption, invalid cross-references,
unsorted ranges or a coherent but wrong dataset. Independent source integrity,
conversion validation and meaningful fresh-process lookups are still needed.

## Production update design to implement and accept

Keep the installed package and selected data directories read-only to the
collector. Run one update at a time as a separate restricted job with unique
staging and temporary directories. Verify resolved paths, ownership and free
space before starting; never target a shared temporary directory, the current
dataset, an allowed rollback dataset or `node_modules`.

Require an explicit absolute `GEODATADIR` in the service configuration. Source
inspection shows that relative paths resolve against the updater's working
directory but against the reader module's directory. An omitted setting selects
bundled package data. Neither is an acceptable way to identify the chosen release.

Obtain the selected provider editions using a reviewed downloader with protected
credentials, verified TLS, bounded redirects/download size and a whole-job
deadline. Hash the actual archives and compare against the source's independently
obtained checksums before extraction. Preserve source edition/build metadata,
archive hashes, converter version and output hashes together. Do not treat the
package's `.checksum` files as proof of any of those properties.

Convert only verified inputs in isolation. Require both editions and all five
nonempty aligned outputs, validate record ordering/references and run a fresh
process against dataset-specific IPv4/IPv6 probes through the actual dashboard
mapper. Expected geographic answers should come from the selected input data;
do not freeze real-world locations across updates. Verify unavailable lookups
stay unavailable and do not produce fabricated map points.

After acceptance, make the versioned directory immutable to the serving account,
switch the selected path and restart the collector. Confirm fresh reports reach
the API/browser with the selected data. A running collector does not reread a
changed `GEODATADIR` automatically, and its node objects also store their lookup
result. A file watcher is not a substitute for this coordinated acceptance.

On failure, keep the selected dataset intact, mark the refresh failed and retry
with a fresh staging directory using bounded pacing. If activation fails,
reselect a still-permitted prior dataset and restart/verify again. Record the
failed attempt without credentials or signed download URLs. Retention must
cover downloaded archives, converted data, rollback copies and host backups;
keeping the last usable data indefinitely is not the retention policy.

This workflow is specified and partly rehearsed here. The subsequent
[read-only dataset validator](restart-dashboard-geoip-validation.md) implements binary
checks and reveals an IPv6 reader compatibility blocker. Its tests pass, while
the bundled dataset is rejected. Protected downloads, compatible conversion,
scheduling and service-manager integration remain unimplemented/unaccepted.
Do not deploy the preload mock or the stock updater as a shortcut.

## Provider selection and release boundary

MaxMind's [update instructions](https://dev.maxmind.com/geoip/updating-databases/)
say CSV users need direct downloads and describe account-authenticated permalinks,
HTTPS redirects and build-date checks. Its `geoipupdate` binary handles MMDB
databases; it is not a drop-in producer of this package's custom `.dat` files.
The installed script constructs legacy query-key URLs, so putting its key in an
environment variable does not remove it from the outgoing URL. A protected
download path still needs review and live acceptance.

MaxMind's [GeoLite guide](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data/)
describes account/license-key setup and says old GeoLite databases must be
deleted within 30 days of a new release. Record the actual source terms and
required attribution for the selected account/data, then enforce its refresh
and deletion obligations. The old bundled-data license review does not approve
retaining newly downloaded data indefinitely.

The account, source editions and production host remain unselected. No account
was created, license accepted, dataset downloaded, public job scheduled or
service deployed. Existing application/build acceptance is retained; its full
suites were not rerun because no application or dependency changed. All 1007
efsn source/module hashes, non-Markdown dashboard sources, installed GeoIP files
and the original dashboard checkout remain unchanged.

The [restart plan](restart-plan.md) owns the remaining launch gates. Exact local
fixtures, results, early harness failures and preservation checks are retained
under `docs/evidence/restart-dashboard-geoip-operations-2026-10-04/`.
