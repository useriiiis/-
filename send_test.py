"""Quick test: send today's briefing email."""
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

print("Loading latest data...")
with open("latest_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

from email_service import send_email
from email_service import render_email
from datetime import datetime

mood = data.get("mood", {
    "mood": "calm", "emoji": "😌☕",
    "vibe": "Peaceful mind, clear analysis",
})

template_data = {
    "date": datetime.now().strftime("%A, %B %d, %Y"),
    "stocks": data.get("stocks", {}),
    "indices": data.get("indices", {}),
    "news": data.get("news", {}),
    "sentiment": data.get("sentiment", {}),
    "briefing": data.get("briefing", ""),
    "keywords": data.get("keywords", {}),
    "mood": mood,
}

from jinja2 import Template
from email_service import EMAIL_TEMPLATE
html = Template(EMAIL_TEMPLATE).render(**template_data)

mood_name = mood.get("mood", "calm")
subject = f"Alpha Signal | {mood_name.title()} Day | {datetime.now().strftime('%Y-%m-%d')}"

# Send to Resend owner (Gmail)
gmail = os.getenv("RESEND_OWNER_EMAIL", "a2735559771@gmail.com")
print(f"\nSending to {gmail}...")
result = send_email(subject, html, receiver=gmail)
print(f"Result: {'SUCCESS' if result else 'FAILED'}")
