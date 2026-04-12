"""AI-powered stock screener for long/short pair selection.

Scans technology stocks across HK and A-share markets,
compares fundamentals with Xiaomi, and uses DeepSeek AI
to recommend the optimal long/short pair trade.
"""

import json
import yfinance as yf
import pandas as pd
from datetime import datetime
from ai_analyzer import _call_deepseek
from stock_data import get_stock_fundamentals, get_stock_history, format_number

TECH_UNIVERSE = {
    # ---- HK-listed tech ----
    "腾讯": "0700.HK",
    "阿里巴巴-HK": "9988.HK",
    "美团": "3690.HK",
    "京东-HK": "9618.HK",
    "网易-HK": "9999.HK",
    "百度-HK": "9888.HK",
    "快手": "1024.HK",
    "哔哩哔哩-HK": "9626.HK",
    "联想集团": "0992.HK",
    "中芯国际-HK": "0981.HK",
    "商汤": "0020.HK",
    "金蝶国际": "0268.HK",
    "金山软件": "3888.HK",
    "微盟集团": "2013.HK",
    "万国数据-HK": "9698.HK",
    "明源云": "0909.HK",
    "小鹏汽车-HK": "9868.HK",
    "理想汽车-HK": "2015.HK",
    "蔚来-HK": "9866.HK",
    "零跑汽车": "9863.HK",
    "舜宇光学": "2382.HK",
    "瑞声科技": "2018.HK",
    "丘钛科技": "1478.HK",
    "ASM太平洋": "0522.HK",
    # ---- A-share tech (SZ/SS) ----
    "立讯精密": "002475.SZ",
    "歌尔股份": "002241.SZ",
    "TCL科技": "000100.SZ",
    "海康威视": "002415.SZ",
    "大华股份": "002236.SZ",
    "传音控股": "688036.SS",
    "韦尔股份": "603501.SS",
    "北方华创": "002371.SZ",
    "中微公司": "688012.SS",
    "澜起科技": "688008.SS",
    "兆易创新": "603986.SS",
    "卓胜微": "300782.SZ",
    "圣邦股份": "300661.SZ",
    "汇顶科技": "603160.SS",
    "科大讯飞": "002230.SZ",
    "用友网络": "600588.SS",
    "浪潮信息": "000977.SZ",
    "紫光股份": "000938.SZ",
    "中兴通讯-A": "000063.SZ",
    "工业富联": "601138.SS",
    "闻泰科技": "600745.SS",
    "深信服": "300454.SZ",
    "寒武纪": "688256.SS",
    "海光信息": "688041.SS",
    "龙芯中科": "688047.SS",
}

POOL_TICKERS = {"1810.HK", "300308.SZ", "603501.SS"}


