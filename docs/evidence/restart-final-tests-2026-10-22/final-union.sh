. "$(dirname "$0")/env.sh"
cd $W
echo "== branch shape"
git log --merges --oneline develop..build/go-toolchain develop..fix/jwt-and-test-fixtures develop..fix/p2p-discovery develop..feature/restart-checkpoints develop..feature/autobuy-retry develop..tools/restart-recovery | wc -l
for b in fix/ticket-encoding-compat fix/fsn-log-json-compat build/go-toolchain fix/jwt-and-test-fixtures fix/p2p-discovery fix/chain-consistency feature/restart-checkpoints feature/autobuy-retry tools/restart-recovery; do
  echo "$b: $(git log --oneline develop..$b | wc -l) commits, base=$(git log -1 --format=%h $b~$(git log --oneline develop..$b | wc -l))"
done
echo "== runtime diff per branch vs parent (excluding tests and vendored Go files)"
for pair in develop:fix/ticket-encoding-compat fix/ticket-encoding-compat:fix/fsn-log-json-compat fix/fsn-log-json-compat:build/go-toolchain develop:fix/jwt-and-test-fixtures develop:fix/p2p-discovery develop:fix/chain-consistency fix/chain-consistency:feature/restart-checkpoints fix/chain-consistency:feature/autobuy-retry fix/chain-consistency:tools/restart-recovery; do
  a=${pair%%:*}; b=${pair##*:}
  echo "$b: $(git diff --shortstat $a $b -- . ':!*_test.go' ':!tests' ':!internal/ticketgzip/internal' ':!internal/logjson/internal')"
done
rm -rf ~/efsn-union && git clone -q $W ~/efsn-union && cd ~/efsn-union
git checkout -q -b union origin/build/go-toolchain
for d in "develop origin/fix/jwt-and-test-fixtures" "develop origin/fix/p2p-discovery" "develop origin/feature/restart-checkpoints" "origin/fix/chain-consistency origin/feature/autobuy-retry"; do
  git diff --binary $d | git apply --index || echo "APPLY FAILED $d"
done
git -c user.name=u -c user.email=u@local commit -q -m union
go version
make all >/dev/null 2>&1 && echo "make all OK"
go vet ./internal/... ./consensus/... ./p2p/discover ./cmd/utils ./tests/restart 2>&1 | grep -v "^#" | grep -E "internal/ticketgzip|internal/logjson|internal/ethapi|consensus|p2p/discover|cmd/utils|tests/restart" | head -5
go test -race -count=1 ./internal/ticketgzip ./internal/logjson ./core/types ./consensus/... ./ethdb/... ./p2p ./cmd/utils ./params ./internal/ethapi 2>&1 | grep -v "no test files"
go test -race -count=1 ./p2p/discover 2>&1 | grep -E "^(--- FAIL|ok|FAIL)"
go test -race -count=1 -timeout 25m -v ./tests/restart 2>&1 | grep -E "^(--- |ok|FAIL)|WARNING: DATA RACE"
cd ~ && rm -rf ~/efsn-union
