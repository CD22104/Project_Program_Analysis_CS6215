import argparse
import json
from leakage.model import config, request, DEFAULT_CONFIG, APIError
from leakage.common import ROOT, write_json

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--config', default=str(DEFAULT_CONFIG))
    args = p.parse_args()
    cfg = config(args.config)
    try:
        response = request(cfg, 'GET', 'models', timeout=20)
        data = {'connected': True, 'models': [r['id'] for r in response.get('data', [])],
                'model_configured': cfg['SOCLAAS_MODEL']}
    except (APIError, OSError, ValueError) as e:
        data = {'connected': False, 'error_type': type(e).__name__,
                'error': str(e) if isinstance(e, APIError) else 'Connection/DNS/TLS failure; check NUS network or VPN'}
    write_json(ROOT / 'runs/environment/model-connectivity.json', data)
    print(json.dumps(data))
    raise SystemExit(0 if data['connected'] else 1)

if __name__ == '__main__':
    main()
