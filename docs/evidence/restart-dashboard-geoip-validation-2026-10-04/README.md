# GeoIP validator evidence

See [the report](../../restart-dashboard-geoip-validation.md) for scope and limits.

- `source-baseline.json` identifies the previous dashboard commit and source bytes.
- `inspect-data.py` independently scans all bundled records; `inspect-ipv6.py`
  counts adjacent range conflicts and captures a few examples. An earlier
  one-line scan copied entire suffixes of the names buffer unnecessarily; it was
  stopped and replaced by the bounded-slice implementation retained here.
- `contracts-1` retains 237 passing contracts and the existing socket test's
  premature queue assertion. `fix-wire-wait.py` records the mechanical test-only
  correction. `contracts-2` passes all 237 contracts and all 14 socket tests.
- `unit.json` and `unit.*.txt` record 59 passing validator tests with the final
  test title and exact source hashes.
- `validation-1` records syntax checks, acceptance of the 204-byte synthetic
  complete dataset, rejection of narrow IPv6 and bundled data, and the real
  dashboard reader returning one country for two independently encoded countries.
- `verification.json` checks source/data/build preservation and process cleanup.
  `commit.json` and `dashboard-geoip-validation.patch` preserve the candidate.

The permanent test fixture in `test/fixtures/geoip-data.json` uses literal bytes
and hashes independently generated in the prior operations investigation with
Python `struct`/`ipaddress`. It contains invented geography for documentation IP
ranges. Neither the production validator nor observed runtime output calculates
its expected answers.

The controllers use Windows Python and the existing WSL `FusionRehearsal` Linux
Node 24.21.0 runtime. New numbered contract output directories are required.
`run-validation.py` uses single-use `validation-1` and scratch paths; adjust those
paths for another attempt. Nothing here downloads data or activates a collector.
