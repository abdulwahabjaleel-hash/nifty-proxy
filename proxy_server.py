import time
import requests
from flask import Flask, jsonify

app = Flask(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://www.nseindia.com/option-chain',
    'X-Requested-With': 'XMLHttpRequest',
}

_cache = {'data': None, 'ts': 0}


def init_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    s.get('https://www.nseindia.com', timeout=12)
    time.sleep(1.5)
    s.get('https://www.nseindia.com/option-chain', timeout=12)
    time.sleep(1.0)
    return s


def get_expiry(session, symbol):
    url = f'https://www.nseindia.com/api/option-chain-contract-info?symbol={symbol}'
    r = session.get(url, timeout=12)
    if r.status_code == 200:
        data = r.json()
        expiries = data.get('expiryDatesByInstrumentType', {})
        for key in expiries:
            if expiries[key]:
                return expiries[key][0]
    return None


def get_data(symbol):
    if _cache['data'] and time.time() - _cache['ts'] < 55:
        return _cache['data']

    s = init_session()

    # Try NEW endpoint (option-chain-v3) first
    try:
        expiry = get_expiry(s, symbol)
        if expiry:
            url = f'https://www.nseindia.com/api/option-chain-v3?type=Indices&symbol={symbol}&expiry={expiry}'
            r = s.get(url, timeout=15)
            if r.status_code == 200:
                _cache['data'] = r.json()
                _cache['ts'] = time.time()
                return _cache['data']
    except Exception as e:
        print(f'v3 attempt failed: {e}')

    # Fallback: Try OLD endpoint
    try:
        url = f'https://www.nseindia.com/api/option-chain-indices?symbol={symbol}'
        r = s.get(url, timeout=15)
        if r.status_code == 200:
            _cache['data'] = r.json()
            _cache['ts'] = time.time()
            return _cache['data']
    except Exception as e:
        print(f'old endpoint failed: {e}')

    raise Exception('Both NSE endpoints failed')


@app.route('/')
def home():
    return 'NSE Proxy Running OK'


@app.route('/nifty-oc')
def nifty():
    try:
        return jsonify(get_data('NIFTY'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/banknifty-oc')
def banknifty():
    try:
        return jsonify(get_data('BANKNIFTY'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
