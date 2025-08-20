import os, json
from urllib.parse import urlparse
from flask import request, session, current_app
from .pdf_utils import extract_pdf_text
from .config import UPLOAD_DIR

def ensure_history():
    if "history" not in session:
        session["history"] = []
    return session["history"]

def is_local_url(url: str) -> bool:
    if not url:
        return False
    if url.startswith("/"):
        return True
    try:
        parsed = urlparse(url)
        host = request.host
        if host and host in parsed.netloc:
            return True
        if parsed.hostname in ("127.0.0.1", "localhost"):
            return True
        return False
    except Exception:
        return False

def build_openai_content(user_msg: str, image_url: str | None = None) -> list:
    from .config import SYSTEM_PROMPT
    content = []
    if user_msg:
        content.append({"type": "input_text", "text": user_msg})

    if image_url:
        if is_local_url(image_url):
            if image_url.startswith("/"):
                local_path = os.path.join(current_app.root_path, image_url.lstrip("/"))
            else:
                parsed = urlparse(image_url)
                local_path = os.path.join(current_app.root_path, parsed.path.lstrip("/"))

            if os.path.exists(local_path):
                if local_path.lower().endswith(".pdf"):
                    pdf_text = extract_pdf_text(local_path)
                    snippet = pdf_text[:15000]
                    content.append({"type": "input_text", "text": f"[Attached PDF content]\n\n{snippet}"})
                else:
                    content.append({"type": "input_text", "text": f"[Attached local file at {image_url}]"})
            else:
                content.append({"type": "input_text", "text": f"[File not found locally: {image_url}]"})
        else:
            content.append({"type": "input_image", "image_url": image_url})
    return content
