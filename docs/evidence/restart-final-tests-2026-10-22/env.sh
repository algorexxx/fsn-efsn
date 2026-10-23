export GOROOT=/home/rehearsal/toolchains/go1.27.3
export PATH=$GOROOT/bin:/usr/local/bin:/usr/bin:/bin
export GOTOOLCHAIN=local
export GOFLAGS=-mod=readonly
export SP=/mnt/c/Users/Peter/AppData/Local/Temp/claude/C--Users-Peter-Documents-CODING-fsn-efsn/a8ea1c11-81b9-474d-b4c3-dda6b28fadac/scratchpad
export SRC=/home/rehearsal/fsn-efsn-src
export W=/home/rehearsal/efsn-branches
export E=docs/evidence
ev() { git -C $SRC show "HEAD:$1"; }
