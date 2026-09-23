import argparse
import json
from pathlib import Path
import subprocess


parser = argparse.ArgumentParser(description="Test receipt-log ownership with a temporary compiler overlay.")
parser.add_argument("--go", default="go")
args = parser.parse_args()
repository = Path(__file__).resolve().parents[2]
overlay = repository / "tmp/restart-receipt-copy-overlay"
overlay.mkdir(parents=True, exist_ok=True)
source = repository / "miner/worker.go"
original = source.read_text(encoding="utf-8")
before = "\t\tcpy := *l\n\t\tresult[i] = &cpy"
after = (
    "\t\tcpy := *l\n"
    "\t\tcpy.Logs = make([]*types.Log, len(l.Logs))\n"
    "\t\tfor j, entry := range l.Logs {\n"
    "\t\t\tentryCopy := *entry\n"
    "\t\t\tentryCopy.Topics = append([]common.Hash(nil), entry.Topics...)\n"
    "\t\t\tentryCopy.Data = common.CopyBytes(entry.Data)\n"
    "\t\t\tcpy.Logs[j] = &entryCopy\n"
    "\t\t}\n"
    "\t\tresult[i] = &cpy"
)
if original.count(before) != 1:
    raise RuntimeError("Expected exactly one receipt-copy expression; review the experiment.")
destination = overlay / source.name
destination.write_text(original.replace(before, after), encoding="utf-8")
overlay_path = overlay / "overlay.json"
overlay_path.write_text(json.dumps({"Replace": {str(source): str(destination)}}, indent=2) + "\n", encoding="utf-8")
command = [args.go, "test", "-race", "-overlay", str(overlay_path), "./tests/restart", "-run=^TestAutoBuyRuntime$", "-v", "-count=3", "-timeout=180s"]
raise SystemExit(subprocess.run(command, cwd=repository).returncode)
