# User: T2 harness clone of efsn-tools-union (tests only + shifted fixture times); builds fsn-recovery and the harness test binary.
set -euo pipefail
. "$(dirname "$0")/../env.sh"
T2=$SP/t2
mkdir -p ~/t2/bin
[ ! -e ~/t2/src-tools ] || { echo "refusing: ~/t2/src-tools exists"; exit 1; }
git clone -q ~/efsn-tools-union ~/t2/src-tools
cd ~/t2/src-tools
git log --oneline -1
cp $T2/harness/t2_harness_test.go $T2/harness/full_state_operator_test.go tests/restart/
cp $T2/harness/context.rlp tests/restart/testdata/context.rlp
sed -i 's/^const jumpTime uint64 = 1790121600$/const jumpTime uint64 = 1792627200/; s/^const ticketEnd uint64 = 1792713600$/const ticketEnd uint64 = 1795219200/' tests/restart/fixture_test.go
grep -n "^const jumpTime\|^const ticketEnd" tests/restart/fixture_test.go
git add -A tests/restart
git -c user.name=t2 -c user.email=t2@local commit -q -m "T2 rehearsal harness: shift fixture jump/ticket end by 29 days, add operator and node-seed tests"
git log --oneline -2
go vet ./tests/restart
go test -c -o ~/t2/bin/t2-harness.test ./tests/restart
go build -o ~/t2/bin/fsn-recovery ./cmd/fsn-recovery
git diff --stat HEAD~1 HEAD -- . ':!tests' | tail -1
sha256sum ~/t2/bin/* ~/final-bin/fsn-recovery | sed "s#$HOME/##"
df -h / | tail -1
