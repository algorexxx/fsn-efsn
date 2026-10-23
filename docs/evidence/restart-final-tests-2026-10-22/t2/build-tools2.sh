set -euo pipefail
. "$(dirname "$0")/../env.sh"
cd ~/t2/src-tools
cp $SP/t2/harness/responses.json tests/restart/testdata/responses.json
git add tests/restart/testdata/responses.json
git -c user.name=t2 -c user.email=t2@local commit -q -m "T2 harness: restore the genesis observation (id 2) needed by the full-state fixture"
git log --oneline -3
go test -c -o ~/t2/bin/t2-harness.test ./tests/restart
sha256sum ~/t2/bin/t2-harness.test
mv $SP/t2/work/operator $SP/t2/work/operator-attempt1
mv $SP/t2/work/operator.log $SP/t2/work/operator-attempt1.log