def screen_stock(ticker: str) -> dict:
    """Fetch key screening metrics for a single stock."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="6mo")

        if hist.empty:
            return {"ticker": ticker, "error": "No price data"}

        latest = hist["Close"].iloc[-1]
        month_ago = hist["Close"].iloc[-22] if len(hist) > 22 else hist["Close"].iloc[0]
        three_mo = hist["Close"].iloc[-66] if len(hist) > 66 else hist["Close"].iloc[0]
        six_mo = hist["Close"].iloc[0]

        return {
            "ticker": ticker,
            "name": info.get("shortName", ticker),
            "price": round(latest, 2),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "pb_ratio": info.get("priceToBook"),
            "ps_ratio": info.get("priceToSalesTrailing12Months"),
            "ev_ebitda": info.get("enterpriseToEbitda"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "gross_margins": info.get("grossMargins"),
            "operating_margins": info.get("operatingMargins"),
            "profit_margins": info.get("profitMargins"),
            "roe": info.get("returnOnEquity"),
            "roa": info.get("returnOnAssets"),
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "beta": info.get("beta"),
            "dividend_yield": info.get("dividendYield"),
            "analyst_target": info.get("targetMeanPrice"),
            "recommendation": info.get("recommendationKey"),
            "momentum_1m": round((latest / month_ago - 1) * 100, 2) if month_ago else None,
            "momentum_3m": round((latest / three_mo - 1) * 100, 2) if three_mo else None,
            "momentum_6m": round((latest / six_mo - 1) * 100, 2) if six_mo else None,
            "avg_volume": int(hist["Volume"].mean()) if not hist["Volume"].empty else 0,
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


def screen_all_candidates(progress_callback=None) -> list:
    """Screen all tech stocks in the universe (excluding pool stocks)."""
    results = []
    total = len(TECH_UNIVERSE)
    for i, (name, ticker) in enumerate(TECH_UNIVERSE.items()):
        if ticker in POOL_TICKERS:
            continue
        if progress_callback:
            progress_callback(i + 1, total, name)
        else:
            print(f"  [{i+1}/{total}] Screening {name} ({ticker})...")

        data = screen_stock(ticker)
        if "error" not in data:
            data["cn_name"] = name
            results.append(data)

    return results


def rank_candidates(candidates: list, xiaomi_data: dict, direction: str = "short") -> list:
    """Rank candidates for long or short pairing with Xiaomi.

    direction: "short" = find stocks to short (pair with long Xiaomi)
               "long"  = find stocks to long (pair with short Xiaomi)
    """
    scored = []
    for c in candidates:
        if c.get("error"):
            continue

        score = 0.0
        reasons = []

        xm_pe = xiaomi_data.get("pe_ratio")
        c_pe = c.get("pe_ratio")

        if direction == "short":
            # For SHORT candidates: want overvalued, weak momentum, poor fundamentals
            if c_pe and xm_pe and c_pe > xm_pe * 1.5:
                score += 20
                reasons.append(f"PE({c_pe:.1f}) much higher than Xiaomi({xm_pe:.1f})")
            if c.get("momentum_3m") and c["momentum_3m"] < -10:
                score += 15
                reasons.append(f"Weak 3M momentum ({c['momentum_3m']:.1f}%)")
            if c.get("revenue_growth") and c["revenue_growth"] < 0:
                score += 15
                reasons.append(f"Negative revenue growth ({c['revenue_growth']*100:.1f}%)")
            if c.get("profit_margins") and c["profit_margins"] < 0:
                score += 10
                reasons.append("Negative profit margins")
            if c.get("operating_margins") and xiaomi_data.get("operating_margins"):
                if c["operating_margins"] < xiaomi_data["operating_margins"]:
                    score += 10
                    reasons.append("Lower operating margins than Xiaomi")
            if c.get("debt_to_equity") and c["debt_to_equity"] > 150:
                score += 10
                reasons.append(f"High leverage (D/E={c['debt_to_equity']:.0f})")
            if c.get("momentum_1m") and c["momentum_1m"] > 15:
                score += 5
                reasons.append("Overextended short-term (mean reversion candidate)")

        else:  # direction == "long"
            # For LONG candidates: want undervalued, strong momentum, good fundamentals
            if c_pe and c_pe < 20 and c_pe > 0:
                score += 15
                reasons.append(f"Attractive PE ({c_pe:.1f})")
            if c.get("momentum_3m") and c["momentum_3m"] > 10:
                score += 15
                reasons.append(f"Strong 3M momentum ({c['momentum_3m']:.1f}%)")
            if c.get("revenue_growth") and c["revenue_growth"] > 0.15:
                score += 15
                reasons.append(f"Strong revenue growth ({c['revenue_growth']*100:.1f}%)")
            if c.get("profit_margins") and c["profit_margins"] > 0.1:
                score += 10
                reasons.append(f"Healthy margins ({c['profit_margins']*100:.1f}%)")
            if c.get("roe") and c["roe"] > 0.15:
                score += 10
                reasons.append(f"High ROE ({c['roe']*100:.1f}%)")
            if c.get("operating_margins") and c["operating_margins"] > 0.1:
                score += 10
                reasons.append("Strong operating margins")
            if c.get("current_ratio") and c["current_ratio"] > 1.5:
                score += 5
                reasons.append("Healthy balance sheet")

        # Liquidity bonus
        if c.get("avg_volume", 0) > 5_000_000:
            score += 5
            reasons.append("High liquidity")

        # Market cap filter: prefer mid-to-large cap for competition credibility
        mc = c.get("market_cap", 0) or 0
        if mc > 50e9:
            score += 5
        elif mc > 10e9:
            score += 3

        c["pair_score"] = round(score, 1)
        c["pair_reasons"] = reasons
        scored.append(c)

    scored.sort(key=lambda x: x["pair_score"], reverse=True)
    return scored


def ai_pair_recommendation(xiaomi_data: dict, top_candidates: list, direction: str) -> str:
    """Use DeepSeek to generate AI recommendation for the best pair trade."""
    cand_text = ""
    for i, c in enumerate(top_candidates[:8], 1):
        cand_text += f"\n{i}. {c.get('cn_name', '')} ({c['ticker']})"
        cand_text += f"\n   Score: {c['pair_score']} | Price: {c['price']}"
        cand_text += f"\n   PE: {c.get('pe_ratio', 'N/A')} | PB: {c.get('pb_ratio', 'N/A')}"
        cand_text += f"\n   Revenue Growth: {c.get('revenue_growth', 'N/A')}"
        cand_text += f"\n   Margins: Gross={c.get('gross_margins', 'N/A')}, Op={c.get('operating_margins', 'N/A')}"
        cand_text += f"\n   Momentum: 1M={c.get('momentum_1m', 'N/A')}%, 3M={c.get('momentum_3m', 'N/A')}%, 6M={c.get('momentum_6m', 'N/A')}%"
        cand_text += f"\n   Reasons: {'; '.join(c.get('pair_reasons', []))}"
        cand_text += f"\n   Market Cap: {format_number(c.get('market_cap', 0))}"
        cand_text += "\n"

    action = "SHORT" if direction == "short" else "LONG"
    xiaomi_action = "LONG" if direction == "short" else "SHORT"

    system_prompt = f"""You are a senior portfolio strategist at UBS preparing for an investment competition.
