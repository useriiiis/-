"""Complete 5-Dimension Stock Analysis for Competition.

Analyzes Xiaomi across 5 pillars:
1. Fundamental Analysis (valuation, growth, margins, balance sheet)
2. Technical Analysis (trend, momentum, RSI, MACD, support/resistance)
3. News & Sentiment (multi-source crawling + AI sentiment)
4. Industry & Competitive Position (peers, market share, moats)
5. Macro & Geopolitical Factors (trade war, policy, FX, rates)

Then: decides LONG or SHORT Xiaomi, and picks the best pair.
"""

import os
import sys
import json
from datetime import datetime

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import yfinance as yf
import pandas as pd
from stock_data import get_stock_fundamentals, get_stock_history, format_number
from crawl_realtime import crawl_xiaomi_news_all, get_realtime_hk_price
from news_fetcher import fetch_rss_news, filter_by_keywords
from ai_analyzer import _call_deepseek, analyze_sentiment, extract_keywords
from stock_screener import screen_all_candidates, rank_candidates, ai_pair_recommendation, TECH_UNIVERSE
from config import XIAOMI_KEYWORDS


def dim1_fundamentals(ticker: str = "1810.HK") -> dict:
    """Dimension 1: Fundamental Analysis."""
    print("\n" + "=" * 60)
    print("  DIMENSION 1: FUNDAMENTAL ANALYSIS")
    print("=" * 60)

    fund = get_stock_fundamentals(ticker)
    print(f"  Company: {fund.get('name', ticker)}")
    print(f"  Market Cap: {format_number(fund.get('market_cap', 0))}")
    print(f"  PE: {fund.get('pe_ratio', 'N/A')} | Forward PE: {fund.get('forward_pe', 'N/A')}")
    print(f"  PB: {fund.get('pb_ratio', 'N/A')} | PS: {fund.get('ps_ratio', 'N/A')}")
    print(f"  Revenue Growth: {fund.get('revenue_growth', 'N/A')}")
    print(f"  Gross Margin: {fund.get('gross_margins', 'N/A')}")
    print(f"  Operating Margin: {fund.get('operating_margins', 'N/A')}")
    print(f"  ROE: {fund.get('roe', 'N/A')} | ROA: {fund.get('roa', 'N/A')}")
    print(f"  D/E: {fund.get('debt_to_equity', 'N/A')}")
    print(f"  Beta: {fund.get('beta', 'N/A')}")
    print(f"  Analyst Target: {fund.get('analyst_target', 'N/A')}")
    print(f"  Recommendation: {fund.get('recommendation', 'N/A')}")

    ai_analysis = _call_deepseek(
        "You are a CFA-level fundamental analyst. No markdown formatting. Be direct.",
        f"""Analyze Xiaomi (1810.HK) fundamentals. Give a CLEAR score out of 10.

Data:
{json.dumps(fund, indent=2, default=str)}

Provide:
1. Valuation Assessment: Is it cheap or expensive vs history and peers? Score /10
2. Growth Quality: Revenue growth sustainability? Score /10
3. Profitability: Margin trends and quality? Score /10
4. Balance Sheet: Financial health? Score /10
5. Overall Fundamental Score: /10
6. Fundamental Verdict: BULLISH / BEARISH / NEUTRAL

Write concisely. English and Chinese.""",
        temperature=0.1,
    )

    return {"data": fund, "ai_analysis": ai_analysis}


