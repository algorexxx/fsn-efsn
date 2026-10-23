# User: rehearsal efsn/bootnode from a clone of efsn-final with the rehearsal's own hashes pinned in mainnetCheckPoints.
set -euo pipefail
. "$(dirname "$0")/../env.sh"
[ ! -e ~/t2/src-node ] || { echo "refusing: ~/t2/src-node exists"; exit 1; }
git clone -q ~/efsn-final ~/t2/src-node
cd ~/t2/src-node
git log --oneline -1
f=consensus/datong/checkpoints.go
old='		15130080: common.HexToHash("0xe93ffded087a79097d4309c7831690161db6ed136f4b1a22c4c83a99db80f99f"),'
[ "$(grep -cF "$old" $f)" = 1 ]
python3 - "$f" <<'PY'
import sys
f = sys.argv[1]
s = open(f, encoding="utf-8").read()
old = '\t\t15130080: common.HexToHash("0xe93ffded087a79097d4309c7831690161db6ed136f4b1a22c4c83a99db80f99f"),\n'
new = ('\t\t15130080: common.HexToHash("0xe463e592a96c93420fbf155824b4ee95ba418ee29312637e8dd08eea43951458"),\n'
       '\t\t15130081: common.HexToHash("0xd2cfe5bb26551cda5c04ced4598a72944daa12da6962f256c376ca5bfa6b9586"),\n'
       '\t\t15130082: common.HexToHash("0x25b2f389e8d70f6442c90fd707ed1f5699c4e7b549d66a5a027a18bcf6bb68a6"),\n'
       '\t\t15130083: common.HexToHash("0x1d68db766979da529fcaf9a8f8f217bcf08f6e3705eb348febd2d28ca83a78db"),\n')
assert s.count(old) == 1
open(f, "w", encoding="utf-8").write(s.replace(old, new))
PY
gofmt -l consensus/datong/ || true
git diff
grep -n "mainnetLastCheckPoint uint64" $f
git -c user.name=t2 -c user.email=t2@local commit -qam "REHEARSAL ONLY (T2): pin synthetic parent and rehearsal recovery blocks"
git log --oneline -2
go vet ./consensus/datong
go build -o ~/t2/bin/efsn ./cmd/efsn
go build -o ~/t2/bin/bootnode ./cmd/bootnode
sha256sum ~/t2/bin/efsn ~/t2/bin/bootnode | sed "s#$HOME/##"
~/t2/bin/efsn version | head -4
df -h / | tail -1
