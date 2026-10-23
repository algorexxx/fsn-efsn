# User: copy the verified compact export into $1 (new dir) and write the copy proof required by requireFullStateCopy.
set -euo pipefail
SRC=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/tmp/preserved-head-state
MAN=/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-state-export-2026-09-24/artifact-SHA256SUMS
DST=$1
[ "$(sha256sum $MAN | cut -c1-64)" = a6c86fc58a9f7b482a02b787a337d600e32a447551e45dbe40d210b498341bbf ]
[ ! -e "$DST" ] || { echo "refusing: $DST exists"; exit 1; }
mkdir -p "$DST"
cp -r $SRC/. "$DST/"
(cd "$DST" && sha256sum --quiet -c $MAN)
[ "$(find "$DST" -type f | wc -l)" = 230 ]
printf '{\n  "Source": "%s",\n  "ManifestSHA256": "a6c86fc58a9f7b482a02b787a337d600e32a447551e45dbe40d210b498341bbf",\n  "Files": 230\n}\n' "$SRC" > "$DST/copy-verified.json"
echo "verified copy $DST"
