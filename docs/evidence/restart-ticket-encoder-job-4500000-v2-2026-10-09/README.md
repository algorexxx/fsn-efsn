# Corrected 4,500,000 job

Prepared after verified D: reclamation. The first attempt failed at the exact
observer-byte comparison before executing any test command or replay. Its
Windows CRLF conversion was the sole unexpected difference. This fresh job
preserves LF bytes and changes exactly the endpoint literal from the verified
3,600,000 observer; see corrected-input.json and inputs/spec.md.

Existing controller, replay executable, recovery checkpoint, release selection,
offline isolation, capacity floors and finite limits are unchanged. A successful
start is not verified completion. Inspect the job's completion, verification and
resource records before continuing or inspecting the working database.
