"""Create a local review archive; performs no publication or external upload."""
import json,zipfile
from pathlib import Path
from leakage.common import ROOT,digest,write_json

def main():
    files=[]
    for name in ('README.md','AGENTS.md','STATUS.md','.gitignore'):
        files.append(ROOT/name)
    for folder in ('src','scripts','specs','prompts','configs','docs','tests','results','data/manifests','data/annotations','data/clean/controlled','data/clean/variants','third_party/patches','third_party/acmart'):
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.key','.env'):
                files.append(p)
    files += [p for p in (ROOT/'report').glob('*') if p.is_file() and p.suffix in ('.tex','.bib','.pdf')]
    # Public evidence contains program results and logs, not private notebook code,
    # transformed input, whole fact dumps, credential files, or model request bodies.
    for p in (ROOT/'runs').rglob('*'):
        if not p.is_file() or any(x in p.parts for x in ('work','model-cache')):continue
        if p.parent.name == 'public-model-records' or p.parent.name == 'model-budget' or (p.suffix == '.json' and ('model' in p.parent.name or p.name == 'generation-manifest.json')):
            files.append(p)
        elif p.name in ('predictions.json','result.json','checks.json','manifest.json','stdout.log',
                       'PreProcessingLeak.csv','Telemetry_PreProcessingLeak.csv',
                       'Telemetry_FinalPreProcessingLeak.csv','EffectAtCall.facts','solver.log') or p.parent==ROOT/'runs/environment':
            files.append(p)
        elif p.name=='candidates.json' and not any('real' in x for x in p.relative_to(ROOT).parts):
            files.append(p)
    files=sorted(set(files))
    manifest={str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in files}
    output=ROOT.parent/'CS6215_review_artifact.zip'
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in files:z.write(p,'leakage-project/'+str(p.relative_to(ROOT)))
        z.writestr('leakage-project/ARTIFACT_MANIFEST.json',json.dumps({'status':'review artifact; student review and publication pending','sha256':manifest},indent=2)+'\n')
    print(output, len(files), 'files')

if __name__=='__main__':main()
