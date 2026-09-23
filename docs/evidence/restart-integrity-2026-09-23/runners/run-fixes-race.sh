set -euo pipefail
results=/home/rehearsal/results/restart-integrity-2026-09-23
ip -brief link > "$results/fixes-race-isolation.txt"
sha256sum /home/rehearsal/fixes-race-tests >> "$results/fixes-race-isolation.txt"
date --utc --iso-8601=seconds > "$results/fixes-race-started.txt"
cd /home/rehearsal/fsn-efsn-fixes/tests/restart
set +e
runuser -u rehearsal -- env GOMAXPROCS=2 /home/rehearsal/fixes-race-tests -test.v -test.count=3 -test.timeout=180s > "$results/fixes-race.txt" 2>&1
result=$?
printf '%s\n' "$result" > "$results/fixes-race-exit-code.txt"
date --utc --iso-8601=seconds > "$results/fixes-race-finished.txt"
tail -n 10 "$results/fixes-race.txt"
exit "$result"
