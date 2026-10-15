"""Export response-only evidence; exact request bodies stay private locally."""
import json
from leakage.common import ROOT,digest,write_json

def main():
    n=0
    for path in sorted((ROOT/'runs/model-cache').glob('*.json')):
        record=json.loads(path.read_text())
        record['messages_sha256']=digest(record.pop('messages'))
        record['request_body_policy']='Private original retained; reconstruct from source/frontend and versioned prompt. No request code redistributed.'
        write_json(ROOT/'runs/public-model-records'/path.name,record);n+=1
    print('Exported',n,'response-only records.')

if __name__=='__main__':main()
