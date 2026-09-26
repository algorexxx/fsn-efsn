import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
command = [str(workspace / "tmp/network-self-windows-tests.exe"), "-test.run=^TestRestartDiscoveryRejectsSelf$", "-test.v"]
result = subprocess.run(command, cwd=workspace, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
(evidence / "windows-unit.txt").write_bytes(result.stdout)
(evidence / "windows-unit-exit.txt").write_text(str(result.returncode) + "\n", encoding="utf-8", newline="\n")
print(result.stdout.decode("utf-8"))
raise SystemExit(result.returncode)
