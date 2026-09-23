set -euo pipefail
source=/home/rehearsal/data/efsn/chaindata
mountpoint=/mnt/fusion-replay-resume
target=/home/rehearsal/replay/resume-validation
results=/home/rehearsal/results/restart-resume-2026-09-23
test ! -e "$target"
mkdir -p "$mountpoint" "$results"
mount --bind "$source" "$mountpoint"
mount -o remount,bind,ro "$mountpoint"
findmnt -no TARGET,OPTIONS -T "$mountpoint" > "$results/isolation.txt"
findmnt -no OPTIONS -T "$mountpoint" | grep -Eq '(^|,)ro(,|$)'
ip -brief link >> "$results/isolation.txt"
sha256sum /home/rehearsal/replay-resume-tests >> "$results/isolation.txt"
cd /home/rehearsal/fsn-efsn/tests/restart
run_stage() {
    name=$1
    end=$2
    resume=$3
    shift 3
    set +e
    runuser -u rehearsal -- env FUSION_RESTART_CHAINDATA="$mountpoint" FUSION_RESTART_FULL_AUDIT=1 FUSION_RESTART_REPLAY_DIR="$target" FUSION_RESTART_REPLAY_END="$end" FUSION_RESTART_REPLAY_RESUME="$resume" FUSION_RESTART_HOST_STORAGE=/mnt/d GOMAXPROCS=2 "$@" /home/rehearsal/replay-resume-tests '-test.run=^TestPreservedHistoryReplay$' -test.v -test.timeout=10m > "$results/$name.txt" 2>&1
    stage_result=$?
    set -e
    printf '%s\n' "$stage_result" > "$results/$name-exit-code.txt"
    tail -n 4 "$results/$name.txt"
}
date --utc --iso-8601=seconds > "$results/started.txt"
run_stage initial 1024 0
test "$stage_result" -eq 0
run_stage accidental-reuse 2048 0
test "$stage_result" -ne 0
grep -q 'replay requires a new directory' "$results/accidental-reuse.txt"
run_stage lower-end 512 1
test "$stage_result" -ne 0
grep -q 'resume head is inconsistent' "$results/lower-end.txt"
touch "$target/operator-stop"
run_stage controlled-stop 2048 1 FUSION_RESTART_REPLAY_STOP_FILE="$target/operator-stop"
test "$stage_result" -ne 0
grep -q 'replay stopped by stop file' "$results/controlled-stop.txt"
run_stage resume 10000 1
test "$stage_result" -eq 0
grep -q 'height=10000 hash=0x1830e440e17cda3a26d02ea650331a584d58a499cbbd3821c622568c8de9b470 root=0xc85623ffdf98796fb39d437ceff4626b7aa56bb5ee12c8b1491a7524ad85cfbf ticketCommitment=0x0f8a8be52d2df5f43c50a33049c1594252d48c6fb523fc35adac5c27750c5456' "$results/resume.txt"
date --utc --iso-8601=seconds > "$results/finished.txt"
printf 'PASS: new, reuse rejection, lower-end rejection, controlled stop and resumed commitment match\n' | tee "$results/result.txt"
