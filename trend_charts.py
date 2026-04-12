"""Trend visualization module with technical indicators.

Generates interactive Plotly charts:
- Candlestick with MA overlays
- Volume profile
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- Relative performance comparison
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import yfinance as yf
import json


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute all technical indicators on a price DataFrame."""
    close = df["Close"]

    # Moving Averages
    df["MA5"] = close.rolling(5).mean()
    df["MA10"] = close.rolling(10).mean()
    df["MA20"] = close.rolling(20).mean()
    df["MA60"] = close.rolling(60).mean()

    # Bollinger Bands (20-day, 2 std)
    df["BB_mid"] = df["MA20"]
    df["BB_std"] = close.rolling(20).std()
    df["BB_upper"] = df["BB_mid"] + 2 * df["BB_std"]
    df["BB_lower"] = df["BB_mid"] - 2 * df["BB_std"]

    # RSI (14-day)
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_hist"] = df["MACD"] - df["MACD_signal"]

    # Volume MA
    df["Vol_MA20"] = df["Volume"].rolling(20).mean()

    return df


def create_full_chart(ticker: str, name: str = "", period: str = "6mo") -> dict:
    """Create a full technical analysis chart as Plotly JSON."""
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)
    if df.empty:
        return {"error": "No data available"}

    df = compute_indicators(df)
    display_name = name or ticker

    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.5, 0.15, 0.15, 0.2],
        subplot_titles=[
            f"{display_name} ({ticker})",
            "Volume",
            "RSI (14)",
            "MACD",
        ],
    )

    # Row 1: Candlestick + MA + Bollinger
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"], name="Price",
        increasing_line_color="#00d26a", decreasing_line_color="#e63946",
        increasing_fillcolor="#0a2e1a", decreasing_fillcolor="#2e0a0f",
    ), row=1, col=1)

    for ma, color in [("MA5", "#ffd60a"), ("MA10", "#ff6b6b"), ("MA20", "#4361ee"), ("MA60", "#7209b7")]:
        if ma in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[ma], name=ma,
                line=dict(color=color, width=1),
            ), row=1, col=1)

    # Bollinger Bands
    fig.add_trace(go.Scatter(
        x=df.index, y=df["BB_upper"], name="BB Upper",
        line=dict(color="rgba(67,97,238,0.3)", width=1, dash="dot"),
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=df.index, y=df["BB_lower"], name="BB Lower",
        line=dict(color="rgba(67,97,238,0.3)", width=1, dash="dot"),
        fill="tonexty", fillcolor="rgba(67,97,238,0.05)",
    ), row=1, col=1)

    # Row 2: Volume
    colors = ["#00d26a" if c >= o else "#e63946" for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(
        x=df.index, y=df["Volume"], name="Volume",
        marker_color=colors, opacity=0.6,
    ), row=2, col=1)
    fig.add_trace(go.Scatter(
        x=df.index, y=df["Vol_MA20"], name="Vol MA20",
        line=dict(color="#ffd60a", width=1),
    ), row=2, col=1)

    # Row 3: RSI
    fig.add_trace(go.Scatter(
        x=df.index, y=df["RSI"], name="RSI",
        line=dict(color="#4361ee", width=1.5),
    ), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="#e63946", opacity=0.5, row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#00d26a", opacity=0.5, row=3, col=1)
    fig.add_hrect(y0=30, y1=70, fillcolor="rgba(67,97,238,0.05)", line_width=0, row=3, col=1)

    # Row 4: MACD
    macd_colors = ["#00d26a" if v >= 0 else "#e63946" for v in df["MACD_hist"]]
    fig.add_trace(go.Bar(
        x=df.index, y=df["MACD_hist"], name="MACD Hist",
        marker_color=macd_colors,
    ), row=4, col=1)
    fig.add_trace(go.Scatter(
        x=df.index, y=df["MACD"], name="MACD",
        line=dict(color="#4361ee", width=1.5),
    ), row=4, col=1)
    fig.add_trace(go.Scatter(
        x=df.index, y=df["MACD_signal"], name="Signal",
        line=dict(color="#e63946", width=1),
    ), row=4, col=1)

    # Layout
    fig.update_layout(
        height=900,
        paper_bgcolor="#0a0a0f",
        plot_bgcolor="#12121a",
        font=dict(color="#707090", size=11),
        showlegend=True,
        legend=dict(bgcolor="rgba(18,18,26,0.8)", font=dict(size=10)),
        xaxis_rangeslider_visible=False,
        margin=dict(l=50, r=20, t=40, b=30),
    )

    for i in range(1, 5):
        fig.update_xaxes(gridcolor="#1e1e2e", row=i, col=1)
        fig.update_yaxes(gridcolor="#1e1e2e", row=i, col=1)

    return json.loads(fig.to_json())


def create_comparison_chart(tickers: dict, period: str = "6mo") -> dict:
    """Create relative performance comparison chart.

    tickers: dict of {name: ticker_symbol}
    """
    fig = go.Figure()
    colors = ["#e63946", "#4361ee", "#00d26a", "#ffd60a", "#7209b7",
              "#ff6b6b", "#00ff88", "#ffed4a", "#a855f7", "#06b6d4"]

    for i, (name, ticker) in enumerate(tickers.items()):
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if hist.empty:
            continue
        normalized = (hist["Close"] / hist["Close"].iloc[0] - 1) * 100
        fig.add_trace(go.Scatter(
            x=hist.index, y=normalized, name=f"{name} ({ticker})",
            line=dict(color=colors[i % len(colors)], width=2),
        ))

    fig.add_hline(y=0, line_dash="dash", line_color="#707090", opacity=0.3)

    fig.update_layout(
        title=dict(text="Relative Performance Comparison (%)", font=dict(color="#fff", size=14)),
        height=500,
        paper_bgcolor="#0a0a0f",
        plot_bgcolor="#12121a",
        font=dict(color="#707090", size=11),
        yaxis_title="Return (%)",
        xaxis=dict(gridcolor="#1e1e2e"),
        yaxis=dict(gridcolor="#1e1e2e"),
        legend=dict(bgcolor="rgba(18,18,26,0.8)"),
        margin=dict(l=50, r=20, t=50, b=30),
    )

    return json.loads(fig.to_json())


def create_valuation_comparison(stocks_data: list) -> dict:
    """Create multi-metric valuation comparison chart."""
    names = [s.get("cn_name", s.get("name", s["ticker"])) for s in stocks_data]
    metrics = {
        "P/E": [s.get("pe_ratio") for s in stocks_data],
        "P/B": [s.get("pb_ratio") for s in stocks_data],
        "P/S": [s.get("ps_ratio") for s in stocks_data],
        "EV/EBITDA": [s.get("ev_ebitda") for s in stocks_data],
    }

    fig = make_subplots(rows=2, cols=2, subplot_titles=list(metrics.keys()))

    colors = ["#e63946", "#4361ee", "#00d26a", "#ffd60a", "#7209b7",
              "#ff6b6b", "#00ff88", "#ffed4a"]

    positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
    for (metric, values), (row, col) in zip(metrics.items(), positions):
        bar_colors = [colors[i % len(colors)] for i in range(len(names))]
        safe_values = [v if v and isinstance(v, (int, float)) else 0 for v in values]
        fig.add_trace(go.Bar(
            x=names, y=safe_values, name=metric,
            marker_color=bar_colors,
            text=[f"{v:.1f}" if v else "N/A" for v in safe_values],
            textposition="outside",
            textfont=dict(color="#c0c0d0", size=10),
            showlegend=False,
        ), row=row, col=col)

    fig.update_layout(
        height=600,
        paper_bgcolor="#0a0a0f",
        plot_bgcolor="#12121a",
        font=dict(color="#707090", size=11),
        margin=dict(l=50, r=20, t=50, b=50),
    )

    for i in range(1, 3):
        for j in range(1, 3):
            fig.update_xaxes(gridcolor="#1e1e2e", row=i, col=j)
            fig.update_yaxes(gridcolor="#1e1e2e", row=i, col=j)

    return json.loads(fig.to_json())


def create_sector_heatmap(stocks_data: list) -> dict:
    """Create a heatmap showing key metrics across stocks."""
    names = [s.get("cn_name", s.get("name", s["ticker"])) for s in stocks_data]
    metrics_labels = ["PE", "PB", "Rev Growth", "Op Margin", "ROE", "1M Mom", "3M Mom"]

    z = []
    for s in stocks_data:
        row = [
            s.get("pe_ratio") or 0,
            s.get("pb_ratio") or 0,
            (s.get("revenue_growth") or 0) * 100,
            (s.get("operating_margins") or 0) * 100,
            (s.get("roe") or 0) * 100,
            s.get("momentum_1m") or 0,
            s.get("momentum_3m") or 0,
        ]
        z.append(row)

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=metrics_labels,
        y=names,
        colorscale=[
            [0, "#e63946"],
            [0.5, "#12121a"],
            [1, "#00d26a"],
        ],
        text=[[f"{v:.1f}" for v in row] for row in z],
        texttemplate="%{text}",
        textfont=dict(size=11, color="#c0c0d0"),
    ))

    fig.update_layout(
        title=dict(text="Stock Metrics Heatmap", font=dict(color="#fff", size=14)),
        height=max(400, len(names) * 35 + 100),
        paper_bgcolor="#0a0a0f",
        plot_bgcolor="#12121a",
        font=dict(color="#707090", size=11),
        margin=dict(l=120, r=20, t=50, b=50),
    )

    return json.loads(fig.to_json())


if __name__ == "__main__":
    print("Generating Xiaomi technical chart...")
    chart = create_full_chart("1810.HK", "小米集团")
    with open("chart_xiaomi.json", "w") as f:
        json.dump(chart, f)
    print("Saved to chart_xiaomi.json")

    print("\nGenerating comparison chart...")
    comp = create_comparison_chart({
        "小米": "1810.HK",
        "腾讯": "0700.HK",
        "中际旭创": "300308.SZ",
    })
    with open("chart_comparison.json", "w") as f:
        json.dump(comp, f)
    print("Saved to chart_comparison.json")
