# Declared automatic full-sync scope

This opt-in Linux test closes the bounded R8 combination defined in
`docs/restart-release-extraction.md`: complete shared synthetic ancestry,
ordinary automatic full-sync scheduling, and an initially unknown incompatible
strictly heavier branch. It does not simulate a year-long fork.

Before execution, bounds are 24 shared blocks, four accepted successors (anchor
at 25), at most twelve competing successors, 90 seconds per connection/sync
result, and six minutes for the complete test. Public keys 1/2 construct normally
validated DaTong blocks at a fixed historical synthetic timestamp. No difficulty
or canonical database entries are fabricated. Receivers have no foreign headers
or bodies before connection. No `lab_sync`, direct post-connection import,
mining, or automatic buying is used. Only enabled loopback exists in the private
network namespace; the service's existing 10-second scheduler drives full sync.

Acceptance requires compatible catch-up across the anchor; explicit downloader
anchor rejection with both expected and foreign hashes while accepted heads and
lookups remain intact; and an unanchored control adopting the exact same heavier
branch and removing displaced canonical lookups. All three cases require live
and cold-process canonical headers/transaction/receipt lookups and matching
full/header/fast heads, state root and ticket commitment. Pending re-injected
transactions may exist in the unanchored control, but cannot have canonical
receipt/block lookups. Race reports or skipped selected cases fail acceptance.

Build source starts from the separately verified stage-5 extraction tree retained
under `/home/rehearsal/results/restart-release-extraction-2026-10-04/source`.
Only the two saved test inputs are overlaid. The prior extraction verifier checks
that baseline before copying; a complete file inventory pins the result before
building. Production code is unchanged. Go 1.21.3 Linux amd64 with CGO and race
detection is the rehearsal toolchain, not an approved final release selection.

The runner refuses existing output directories, checks capacity, hashes the
executable before running, preserves logs and exit codes, and retains source and
binary outside `/tmp`. No historical database, backup or real key is opened.
Results are pending until an actual recorded run meets these checks.
