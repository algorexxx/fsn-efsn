# External monitoring check

4 October scope update: launch supervision uses SSH checks and self-hosted
fsn-stats. This external-monitor integration is optional and parked; it is not
a launch prerequisite. The command remains available as a local diagnostic.

`fsn-observe --history-check` supplies a small offline check that such a service
can run. It evaluates retained collection freshness, logical budget headroom
and unresolved incidents, returning JSON and a process exit status. It does not
contact a node, send notifications, schedule itself or modify retained events.
No monitoring provider or production threshold has been selected.

```text
fsn-observe --history ABSOLUTE_HISTORY --history-check --report-max-age REVIEWED_DURATION --history-min-free REVIEWED_BYTES
```

All placeholders must be replaced. `--report-max-age` is a positive Go duration,
such as a value ending in `s` or `m`; `--history-min-free` is a positive integer
no larger than the history's logical budget. Neither flag has a deployment
default. Choose the collection interval, total work deadline, accepted coverage
gap, maximum event size and operator response time together before setting them.
The byte check is not a filesystem free-space check.

The version-1 result contains `CheckedUTC`, the supplied bounds, `Problems` and
the reconstructed `History` status, including its scope, sequence, collection
timestamp, byte usage and incidents. `MaxReportAge` is rendered as a duration
string. Match the reported scope against the deployment manifest and retain
this detailed evidence locally. Refer notifications to the appropriate incident
IDs and the [response guide](restart-monitoring-response.md).

| Outcome | Process result |
| --- | --- |
| No triggered conditions | JSON with an empty `Problems` array; exit 0 |
| One or more triggered conditions | JSON with those condition codes; diagnostic on stderr; exit 1 |
| Missing/locked/corrupt history, invalid arguments or output failure | Nonzero exit; do not treat missing or incomplete JSON as success |
| Process killed, unavailable host or no scheduled result | External monitor must mark the check unavailable; no successful result exists |

Ordinary `--history-status` keeps its original meaning: exit 0 means status was
read. Only the new check applies these conditions. Even a successful check is
not a general chain-health verdict or proof of complete block/ticket coverage.

| Condition code | Trigger |
| --- | --- |
| `collection_missing` | No collection report has ever been committed |
| `collection_stale` | Age of `LastReportUTC` is greater than or equal to the supplied maximum |
| `history_time_in_future` | A retained collection or event timestamp is later than the check time |
| `history_headroom_low` | Remaining logical bytes are strictly below the supplied minimum |
| `unresolved_incidents` | At least one incident is not resolved; acknowledged, absent-on-latest-observation and unknown observations still require review |

Fresh reviews, backfills and anchor-inventory events do not refresh collection
freshness. A failed collection append also leaves the old collection time in
place. Monitor the collector's own nonzero exit immediately; this history check
detects its stale durable result when the configured interval expires. A
successful but incomplete RPC report can be fresh and still carry unresolved
incidents. An operator resolution is a recorded assertion, not verified repair.

## Integration contract

Run collection, backfill, reviews and this check serially for a history: LevelDB
opens exclusively. Check after the writer has exited, including when it failed.
Do not use a shell `&&` chain that skips the check on collection failure. Capture
both exit statuses rather than allowing a later successful command to hide the
earlier failure. A lock failure means the check was unavailable; it is not proof
that the chain stopped.

Give the entire scheduled job an external deadline and have the monitoring
service watch for missed completion. Local history replay is not covered by the
collector's RPC `--timeout`, and that flag is invalid for this offline operation.
If a writer hangs, a job never starts, the runner dies or the host disappears,
the external absence-of-result check must still notify the operator. A timer
on the same machine, with no independent missed-result detection, is insufficient.
Keep physical disk checks alongside the logical headroom check.

The service should retain stable incident IDs for deduplication, support
notification acknowledgement/reminders and preserve unresolved state. The
existing local `--history-action acknowledge` records an evidence review; it
does not acknowledge receipt of a message in the monitoring service. Choose
maintenance windows explicitly rather than manufacturing a successful result.

Before deployment, select the actual service, responder route, cadence,
deadlines, reminder/escalation policy and physical/logical headroom. Then exercise
real message receipt and acknowledgement, collector failure, missed scheduling,
host loss, a full history and restored collection. These checks must use the
approved thresholds and monitoring service. None of that external deployment or
delivery is claimed by the local acceptance below.

## Local acceptance

The [evidence bundle](evidence/restart-observer-check-2026-10-04/README.md)
records fixed-clock boundary/incident tests, failed-append and later-review
behavior, command validation and actual executable exit checks. The command
fixture contains an intentionally retired synthetic node, so a clear check
establishes only its declared history conditions. It is not a healthy producer
fixture. The captured history export stays byte-identical across checks.

Head-stall windows, sustained-divergence timing, complete ticket accounting,
external notification delivery and check/host-loss detection still require their
own acceptance. This change belongs solely to the observer; normal node and
consensus behavior remain unchanged.
