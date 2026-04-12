"""Main daily execution script - fetches data, runs AI analysis, sends email."""

import sys
import json
import os
from datetime import datetime

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from stock_data import get_all_watched_quotes, get_market_indices
from news_fetcher import get_daily_news_digest
from ai_analyzer import (
    summarize_news,
    analyze_sentiment,
    extract_keywords,
    generate_daily_briefing,
    _determine_mood,
)
from email_service import send_daily_briefing, preview_email


def run_daily_pipeline(send_email: bool = True, preview_only: bool = False):
    """Execute the full daily pipeline."""
    print("=" * 60)
    print(f"  ALPHA SIGNAL - Daily Pipeline")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Step 1: Fetch stock data
    print("\n[1/6] Fetching stock quotes...")
    stocks = get_all_watched_quotes()
    for name, data in stocks.items():
        if "error" not in data:
            arrow = "▲" if data["change_pct"] >= 0 else "▼"
            print(f"  {arrow} {name}: ${data['price']} ({data['change_pct']:+.2f}%)")
        else:
            print(f"  ✗ {name}: {data.get('error', 'Unknown error')}")

    # Step 2: Fetch market indices
    print("\n[2/6] Fetching market indices...")
    indices = get_market_indices()
    for name, data in indices.items():
        if "error" not in data:
            print(f"  {name}: {data['price']} ({data['change_pct']:+.2f}%)")

    # Step 3: Fetch and categorize news
    print("\n[3/6] Fetching news...")
    news_digest = get_daily_news_digest()
    categories = news_digest.get("categories", {})

    # Step 4: AI Sentiment Analysis
    print("\n[4/6] Running AI sentiment analysis...")
    sentiment = {}
    for topic in ["xiaomi", "qqq_intel", "macro"]:
        articles = categories.get(topic, [])
        if articles:
            print(f"  Analyzing {topic} sentiment ({len(articles)} articles)...")
            sentiment[topic] = analyze_sentiment(articles, topic)
            s = sentiment[topic]
            if isinstance(s, dict) and "overall_sentiment" in s:
                print(f"  → {topic}: {s['overall_sentiment']} (score: {s.get('sentiment_score', 'N/A')})")

    # Step 5: AI Keyword Extraction
    print("\n[5/6] Extracting keywords and themes...")
    all_articles = []
    for cat_articles in categories.values():
        all_articles.extend(cat_articles)
    keywords = extract_keywords(all_articles[:30]) if all_articles else {}

    # Step 6: Determine AI mood & generate briefing
    print("\n[6/7] Determining Alpha's mood...")
    mood = _determine_mood(stocks, indices)
    print(f"  Today's mood: {mood['mood']} {mood['emoji']}")
    print(f"  Vibe: {mood['vibe']}")

    print("\n[7/7] Generating AI morning briefing with personality...")
    briefing = generate_daily_briefing(stocks, indices, news_digest)

    # Send or preview
    print("\n" + "=" * 60)
    if preview_only:
        print("Generating email preview...")
        preview_email(stocks, indices, categories, sentiment, briefing, keywords, mood)
        print("✓ Preview saved to email_preview.html")
    elif send_email:
        print("Sending daily briefing email...")
        success = send_daily_briefing(
            stocks, indices, categories, sentiment, briefing, keywords, mood
        )
        if success:
            print("✓ Email sent successfully!")
        else:
            print("✗ Email sending failed. Check configuration in .env")
            print("  Generating preview as fallback...")
            preview_email(stocks, indices, categories, sentiment, briefing, keywords, mood)
    else:
        print("Pipeline complete (no email/preview requested)")

    # Save data for web dashboard
    output = {
        "timestamp": datetime.now().isoformat(),
        "stocks": stocks,
        "indices": indices,
        "news": {k: [{"title": a["title"], "source": a["source"],
                       "published": a["published"], "link": a["link"]}
                      for a in v[:10]]
                 for k, v in categories.items()},
        "sentiment": sentiment,
        "keywords": keywords,
        "briefing": briefing,
        "mood": mood,
    }
    with open("latest_data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)
    print("✓ Data saved to latest_data.json")

    print("\n" + "=" * 60)
    print("  Pipeline complete!")
    print("=" * 60)
    return output


if __name__ == "__main__":
    preview = "--preview" in sys.argv
    no_email = "--no-email" in sys.argv

    if preview:
        run_daily_pipeline(send_email=False, preview_only=True)
    elif no_email:
        run_daily_pipeline(send_email=False)
    else:
        run_daily_pipeline(send_email=True)
