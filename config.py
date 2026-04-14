import os
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")


EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.qq.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SEND_TIME = os.getenv("SEND_TIME", "08:00")

WATCHED_STOCKS = {
    "小米集团": {"ticker": "1810.HK", "market": "HKEX", "sector": "科技"},
    "QQQ": {"ticker": "QQQ", "market": "NASDAQ", "sector": "科技ETF"},
    "Intel": {"ticker": "INTC", "market": "NASDAQ", "sector": "半导体"},
    "微软": {"ticker": "MSFT", "market": "NASDAQ", "sector": "科技巨头"},
    "Bitcoin": {"ticker": "BTC-USD", "market": "Crypto", "sector": "加密货币"},
}

MARKET_INDICES = {
    "标普500": "^GSPC",
    "纳斯达克": "^IXIC",
    "恒生指数": "^HSI",
    "沪深300": "000300.SS",
    "道琼斯": "^DJI",
}

COMPETITION_STOCKS = {
    "科技": {
        "小米": "1810.HK",
        "中际旭创": "300308.SZ",
        "豪威": "603501.SS",
    },
    "消费": {
        "石头科技": "688169.SS",
        "泡泡玛特": "9992.HK",
        "名创优品": "9896.HK",
    },
    "工业": {
        "宁德时代": "300750.SZ",
        "比亚迪": "002594.SZ",
        "三一重工": "600031.SS",
    },
    "医疗健康": {
        "百济神州": "688235.SS",
        "微创机器人": "2252.HK",
        "爱尔眼科": "300015.SZ",
    },
    "能源": {
        "思源电气": "002028.SZ",
        "东方电气": "600875.SS",
        "杰瑞股份": "002353.SZ",
    },
}

NEWS_RSS_FEEDS = {
    "Reuters Business": "https://feeds.reuters.com/reuters/businessNews",
    "Reuters Tech": "https://feeds.reuters.com/reuters/technologyNews",
    "CNBC Top": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
    "CNBC Tech": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910",
    "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
    "FT Markets": "https://www.ft.com/markets?format=rss",
    "WSJ Markets": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
}

XIAOMI_KEYWORDS = [
    "Xiaomi", "小米", "Lei Jun", "雷军", "1810.HK",
    "MIUI", "HyperOS", "Xiaomi EV", "SU7", "小米汽车",
    "Xiaomi Auto", "小米手机", "Redmi",
]

MACRO_KEYWORDS = [
    "Federal Reserve", "Fed", "美联储", "interest rate", "利率",
    "inflation", "通胀", "GDP", "trade war", "贸易战",
    "tariff", "关税", "geopolitical", "地缘政治",
    "China economy", "中国经济", "semiconductor", "芯片",
    "AI", "artificial intelligence", "人工智能",
]
