set -euo pipefail
cd /mnt/c/Users/Peter/Documents/CODING/fsn-efsn
export GOTOOLCHAIN=local GOPROXY=off CGO_ENABLED=1 GOMAXPROCS=2
/opt/fusion-toolchain/go/bin/go test -mod=readonly -p=2 -c -o tmp/dashboard-presentation-tests ./tests/restart
