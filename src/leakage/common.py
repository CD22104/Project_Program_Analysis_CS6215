import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def digest(value):
    if not isinstance(value, bytes):
        value = (value if isinstance(value, str) else json.dumps(value, sort_keys=True)).encode()
    return hashlib.sha256(value).hexdigest()

def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")

def implementation_digest():
    files = (list((ROOT / 'src').rglob('*.py')) + list((ROOT / 'specs').glob('*')) + list((ROOT / 'prompts').glob('*'))
             + list((ROOT/'scripts').glob('*.py')) + list((ROOT/'configs').glob('*.lock'))
             + [ROOT/'configs/versions.json',ROOT/'configs/tool-downloads.json',ROOT/'configs/model-service.json'])
    return digest({str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in sorted(files) if p.is_file()})

