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
from gemini_analyzer import _determine_sigma_mood, generate_gemini_briefing


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
    print("\n[6/8] Determining Alpha's mood (DeepSeek)...")
    mood_alpha = _determine_mood(stocks, indices)
    print(f"  Alpha's mood: {mood_alpha['mood']} {mood_alpha['emoji']}")

    print("\n[7/8] Generating Alpha's morning briefing...")
    briefing_alpha = generate_daily_briefing(stocks, indices, news_digest)

    print("\n[8/8] Determining Sigma's mood & generating briefing (Gemini)...")
    mood_sigma = _determine_sigma_mood(stocks, indices)
    print(f"  Sigma's mood: {mood_sigma['mood']} {mood_sigma['emoji']}")
    briefing_sigma = generate_gemini_briefing(stocks, indices, news_digest)

    # Send or preview
    print("\n" + "=" * 60)
    if preview_only:
        print("Generating email previews...")
        preview_email(stocks, indices, categories, sentiment, briefing_alpha, keywords, mood_alpha, "Alpha")
        preview_email(stocks, indices, categories, sentiment, briefing_sigma, keywords, mood_sigma, "Sigma")
        print("✓ Previews saved to email_preview_alpha.html and email_preview_sigma.html")
    elif send_email:
        print("Sending Alpha's daily briefing email...")
        success_alpha = send_daily_briefing(
            stocks, indices, categories, sentiment, briefing_alpha, keywords, mood_alpha, "Alpha"
        )
        print("Sending Sigma's daily briefing email...")
        success_sigma = send_daily_briefing(
            stocks, indices, categories, sentiment, briefing_sigma, keywords, mood_sigma, "Sigma"
        )
        if success_alpha and success_sigma:
            print("✓ Both emails sent successfully!")
        else:
            print("✗ Some emails failed to send. Check configuration in .env")
            print("  Generating previews as fallback...")
            preview_email(stocks, indices, categories, sentiment, briefing_alpha, keywords, mood_alpha, "Alpha")
            preview_email(stocks, indices, categories, sentiment, briefing_sigma, keywords, mood_sigma, "Sigma")
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
        "briefing": briefing_alpha,
        "mood": mood_alpha,
        "briefing_sigma": briefing_sigma,
        "mood_sigma": mood_sigma,
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
