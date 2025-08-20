import os, uuid, json
from flask import Blueprint, render_template, request, jsonify, session, Response, stream_with_context
from werkzeug.utils import secure_filename
from .helpers import ensure_history, build_openai_content
from .openai_client import client
from .config import UPLOAD_DIR, SYSTEM_PROMPT

bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    history = ensure_history()
    return render_template("index.html", history=history)

@bp.post("/clear")
def clear():
    session["history"] = []
    return jsonify({"ok": True})

@bp.post("/upload")
def upload():
    if "file" not in request.files:
        return jsonify({"error": "no file"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "empty filename"}), 400
    name = secure_filename(f.filename)
    ext = os.path.splitext(name)[1].lower() or ".png"
    fname = f"{uuid.uuid4().hex}{ext}"
    dest = os.path.join(UPLOAD_DIR, fname)
    f.save(dest)
    url = f"/static/uploads/{fname}"
    return jsonify({"url": url})

def call_openai_sync(user_msg: str, image_url: str | None = None) -> str:
    if not client:
        raise RuntimeError("OpenAI API key not configured.")
    content = build_openai_content(user_msg, image_url)
    resp = client.responses.create(
        model="gpt-4o-mini",
        instructions=SYSTEM_PROMPT,
        input=[{"role": "user", "content": content}],
    )
    return resp.output_text or ""

@bp.post("/chat")
def chat():
    data = request.get_json(force=True)
    user_msg = (data or {}).get("message", "").strip()
    image_url = (data or {}).get("image_url")

    if not user_msg and not image_url:
        return jsonify({"error": "empty message"}), 400

    history = ensure_history()
    history.append({"role": "user", "content": user_msg, "image_url": image_url})
    session.modified = True

    try:
        reply = call_openai_sync(user_msg, image_url) if client else "API key missing."
    except Exception as e:
        reply = f"AI service error: {e}"

    history.append({"role": "assistant", "content": reply})
    session.modified = True
    return jsonify({"reply": reply})

@bp.post("/stream")
def stream():
    data = request.get_json(force=True)
    user_msg = (data or {}).get("message", "").strip()
    image_url = (data or {}).get("image_url")

    if not user_msg and not image_url:
        return jsonify({"error": "empty message"}), 400

    history = ensure_history()
    history.append({"role": "user", "content": user_msg, "image_url": image_url})
    session.modified = True

    if not client:
        reply = "API key missing."
        history.append({"role": "assistant", "content": reply})
        session.modified = True
        return jsonify({"reply": reply})

    content = build_openai_content(user_msg, image_url)

    @stream_with_context
    def openai_stream():
        full_chunks = []
        try:
            with client.responses.stream(
                model="gpt-4o-mini",
                instructions=SYSTEM_PROMPT,
                input=[{"role": "user", "content": content}],
            ) as s:
                for event in s:
                    if event.type == "response.output_text.delta":
                        chunk = event.delta or ""
                        if chunk:
                            full_chunks.append(chunk)
                            yield f"data: {json.dumps({'delta': chunk})}\n\n"
                    elif event.type == "response.completed":
                        final_text = "".join(full_chunks).strip()
                        history.append({"role": "assistant", "content": final_text})
                        session.modified = True
                        yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            err = f" AI stream error: {e}"
            history.append({"role": "assistant", "content": err})
            session.modified = True
            yield f"data: {json.dumps({'delta': err})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"

    return Response(openai_stream(), mimetype="text/event-stream")

@bp.get("/health")
def health():
    return jsonify({"openai_present": bool(client)})

@bp.get("/config")
def config():
    return jsonify({"using_openai": bool(client), "model": "gpt-4o-mini"})
