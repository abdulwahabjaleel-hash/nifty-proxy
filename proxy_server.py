import time
import requests
from flask import Flask, jsonify

app = Flask(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://www.nseindia.com/option-chain',
    'X-Requested-With': 'XMLHttpRequest',
    'sec-ch-ua': '"Chromium";v="124"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
}

_cache = {'data': None, 'ts': 0}


def init_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    try:
        s.get('https://www.nseindia.com', timeout=15)
        time.sleep(2)
        s.get('https://www.nseindia.com/option-chain', timeout=15)
        time.sleep(1.5)
        s.get('https://www.nseindia.com/api/allIndices', timeout=10)
        time.sleep(1)
    except Exception as e:
        print(f'Session init error: {e}')
    return s


def get_data(symbol):
    if _cache['data'] and time.time() - _cache['ts'] < 55:
        return _cache['data']

    s = init_session()

    # Try v3 endpoint (new NSE API)
    try:
        cr = s.get(
            f'https://www.nseindia.com/api/option-chain-contract-info?symbol={symbol}',
            timeout=12
        )
        if cr.status_code == 200:
            expiry_map = cr.json().get('expiryDatesByInstrumentType', {})
            expiry = None
            for key, dates in expiry_map.items():
                if dates:
                    expiry = dates[0]
                    break
            if expiry:
                r = s.get(
                    f'https://www.nseindia.com/api/option-chain-v3?type=Indices&symbol={symbol}&expiry={expiry}',
                    timeout=15
                )
                if r.status_code == 200:
                    _cache['data'] = r.json()
                    _cache['ts'] = time.time()
                    return _cache['data']
    except Exception as e:
        print(f'v3 error: {e}')

    # Fallback old endpoint
    try:
        r = s.get(
            f'https://www.nseindia.com/api/option-chain-indices?symbol={symbol}',
            timeout=15
        )
        if r.status_code == 200:
            _cache['data'] = r.json()
            _cache['ts'] = time.time()
            return _cache['data']
    except Exception as e:
        print(f'Old endpoint error: {e}')

    raise Exception('NSE blocked this server IP. Move to PythonAnywhere.')


@app.route('/')
def home():
    return 'NSE Proxy Running OK'


@app.route('/nifty-oc')
def nifty():
    try:
        return jsonify(get_data('NIFTY'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/debug')
def debug():
    s = init_session()
    out = {}
    for url in [
        'https://www.nseindia.com/api/allIndices',
        'https://www.nseindia.com/api/option-chain-contract-info?symbol=NIFTY',
        'https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY',
    ]:
        try:
            r = s.get(url, timeout=10)
            out[url.split('/')[-1]] = r.status_code
        except Exception as e:
            out[url.split('/')[-1]] = str(e)
    return jsonify(out)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
