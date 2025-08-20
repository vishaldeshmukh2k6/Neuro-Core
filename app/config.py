import os
from pathlib import Path

# Upload directory
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = (
    "You are a helpful, concise assistant. "
    "Format answers in Markdown. Use bullet points where helpful. "
    "When returning code, use fenced code blocks with language tags."
)
