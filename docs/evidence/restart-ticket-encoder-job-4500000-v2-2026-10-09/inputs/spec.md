# Corrected finite replay: 3,600,000 to 4,500,000

The first job refused preparation before any observer compilation or replay
because its observer source had CRLF line endings. The retained preceding
observer uses LF, and the controller correctly requires exactly one endpoint
literal change with no other byte differences.

This fresh job changes only the job name and corrects that input's line endings.
The observer is copied as bytes from the 3,600,000 input with exactly one
3600000 to 4500000 literal substitution. The prior failed job and all its inputs,
logs and completion records remain preserved. The corrected-input.json record
documents the byte comparison. The prepared replay executable, source/release
selection, controller, 11 GiB target ceiling, 6h/6h15m/6h30m finite time limits,
20/50 GiB per-batch reserves and existing starting-capacity calculation remain
unchanged. Preserve the separate 2,400,000 recovery checkpoint and original backup.

Run the existing private offline mount/network launcher after fresh capacity
checks and full cold starting-inventory validation. Both endpoint cold checks,
all preservation checks and automatic evidence verification are still required.
Do not open public peers, sign real keys, mine publicly or start another writer.
