import time
import requests
from flask import Flask, jsonify

app = Flask(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': '*/*',
    'Referer': 'https://www.nseindia.com/'
}

_cache = {'data': None, 'ts': 0}


def get_data(symbol):
    if _cache['data'] and time.time() - _cache['ts'] < 55:
        return _cache['data']
    s = requests.Session()
    s.headers.update(HEADERS)
    s.get('https://www.nseindia.com', timeout=10)
    time.sleep(1)
    s.get('https://www.nseindia.com/option-chain', timeout=10)
    time.sleep(0.5)
    r = s.get(
        f'https://www.nseindia.com/api/option-chain-indices?symbol={symbol}',
        timeout=15
    )
    r.raise_for_status()
    _cache['data'] = r.json()
    _cache['ts'] = time.time()
    return _cache['data']


@app.route('/')
def home():
    return 'NSE Proxy Running OK'


@app.route('/nifty-oc')
def nifty():
    try:
        return jsonify(get_data('NIFTY'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
