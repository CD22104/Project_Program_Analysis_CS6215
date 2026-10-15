"""Audit raw author labels privately; never provide them to analyzer/model inputs."""
import argparse
import ast
import collections
import csv
import hashlib
import json
import random
import zipfile
from pathlib import Path
from leakage.common import ROOT, digest, write_json
from leakage.sanitize import extract_notebook

def label_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    # The released header has six fields while every record has eight. Name only
    # documented columns; keep trailing fields uninterpreted and retain raw rows.
    records = []
    for index, row in enumerate(rows[1:], 2):
        if len(row) != 8:
            raise ValueError("Unexpected label width at row " + str(index))
        records.append({"row_number": index, "raw": row, "nb": row[0], "model": row[1],
                        "pre_raw": row[2], "overlap_raw": row[3], "multi_raw": row[4],
                        "uninterpreted_tail": row[5:], "review_status": "pending_student_review"})
    return {"header": rows[0], "records": records}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--materials", type=Path, required=True)
    args = p.parse_args()
    materials = args.materials.resolve()
    private = ROOT.parent / "private-annotations"
    private.mkdir(exist_ok=True)
    audits = {}
    for name in ("ground-truth.csv", "manual-labels.csv"):
        data = label_rows(materials / name)
        write_json(private / (name + ".json"), data)
        audits[name] = {"sha256": digest((materials / name).read_bytes()), "header_width": len(data["header"]),
                        "record_count": len(data["records"]), "record_widths": [8],
                        "blank_pre_count": sum(not r["pre_raw"].strip() for r in data["records"]),
                        "parser": "positional first five documented fields; raw tail preserved"}
    members, manifest, seen = [], [], set()
    with zipfile.ZipFile(materials / "sample-notebooks.zip") as archive:
        members = archive.namelist()
        for name in sorted(n for n in members if n.endswith(".ipynb")):
            raw = archive.read(name)
            sid = "real_" + digest(name)[:12]
            r = {"sample_id": sid, "archive_member": name, "raw_sha256": digest(raw),
                 "source_repository": None, "license": "unconfirmed; download only; do not redistribute",
                 "review_status": "pending_student_review", "partition": "excluded", "source_kind": "real"}
            try:
                source, mapping = extract_notebook(json.loads(raw))
                tree = ast.parse(source)
                source_hash = digest(ast.dump(tree, include_attributes=False))
                calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
                def call_name(n):
                    if isinstance(n, ast.Name): return n.id
                    if isinstance(n, ast.Attribute): return call_name(n.value) + '.' + n.attr
                    return '<dynamic>'
                names = {call_name(n.func) for n in calls}
                r["source_sha256"] = digest(source)
                if source_hash in seen:
                    r["exclusion_reason"] = "exact AST duplicate"
                elif not any(n.endswith("train_test_split") for n in names):
                    r["exclusion_reason"] = "no statically explicit train_test_split; manual scope review needed"
                elif not any(n.endswith(".fit") for n in names) or not any(n.endswith((".predict", ".score")) for n in names):
                    r["exclusion_reason"] = "no explicit fit and evaluation pair"
                else:
                    r["partition"] = "candidate"
                    r["exclusion_reason"] = None
                seen.add(source_hash)
                target = ROOT / "data/clean/real" / (sid + ".py")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(source)
                write_json(target.with_suffix(".map.json"), mapping)
                r["source_path"] = str(target.relative_to(ROOT))
            except (SyntaxError, ValueError, tokenize_error()) as e:
                r["exclusion_reason"] = "code-only export not Python-parseable: " + type(e).__name__
            manifest.append(r)
    # Select without labels or predictions; dev count and partitions are provisional
    # until student scope/annotation review. Near duplicates still need review.
    candidates = sorted((r for r in manifest if r["partition"] == "candidate"), key=lambda r: r["sample_id"])
    random.Random(6215).shuffle(candidates)
    for i, r in enumerate(candidates):
        r["partition"] = "dev" if i < min(5, len(candidates)) else "test_pending_freeze"
    audits["archive"] = {"sha256": digest((materials / "sample-notebooks.zip").read_bytes()),
                         "notebooks": sum(n.endswith(".ipynb") for n in members),
                         "author_html_count": sum(n.endswith(".html") for n in members),
                         "html_read": False, "notebook_outputs_used": False,
                         "candidates": len(candidates), "confirmed_repository_count": 0,
                         "exclusions": dict(collections.Counter(r["exclusion_reason"] for r in manifest if r["exclusion_reason"]))}
    write_json(ROOT / "data/manifests/author-data-audit.json", audits)
    write_json(ROOT / "data/manifests/real.json", manifest)
    # A review queue can refer to raw labels but lives outside the artifact.
    write_json(private / "review-queue.json", [{k: r.get(k) for k in ("sample_id", "archive_member", "partition", "source_path", "review_status")} for r in candidates])
    print(json.dumps({"notebooks": audits["archive"]["notebooks"], "candidates": len(candidates),
                      "excluded": len(manifest) - len(candidates), "student_review": "pending"}))

def tokenize_error():
    import tokenize
    return tokenize.TokenError

if __name__ == "__main__":
    main()
