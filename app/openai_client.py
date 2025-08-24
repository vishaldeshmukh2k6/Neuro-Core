import os
from openai import OpenAI
from ollama import Client as OllamaClient

raw_key = (os.getenv("OPENAI_API_KEY") or "").strip()
api_key = raw_key if raw_key.startswith("sk-") else ""

if not api_key:
    # Fallback to Ollama
    client = OllamaClient(host='http://localhost:11434')
else:
    client = OpenAI(api_key=api_key)
