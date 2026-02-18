#!/usr/bin/env python3
"""
Daily data updater for Unreal Engine Hub
- Fetches stock prices from Yahoo Finance
- Fetches news + images from NewsAPI.org
- Translates summaries to Korean via unofficial Google Translate
"""
import json, urllib.request, urllib.parse
import datetime, time, os

# ── API Key (GitHub Secret > fallback) ────────────────────────────────────────
NEWS_API_KEY = os.environ.get('NEWS_API_KEY', 'de6682f46f90485d99bd48c42e7feaba')

# ── Stock tickers ─────────────────────────────────────────────────────────────
TICKERS = [
    ('TSLA',   'Tesla',       '🇺🇸'),
    ('NVDA',   'NVIDIA',      '🇺🇸'),
    ('TM',     'Toyota',      '🇯🇵'),
    ('HYMTF',  'Hyundai',     '🇰🇷'),
    ('BYDDF',  'BYD',         '🇨🇳'),
    ('MBG.DE', 'Mercedes',    '🇩🇪'),
    ('BMW.DE', 'BMW',         '🇩🇪'),
    ('GM',     'GM',          '🇺🇸'),
    ('F',      'Ford',        '🇺🇸'),
    ('MBLY',   'Mobileye',    '🇺🇸'),
    ('BIDU',   'Baidu',       '🇨🇳'),
    ('VWAGY',  'Volkswagen',  '🇩🇪'),
    ('HMC',    'Honda',       '🇯🇵'),
]

# ── NewsAPI queries ────────────────────────────────────────────────────────────
NEWS_QUERIES = {
    'unreal':     '"Unreal Engine" OR "Epic Games"',
    'gis':        '"Unreal Engine" GIS OR "digital twin" OR Cesium OR ArcGIS',
    'us_av':      'autonomous driving Waymo OR Tesla OR NVIDIA OR "self-driving"',
    'china_av':   'China "autonomous vehicle" OR "self-driving" BYD OR Baidu OR DeepSeek',
    'europe_av':  'Europe "autonomous vehicle" OR "self-driving" Mercedes OR BMW OR Volkswagen OR Wayve',
    'linkedin_av': '"AV simulation" OR "autonomous driving simulation" OR "CARLA simulator" OR "driving simulator"',
}


def fetch_stock(ticker):
    url = (f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}'
           f'?interval=1d&range=2d')
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        d = json.loads(r.read())
    meta  = d['chart']['result'][0]['meta']
    price = meta['regularMarketPrice']
    prev  = meta.get('chartPreviousClose', price)
    chg   = round((price - prev) / prev * 100, 2) if prev else 0.0
    return {
        'price':      round(price, 2),
        'change_pct': chg,
        'currency':   meta.get('currency', 'USD'),
    }


def translate_ko(text):
    """Unofficial Google Translate endpoint — no API key required."""
    if not text:
        return text
    try:
        q = urllib.parse.quote(text[:500])
        url = (f'https://translate.googleapis.com/translate_a/single'
               f'?client=gtx&sl=en&tl=ko&dt=t&q={q}')
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read())
        return ''.join(seg[0] for seg in result[0] if seg[0])
    except Exception as e:
        print(f'    translate error: {e}')
        return text


def fetch_news(query, limit=5):
    try:
        q = urllib.parse.quote(query)
        url = (f'https://newsapi.org/v2/everything'
               f'?q={q}&language=en&sortBy=publishedAt&pageSize={limit}'
               f'&apiKey={NEWS_API_KEY}')
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())

        results = []
        for art in data.get('articles', []):
            title = (art.get('title') or '').strip()
            if not title or title == '[Removed]':
                continue

            desc   = (art.get('description') or '').strip()[:300]
            link   = art.get('url', '')
            image  = art.get('urlToImage') or ''
            pub    = art.get('publishedAt', '')
            source = art.get('source', {}).get('name', '')

            title_ko = translate_ko(title)
            desc_ko  = translate_ko(desc) if desc else ''
            time.sleep(0.3)

            results.append({
                'title':      title,
                'title_ko':   title_ko,
                'link':       link,
                'summary':    desc,
                'summary_ko': desc_ko,
                'date':       pub,
                'source':     source,
                'image':      image,
            })
            if len(results) >= limit:
                break

        return results

    except Exception as e:
        print(f'    news fetch error: {e}')
        return []


# ── Main ──────────────────────────────────────────────────────────────────────
now = datetime.datetime.utcnow()
output = {
    'updated':     now.strftime('%Y-%m-%d %H:%M UTC'),
    'updated_kst': (now + datetime.timedelta(hours=9)).strftime('%Y-%m-%d %H:%M KST'),
    'stocks': {},
    'news':   {},
}

print('── Stocks ──')
for ticker, name, flag in TICKERS:
    try:
        s = fetch_stock(ticker)
        output['stocks'][ticker] = {**s, 'name': name, 'flag': flag}
        print(f'  {ticker}: {s["currency"]} {s["price"]:,.2f}  ({s["change_pct"]:+.2f}%)')
    except Exception as e:
        print(f'  {ticker} ERROR: {e}')
    time.sleep(0.4)

print('── News ──')
for section, query in NEWS_QUERIES.items():
    print(f'  {section} ...')
    articles = fetch_news(query, limit=5)
    output['news'][section] = articles
    print(f'    → {len(articles)} articles')
    time.sleep(1)

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f'\nOK  data.json saved  [{output["updated_kst"]}]')
