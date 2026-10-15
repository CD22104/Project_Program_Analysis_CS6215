"""Package only tracked files from the anonymized public checkout."""
import hashlib,json,subprocess,zipfile
from pathlib import Path
from leakage.common import ROOT

def main():
    names=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    files={n:(ROOT/n).read_bytes() for n in names if n and not n.startswith('report/')}
    assert not any(n.startswith(('runs/model-cache/','data/clean/real/')) for n in files)
    manifest={'status':'Anonymized code and evidence; signed report excluded',
              'sha256':{n:hashlib.sha256(b).hexdigest() for n,b in sorted(files.items())}}
    target=ROOT.parent/'CS6215_public_code_artifact.zip'
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for n,b in sorted(files.items()):archive.writestr('leakage-project/'+n,b)
        archive.writestr('leakage-project/ARTIFACT_MANIFEST.json',json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(target,len(files),'public files')

if __name__=='__main__':main()
