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
    'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124"',
    'sec-ch-ua-mobile': '?0',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
}

_cache = {'data': None, 'ts': 0}


def init_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    # Step 1: Hit homepage to get initial cookies
    s.get('https://www.nseindia.com', timeout=12)
    time.sleep(1.5)
    # Step 2: Hit option chain page to get session cookies
    s.get('https://www.nseindia.com/option-chain', timeout=12)
    time.sleep(1.0)
    # Step 3: Hit market data page (extra cookie layer NSE needs)
    s.get('https://www.nseindia.com/market-data/live-equity-market', timeout=10)
    time.sleep(0.5)
    return s


def get_data(symbol):
    if _cache['data'] and time.time() - _cache['ts'] < 55:
        return _cache['data']

    s = init_session()
    url = f'https://www.nseindia.com/api/option-chain-indices?symbol={symbol}'
    r = s.get(url, timeout=15)
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


@app.route('/banknifty-oc')
def banknifty():
    try:
        return jsonify(get_data('BANKNIFTY'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
