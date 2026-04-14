import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GEMINI_API_KEY")
# Try a few common proxy base URLs if the official one fails
base_urls = [
    "https://api.deepseek.com", # Fallback to deepseek if gemini proxy fails
    "https://generativelanguage.googleapis.com/v1beta/openai/",
    "https://api.openai-proxy.com/v1",
]

for url in base_urls:
    print(f"Testing {url}...")
    client = OpenAI(api_key=key if "deepseek" not in url else os.getenv("DEEPSEEK_API_KEY"), base_url=url)
    try:
        response = client.chat.completions.create(
            model="deepseek-chat" if "deepseek" in url else "gemini-pro",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        print(f"SUCCESS with {url}: {response.choices[0].message.content}")
        break
    except Exception as e:
        print(f"Failed: {e}")
