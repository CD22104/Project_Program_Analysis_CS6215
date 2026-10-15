import argparse
import json
from pathlib import Path
from leakage.baseline import BASELINE, run
from leakage.common import ROOT, write_json

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="runs/baseline-smoke")
    p.add_argument("--legacy-function", action="store_true", help="Also run the documented legacy notebook with obsolete imports")
    args = p.parse_args()
    out = ROOT / args.out
    out.mkdir(parents=True,exist_ok=False)
    expectations = {"test0.py": ["LogisticRegression.fit"], "test1.py": ["LogisticRegression.fit"],
                    "test2.py": ["LogisticRegression.fit"], "test3.py": [], "test4.py": []}
    sources={name:BASELINE/'tests/inputs'/name for name in expectations}
    original=(BASELINE/'tests/inputs/test0.py').read_text()
    old="df['Fare'] = df['Fare'].fillna(np.mean(df['Fare']), inplace = False)"
    for suffix,fill in [('positive',"np.mean(frame['Fare'])"),('negative','0')]:
        name='wrapper_'+suffix+'.py'
        helper="def fill_column(frame):\n    return frame['Fare'].fillna("+fill+", inplace=False)\n\ndf['Fare'] = fill_column(df)"
        source=out/name;source.write_text(original.replace(old,helper));sources[name]=source
        expectations[name]=['LogisticRegression.fit'] if suffix=='positive' else []
    if args.legacy_function:
        expectations['nb_481597.py']=['RandomForestRegressor.fit']
        sources['nb_481597.py']=BASELINE/'tests/inputs/nb_481597.py'
    rows = []
    for name, expected in expectations.items():
        r = run(sources[name], out / Path(name).stem)
        actual = sorted(set(row[2] for row in r["raw_preprocessing_rows"]))
        rows.append({"sample": name, "status": r["status"], "expected_methods": expected,
                     "actual_methods": actual, "passed": actual == sorted(expected) and r["status"] in ("leak", "no_finding"),
                     "elapsed_seconds": r["elapsed_seconds"]})
        print(json.dumps(rows[-1]), flush=True)
    write_json(out / "checks.json", rows)
    raise SystemExit(0 if all(r["passed"] for r in rows) else 1)

if __name__ == "__main__":
    main()
