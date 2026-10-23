set -e
. "$(dirname "$0")/../env.sh"
date -u
rm -rf ~/efsn-tools-union && git clone -q ~/efsn-final ~/efsn-tools-union && cd ~/efsn-tools-union
git -C $W diff --binary fix/chain-consistency tools/restart-recovery | git apply --index --exclude=tests/restart/purchase_test.go
git -c user.name=t -c user.email=t@local commit -q -m "final candidate + tools/restart-recovery"
grep -c ticketgzip core/state/statedb.go
go build -o ~/final-bin/fsn-recovery.union ./cmd/fsn-recovery
go vet ./cmd/fsn-recovery ./tests/restart
go test -race -count=1 ./cmd/fsn-recovery/... 2>&1 | tail -5
cmp ~/final-bin/fsn-recovery ~/final-bin/fsn-recovery.union && echo SAME || echo "binaries differ (expected)"
mv ~/final-bin/fsn-recovery ~/final-bin/fsn-recovery.WRONG-unfrozen-encoders
mv ~/final-bin/fsn-recovery.union ~/final-bin/fsn-recovery
sha256sum ~/final-bin/* | sed "s#$HOME/##"
