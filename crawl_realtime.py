"""Real-time financial data crawler.

Scrapes live data from Chinese financial sources:
- Sina Finance (新浪财经)
- East Money (东方财富)
- Tencent Finance (腾讯财经)
- Snowball (雪球)
- HK Exchange news
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def crawl_sina_stock_news(stock_code: str = "1810", market: str = "hk") -> list:
    """Crawl latest news from Sina Finance for a stock."""
    articles = []
    try:
        url = f"https://search.sina.com.cn/news?q={stock_code}+%E5%B0%8F%E7%B1%B3&range=all&c=news&sort=time"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        for item in soup.select(".result .box-result")[:10]:
            title_el = item.select_one("h2 a")
            if title_el:
                articles.append({
                    "title": title_el.get_text(strip=True),
                    "link": title_el.get("href", ""),
                    "source": "Sina Finance",
                    "published": datetime.now().strftime("%Y-%m-%d"),
                    "summary": item.select_one(".content")
                              .get_text(strip=True)[:200] if item.select_one(".content") else "",
                })
    except Exception as e:
        print(f"[Crawl] Sina error: {e}")
    return articles


def crawl_eastmoney_news(stock_code: str = "01810", market: str = "116") -> list:
    """Crawl East Money (东方财富) stock news."""
    articles = []
    try:
        url = f"https://search.eastmoney.com/web/web?keyword={stock_code}&type=0"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        for item in data.get("result", {}).get("article", {}).get("list", [])[:10]:
            articles.append({
                "title": re.sub(r"<.*?>", "", item.get("title", "")),
                "link": item.get("url", ""),
                "source": "East Money",
                "published": item.get("date", datetime.now().strftime("%Y-%m-%d")),
                "summary": re.sub(r"<.*?>", "", item.get("content", ""))[:200],
            })
    except Exception as e:
        print(f"[Crawl] EastMoney error: {e}")
    return articles


def crawl_snowball_discussion(stock_symbol: str = "01810") -> list:
    """Crawl Snowball (雪球) discussions about a stock."""
    articles = []
    try:
        url = f"https://xueqiu.com/query/v1/search/status.json?q={stock_symbol}&count=10&sort=time"
        resp = requests.get(url, headers={**HEADERS, "Cookie": "xq_a_token=test"}, timeout=10)
        data = resp.json() if resp.ok else {}
        for item in data.get("list", [])[:10]:
            articles.append({
                "title": re.sub(r"<.*?>", "", item.get("title", item.get("text", "")[:80])),
                "link": f"https://xueqiu.com{item.get('target', '')}",
                "source": "Snowball/雪球",
                "published": datetime.now().strftime("%Y-%m-%d"),
                "summary": re.sub(r"<.*?>", "", item.get("text", ""))[:200],
            })
    except Exception as e:
        print(f"[Crawl] Snowball error: {e}")
    return articles


def crawl_google_finance_news(ticker: str = "HKG:1810") -> list:
    """Crawl Google Finance news for a ticker."""
    articles = []
    try:
        url = f"https://www.google.com/finance/quote/{ticker}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        for item in soup.select("[data-article-url]")[:10]:
            title_el = item.select_one("[data-article-url] div")
            if title_el:
                articles.append({
                    "title": title_el.get_text(strip=True),
                    "link": item.get("data-article-url", ""),
                    "source": "Google Finance",
                    "published": datetime.now().strftime("%Y-%m-%d"),
                    "summary": "",
                })
    except Exception as e:
        print(f"[Crawl] Google Finance error: {e}")
    return articles


def crawl_xiaomi_news_all() -> list:
    """Crawl Xiaomi news from all Chinese + English sources."""
    all_news = []
    print("[Crawl] Fetching Sina Finance...")
    all_news.extend(crawl_sina_stock_news("小米"))
    print(f"  Got {len(all_news)} articles")

    print("[Crawl] Fetching East Money...")
    em = crawl_eastmoney_news("01810")
    all_news.extend(em)
    print(f"  Got {len(em)} articles")

    print("[Crawl] Fetching Snowball...")
    xq = crawl_snowball_discussion("01810")
    all_news.extend(xq)
    print(f"  Got {len(xq)} articles")

    print("[Crawl] Fetching DuckDuckGo Xiaomi news...")
    from news_fetcher import search_web_news
    ddg = search_web_news("Xiaomi 1810.HK stock news latest 2026", 10)
    all_news.extend(ddg)
    print(f"  Got {len(ddg)} articles")

    ddg_cn = search_web_news("小米集团 1810.HK 股价 最新消息 2026", 10)
    all_news.extend(ddg_cn)
    print(f"  Got {len(ddg_cn)} CN articles")

    print(f"[Crawl] Total: {len(all_news)} articles")
    return all_news


def crawl_sector_news(keywords: list) -> list:
    """Crawl news about a sector/theme."""
    all_news = []
    from news_fetcher import search_web_news
    for kw in keywords[:3]:
        results = search_web_news(f"{kw} stock news 2026", 8)
        all_news.extend(results)
    return all_news


def get_realtime_hk_price(code: str = "01810") -> dict:
    """Get real-time HK stock price from Tencent Finance API."""
    try:
        url = f"https://qt.gtimg.cn/q=r_hk{code}"
        resp = requests.get(url, headers=HEADERS, timeout=5)
        resp.encoding = "gbk"
        text = resp.text
        parts = text.split("~")
        if len(parts) > 40:
            return {
                "name": parts[1],
                "price": float(parts[3]),
                "change": float(parts[6]),
                "change_pct": float(parts[7]),
                "high": float(parts[33]),
                "low": float(parts[34]),
                "volume": int(float(parts[36])),
                "turnover": parts[37],
                "pe": float(parts[39]) if parts[39] else None,
                "pb": float(parts[40]) if parts[40] else None,
                "time": parts[30],
            }
    except Exception as e:
        print(f"[Crawl] Tencent price error: {e}")
    return {}


def get_realtime_a_price(code: str = "sz002475") -> dict:
    """Get real-time A-share stock price from Tencent Finance API."""
    try:
        url = f"https://qt.gtimg.cn/q={code}"
        resp = requests.get(url, headers=HEADERS, timeout=5)
        resp.encoding = "gbk"
        text = resp.text
        parts = text.split("~")
        if len(parts) > 40:
            return {
                "name": parts[1],
                "price": float(parts[3]),
                "change": float(parts[31]),
                "change_pct": float(parts[32]),
                "high": float(parts[33]),
                "low": float(parts[34]),
                "volume": int(float(parts[36])),
                "pe": float(parts[39]) if parts[39] != "" else None,
                "time": parts[30],
            }
    except Exception as e:
        print(f"[Crawl] Tencent A-share price error: {e}")
    return {}


if __name__ == "__main__":
    print("=== Real-time HK Price ===")
    price = get_realtime_hk_price("01810")
    print(json.dumps(price, ensure_ascii=False, indent=2))

    print("\n=== Xiaomi News Crawl ===")
    news = crawl_xiaomi_news_all()
    for n in news[:5]:
        print(f"  [{n['source']}] {n['title']}")
