# Complete-state funded participant entry

Baseline: `4afa625`. This prepares and validates the funded two-producer starting
point for the next complete-state partition/manual-repair rehearsal. It does not
inject a partition or demonstrate rollback repair itself.

`prepare-copies.py` checks all 230 source files against the original compact-state
manifest and makes two fresh copies with a 50-GiB free-space reserve. Both earlier
attempts' copies, source and binary identities are preserved. The corrected attempt
uses `tmp/full-state-participant-2026-09-26-attempt-03`. The original backup is
untouched and all new chain-database copies are on C:. The complete-state export
has recent execution context, not complete historical bodies.

`check-linux.sh build` uses the existing WSL Go 1.21.3 toolchain, offline cached
dependencies, two workers and race instrumentation. `check-linux.sh run` executes
inside a new enabled-loopback-only namespace with public test keys. No external
peers, real keys or production signing are involved. The partition opt-in supplies
the namespace guard; this entry case does not apply packet loss.

Both copies execute the three reviewed recovery blocks. The next three blocks
are signed by the donation test key and imported independently. Alongside normal
donation purchases, they include:

1. The backup test key's conversion of 10,000 mature FSN time-lock rights into
   liquid FSN credited to a previously absent public test key 3.
2. Its ordinary 2,020.102-FSN transfer to that entrant.
3. The entrant's first funded ordinary ticket purchase.

The backup signs two transactions but no additional block or ticket purchase.
There is no new direct state allocation beyond the earlier audited substitutions.
This is a hypothetical contribution of the backup fixture's existing rights. It
does not establish permission to spend the real owner's funds, reserve availability
or a requirement to fund another producer at launch.

Two actual services then mine and buy tickets. Acceptance requires canonical
purchases and signed blocks from both owners, matching stopped heads, independently
reopened databases, exact block/receipt/ticket/account-difference agreement, and
an independent audit of all future FSN interval rights. The ledger includes the
conversion's 0.001-FSN native fee, gas, ordinary rewards and first-retreat losses.
It also checks unrelated account fields and backup-account immutability after
the funding transactions.

`participant-race.txt` and `participant-exit.txt` retain the first failed attempt:
the first appended purchase used a start near the current clock, more than three
hours after the parent timestamp. Construction rejected it before funding. The
corrected source uses each parent timestamp for the start and a sufficiently long
end. `attempt-01/` retains its source, runner, preparation proofs and executable
identity. The failed executable remains in ignored `tmp/`.

`participant-attempt-02-race.txt` retains the second failed attempt: both funding
prefixes pass, then the entrant service is rejected by the harness allowance for
public test keys 1 and 2 only. The harness now permits public test key 3 as well.
Its previous source and executable identity remain in `attempt-02/`. The network
and real-key exclusions are unchanged.

The final attempt passes in 119.58 seconds with ten suffix blocks, 14 successful
transactions and four live canonical blocks signed by both producers. Both cold
databases and the independent complete-account interval ledger agree. The source
export still matches all 230 original file hashes. `verify-evidence.py` validates
the retained attempts, executable identities, blocks, source files and hashes;
`verify-index.py` checks exact staged scope and byte identities before commit.