def dim2_technicals(ticker: str = "1810.HK") -> dict:
    """Dimension 2: Technical Analysis."""
    print("\n" + "=" * 60)
    print("  DIMENSION 2: TECHNICAL ANALYSIS")
    print("=" * 60)

    hist = get_stock_history(ticker, period="1y")
    if hist.empty:
        return {"error": "No data"}

    close = hist["Close"]
    latest = close.iloc[-1]
    ma5 = close.rolling(5).mean().iloc[-1]
    ma20 = close.rolling(20).mean().iloc[-1]
    ma60 = close.rolling(60).mean().iloc[-1] if len(close) > 60 else None
    ma120 = close.rolling(120).mean().iloc[-1] if len(close) > 120 else None

    # RSI
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean().iloc[-1]
    loss = (-delta).clip(lower=0).rolling(14).mean().iloc[-1]
    rsi = 100 - (100 / (1 + gain / loss)) if loss != 0 else 50

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean().iloc[-1]
    ema26 = close.ewm(span=26, adjust=False).mean().iloc[-1]
    macd = ema12 - ema26
    signal = close.ewm(span=12, adjust=False).mean().ewm(span=9, adjust=False).mean().iloc[-1]

    # Momentum
    ret_1w = (latest / close.iloc[-5] - 1) * 100 if len(close) > 5 else 0
    ret_1m = (latest / close.iloc[-22] - 1) * 100 if len(close) > 22 else 0
    ret_3m = (latest / close.iloc[-66] - 1) * 100 if len(close) > 66 else 0
    ret_6m = (latest / close.iloc[-132] - 1) * 100 if len(close) > 132 else 0

    # 52w range
    high_52w = close.max()
    low_52w = close.min()
    pct_from_high = (latest / high_52w - 1) * 100
    pct_from_low = (latest / low_52w - 1) * 100

    # Volume trend
    vol_avg_20 = hist["Volume"].rolling(20).mean().iloc[-1]
    vol_latest = hist["Volume"].iloc[-1]
    vol_ratio = vol_latest / vol_avg_20 if vol_avg_20 > 0 else 1

    tech = {
        "price": round(latest, 2),
        "ma5": round(ma5, 2),
        "ma20": round(ma20, 2),
        "ma60": round(ma60, 2) if ma60 else None,
        "ma120": round(ma120, 2) if ma120 else None,
        "rsi_14": round(rsi, 1),
        "macd": round(macd, 3),
        "ret_1w": round(ret_1w, 2),
        "ret_1m": round(ret_1m, 2),
        "ret_3m": round(ret_3m, 2),
        "ret_6m": round(ret_6m, 2),
        "high_52w": round(high_52w, 2),
        "low_52w": round(low_52w, 2),
        "pct_from_52w_high": round(pct_from_high, 2),
        "pct_from_52w_low": round(pct_from_low, 2),
        "volume_ratio": round(vol_ratio, 2),
        "above_ma20": latest > ma20,
        "above_ma60": latest > ma60 if ma60 else None,
        "trend": "UP" if ma5 > ma20 and (ma60 is None or ma20 > ma60) else
                 "DOWN" if ma5 < ma20 and (ma60 is None or ma20 < ma60) else "MIXED",
    }

    print(f"  Price: {tech['price']} | MA20: {tech['ma20']} | MA60: {tech['ma60']}")
    print(f"  RSI(14): {tech['rsi_14']} | MACD: {tech['macd']}")
    print(f"  Trend: {tech['trend']}")
    print(f"  1W: {tech['ret_1w']:+.2f}% | 1M: {tech['ret_1m']:+.2f}% | 3M: {tech['ret_3m']:+.2f}% | 6M: {tech['ret_6m']:+.2f}%")
    print(f"  52W High: {tech['high_52w']} ({tech['pct_from_52w_high']:+.1f}%) | Low: {tech['low_52w']} ({tech['pct_from_52w_low']:+.1f}%)")
    print(f"  Volume ratio: {tech['volume_ratio']:.2f}x avg")

    ai_analysis = _call_deepseek(
        "You are a top technical analyst. No markdown formatting. Give clear scores.",
        f"""Technical analysis for Xiaomi (1810.HK):

{json.dumps(tech, indent=2)}

Provide:
1. Trend Assessment: What's the primary trend? Score /10 (10=strong uptrend)
2. Momentum: Is momentum building or fading? Score /10
3. RSI Signal: Overbought/oversold/neutral? Score /10
4. Volume Confirmation: Does volume support the trend? Score /10
5. Overall Technical Score: /10
6. Technical Verdict: BULLISH / BEARISH / NEUTRAL
7. Key support and resistance levels

Concise. English + Chinese.""",
        temperature=0.1,
    )

    return {"data": tech, "ai_analysis": ai_analysis}


