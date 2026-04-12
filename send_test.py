"""Quick test: send today's briefing to ALL configured recipients."""
import os
import sys
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from dotenv import load_dotenv
load_dotenv()

import json
from email_service import send_email
from jinja2 import Template
from email_service import EMAIL_TEMPLATE
from datetime import datetime

print("Loading latest data...")
with open("latest_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

mood = data.get("mood", {
    "mood": "calm", "emoji": "☕",
    "vibe": "Peaceful mind, clear analysis",
})

html = Template(EMAIL_TEMPLATE).render(
    date=datetime.now().strftime("%A, %B %d, %Y"),
    stocks=data.get("stocks", {}),
    indices=data.get("indices", {}),
    news=data.get("news", {}),
    sentiment=data.get("sentiment", {}),
    briefing=data.get("briefing", ""),
    keywords=data.get("keywords", {}),
    mood=mood,
)

mood_name = mood.get("mood", "calm")
subject = f"Alpha Signal | {mood_name.title()} Day | {datetime.now().strftime('%Y-%m-%d')}"

receivers = os.getenv("EMAIL_RECEIVER", "")
print(f"\nSending to: {receivers}")
result = send_email(subject, html)
print(f"Result: {'SUCCESS' if result else 'FAILED'}")
