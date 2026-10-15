"""Strict adapter around the unchanged, pinned upstream executable.

The upstream CLI can exit zero after failure. Require success marker, fresh IR,
valid type JSON, fact inputs, and all three preprocessing result relations.
"""
import csv
import json
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path
from .common import ROOT, digest, write_json
from .projection import train_affecting

BASELINE = ROOT / "third_party/leakage-analysis"
PIN = "a7d038bfec6b8ddbe21d87dde54b806aecdd79f7"
PYRIGHT_PIN = "e3d7d9c44ac69fa6bc66bb8a47377fcec034e503"

def environment():
    env = os.environ.copy()
    env["PATH"] = str(ROOT / ".env-baseline/bin") + ":" + str(ROOT / ".tools/souffle/usr/bin") + ":" + env.get("PATH", "")
    env["LD_LIBRARY_PATH"] = str(ROOT / ".env-ffi/lib") + ":" + str(ROOT / ".env-baseline/lib") + ":" + env.get("LD_LIBRARY_PATH", "")
    return env

def run(source, out, timeout=720):
    source, out = Path(source).resolve(), Path(out).resolve()
    # A fresh directory is essential: upstream silently reuses type files otherwise.
    out.mkdir(parents=True, exist_ok=False)
    work = out / "work"
    work.mkdir()
    inp = work / "input.py"
    inp.write_bytes(source.read_bytes())
    config = {"baseline": PIN, "pyright": PYRIGHT_PIN, "timeout_seconds": timeout,
              "python_dependencies_sha256": digest((ROOT / 'configs/requirements-baseline.lock').read_bytes()),
              "tool_versions_sha256": digest((ROOT / 'configs/versions.json').read_bytes())}
    result = {"sample_id": source.stem, "source_sha256": digest(inp.read_bytes()),
              "method": "S0", "config_sha256": digest(config), "status": "error",
              "diagnostics": [], "errors": [], "raw_preprocessing_rows": [],
              "location_available": False, "scope_projection": "raw upstream; may include test-only effects"}
    start = time.monotonic()
    cmd = [str(ROOT / ".env-baseline/bin/python"), "-m", "src.main", str(inp)]
    result["command"] = cmd
    try:
        actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=BASELINE, text=True).strip()
        pyright = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=BASELINE / "pyright", text=True).strip()
        if actual != PIN or pyright != PYRIGHT_PIN:
            raise RuntimeError("Pinned baseline/Pyright commit mismatch")
        for directory,source_dir in ((BASELINE,'src'),(BASELINE/'pyright','packages/pyright-internal/src')):
            if subprocess.run(['git','diff','--quiet','HEAD','--',source_dir],cwd=directory).returncode:
                raise RuntimeError('Pinned analysis source has local semantic modifications')
        with (out / "stdout.log").open("w") as log:
            p = subprocess.Popen(cmd, cwd=BASELINE, env=environment(), stdout=log,
                                 stderr=subprocess.STDOUT, start_new_session=True)
            try:
                result["returncode"] = p.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid, signal.SIGKILL)
                p.wait()
                result["status"] = "timeout"
                result["errors"].append("Whole baseline process group exceeded timeout")
        log = (out / "stdout.log").read_text(errors="replace")
        if result["status"] != "timeout":
            if result["returncode"] or "Success!" not in log or "Failed" in log or "Traceback" in log:
                raise RuntimeError("Upstream stage failure; inspect stdout.log")
            if "reportMissingImports" in log:
                raise RuntimeError("Unresolved Python library imports invalidate this baseline run")
            json.loads(Path(str(inp) + ".json").read_text())
            if not Path(str(inp) + ".ir.py").is_file():
                raise RuntimeError("Missing transformed source")
            facts = work / "input-fact"
            if not (facts / "Invoke.facts").is_file():
                raise RuntimeError("Missing invocation facts")
            required = {"PreProcessingLeak.csv": 4, "Telemetry_PreProcessingLeak.csv": 12,
                        "Telemetry_FinalPreProcessingLeak.csv": 12}
            for name, columns in required.items():
                path = facts / name
                with path.open(newline="") as f:
                    rows = list(csv.reader(f, delimiter="\t"))
                if any(len(row) != columns for row in rows):
                    raise RuntimeError("Unexpected column count in " + name)
                shutil.copy2(path, out / name)
                if name == "PreProcessingLeak.csv":
                    result["raw_preprocessing_rows"] = rows
            result["status"] = "leak" if result["raw_preprocessing_rows"] else "no_finding"
            result["train_affecting_projection"] = train_affecting(facts)
            result["scope_status"] = "leak" if result["train_affecting_projection"] else "no_finding"
    except Exception as e:
        result["errors"].append(str(e))
    result["elapsed_seconds"] = time.monotonic() - start
    write_json(out / "result.json", result)
    return result