def dim3_sentiment(ticker: str = "1810.HK") -> dict:
    """Dimension 3: News & Sentiment Analysis."""
    print("\n" + "=" * 60)
    print("  DIMENSION 3: NEWS & SENTIMENT ANALYSIS")
    print("=" * 60)

    # Crawl from multiple sources
    print("  Crawling real-time news...")
    crawled = crawl_xiaomi_news_all()
    print(f"  Crawled: {len(crawled)} articles")

    print("  Fetching RSS feeds...")
    rss = fetch_rss_news(max_per_feed=10)
    xiaomi_rss = filter_by_keywords(rss, XIAOMI_KEYWORDS)
    print(f"  RSS Xiaomi articles: {len(xiaomi_rss)}")

    all_articles = crawled + xiaomi_rss

    # AI Sentiment
    print("  Running AI sentiment analysis...")
    sentiment = analyze_sentiment(all_articles[:25], "Xiaomi 1810.HK")

    # AI Keywords
    print("  Extracting keywords...")
    keywords = extract_keywords(all_articles[:20])

    # News summary
    titles = [a["title"] for a in all_articles[:20] if a.get("title")]
    print(f"  Top headlines:")
    for t in titles[:5]:
        print(f"    - {t}")

    ai_analysis = _call_deepseek(
        "You are a sentiment analysis expert. No markdown formatting.",
        f"""Analyze Xiaomi news sentiment from {len(all_articles)} articles.

Sentiment data: {json.dumps(sentiment, default=str, ensure_ascii=False)[:1000]}
Keywords: {json.dumps(keywords, default=str, ensure_ascii=False)[:800]}
Top headlines: {chr(10).join(titles[:15])}

Provide:
1. Overall News Sentiment: Score /10 (10=very positive)
2. Positive Catalysts found in news
3. Negative Risks found in news
4. Social Media Buzz: hot or cold?
5. Sentiment Verdict: BULLISH / BEARISH / NEUTRAL

Concise. English + Chinese.""",
        temperature=0.1,
    )

    return {
        "article_count": len(all_articles),
        "sentiment": sentiment,
        "keywords": keywords,
        "top_headlines": titles[:10],
        "ai_analysis": ai_analysis,
    }


def dim4_competitive(ticker: str = "1810.HK") -> dict:
    """Dimension 4: Industry & Competitive Position."""
    print("\n" + "=" * 60)
    print("  DIMENSION 4: INDUSTRY & COMPETITIVE POSITION")
    print("=" * 60)

    peers = {
        "腾讯": "0700.HK",
        "阿里": "9988.HK",
        "美团": "3690.HK",
        "快手": "1024.HK",
        "联想": "0992.HK",
        "中芯国际": "0981.HK",
    }

    xiaomi = get_stock_fundamentals(ticker)
    peer_data = {}
    for name, t in peers.items():
        print(f"  Fetching {name} ({t})...")
        peer_data[name] = get_stock_fundamentals(t)

    comparison = f"Xiaomi: PE={xiaomi.get('pe_ratio','N/A')}, PB={xiaomi.get('pb_ratio','N/A')}, "
    comparison += f"Rev Growth={xiaomi.get('revenue_growth','N/A')}, Margins={xiaomi.get('operating_margins','N/A')}\n"
    for name, d in peer_data.items():
        comparison += f"{name}: PE={d.get('pe_ratio','N/A')}, PB={d.get('pb_ratio','N/A')}, "
        comparison += f"Rev Growth={d.get('revenue_growth','N/A')}, Margins={d.get('operating_margins','N/A')}\n"

    ai_analysis = _call_deepseek(
        "You are an industry analyst at UBS. No markdown formatting.",
        f"""Analyze Xiaomi's competitive position in HK tech sector.

Xiaomi vs Peers:
{comparison}

Consider:
- Smartphone market share trends (global + China)
- IoT ecosystem strength
- EV business (SU7) potential and risks
- AI/HyperOS software ecosystem
- Revenue diversification
- Brand strength in emerging markets

Provide:
1. Competitive Moat: Score /10
2. Market Position: improving or deteriorating?
3. Key competitive advantages
4. Key competitive weaknesses
5. EV Business Assessment
6. Competitive Verdict: BULLISH / BEARISH / NEUTRAL

English + Chinese.""",
        temperature=0.2,
    )

    return {
        "xiaomi": xiaomi,
        "peers": {name: {"pe": d.get("pe_ratio"), "pb": d.get("pb_ratio"),
                         "growth": d.get("revenue_growth")}
                  for name, d in peer_data.items()},
        "ai_analysis": ai_analysis,
    }


