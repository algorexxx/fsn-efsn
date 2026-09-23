import argparse
import json
from pathlib import Path
import subprocess


parser = argparse.ArgumentParser(description="Run the temporary parent-time reconstruction overlay.")
parser.add_argument("--go", default="go")
parser.add_argument("--race", action="store_true")
args = parser.parse_args()
repository = Path(__file__).resolve().parents[2]
overlay = repository / "tmp/restart-reconstruction-overlay"
overlay.mkdir(parents=True, exist_ok=True)
replacements = {}
changes = [
    (
        "consensus/datong/consensus.go",
        "tickets, err = tickets.ClearExpiredTickets(header.Time)",
        "cleanupParent, err := getParent(chain, header, nil)\n"
        "\tif err != nil {\n\t\treturn nil, err\n\t}\n"
        "\ttickets, err = tickets.ClearExpiredTickets(cleanupParent.Time)",
    ),
    (
        "tests/restart/reconstruction_test.go",
        "const expectParentTimeReconstruction = false",
        "const expectParentTimeReconstruction = true",
    ),
]
for relative, before, after in changes:
    source = repository / relative
    original = source.read_text(encoding="utf-8")
    if original.count(before) != 1:
        raise RuntimeError(f"Expected exactly one replacement in {relative}; review the experiment.")
    destination = overlay / source.name
    destination.write_text(original.replace(before, after), encoding="utf-8")
    replacements[str(source)] = str(destination)

overlay_path = overlay / "overlay.json"
overlay_path.write_text(json.dumps({"Replace": replacements}, indent=2) + "\n", encoding="utf-8")
command = [args.go, "test", "-overlay", str(overlay_path), "./tests/restart", "-v", "-count=1", "-timeout=90s"]
if args.race:
    command.insert(2, "-race")
raise SystemExit(subprocess.run(command, cwd=repository).returncode)
