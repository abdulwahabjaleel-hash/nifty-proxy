import time
import requests
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # This allows GitHub Pages to call Railway

S = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
    'Referer': 'https://www.nseindia.com/option-chain',
    'X-Requested-With': 'XMLHttpRequest',
}

cache = {'d': None, 't': 0}


def make_session():
    s = requests.Session()
    s.headers.update(S)
    s.get('https://www.nseindia.com', timeout=15)
    time.sleep(2)
    s.get('https://www.nseindia.com/option-chain', timeout=15)
    time.sleep(1.5)
    s.get('https://www.nseindia.com/api/allIndices', timeout=10)
    time.sleep(1)
    return s


def get_nearest_expiry(s, symbol):
    url = f'https://www.nseindia.com/api/option-chain-contract-info?symbol={symbol}'
    r = s.get(url, timeout=12)
    r.raise_for_status()
    data = r.json()
    expiry_map = data.get('expiryDatesByInstrumentType', {})
    for key in expiry_map:
        if expiry_map[key]:
            return expiry_map[key][0]
    dates = data.get('expiryDates', [])
    if dates:
        return dates[0]
    records = data.get('records', {})
    dates2 = records.get('expiryDates', [])
    if dates2:
        return dates2[0]
    raise Exception(f'No expiry found. Keys: {list(data.keys())}')


def fetch(symbol):
    if cache['d'] and time.time() - cache['t'] < 55:
        return cache['d']
    s = make_session()
    expiry = get_nearest_expiry(s, symbol)
    url = f'https://www.nseindia.com/api/option-chain-v3?type=Indices&symbol={symbol}&expiry={expiry}'
    r = s.get(url, timeout=15)
    r.raise_for_status()
    cache['d'] = r.json()
    cache['t'] = time.time()
    return cache['d']


@app.route('/')
def home():
    return 'NSE Proxy Running OK'


@app.route('/nifty-oc')
def nifty():
    try:
        return jsonify(fetch('NIFTY'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/banknifty-oc')
def banknifty():
    try:
        return jsonify(fetch('BANKNIFTY'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/debug')
def debug():
    try:
        s = make_session()
        expiry = get_nearest_expiry(s, 'NIFTY')
        url = f'https://www.nseindia.com/api/option-chain-v3?type=Indices&symbol=NIFTY&expiry={expiry}'
        r = s.get(url, timeout=15)
        return jsonify({
            'expiry_found': expiry,
            'v3_status': r.status_code,
            'strikes_count': len(r.json().get('records', {}).get('data', [])) if r.status_code == 200 else 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
