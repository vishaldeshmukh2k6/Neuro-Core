import os, uuid, json
from flask import Blueprint, render_template, request, jsonify, session, Response, stream_with_context
from werkzeug.utils import secure_filename
from .helpers import ensure_history, build_openai_content, build_ollama_content, extract_personal_info, extract_teaching_command, extract_api_command, fetch_api_data, store_api_data
from .openai_client import client, OllamaClient
from .config import UPLOAD_DIR, SYSTEM_PROMPT, OPENAI_MODEL, OLLAMA_MODEL

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
    
    # Debug: Check if file exists and is readable
    debug_info = {
        "file_exists": os.path.exists(dest),
        "file_size": os.path.getsize(dest) if os.path.exists(dest) else 0,
        "file_path": dest,
        "file_name": name,
        "file_extension": ext
    }
    
    # Extract and store file content in memory
    from .helpers import extract_file_content_to_memory
    try:
        storage_result = extract_file_content_to_memory(dest)
        debug_info["storage_result"] = storage_result
        debug_info["storage_success"] = True
    except Exception as e:
        debug_info["storage_error"] = str(e)
        debug_info["storage_success"] = False
        storage_result = f"Error: {str(e)}"
    
    # Debug: Check memory after storage
    from .helpers import ensure_memory
    memory = ensure_memory()
    debug_info["memory_after"] = {
        "files_count": len(memory.get("files", {})),
        "file_names": list(memory.get("files", {}).keys()) if "files" in memory else []
    }
    
    return jsonify({
        "url": url, 
        "storage_result": storage_result,
        "filename": name,
        "debug": debug_info
    })

