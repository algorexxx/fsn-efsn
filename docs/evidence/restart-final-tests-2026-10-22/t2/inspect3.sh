cd /home/rehearsal/efsn-tools-union/tests/restart
grep -n "context.rlp\|docs/evidence\|FUSION_RESTART_FULL_STATE\|Getenv" *.go | head -30
grep -n "func requireReplaySpace\|func readHandoverJSON\|func writeStateExportJSON\|func offlineChainPath\|func runRecoveryOperator(" *.go
ls ../../docs 2>/dev/null | head
sed -n '/func offlineChainPath/,/^}/p' recovery_offline_test.go
sed -n '/func runRecoveryOperator(/,/^}/p' recovery_operator_test.go