def dim5_macro() -> dict:
    """Dimension 5: Macro & Geopolitical Factors."""
    print("\n" + "=" * 60)
    print("  DIMENSION 5: MACRO & GEOPOLITICAL")
    print("=" * 60)

    rss = fetch_rss_news(max_per_feed=8)
    from config import MACRO_KEYWORDS
    macro_news = filter_by_keywords(rss, MACRO_KEYWORDS)
    print(f"  Macro news articles: {len(macro_news)}")

    macro_headlines = [a["title"] for a in macro_news[:15]]

    # Key macro data points
    indices = {}
    for name, ticker in [("HSI", "^HSI"), ("SPX", "^GSPC"), ("USD/CNH", "USDCNH=X"), ("US10Y", "^TNX")]:
        try:
            hist = yf.Ticker(ticker).history(period="5d")
            if not hist.empty:
                latest = hist["Close"].iloc[-1]
                prev = hist["Close"].iloc[-2] if len(hist) > 1 else latest
                indices[name] = {"price": round(latest, 2), "change_pct": round((latest/prev-1)*100, 2)}
        except Exception:
            pass

    print(f"  Macro indices: {json.dumps(indices, default=str)}")

    ai_analysis = _call_deepseek(
        "You are a macro strategist. No markdown formatting.",
        f"""Analyze macro/geopolitical factors affecting Xiaomi (1810.HK).

Market indices: {json.dumps(indices, default=str)}
Recent macro headlines:
{chr(10).join(macro_headlines[:10])}

Consider:
1. US-China trade/tech tensions impact on Xiaomi
2. China domestic consumption recovery
3. Interest rate environment (Fed + PBOC)
4. Currency (USD/CNH) impact on HK-listed stocks
5. Global smartphone demand cycle
6. China EV policy support
7. Geopolitical risks (sanctions, export controls)

Provide:
1. Macro Tailwinds: Score /10
2. Geopolitical Risk: Score /10 (10=high risk)
3. Key tailwinds for Xiaomi
4. Key headwinds for Xiaomi
5. Macro Verdict: BULLISH / BEARISH / NEUTRAL for Xiaomi

English + Chinese.""",
        temperature=0.2,
    )

    return {
        "indices": indices,
        "macro_headlines": macro_headlines[:10],
        "ai_analysis": ai_analysis,
    }


def final_verdict(dim1, dim2, dim3, dim4, dim5) -> str:
    """AI synthesizes all 5 dimensions into a final LONG/SHORT decision."""
    print("\n" + "=" * 60)
    print("  FINAL VERDICT: SYNTHESIZING ALL 5 DIMENSIONS")
    print("=" * 60)

    summary = f"""
DIMENSION 1 - FUNDAMENTALS:
{dim1['ai_analysis'][:600]}

DIMENSION 2 - TECHNICALS:
{dim2['ai_analysis'][:600]}

DIMENSION 3 - SENTIMENT:
{dim3['ai_analysis'][:600]}

DIMENSION 4 - COMPETITIVE:
{dim4['ai_analysis'][:600]}

DIMENSION 5 - MACRO:
{dim5['ai_analysis'][:600]}
"""

    verdict = _call_deepseek(
        """You are the Chief Investment Officer at a top hedge fund. 
You must make a DECISIVE call. No fence-sitting. No markdown formatting.
This is for a UBS investment competition - the analysis must be sharp and well-reasoned.""",
        f"""Based on all 5 dimensions of analysis for Xiaomi (1810.HK):

{summary}

You MUST provide:

1. FINAL DECISION: LONG or SHORT Xiaomi (1810.HK)?
   - State clearly: "I recommend LONG Xiaomi" or "I recommend SHORT Xiaomi"
   - Conviction: HIGH / MEDIUM / LOW

2. THE 5 KEY REASONS (one from each dimension):
   Reason 1 (Fundamental): ...
   Reason 2 (Technical): ...
   Reason 3 (Sentiment): ...
   Reason 4 (Competitive): ...
   Reason 5 (Macro): ...

3. RISK FACTORS: Top 3 risks to this call

4. TIME HORIZON: How long should this trade last?

5. PAIR TRADE DIRECTION: If LONG Xiaomi, we need to SHORT a tech peer.
   If SHORT Xiaomi, we need to LONG a tech peer.
   Suggest 3 ideal pair candidates from HK/A-share tech sector
   (NOT 中际旭创 300308.SZ or 豪威 603501.SS - those are in the competition pool).

Be decisive. Be specific. English + Chinese.""",
        temperature=0.2,
    )

    return verdict