def call_openai_sync(user_msg: str, image_url: str | None = None) -> str:
    if not client:
        raise RuntimeError("AI client not configured.")
    
    if isinstance(client, OllamaClient): # type: ignore
        messages = build_ollama_content(user_msg, image_url, SYSTEM_PROMPT)
        resp = client.chat(model=OLLAMA_MODEL, messages=messages)
        return resp['message']['content'] or ""
    else:
        content = build_openai_content(user_msg, image_url)
        resp = client.responses.create(
                model=OPENAI_MODEL,
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

    # Check for personal info, teaching commands, or API commands first
    personal_response = extract_personal_info(user_msg)
    teaching_response = extract_teaching_command(user_msg)
    api_command = extract_api_command(user_msg)
    
    if personal_response:
        reply = personal_response
    elif teaching_response:
        reply = teaching_response
    elif api_command:
        if api_command == "URL_NOT_FOUND":
            reply = "I can fetch data from APIs! Please provide a URL. For example: 'fetch api https://api.example.com/data' or 'get data from https://jsonplaceholder.typicode.com/posts/1'"
        else:
            # Fetch data from the API
            try:
                api_result = fetch_api_data(api_command)
                if api_result['success']:
                    # Store the API data
                    storage_result = store_api_data(api_command, api_result['data'])
                    reply = f" {storage_result}\n\nI've fetched and stored data from: {api_command}\n\nNow you can ask me questions about this data!"
                else:
                    reply = f" Failed to fetch API data: {api_result.get('error', 'Unknown error')}"
            except Exception as e:
                reply = f" Error processing API request: {str(e)}"
    else:
        try:
            reply = call_openai_sync(user_msg, image_url) if client else "AI client not configured."
        except Exception as e:
            reply = f"AI service error: {e}"

    history.append({"role": "assistant", "content": reply})
    session.modified = True
    return jsonify({"reply": reply})

@bp.post("/teach")
def teach():
    """Endpoint to teach the AI new information"""
    data = request.get_json(force=True)
    lesson = (data or {}).get("lesson", "").strip()
    
    if not lesson:
        return jsonify({"error": "no lesson provided"}), 400
    
    from .helpers import teach_ai
    response = teach_ai(lesson)
    return jsonify({"response": response})

@bp.get("/memory")
def get_memory():
    """Get current user memory"""
    from .helpers import ensure_memory
    memory = ensure_memory()
    return jsonify({"memory": memory})

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

    # Check for personal info or teaching commands first
    personal_response = extract_personal_info(user_msg)
    teaching_response = extract_teaching_command(user_msg)
    api_command = extract_api_command(user_msg)
    
    if personal_response:
        reply = personal_response
        history.append({"role": "assistant", "content": reply})
        session.modified = True
        return jsonify({"reply": reply})
    elif teaching_response:
        reply = teaching_response
        history.append({"role": "assistant", "content": reply})
        session.modified = True
        return jsonify({"reply": reply})
    elif api_command:
        if api_command == "URL_NOT_FOUND":
            reply = "I can fetch data from APIs! Please provide a URL. For example: 'fetch api https://api.example.com/data' or 'get data from https://jsonplaceholder.typicode.com/posts/1'"
        else:
            # Fetch data from the API
            try:
                api_result = fetch_api_data(api_command)
                if api_result['success']:
                    # Store the API data
                    storage_result = store_api_data(api_command, api_result['data'])
                    reply = f" {storage_result}\n\nI've fetched and stored data from: {api_command}\n\nNow you can ask me questions about this data!"
                else:
                    reply = f" Failed to fetch API data: {api_result.get('error', 'Unknown error')}"
            except Exception as e:
                reply = f" Error processing API request: {str(e)}"
        
        history.append({"role": "assistant", "content": reply})
        session.modified = True
        return jsonify({"reply": reply})

    if not client:
        reply = "AI client not configured."
        history.append({"role": "assistant", "content": reply})
        session.modified = True
        return jsonify({"reply": reply})

    if isinstance(client, OllamaClient): # type: ignore
        @stream_with_context
        def ollama_stream():
            full_chunks = []
            try:
                messages = build_ollama_content(user_msg, image_url, SYSTEM_PROMPT)
                for event in client.chat(model=OLLAMA_MODEL, messages=messages, stream=True):
                    chunk = event['message']['content'] or ""
                    if chunk:
                        full_chunks.append(chunk)
                        yield f"data: {json.dumps({'delta': chunk})}\n\n"
                final_text = "".join(full_chunks).strip()
                history.append({"role": "assistant", "content": final_text})
                session.modified = True
                yield f"data: {json.dumps({'done': True})}\n\n"
            except Exception as e:
                err = f"AI stream error: {e}"
                history.append({"role": "assistant", "content": err})
                session.modified = True
                yield f"data: {json.dumps({'delta': err})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"
        return Response(ollama_stream(), mimetype="text/event-stream")
    
    else:
        content = build_openai_content(user_msg, image_url)

    @stream_with_context
    def openai_stream():
        full_chunks = []
        try:
            with client.responses.stream(
                    model=OPENAI_MODEL,
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

@bp.post("/api-fetch")
def api_fetch():
    """Direct endpoint to fetch and store API data"""
    data = request.get_json(force=True)
    api_url = (data or {}).get("url", "").strip()
    api_key = (data or {}).get("api_key", "").strip() or None
    headers = (data or {}).get("headers", {}) or {}
    
    if not api_url:
        return jsonify({"error": "no API URL provided"}), 400
    
    try:
        # Fetch data from the API
        api_result = fetch_api_data(api_url, api_key, headers)
        
        if api_result['success']:
            # Store the API data
            storage_result = store_api_data(api_url, api_result['data'], api_key)
            return jsonify({
                "success": True,
                "message": storage_result,
                "api_url": api_url,
                "data_preview": str(api_result['data'])[:500] + "..." if len(str(api_result['data'])) > 500 else str(api_result['data'])
            })
        else:
            return jsonify({
                "success": False,
                "error": api_result.get('error', 'Unknown error'),
                "status_code": api_result.get('status_code')
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }), 500

@bp.get("/health")
def health():
    return jsonify({"openai_present": bool(client)})

@bp.get("/config")
def config():
    model_name = OLLAMA_MODEL if isinstance(client, OllamaClient) else OPENAI_MODEL
    return jsonify({"using_openai": not isinstance(client, OllamaClient), "model": model_name})

@bp.get("/files")
def get_stored_files():
    """Get list of stored files and their metadata"""
    from .helpers import ensure_memory
    memory = ensure_memory()
    files = memory.get("files", {})
    
    file_list = []
    for file_name, file_info in files.items():
        file_list.append({
            "name": file_name,
            "type": file_info["type"],
            "uploaded_at": file_info["uploaded_at"],
            "content_length": len(file_info["content"])
        })
    
    return jsonify({"files": file_list})

@bp.get("/file/<filename>")
def get_file_content(filename):
    """Get content of a specific stored file"""
    from .helpers import ensure_memory
    memory = ensure_memory()
    files = memory.get("files", {})
    
    if filename in files:
        file_info = files[filename]
        return jsonify({
            "name": filename,
            "type": file_info["type"],
            "content": file_info["content"][:5000],  # Limit content for display
            "uploaded_at": file_info["uploaded_at"]
        })
    else:
        return jsonify({"error": "File not found"}), 404

@bp.get("/debug/memory")
def debug_memory():
    """Debug endpoint to see current memory state"""
    from .helpers import ensure_memory
    memory = ensure_memory()
    
    debug_info = {
        "memory_keys": list(memory.keys()),
        "files_count": len(memory.get("files", {})),
        "file_names": list(memory.get("files", {}).keys()) if "files" in memory else [],
        "memory_size": len(str(memory)),
        "session_id": session.get("_id", "unknown")
    }
    
    return jsonify(debug_info)

@bp.get("/debug/files")
def debug_files():
    """Debug endpoint to see file storage details"""
    from .helpers import ensure_memory
    memory = ensure_memory()
    files = memory.get("files", {})
    
    file_details = []
    for file_name, file_info in files.items():
        file_details.append({
            "name": file_name,
            "type": file_info["type"],
            "content_length": len(file_info["content"]),
            "content_preview": file_info["content"][:200] + "..." if len(file_info["content"]) > 200 else file_info["content"],
            "uploaded_at": file_info["uploaded_at"]
        })
    
    return jsonify({"files": file_details, "total_files": len(files)})

@bp.get("/debug/apis")
def debug_apis():
    """Debug endpoint to see stored API data"""
    from .helpers import load_global_memory
    global_memory = load_global_memory()
    apis = global_memory.get("apis", {})
    
    api_details = []
    for api_key, api_info in apis.items():
        api_details.append({
            "key": api_key,
            "url": api_info["url"],
            "fetched_at": api_info["fetched_at"],
            "api_key_provided": api_info["api_key_provided"],
            "data_type": type(api_info["data"]).__name__,
            "data_preview": str(api_info["data"])[:500] + "..." if len(str(api_info["data"])) > 500 else str(api_info["data"])
        })
    
    return jsonify({"apis": api_details, "total_apis": len(apis)})

@bp.get("/debug/global-memory")
def debug_global_memory():
    """Debug endpoint to see the complete global memory structure"""
    from .helpers import load_global_memory
    global_memory = load_global_memory()
    
    memory_summary = {
        "total_keys": len(global_memory.keys()),
        "keys": list(global_memory.keys()),
        "files_count": len(global_memory.get("files", {})),
        "apis_count": len(global_memory.get("apis", {})),
        "lessons_count": len(global_memory.get("lessons", [])),
        "memory_size": len(str(global_memory))
    }
    
    return jsonify(memory_summary)

@bp.get("/test-session")
def test_session():
    """Test if Flask sessions are working"""
    if "test_counter" not in session:
        session["test_counter"] = 0
    
    session["test_counter"] += 1
    session.modified = True
    
    return jsonify({
        "counter": session["test_counter"],
        "session_id": session.get("_id", "unknown"),
        "session_keys": list(session.keys())
    })

@bp.get("/test-file-extraction")
def test_file_extraction():
    """Test file content extraction manually"""
    from .helpers import extract_file_content_to_memory, ensure_memory
    
    # Test with an existing PDF file
    test_file = "static/uploads/2e4980452e0b4d91bd05e2d675f39ccd.pdf"
    
    if not os.path.exists(test_file):
        return jsonify({"error": "Test file not found"})
    
    # Extract content
    result = extract_file_content_to_memory(test_file)
    
    # Check memory
    memory = ensure_memory()
    
    return jsonify({
        "extraction_result": result,
        "memory_state": {
            "files_count": len(memory.get("files", {})),
            "file_names": list(memory.get("files", {}).keys()) if "files" in memory else [],
            "memory_keys": list(memory.keys())
        }
    })

@bp.get("/test-context")
def test_context():
    """Test endpoint to debug context retrieval"""
    from .helpers import get_file_context_for_question, get_api_context_for_question, get_memory_context
    
    test_question = "What is Swadesi Way?"
    
    memory_context = get_memory_context()
    file_context = get_file_context_for_question(test_question)
    api_context = get_api_context_for_question(test_question)
    
    return jsonify({
        "test_question": test_question,
        "memory_context_length": len(memory_context) if memory_context else 0,
        "memory_context_preview": memory_context[:500] if memory_context else "None",
        "file_context_length": len(file_context) if file_context else 0,
        "file_context_preview": file_context[:500] if file_context else "None",
        "api_context_length": len(api_context) if api_context else 0,
        "api_context_preview": api_context[:500] if api_context else "None"
    })

@bp.get("/test-messages")
def test_messages():
    """Test endpoint to see what messages would be sent to the AI"""
    from .helpers import build_ollama_content
    from .config import SYSTEM_PROMPT
    
    test_question = "What is Swadesi Way?"
    
    messages = build_ollama_content(test_question, None, SYSTEM_PROMPT)
    
    message_details = []
    for i, msg in enumerate(messages):
        message_details.append({
            "role": msg["role"],
            "content_length": len(msg["content"]),
            "content_preview": msg["content"][:500] + "..." if len(msg["content"]) > 500 else msg["content"]
        })
    
    return jsonify({
        "test_question": test_question,
        "total_messages": len(messages),
        "messages": message_details
    })
