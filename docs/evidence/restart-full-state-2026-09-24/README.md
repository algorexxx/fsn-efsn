# Full-state rehearsal evidence, 24 September 2026

See [the report](../../restart-full-state-rehearsal.md) for scope, findings and
remaining gates. No real key, production anchor or original backup was changed.

- `context.rlp`: 256 linked historical headers, preserved final block/receipts
  and source total difficulty; read-only Linux extraction.
- `context-initial-uncles-assumption.txt`: failed initial harness assumption,
  corrected for Fusion's PoS use of the `UncleHash` header field.
- `*-copy-verified.json`: exact 230-file source-manifest identity checked for
  each fresh C: copy. `source-preserved.txt` confirms the original artifact still
  matches after all runs.
- `*-fixture.json`: exact synthetic funding, nonce and two-ticket substitution,
  original/synthetic headers and all three changed account RLP records.
- `block-*.rlp` and `block-*.json`: signed public-test-key bridge and full ledger
  for each block (headers, receipts, tickets, complete account differences).
- `producer-*.txt` / `verifier-*.txt`: separate preparation, production/import
  and cold processes, with explicit exit codes. The initial execution harness
  printed hash bytes with `%s`; JSON/RLP and the ledger-audit log provide the
  readable hex identities. This formatting is fixed in the final test source.
- `*-cold-verified.json`: full root/code traversal inventories. The cold logs
  additionally contain head/ledger/context and ticket-reconstruction results.
- `accounting.json`, `accounting-linux.json`: byte-identical independently
  decoded full account ledgers and aggregate liquid accounting. Every native
  purchase is checked for success, no Error payload, correct owner and live
  5,000-FSN ticket.
- `final-windows-suite.txt`: ordinary restart suite PASS, opt-in external-data,
  node-service and process-crash cases skipped as recorded. This is not a whole
  repository build/test claim.
- `focused-windows.txt` and `final-linux-race.txt`: twenty positive/negative
  accounting/context cases, twice on Linux with race detection.
- `final-identities.json`, `final-linux-identity.txt`: retained executable and
  final helper source hashes. The original execution binary precedes the final
  readable-hash formatting, helper negative tests and stronger ledger audit;
  the final audit validates its actual saved artifacts on both platforms.
- `*-artifact-SHA256SUMS`: closed disposable DB file manifests, not files in
  this evidence folder. Their small metadata files are included in their counts.
- `closed-artifacts.json`: measured sizes of the final closed copies.
- `SHA256SUMS`: hashes of all evidence files other than the manifest itself.

`run-windows.ps1` refuses existing copy targets and checks all source/copy files
and capacity before executing. `export-context.sh` and `check-final-linux.sh`
retain separate Linux build sources and binary identities. `archive.py` verifies
the preserved input, matches results and archives outputs without replacing
existing artifacts. These are exact-run records, not unattended production tools.
