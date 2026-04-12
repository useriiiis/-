"""News fetching and aggregation module."""

import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from config import NEWS_RSS_FEEDS, XIAOMI_KEYWORDS, MACRO_KEYWORDS
import re
import time


def fetch_rss_news(max_per_feed: int = 15) -> list:
    """Fetch news from all configured RSS feeds."""
    all_articles = []

    for source, url in NEWS_RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_per_feed]:
                published = ""
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d %H:%M")
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    published = datetime(*entry.updated_parsed[:6]).strftime("%Y-%m-%d %H:%M")

                article = {
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "summary": _clean_html(entry.get("summary", "")),
                    "source": source,
                    "published": published,
                }
                all_articles.append(article)
        except Exception as e:
            print(f"Error fetching {source}: {e}")
            continue

    return all_articles


def _clean_html(text: str) -> str:
    """Remove HTML tags from text."""
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    clean = soup.get_text(separator=" ", strip=True)
    clean = re.sub(r"\s+", " ", clean)
    return clean[:500]


def filter_by_keywords(articles: list, keywords: list) -> list:
    """Filter articles that match any of the given keywords."""
    filtered = []
    for article in articles:
        text = f"{article['title']} {article['summary']}".lower()
        matched_keywords = []
        for kw in keywords:
            if kw.lower() in text:
                matched_keywords.append(kw)
        if matched_keywords:
            article["matched_keywords"] = matched_keywords
            filtered.append(article)
    return filtered


def get_xiaomi_news(articles: list = None) -> list:
    """Get Xiaomi-related news."""
    if articles is None:
        articles = fetch_rss_news()
    return filter_by_keywords(articles, XIAOMI_KEYWORDS)


def get_macro_news(articles: list = None) -> list:
    """Get macro/geopolitical news."""
    if articles is None:
        articles = fetch_rss_news()
    return filter_by_keywords(articles, MACRO_KEYWORDS)


def get_stock_specific_news(articles: list, keywords: list) -> list:
    """Get news related to specific stock keywords."""
    return filter_by_keywords(articles, keywords)


def categorize_news(articles: list) -> dict:
    """Categorize all news into groups."""
    all_articles = articles if articles else fetch_rss_news()

    categories = {
        "xiaomi": filter_by_keywords(all_articles, XIAOMI_KEYWORDS),
        "macro": filter_by_keywords(all_articles, MACRO_KEYWORDS),
        "qqq_intel": filter_by_keywords(all_articles, [
            "QQQ", "Invesco", "Intel", "INTC", "Pat Gelsinger",
            "semiconductor", "chip", "foundry", "NASDAQ",
        ]),
        "tech": filter_by_keywords(all_articles, [
            "tech", "technology", "AI", "artificial intelligence",
            "cloud", "SaaS", "software", "hardware",
        ]),
        "market": filter_by_keywords(all_articles, [
            "S&P 500", "Dow Jones", "NASDAQ", "market", "stocks",
            "bull", "bear", "rally", "crash", "correction",
            "Wall Street", "Hong Kong", "Hang Seng",
        ]),
    }

    seen_links = set()
    for cat in categories:
        unique = []
        for a in categories[cat]:
            if a["link"] not in seen_links:
                seen_links.add(a["link"])
                unique.append(a)
        categories[cat] = unique

    return categories


def search_web_news(query: str, num_results: int = 10) -> list:
    """Search for news using DuckDuckGo (no API key needed)."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        url = f"https://html.duckduckgo.com/html/?q={query}+news"
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        results = []
        for item in soup.select(".result")[:num_results]:
            title_elem = item.select_one(".result__title a")
            snippet_elem = item.select_one(".result__snippet")
            if title_elem:
                results.append({
                    "title": title_elem.get_text(strip=True),
                    "link": title_elem.get("href", ""),
                    "summary": snippet_elem.get_text(strip=True) if snippet_elem else "",
                    "source": "DuckDuckGo Search",
                    "published": datetime.now().strftime("%Y-%m-%d"),
                })
        return results
    except Exception as e:
        print(f"Web search error: {e}")
        return []


def get_daily_news_digest() -> dict:
    """Get complete daily news digest for all categories."""
    print("[News] Fetching RSS feeds...")
    all_articles = fetch_rss_news()
    print(f"[News] Fetched {len(all_articles)} articles from RSS feeds")

    print("[News] Searching for Xiaomi news...")
    xiaomi_web = search_web_news("Xiaomi stock 1810.HK latest news 2026")
    all_articles.extend(xiaomi_web)

    print("[News] Searching for Intel news...")
    intel_web = search_web_news("Intel INTC stock news 2026")
    all_articles.extend(intel_web)

    print("[News] Categorizing articles...")
    categories = categorize_news(all_articles)

    print(f"[News] Categories: " + ", ".join(
        f"{k}({len(v)})" for k, v in categories.items()
    ))

    return {
        "categories": categories,
        "total_articles": len(all_articles),
        "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


if __name__ == "__main__":
    digest = get_daily_news_digest()
    for cat, articles in digest["categories"].items():
        print(f"\n=== {cat.upper()} ({len(articles)} articles) ===")
        for a in articles[:3]:
            print(f"  - {a['title']}")
            print(f"    Source: {a['source']} | {a['published']}")
