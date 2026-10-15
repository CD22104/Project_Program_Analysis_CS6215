"""Zero-cost SoCLaaS client. No shell sourcing; keys never enter run artifacts."""
import fcntl
import http.client
import json
import os
import shlex
import socket
import ssl
import time
from pathlib import Path
from urllib.parse import urlsplit
from .common import ROOT, digest, write_json

DEFAULT_CONFIG = Path.home() / ".config/course/soclaas.env"
PUBLIC_CANDIDATE_FIELDS = (
    "candidate_id", "source_sha256", "ir_sha256", "invocation", "context", "function_id",
    "canonical_method", "code", "ir_line", "input_variable", "input_index", "return_variable",
    "receiver", "state_version", "resolved_axis", "input_rank", "sample_axis", "primitive_spec_sha256",
    "resolved_parameters", "function_parameter_dependencies")

def config(path=DEFAULT_CONFIG):
    result = {}
    if Path(path).exists():
        for line in Path(path).read_text().splitlines():
            parts = shlex.split(line, comments=True)
            if parts and parts[0] == "export":
                parts = parts[1:]
            if not parts:
                continue
            key, value = " ".join(parts).split("=", 1)
            result[key.strip()] = value.strip()
    for key in ("SOCLAAS_BASE_URL", "SOCLAAS_API_KEY", "SOCLAAS_MODEL", "SOCLAAS_CONNECT_HOST", "SOCLAAS_CONNECT_PORT"):
        if key in os.environ:
            result[key] = os.environ[key]
    for key in ("SOCLAAS_BASE_URL", "SOCLAAS_API_KEY", "SOCLAAS_MODEL"):
        if not result.get(key):
            raise ValueError("Missing " + key)
    u = urlsplit(result["SOCLAAS_BASE_URL"])
    if u.scheme != "https" or u.hostname != "soclaas-api.comp.nus.edu.sg" or u.username or u.query or u.fragment:
        raise ValueError("Only the user-authorized free SoCLaaS HTTPS service is configured")
    if result.get("SOCLAAS_CONNECT_HOST") not in (None, "127.0.0.1", "localhost", "::1"):
        raise ValueError("An optional SSH tunnel must listen on loopback")
    return result

class TunnelHTTPS(http.client.HTTPSConnection):
    def __init__(self, host, connect_host, connect_port, timeout):
        super().__init__(host, timeout=timeout, context=ssl.create_default_context())
        self.connect_host, self.connect_port = connect_host, connect_port

    def connect(self):
        sock = socket.create_connection((self.connect_host, self.connect_port), self.timeout)
        # Keep original certificate verification and SNI when crossing an SSH tunnel.
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)

class APIError(Exception):
    pass

def request(cfg, method, resource, body=None, timeout=120):
    u = urlsplit(cfg["SOCLAAS_BASE_URL"])
    if cfg.get("SOCLAAS_CONNECT_PORT"):
        conn = TunnelHTTPS(u.hostname, cfg.get("SOCLAAS_CONNECT_HOST", "127.0.0.1"), int(cfg["SOCLAAS_CONNECT_PORT"]), timeout)
    else:
        conn = http.client.HTTPSConnection(u.hostname, port=u.port or 443, timeout=timeout)
    try:
        payload = json.dumps(body).encode() if body is not None else None
        conn.request(method, u.path.rstrip("/") + "/" + resource.lstrip("/"), body=payload,
                     headers={"Authorization": "Bearer " + cfg["SOCLAAS_API_KEY"], "Content-Type": "application/json"})
        response = conn.getresponse()
        raw = response.read()
        if response.status != 200:
            # Avoid logging arbitrary upstream error bodies which could echo headers.
            raise APIError("SoCLaaS HTTP " + str(response.status))
        return json.loads(raw)
    finally:
        conn.close()

