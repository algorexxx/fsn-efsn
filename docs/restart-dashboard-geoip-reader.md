# Dashboard GeoIP reader decision

Follow-up: the [MMDB integration](restart-dashboard-mmdb.md) is now complete in
the isolated dashboard candidate. This report records the preceding comparison.

Local evidence date: 2026-10-04. Use an unmodified standard MMDB reader and a
single City database for the next dashboard implementation. The selected reader
candidate is `mmdb-lib` 3.0.3. Its published package has no runtime dependencies,
and its offline compatibility checks pass on Linux Node 24.21.0.

This is a tested design decision, not a completed migration. The dashboard
checkout remains at `2e047abb1eaab6e9315373e39af68212a399b451`, still using
`geoip-lite` 2.0.3. The experiment changes only scratch copies and an in-memory
copy of the node model. No production configuration, dependency lock, frontend
build, efsn source, chain data or consensus rule changes.

## Why replace the custom format

The [previous investigation](restart-dashboard-geoip-validation.md) established
that `geoip-lite` compares only the upper 64 bits of IPv6 addresses. This slice
tests both a correction to that reader and the MMDB alternative.

| Option | Observed result | Maintenance consequence |
| --- | --- | --- |
| Keep the pinned reader | Confuses two different single-address IPv6 records and returns a record for neighboring addresses outside either range | Not acceptable for correct IPv6 lookup |
| Extend the reader to compare all 128 bits | A scratch copy reads `2001:db8::1` as NO, `::2` as SE, and rejects the adjacent gaps correctly | Still needs a reproducibly maintained package correction, valid regenerated data, and a protected custom conversion/update path |
| Read standard MMDB directly | All 3,007 independently expected lookup cases pass, including distinctions within the lower 64 bits | Removes our need to maintain the five-file conversion format and precision patch; needs a small dashboard adapter and controlled data loading |

The old reader correction touches its `readip6` and `cmp6` functions. It does not
repair the bundled dataset: the preceding full scan found 751 adjacent
overlap/out-of-order pairs in Country IPv6 and 3,557 in City IPv6 even with full
128-bit comparison. Those findings are retained; this slice does not sort,
merge, round or otherwise reinterpret that data. A fresh conversion would need
independent acceptance before it could be used.

`mmdb-lib` is a third-party library. The published `maxmind` 5.0.7 package uses
that exact version, and MaxMind's official `@maxmind/geoip2-node` 7.1.0 wrapper
depends on `maxmind`. The official wrapper also offers web-service APIs and
response models that this dashboard does not need. Our candidate uses the
underlying synchronous `Reader` directly, without file watching or a lookup
cache. See the [official client's description of its reader](https://github.com/maxmind/GeoIP2-node#database-usage)
and the [reader's source](https://github.com/runk/mmdb-lib).

The selected tarball matched npm's published SHA-512 integrity value. The npm
bulk advisory endpoint returned no entries for `mmdb-lib` 3.0.3 at the recorded
check time. This is a package-specific advisory observation, not a new audit of
the whole dashboard or a guarantee that the decoder has no defects.

## What passed

Fixtures are pinned to MaxMind's public test-data repository commit
`276926d23b4109ca5452709bfb5931c338afb34c`. Downloads are small synthetic test
databases, not current location data. Each downloaded file matches the pinned
Git blob and a recorded SHA-256. No provider account, license key, public IP
lookup service or production dataset was used.

- **2,449 City lookups:** expectations come from the published source JSON's
  242 networks. Python's independent address arithmetic selects boundaries,
  midpoints, neighboring addresses and longest-prefix matches. Cases include
  compressed/expanded IPv6 and dotted/hexadecimal IPv4-mapped forms. The complete
  returned records match, including names, country fields and coordinates.
- **558 IPv6 precision lookups:** 186 cases each against the published 24-, 28-
  and 32-bit tree-record fixtures. Expectations are derived with Python from the
  range and encoding documented in MaxMind's generator. These include adjacent
  addresses inside one upper-64-bit group and gaps just outside the stored range.
- **Seven lookup mappings and eight field cases:** the proposed adapter returns
  country/coordinates, preserves a country without coordinates, rejects invalid
  input before the reader, and leaves absent geography unavailable. It does not
  turn missing coordinates into `[0, 0]` or substitute registered-country data
  for a missing location country. Explicitly supplied valid zero coordinates
  remain valid.
- **Node and snapshot compatibility:** an in-memory copy of the existing node
  model uses the prototype for five inputs. Its output passes through the actual
  unchanged snapshot mapper and produces the four expected map points. The copy
  replaces the dependency and removes the old textual `::ffff:` stripping so the
  new reader can process the complete mapped address.
- **Old-reader comparison:** five inputs reproduce its current result, and the
  same five pass the independently encoded expected result with the scratch
  precision correction. The installed package remains unchanged.

The [upstream fixture documentation](https://github.com/maxmind/MaxMind-DB/tree/276926d23b4109ca5452709bfb5931c338afb34c/test-data)
and source/generator hashes are captured in the evidence bundle. Only the named
valid fixtures are decoded. Runs use a 128 MiB V8 old-space limit and a 30- or
45-second process deadline; this is not a production database memory measurement
or a comprehensive malformed-file decoder assessment.

## Exact implementation scope

1. Replace `geoip-lite` with pinned `mmdb-lib` and regenerate the backend lock
   reproducibly. Remove the superseded five-file runtime validation path when
   the migration lands; retain the investigation as historical evidence. Keep
   one active reader and one data format.
2. Add an explicit MMDB file setting and a bounded startup loader. Verify the
   staged file's byte budget and approved hash before constructing the reader,
   then check its type/version metadata before accepting it. Separate intentional
   operation without location data from a configured file that is missing or
   invalid; do not silently fall
   back to stale packaged data. The prototype is not this loader.
3. Map only the fields the dashboard consumes: `country` and `ll`. Validate the
   address with Node's IP parser before calling the reader, preserve full mapped
   addresses, and represent missing coordinates as `null`. Do not infer a
   location from the account's registered country.
4. Correct the snapshot mapper to retain a valid country when `ll` is absent,
   while omitting its map point. The current mapper discards the entire geography
   object in that case, losing a useful flag. The experiment explicitly records
   this current limitation; it is not reported as a completed fix. Keep both
   country flags and map points covered by frontend acceptance.
5. Run backend, frontend and combined telemetry/database/browser acceptance on
   the actual changed checkout. Recheck the resulting dependency tree and lock;
   the isolated prototype does not replace those checks.

Then finish the [GeoIP operations work](restart-dashboard-geoip-operations.md)
using immutable staged MMDB files and a supervised fresh-reader switch/rollback.
The old custom CSV conversion job is no longer the chosen direction. Source
account/edition, protected download and independent integrity checks, production
size/freshness budgets, attribution, refresh/deletion policy and service
supervision remain open. No updater or scheduler is activated here.

The [restart plan](restart-plan.md) still owns G6 and launch approval. This
decision affects dashboard geography only; it has no role in chain validation,
ticket selection, producer admission or the restart anchor.

## Evidence

`docs/evidence/restart-dashboard-geoip-reader-2026-10-04/` contains pinned package
metadata, source provenance, reproducible case generation, the scratch-only
prototypes, raw results and preservation verification. Expected values are
derived before the Node reader runs. Downloaded binaries and installed package
copies remain under ignored `tmp/dashboard-geoip-reader/`; they are not shipped
as production data. All tracked dashboard files, the original dashboard
checkout, existing GeoIP datasets, compiled assets and 1,007 efsn source/module
files are checked for preservation.