Your task is to recommend the BEST stock to {action} as a pair trade with {xiaomi_action} Xiaomi (1810.HK).

Requirements:
- The selected stock must be from the HK or A-share market
- It must be in the Technology sector
- It CANNOT be 中际旭创 (300308.SZ) or 豪威 (603501.SS) as those are in the competition pool
- The pair trade thesis must be compelling and well-argued
- Consider: valuation divergence, growth trajectories, competitive positioning, catalysts"""

    user_prompt = f"""Xiaomi (1810.HK) Fundamentals:
{json.dumps(xiaomi_data, indent=2, default=str)}

Top {action} Candidates (ranked by quantitative score):
{cand_text}

Please provide:

1. **TOP PICK: Your #1 recommendation** - Which stock and why (2-3 sentences)
2. **RUNNER-UP: Your #2 pick** - Alternative choice
3. **Pair Trade Thesis** ({xiaomi_action} Xiaomi + {action} your pick):
   - Why this specific combination creates alpha
   - Valuation divergence argument
   - Growth trajectory comparison
   - Sector/competitive dynamics
4. **Catalyst Timeline** - What events could drive the trade in 3-6 months
5. **Risk Analysis** - What could go wrong and how to mitigate
6. **Conviction Level** - High/Medium/Low with reasoning

Write in English for competition submission, with Chinese (中文) notes for key insights.
Be specific with numbers and make a decisive recommendation."""

    return _call_deepseek(system_prompt, user_prompt, temperature=0.2)


def run_full_screening(direction: str = "short") -> dict:
    """Run the complete screening pipeline."""
    print("=" * 60)
    print(f"  ALPHA SIGNAL - Stock Pair Screener")
    print(f"  Direction: {'LONG Xiaomi + SHORT ???' if direction == 'short' else 'SHORT Xiaomi + LONG ???'}")
    print(f"  Universe: {len(TECH_UNIVERSE)} tech stocks (HK + A-share)")
    print("=" * 60)

    # Step 1: Get Xiaomi data
    print("\n[1/4] Fetching Xiaomi fundamentals...")
    xiaomi = get_stock_fundamentals("1810.HK")
    print(f"  Xiaomi PE: {xiaomi.get('pe_ratio', 'N/A')}, Market Cap: {format_number(xiaomi.get('market_cap', 0))}")

    # Step 2: Screen all candidates
    print(f"\n[2/4] Screening {len(TECH_UNIVERSE)} tech stocks...")
    candidates = screen_all_candidates()
    print(f"  Successfully screened: {len(candidates)} stocks")

    # Step 3: Rank candidates
    print(f"\n[3/4] Ranking candidates for {direction.upper()} direction...")
    ranked = rank_candidates(candidates, xiaomi, direction)

    print("\n  Top 10 candidates:")
    for i, c in enumerate(ranked[:10], 1):
        print(f"  {i}. {c.get('cn_name', '')} ({c['ticker']}) - Score: {c['pair_score']}")
        if c.get("pair_reasons"):
            print(f"     Reasons: {'; '.join(c['pair_reasons'][:3])}")

    # Step 4: AI recommendation
    print(f"\n[4/4] Generating AI pair trade recommendation...")
    recommendation = ai_pair_recommendation(xiaomi, ranked[:8], direction)

    result = {
        "direction": direction,
        "xiaomi": xiaomi,
        "total_screened": len(candidates),
        "top_candidates": [
            {k: v for k, v in c.items() if k != "pair_reasons" or True}
            for c in ranked[:15]
        ],
        "ai_recommendation": recommendation,
        "timestamp": datetime.now().isoformat(),
    }

    output_file = f"screening_{direction}_{datetime.now().strftime('%Y%m%d')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n  Results saved to {output_file}")

    return result


if __name__ == "__main__":
    import sys
    direction = sys.argv[1] if len(sys.argv) > 1 else "short"
    result = run_full_screening(direction)
    print("\n" + "=" * 60)
    print("  AI RECOMMENDATION:")
    print("=" * 60)
    print(result["ai_recommendation"])
