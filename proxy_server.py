import time
import requests
from flask import Flask, jsonify

app = Flask(__name__)

S = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
    'Referer': 'https://www.nseindia.com/option-chain',
    'X-Requested-With': 'XMLHttpRequest',
}

cache = {'d': None, 't': 0}


def session():
    s = requests.Session()
    s.headers.update(S)
    s.get('https://www.nseindia.com', timeout=15)
    time.sleep(2)
    s.get('https://www.nseindia.com/option-chain', timeout=15)
    time.sleep(1.5)
    s.get('https://www.nseindia.com/api/allIndices', timeout=10)
    time.sleep(1)
    return s


def fetch(symbol):
    if cache['d'] and time.time() - cache['t'] < 55:
        return cache['d']
    s = session()
    errors = []

    # Try v3 endpoint
    try:
        cr = s.get(f'https://www.nseindia.com/api/option-chain-contract-info?symbol={symbol}', timeout=12)
        if cr.status_code == 200:
            expiry = None
            for k, v in cr.json().get('expiryDatesByInstrumentType', {}).items():
                if v:
                    expiry = v[0]
                    break
            if expiry:
                r = s.get(f'https://www.nseindia.com/api/option-chain-v3?type=Indices&symbol={symbol}&expiry={expiry}', timeout=15)
                if r.status_code == 200:
                    cache['d'] = r.json()
                    cache['t'] = time.time()
                    return cache['d']
                errors.append(f'v3={r.status_code}')
        else:
            errors.append(f'contract={cr.status_code}')
    except Exception as e:
        errors.append(f'v3_err={e}')

    # Try old endpoint
    try:
        r = s.get(f'https://www.nseindia.com/api/option-chain-indices?symbol={symbol}', timeout=15)
        if r.status_code == 200:
            cache['d'] = r.json()
            cache['t'] = time.time()
            return cache['d']
        errors.append(f'old={r.status_code}')
    except Exception as e:
        errors.append(f'old_err={e}')

    raise Exception(' | '.join(errors))


@app.route('/')
def home():
    return 'OK'


@app.route('/nifty-oc')
def nifty():
    try:
        return jsonify(fetch('NIFTY'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/debug')
def debug():
    s = session()
    out = {}
    for label, url in [
        ('homepage', 'https://www.nseindia.com'),
        ('allIndices', 'https://www.nseindia.com/api/allIndices'),
        ('contract_info', 'https://www.nseindia.com/api/option-chain-contract-info?symbol=NIFTY'),
        ('old_endpoint', 'https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY'),
    ]:
        try:
            r = s.get(url, timeout=10)
            out[label] = r.status_code
        except Exception as e:
            out[label] = str(e)
    return jsonify(out)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
