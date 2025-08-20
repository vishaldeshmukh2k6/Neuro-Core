import os
from openai import OpenAI

raw_key = (os.getenv("OPENAI_API_KEY") or "").strip()
api_key = raw_key if raw_key.startswith("sk-") else ""
client = OpenAI(api_key=api_key) if api_key else None
