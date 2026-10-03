# Dashboard collector input acceptance

3 October 2026. Dashboard commit `3d73e9576e4565bbabb3f6124dfad1bdc5e70fe1`,
following `a5bee3f`, now passes **120 contracts and eight real
loopback socket tests** with explicit incoming-message, connection, login-wait
and application-message limits. G6 remains open. No efsn, consensus, recovery,
frontend or database implementation changed in this step.

## Explicit change list

1. Require four collector limits at startup, documented in the dashboard's
   `docs/collector-input-limits.md`. Existing loopback and credential rules remain.
2. Apply the byte threshold to all three Primus transports with compression off,
   and use the HTTP server's shared TCP connection cap.
3. Check application envelopes and a per-connection, continuously refilled
   message allowance before the legacy event plugin dispatches them.
4. Expire incomplete telemetry registration; cancel its timer on success/end
   and prevent delayed callbacks from claiming a replacement session.
5. Cap history replies at the existing efsn/collector batch size of 50 entries.
6. Destroy the affected socket on transport/JSON decoding errors. Actual wire
   testing showed the old WebSocket library otherwise retained it during its
   30-second close-handshake window.

The dashboard branch retains its existing dependency versions. Four values must
be chosen from real deployment measurements; test-fixture values are not a
production prescription. A configured threshold can reject a legitimate large
history report, so real telemetry sizing remains necessary before public use.

## Evidence and limits

The final run uses Node 22.11.0. Deterministic tests check gradual refill, the
burst cap, cross-connection isolation, late registration and configuration
failure before startup. Real sockets check silent-login expiry, all three byte
limits, fragmented-message totals, rate rejection, reuse of a freed TCP slot,
malformed envelopes/JSON and subsequent ordinary connections. Normal 50-block
history is admitted; 51 entries end the reporting session.

The pinned receiver rejects messages at the exact byte threshold: 2047 bytes
pass with a 2048 setting, while 2048 do not. Transport-error cleanup causes
abnormal closure code 1006. This is intentional fail-closed behavior. Primus
control messages, WebSocket control frames, HTTP handshakes and reconnect rates
are outside the application-message limiter; the public proxy still needs its
own limits. Ordinary session rejection retains Primus's graceful closure.

The first wire attempt exposed the transport cleanup issue, a test race between
client closure and the server freeing its TCP slot, and an overly broad chart
assertion in the new admission test. The second attempt isolated the chart
defect. The final history admission test checks the bounded chart length and
the reported node head; it does not claim that the inherited chart order works.
Failed attempts and a separate small chart probe are retained in the
[evidence bundle](evidence/restart-dashboard-input-2026-10-03/README.md).

There is no new PostgreSQL or browser acceptance claim in this step. Their
implementation and dependencies are unchanged, and their earlier results remain
linked in the [plan](restart-plan.md). Tests used only synthetic credentials and
local/in-memory data; no restored chain, validator key or large disk job was used.
The verifier matches all 696 tested source files to the committed bytes and
checks the portable patch, unchanged locks and preserved original checkout.
All collector test processes are stopped.

## Newly isolated follow-up work

The unmodified chart cache has two reproduced defects: a partially populated
cache ignores head 101 after head 100; head 100 followed by history 51–100 stores
50 heights but charts 51–90 instead of the latest 40. Source review also finds
no cap on retained forks at one height. These are dashboard reporting/retention
issues, not evidence of a chain-consensus defect.

Next implement honest per-node report freshness, then correct and bound the
chart cache, including slow-consumer/outbound-memory review. Complete actual
efsn/RPC comparisons and production dependency/runtime, supervision and TLS
acceptance before public use. Dashboard enrollment remains separate from
permission to mine. Nothing was pushed or deployed.
