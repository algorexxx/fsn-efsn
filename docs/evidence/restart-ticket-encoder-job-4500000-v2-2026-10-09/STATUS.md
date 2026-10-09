# Corrected finite job dispatched

Dispatched 9 October 2026 at 16:15:14 UTC (18:15:14 Europe/Stockholm), following
verified D: reclamation and fresh capacity checks. The preceding attempt's
CRLF observer input is corrected without changing executable/controller/source
selection or any limit. Prior verified endpoint remains 3,600,000.

Resume checks passed and replay started at 16:18:06 UTC. Target is 4,500,000;
completion remains pending.
Use runtime status.json, completion.json, verification.json and resource records
before subsequent work. Do not start another writer or hash a live database.

At 16:17:29 UTC, all four initial commands passed: observer compilation, build
identity inspection, starting-height cold check and preserved-history reference.
The unchanged replay binary identity is recorded, and 1,519 prior evidence files
verified. Final resume checks were still in progress at this observation; no
completed-history claim is made. See initial-observation.json.

[Active observation](active-observation.json): replay PID 653, no recorded
failure or stop reason, first successful size measurement 7,580,307,456 bytes.
This is provisional running evidence, not a verified endpoint. Use later
runtime/completion records on follow-up; do not hash the live working database.
