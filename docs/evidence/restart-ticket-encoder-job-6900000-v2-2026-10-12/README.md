# Continue the interrupted range toward 6,900,000

Prepared from separately verified 6,623,296 after the first attempt's size-scan
stop. The original failure is retained. The live allocation fix passes 32 tests
and matches du on the closed checkpoint. See [finite limits](inputs/spec.md).
Preparation adds no coverage; launch, startup and final cold verification must
be observed separately. Capacity and resource gates remain unchanged.
