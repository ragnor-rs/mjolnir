"""Run every command `host.checks` names as its `mirrors`, in order, over this tree."""
import json
import shlex
import subprocess
import sys

cfg = json.loads(subprocess.run(["python3", "plugins/mjolnir/scripts/config.py"],
                                capture_output=True, text=True, check=True).stdout)
checks = cfg["config"]["host"]["checks"]

red = []
for entry in checks:
    name, cmd = entry["workflow"], entry["mirrors"]
    proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    mark = "green" if proc.returncode == 0 else "RED  "
    print("%s  %-26s %s" % (mark, name, cmd))
    if proc.returncode != 0:
        red.append((name, cmd, proc.returncode, proc.stdout[-3000:], proc.stderr[-2000:]))

print("\n%d of %d green" % (len(checks) - len(red), len(checks)))
for name, cmd, rc, out, err in red:
    print("\n===== RED: %s (exit %d)\n%s" % (name, rc, cmd))
    print(out)
    print(err)
sys.exit(1 if red else 0)
