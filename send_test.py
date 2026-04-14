"""Quick test: send today's briefing to ALL configured recipients (Both Alpha & Sigma)."""
import os
import sys
import json
from dotenv import load_dotenv
from datetime import datetime
from jinja2 import Template
from email_service import send_email, EMAIL_TEMPLATE

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()

print("Loading latest data...")
with open("latest_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

receivers = os.getenv("EMAIL_RECEIVER", "")
print(f"Target receivers: {receivers}")

# ==========================================
# 1. Send Alpha (DeepSeek)
# ==========================================
mood_alpha = data.get("mood", {
    "mood": "calm", "emoji": "☕",
    "vibe": "Peaceful mind, clear analysis",
})

html_alpha = Template(EMAIL_TEMPLATE).render(
    date=datetime.now().strftime("%A, %B %d, %Y"),
    stocks=data.get("stocks", {}),
    indices=data.get("indices", {}),
    news=data.get("news", {}),
    sentiment=data.get("sentiment", {}),
    briefing=data.get("briefing", ""),
    keywords=data.get("keywords", {}),
    mood=mood_alpha,
    ai_name="Alpha"
)

mood_name_alpha = mood_alpha.get("mood", "calm")
emoji_alpha = mood_alpha.get("emoji", "📊")
# Strip extra text from emoji if it's combined like "🔥😱" -> just use the first char or keep it short
subject_alpha = f"{emoji_alpha} Alpha Signal | {mood_name_alpha.title()} Day | {datetime.now().strftime('%Y-%m-%d')}"

print(f"\n[1/2] Sending Alpha Email...")
result_alpha = send_email(subject_alpha, html_alpha)
print(f"Alpha Result: {'SUCCESS' if result_alpha else 'FAILED'}")


# ==========================================
# 2. Send Sigma (Gemini)
# ==========================================
mood_sigma = data.get("mood_sigma", {
    "mood": "calculated", "emoji": "♟️",
    "vibe": "Executing algorithms with precision.",
})

html_sigma = Template(EMAIL_TEMPLATE).render(
    date=datetime.now().strftime("%A, %B %d, %Y"),
    stocks=data.get("stocks", {}),
    indices=data.get("indices", {}),
    news=data.get("news", {}),
    sentiment=data.get("sentiment", {}),
    briefing=data.get("briefing_sigma", ""),
    keywords=data.get("keywords", {}),
    mood=mood_sigma,
    ai_name="Sigma"
)

mood_name_sigma = mood_sigma.get("mood", "calculated")
emoji_sigma = mood_sigma.get("emoji", "🧊")
subject_sigma = f"{emoji_sigma} Sigma Signal | {mood_name_sigma.title()} Day | {datetime.now().strftime('%Y-%m-%d')}"

print(f"\n[2/2] Sending Sigma Email...")
result_sigma = send_email(subject_sigma, html_sigma)
print(f"Sigma Result: {'SUCCESS' if result_sigma else 'FAILED'}")

print("\nDone!")
