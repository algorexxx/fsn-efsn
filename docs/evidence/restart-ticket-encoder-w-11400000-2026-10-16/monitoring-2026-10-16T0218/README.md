# Runtime status unavailable during the 02:18 UTC heartbeat

Two read-only FusionRehearsal status commands failed with
`Wsl/Service/0x8007274c`; the retry returned -1. `wsl --list --verbose`
succeeded and reported FusionRehearsal and docker-desktop running. The host
dispatcher PID 87064 remains alive, but no inner completion, verification,
outer completion or host-exit record exists. Host output/error logs are empty.
This is a monitoring failure; the test's runtime health and current height
cannot be established. It is not a verified replay failure or completion.

Host metadata at 2026-10-16T02:22:07.8257652+00:00 records 0.712 GiB available physical
RAM and 4.064 GiB free on C:. D: remains above the running reserve. These
observations do not establish the cause of the WSL connection failures.
No new writer, database hash, mounted-image hash, service restart, process
termination or data cleanup was performed. Frozen inputs and finite limits
remain unchanged. Last verified checkpoint is 11,100,000; the 11,400,000
continuation remains unverified with unknown runtime state.

Stop dependent launches while WSL is inaccessible. Ask the user to close
unneeded Windows applications to free RAM, then recheck the existing job.
Closing unrelated applications may discard unsaved work, so it is left to the
user. Do not force WSL termination against a potentially active mounted image.
Once access returns, inspect completion, process, resource and attachment state
before any recovery or continuation. Preserve all existing evidence and data.
