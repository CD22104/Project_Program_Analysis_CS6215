import json
from leakage.common import ROOT,digest,write_json
from leakage.variants import rename,wrap,comments

def main():
    base=json.loads((ROOT/'data/manifests/controlled.json').read_text())
    labels=json.loads((ROOT/'data/annotations/controlled.json').read_text())
    lookup={r['sample_id']:r for r in labels}
    manifest=[];derived_labels=[]
    transforms={'rename':rename,'wrap1':lambda s:wrap(s,1),'wrap2':lambda s:wrap(s,2),'comments':comments}
    for row in base:
        if row['partition']=='dev':continue
        source=(ROOT/row['source_path']).read_text()
        for kind,transform in transforms.items():
            variant=transform(source)
            sid=row['sample_id']+'_'+kind
            path=ROOT/'data/clean/variants'/(sid+'.py');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(variant)
            manifest.append({**row,'sample_id':sid,'base_sample_id':row['sample_id'],'variant':kind,
                             'source_path':str(path.relative_to(ROOT)),'source_sha256':digest(variant)})
            derived_labels.append({**lookup[row['sample_id']],'sample_id':sid,'base_sample_id':row['sample_id']})
    write_json(ROOT/'data/manifests/variants.json',manifest)
    write_json(ROOT/'data/annotations/variants.json',derived_labels)
    print(len(manifest),'paired variants prepared; no analysis performed')

if __name__=='__main__':main()
