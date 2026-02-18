#!/usr/bin/env python3
"""
Daily data updater for Unreal Engine Hub
- Fetches stock prices from Yahoo Finance
- Fetches news from Google News RSS
- Translates summaries to Korean via unofficial Google Translate
"""
import json, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
import datetime, re, time

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

# ── Google News RSS queries ────────────────────────────────────────────────────
NEWS_FEEDS = {
    'unreal':   'https://news.google.com/rss/search?q=%22Unreal+Engine%22+OR+%22Epic+Games%22&hl=en-US&gl=US&ceid=US:en',
    'gis':      'https://news.google.com/rss/search?q=%22Unreal+Engine%22+GIS+OR+%22digital+twin%22+OR+Cesium+OR+ArcGIS&hl=en-US&gl=US&ceid=US:en',
    'us_av':    'https://news.google.com/rss/search?q=autonomous+driving+simulation+Waymo+OR+Tesla+OR+NVIDIA+OR+%22self-driving%22&hl=en-US&gl=US&ceid=US:en',
    'china_av':  'https://news.google.com/rss/search?q=China+%22autonomous+vehicle%22+OR+%22self-driving%22+BYD+OR+Baidu+OR+DeepSeek&hl=en-US&gl=US&ceid=US:en',
    'europe_av': 'https://news.google.com/rss/search?q=Europe+%22autonomous+vehicle%22+OR+%22self-driving%22+Mercedes+OR+BMW+OR+Volkswagen+OR+Wayve+OR+Mobileye&hl=en-US&gl=US&ceid=US:en',
    'linkedin_av': 'https://news.google.com/rss/search?q=%22AV+simulation%22+OR+%22autonomous+driving+simulation%22+OR+%22CARLA+simulator%22+OR+%22driving+simulator%22+OR+%22synthetic+data+autonomous%22&hl=en-US&gl=US&ceid=US:en',
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


def fetch_news(url, limit=5):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            root = ET.fromstring(r.read())

        items   = root.findall('.//item')
        results = []

        for item in items:
            title    = (item.findtext('title')       or '').strip()
            link     = (item.findtext('link')        or '').strip()
            raw_desc = item.findtext('description')  or ''
            desc     = re.sub(r'<[^>]+>', '', raw_desc).strip()[:300]
            pub      = (item.findtext('pubDate')     or '').strip()
            src_el   = item.find('{https://news.google.com/rss}source')
            source   = src_el.text if src_el is not None else ''

            if not title:
                continue

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
for section, feed_url in NEWS_FEEDS.items():
    print(f'  {section} ...')
    articles = fetch_news(feed_url, limit=5)
    output['news'][section] = articles
    print(f'    → {len(articles)} articles')
    time.sleep(1)

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f'\n✅  data.json saved  [{output["updated_kst"]}]')
