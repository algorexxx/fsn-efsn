set -e
. "$(dirname "$0")/../env.sh"
rm -rf ~/efsn-final && git clone -q $W ~/efsn-final && cd ~/efsn-final
git checkout -q -b final origin/build/go-toolchain
for d in "develop origin/fix/jwt-and-test-fixtures" "develop origin/fix/p2p-discovery" "develop origin/feature/restart-checkpoints" "origin/fix/chain-consistency origin/feature/autobuy-retry"; do
  git diff --binary $d | git apply --index
done
git -c user.name=t -c user.email=t@local commit -q -m "final candidate (union of mergeable branches)"
echo "final candidate commit: $(git rev-parse HEAD)"
for b in build/go-toolchain fix/jwt-and-test-fixtures fix/p2p-discovery feature/restart-checkpoints feature/autobuy-retry; do echo "  $b $(git rev-parse --short origin/$b)"; done
go version
mkdir -p ~/t1 ~/final-bin
cp $SP/t1/t1_replay_linux_test.go tests/restart/
go vet ./tests/restart
go test -c -o ~/t1/replay.test ./tests/restart
go build -o ~/final-bin/efsn ./cmd/efsn
go build -o ~/final-bin/bootnode ./cmd/bootnode
git -C $W rev-parse --short tools/restart-recovery
rm -rf ~/efsn-tools && git clone -q $W ~/efsn-tools && cd ~/efsn-tools && git checkout -q origin/tools/restart-recovery
go build -o ~/final-bin/fsn-recovery ./cmd/fsn-recovery
sha256sum ~/t1/replay.test ~/final-bin/* | sed "s#$HOME/##"
~/final-bin/efsn version | head -3
df -h / | tail -1