def messages(candidate):
    public = {k: candidate[k] for k in PUBLIC_CANDIDATE_FIELDS if k in candidate}
    return [{"role": "system", "content": (ROOT / "prompts/effects-v1.txt").read_text()},
            {"role": "user", "content": json.dumps({"candidate": public,
              "primitive_specification": json.loads((ROOT / "specs/primitives.json").read_text()),
              "output_schema": json.loads((ROOT / "specs/summary.schema.json").read_text())}, sort_keys=True)}]

def cache_key(candidate, cfg, repeat=0):
    return digest({"messages": messages(candidate), "model": cfg["SOCLAAS_MODEL"],
                   "endpoint": cfg["SOCLAAS_BASE_URL"], "temperature": 0, "max_tokens": 1200,
                   "replicate": repeat})

class Budget:
    """File-locked reservation ledger. Failed calls keep their full reservation."""
    def __init__(self, path, limit):
        self.path, self.limit = Path(path), limit
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def reserve(self, amount, key):
        with self.path.open("a+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.seek(0)
            entries = [json.loads(l) for l in f if l.strip()]
            used = sum(e["reserved_tokens"] for e in entries)
            if used + amount > self.limit:
                raise ValueError("Software token budget exhausted")
            f.write(json.dumps({"cache_key": key, "reserved_tokens": amount, "time_unix": time.time()}) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def settle(self, reserved, actual, key):
        if type(actual) is not int or actual < 0:
            return
        with self.path.open('a+') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.write(json.dumps({'cache_key':key,'reserved_tokens':actual-reserved,
                                'actual_tokens':actual,'kind':'settlement','time_unix':time.time()})+'\n')
            f.flush();os.fsync(f.fileno())

def generate(candidate, cfg, cache_dir, budget, repeat=0):
    key = cache_key(candidate, cfg, repeat)
    path = Path(cache_dir) / (key + ".json")
    if path.exists():
        record = json.loads(path.read_text())
        return {**record, "cache_hit": True}
    msg = messages(candidate)
    payload = {"model": cfg["SOCLAAS_MODEL"], "messages": msg, "temperature": 0,
               "max_tokens": 1200, "stream": False}
    # UTF-8 byte count plus overhead is a conservative token reservation for each
    # attempt. Actual provider usage is retained separately, including retries.
    reserve = len(json.dumps(msg, ensure_ascii=False).encode()) + 1200 + 512
    record = {"origin": "live_api", "cache_key": key, "candidate_id": candidate["candidate_id"],
              "model_requested": cfg["SOCLAAS_MODEL"], "messages": msg, "parameters": {"temperature": 0, "max_tokens": 1200},
              "attempts": [], "cache_hit": False, "replicate": repeat, "summary": None}
    for attempt in range(3):
        try:
            budget.reserve(reserve, key)
        except ValueError:
            record['budget_exhausted'] = True
            break
        start = time.monotonic()
        entry = {"attempt": attempt + 1, "reservation_tokens": reserve}
        try:
            raw = request(cfg, "POST", "chat/completions", payload)
            entry.update(response=raw, usage=raw.get("usage"), model_returned=raw.get("model"), success=True)
            usage = raw.get('usage') or {}
            budget.settle(reserve, usage.get('total_tokens'), key)
            content = raw["choices"][0]["message"]["content"]
            if content.startswith("```json") and content.rstrip().endswith("```"):
                content = content.strip()[7:-3].strip()
            record["summary"] = json.loads(content)
        except (APIError, OSError, ValueError, KeyError, IndexError, TypeError) as e:
            entry.update(success=False, error_type=type(e).__name__)
            if isinstance(e, APIError):
                entry["error"] = str(e)
        entry["elapsed_seconds"] = time.monotonic() - start
        record["attempts"].append(entry)
        # Invalid JSON is a recorded model failure; do not resample for a nicer answer.
        if entry["success"] or "response" in entry:
            break
        if attempt < 2:
            time.sleep(1 + attempt)
    write_json(path, record)
    return record
