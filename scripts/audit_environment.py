"""Record reproducibility metadata without reading or recording credential values."""
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def capture(cmd):
    p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return {"command": cmd, "returncode": p.returncode, "output": p.stdout}

def main():
    d = {"platform": platform.platform(), "python": platform.python_version(),
         "cpu_count": os.cpu_count(), "disk": dict(zip(("total", "used", "free"), shutil.disk_usage(ROOT))),
         "credential_variable_names": sorted(k for k in os.environ if "API_KEY" in k or "BASE_URL" in k),
         "tools": {n: shutil.which(n) for n in ("node", "npm", "souffle", "docker", "pdflatex")},
         "checks": [capture(["git", "-C", str(ROOT / "third_party/leakage-analysis"), "rev-parse", "HEAD"]),
                    capture(["git", "-C", str(ROOT / "third_party/leakage-analysis/pyright"), "rev-parse", "HEAD"])]}
    out = ROOT / "runs/environment/audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(d, indent=2) + "\n")
    print(out.relative_to(ROOT))

if __name__ == "__main__":
    main()
