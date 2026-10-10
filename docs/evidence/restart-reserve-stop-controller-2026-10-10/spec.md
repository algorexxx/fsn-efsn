# Native reserve-stop provenance gates

Only the offline test controller changes. A native host-reserve refusal has no
STOP marker; require exact failed completion/log/run identities, qualified cold
inspection and its recorded discovery refusal. Preserve old STOP-based rules.
First run the two affected legacy stopped-checkpoint provenance tests. After
the actual new inspection verifies, run the two native-reserve provenance tests.
Do not claim acceptance or start replay before both stages pass. No database,
network, key or runtime-code workload is part of these small controller tests.