def run_full_analysis():
    """Run complete 5-dimension analysis pipeline."""
    print("\n" + "#" * 60)
    print("#" + " " * 58 + "#")
    print("#   ALPHA SIGNAL - FULL 5-DIMENSION STOCK ANALYSIS" + " " * 7 + "#")
    print("#   Target: Xiaomi (1810.HK)" + " " * 30 + "#")
    print(f"#   Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}" + " " * 33 + "#")
    print("#" + " " * 58 + "#")
    print("#" * 60)

    # Run all 5 dimensions
    d1 = dim1_fundamentals()
    d2 = dim2_technicals()
    d3 = dim3_sentiment()
    d4 = dim4_competitive()
    d5 = dim5_macro()

    # Final AI verdict
    verdict = final_verdict(d1, d2, d3, d4, d5)

    print("\n" + "#" * 60)
    print("  FINAL VERDICT")
    print("#" * 60)
    print(verdict)

    # Now run the screener based on the verdict
    direction = "short"  # default: long Xiaomi, find short
    if "SHORT Xiaomi" in verdict or "short Xiaomi" in verdict.lower().split("recommend")[1][:50] if "recommend" in verdict.lower() else False:
        direction = "long"

    print(f"\n\n{'='*60}")
    print(f"  SCREENING FOR PAIR TRADE: {'LONG Xiaomi -> Find SHORT' if direction=='short' else 'SHORT Xiaomi -> Find LONG'}")
    print(f"{'='*60}")

    xiaomi_fund = d1["data"]
    print("\n  Screening 50+ tech stocks...")
    candidates = screen_all_candidates()
    ranked = rank_candidates(candidates, xiaomi_fund, direction)

    print(f"\n  Top 5 {direction.upper()} candidates:")
    for i, c in enumerate(ranked[:5], 1):
        print(f"  {i}. {c.get('cn_name','')} ({c['ticker']}) Score={c['pair_score']}")

    print("\n  Generating AI pair recommendation...")
    pair_rec = ai_pair_recommendation(xiaomi_fund, ranked[:8], direction)

    print("\n" + "#" * 60)
    print("  AI PAIR TRADE RECOMMENDATION")
    print("#" * 60)
    print(pair_rec)

    # Save everything
    output = {
        "timestamp": datetime.now().isoformat(),
        "target": "1810.HK",
        "dim1_fundamentals": {"data": d1["data"], "analysis": d1["ai_analysis"]},
        "dim2_technicals": {"data": d2["data"], "analysis": d2["ai_analysis"]},
        "dim3_sentiment": {
            "article_count": d3["article_count"],
            "headlines": d3["top_headlines"],
            "analysis": d3["ai_analysis"],
        },
        "dim4_competitive": {"analysis": d4["ai_analysis"]},
        "dim5_macro": {"indices": d5["indices"], "analysis": d5["ai_analysis"]},
        "final_verdict": verdict,
        "pair_direction": direction,
        "top_candidates": [
            {"name": c.get("cn_name", ""), "ticker": c["ticker"], "score": c["pair_score"]}
            for c in ranked[:10]
        ],
        "pair_recommendation": pair_rec,
    }

    outfile = f"full_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n  Full report saved to {outfile}")

    return output


if __name__ == "__main__":
    run_full_analysis()
