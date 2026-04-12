"""Stock data fetching module using yfinance."""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from config import WATCHED_STOCKS, MARKET_INDICES, COMPETITION_STOCKS


def get_stock_quote(ticker: str) -> dict:
    """Get current/latest stock quote data."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="5d")

        if hist.empty:
            return {"ticker": ticker, "error": "No data available"}

        latest = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) > 1 else latest

        change = latest["Close"] - prev["Close"]
        change_pct = (change / prev["Close"]) * 100 if prev["Close"] != 0 else 0

        return {
            "ticker": ticker,
            "name": info.get("shortName", ticker),
            "price": round(latest["Close"], 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "volume": int(latest["Volume"]),
            "high": round(latest["High"], 2),
            "low": round(latest["Low"], 2),
            "open": round(latest["Open"], 2),
            "prev_close": round(prev["Close"], 2),
            "market_cap": info.get("marketCap", "N/A"),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "52w_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "52w_low": info.get("fiftyTwoWeekLow", "N/A"),
            "date": latest.name.strftime("%Y-%m-%d"),
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


def get_stock_history(ticker: str, period: str = "6mo") -> pd.DataFrame:
    """Get historical stock data."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        return hist
    except Exception:
        return pd.DataFrame()


def get_all_watched_quotes() -> dict:
    """Get quotes for all watched stocks."""
    quotes = {}
    for name, info in WATCHED_STOCKS.items():
        quotes[name] = get_stock_quote(info["ticker"])
    return quotes


def get_market_indices() -> dict:
    """Get major market indices data."""
    indices = {}
    for name, ticker in MARKET_INDICES.items():
        indices[name] = get_stock_quote(ticker)
    return indices


def get_competition_sector_data(sector: str) -> dict:
    """Get stock data for all companies in a competition sector."""
    if sector not in COMPETITION_STOCKS:
        return {}
    sector_data = {}
    for name, ticker in COMPETITION_STOCKS[sector].items():
        sector_data[name] = get_stock_quote(ticker)
    return sector_data


def get_stock_fundamentals(ticker: str) -> dict:
    """Get fundamental financial data for a stock."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        return {
            "ticker": ticker,
            "name": info.get("shortName", ticker),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "market_cap": info.get("marketCap", "N/A"),
            "enterprise_value": info.get("enterpriseValue", "N/A"),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "forward_pe": info.get("forwardPE", "N/A"),
            "peg_ratio": info.get("pegRatio", "N/A"),
            "pb_ratio": info.get("priceToBook", "N/A"),
            "ps_ratio": info.get("priceToSalesTrailing12Months", "N/A"),
            "ev_ebitda": info.get("enterpriseToEbitda", "N/A"),
            "revenue": info.get("totalRevenue", "N/A"),
            "revenue_growth": info.get("revenueGrowth", "N/A"),
            "gross_margins": info.get("grossMargins", "N/A"),
            "operating_margins": info.get("operatingMargins", "N/A"),
            "profit_margins": info.get("profitMargins", "N/A"),
            "roe": info.get("returnOnEquity", "N/A"),
            "roa": info.get("returnOnAssets", "N/A"),
            "debt_to_equity": info.get("debtToEquity", "N/A"),
            "current_ratio": info.get("currentRatio", "N/A"),
            "free_cashflow": info.get("freeCashflow", "N/A"),
            "dividend_yield": info.get("dividendYield", "N/A"),
            "beta": info.get("beta", "N/A"),
            "52w_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "52w_low": info.get("fiftyTwoWeekLow", "N/A"),
            "50d_avg": info.get("fiftyDayAverage", "N/A"),
            "200d_avg": info.get("twoHundredDayAverage", "N/A"),
            "analyst_target": info.get("targetMeanPrice", "N/A"),
            "recommendation": info.get("recommendationKey", "N/A"),
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


def get_comparable_companies(ticker: str) -> list:
    """Get comparable companies for a given stock via sector matching."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        sector = info.get("sector", "")
        industry = info.get("industry", "")

        for sec_name, stocks in COMPETITION_STOCKS.items():
            for name, t in stocks.items():
                if t == ticker:
                    comps = []
                    for comp_name, comp_ticker in stocks.items():
                        if comp_ticker != ticker:
                            comp_data = get_stock_fundamentals(comp_ticker)
                            comp_data["comp_name"] = comp_name
                            comps.append(comp_data)
                    return comps

        return []
    except Exception as e:
        return []


def format_number(num) -> str:
    """Format large numbers for display."""
    if isinstance(num, str) or num == "N/A":
        return str(num)
    if num >= 1e12:
        return f"{num/1e12:.2f}T"
    if num >= 1e9:
        return f"{num/1e9:.2f}B"
    if num >= 1e6:
        return f"{num/1e6:.2f}M"
    if num >= 1e3:
        return f"{num/1e3:.2f}K"
    return f"{num:.2f}"


if __name__ == "__main__":
    print("=== Watched Stocks ===")
    quotes = get_all_watched_quotes()
    for name, data in quotes.items():
        if "error" not in data:
            print(f"{name}: ${data['price']} ({data['change_pct']:+.2f}%)")
        else:
            print(f"{name}: Error - {data['error']}")

    print("\n=== Market Indices ===")
    indices = get_market_indices()
    for name, data in indices.items():
        if "error" not in data:
            print(f"{name}: {data['price']} ({data['change_pct']:+.2f}%)")
        else:
            print(f"{name}: Error - {data['error']}")
