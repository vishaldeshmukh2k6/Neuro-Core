import os, uuid, json
from flask import Blueprint, render_template, request, jsonify, session, Response, stream_with_context, redirect, url_for
from werkzeug.utils import secure_filename
from .helpers import build_ollama_content, extract_personal_info, extract_teaching_command, extract_api_command, fetch_api_data, store_api_data
from .session_manager import ChatSessionManager
from .chat_memory import ChatMemoryManager
from .openai_client import client
from .langchain_client import langchain_client
from .config import UPLOAD_DIR, SYSTEM_PROMPT, OLLAMA_MODEL
from .auth import auth_manager
from .database import user_db
from .ai_trainer import ai_trainer

bp = Blueprint("main", __name__)

@bp.route("/")
def home():
    """Landing page"""
    user = auth_manager.get_current_user()
    return render_template("home.html", user=user)

@bp.route("/chat")
def chat_interface():
    """Main chat interface"""
    user = auth_manager.get_current_user()
    active_chat_id = request.args.get('id')
    return render_template("index.html", history=[], user=user, active_chat_id=active_chat_id)

@bp.route("/auth")
def auth_page():
    return render_template("auth.html")

@bp.route("/chatbot/coming-soon")
def chatbot_coming_soon():
    return render_template("coming_soon.html")

@bp.route("/chatbot")
def chatbot_interface():
    """Chatbot interface (Coming Soon)"""
    user = auth_manager.get_current_user()
    return render_template("index.html", user=user, show_chatbot_coming_soon=True)

@bp.post("/auth/login")
def login():
    data = request.get_json()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password required'})
    
    result = auth_manager.login_user(email, password)
    return jsonify(result)

@bp.post("/auth/signup")
def signup():
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    mobile = data.get('mobile', '').strip()
    password = data.get('password', '')
    
    if not all([name, email, mobile, password]):
        return jsonify({'success': False, 'error': 'All fields are required'})
    
    result = auth_manager.register_user(email, mobile, password, name)
    return jsonify(result)

@bp.post("/auth/google")
def google_auth():
    data = request.get_json()
    credential = data.get('credential', '')
    
    if not credential:
        return jsonify({'success': False, 'error': 'Google credential required'})
    
    result = auth_manager.google_login(credential)
    return jsonify(result)

@bp.post("/auth/logout")
def logout():
    result = auth_manager.logout_user()
    return jsonify(result)

@bp.get("/user-status")
def get_user_status():
    """Get current user status"""
    user = auth_manager.get_current_user()
    return jsonify({'is_authenticated': bool(user), 'user': user})


@bp.route("/user-status")
def user_status():
    user = auth_manager.get_current_user()
    return jsonify({
        "is_authenticated": user is not None and not user.get('is_guest', False),
        "user": user
    })
@bp.post("/clear")
def clear():
    ChatMemoryManager.clear_active_chat_history()
    return jsonify({"ok": True})

@bp.post("/new-chat")
def new_chat():
    """Clear active chat to force creation of new chat on next message"""
    user_id = session.get('user_id', 'guest')
    # Clear the active chat ID to force new chat creation
    ChatSessionManager.clear_active_chat(user_id)
    return jsonify({"success": True, "message": "Ready for new chat"})

@bp.post("/upload")
def upload():
    if not auth_manager.is_authenticated():
        return jsonify({"error": "File upload requires login"}), 401
    
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
    
    from .helpers import extract_file_content_to_memory
    try:
        storage_result = extract_file_content_to_memory(dest)
    except Exception as e:
        storage_result = f"Error: {str(e)}"
    
    return jsonify({
        "url": url, 
        "storage_result": storage_result,
        "filename": name
    })


def call_openai_sync(user_msg: str, image_url: str | None = None) -> str:
    if not client:
        raise RuntimeError("AI client not configured.")
    
    messages = build_ollama_content(user_msg, image_url, SYSTEM_PROMPT)
    resp = client.chat(model=OLLAMA_MODEL, messages=messages)
    
    content = ""
    try:
        if isinstance(resp, dict):
            if "message" in resp and isinstance(resp["message"], dict):
                content = resp["message"].get("content", "")
            elif "content" in resp:
                content = resp["content"]
            elif "response" in resp:
                content = resp["response"]
        elif hasattr(resp, "message") and hasattr(resp.message, "content"):
            content = resp.message.content
        elif hasattr(resp, "content"):
            content = resp.content
        elif hasattr(resp, "response"):
            content = resp.response
    except Exception:
        content = ""
    
    if not isinstance(content, str):
        content = str(content or "")
    
    content = content.strip()
    return content or "I'm sorry, I couldn't generate a response. Please try again."

@bp.post("/chat")
def chat():
    data = request.get_json(force=True)
    user_msg = (data or {}).get("message", "").strip()
    image_url = (data or {}).get("image_url")

    if not user_msg and not image_url:
        return jsonify({"error": "empty message"}), 400

    # Add user message to history first
    ChatMemoryManager.add_to_active_chat_history({"role": "user", "content": user_msg, "image_url": image_url})
    history = ChatMemoryManager.get_active_chat_history()

    # Check for personal info, teaching commands, or API commands first
    personal_response = extract_personal_info(user_msg)
    teaching_response = extract_teaching_command(user_msg)
    api_command = extract_api_command(user_msg)
    
    if personal_response:
        reply: str = personal_response
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
            # Use LangChain for better user-friendly responses
            # Convert history to LangChain format - limit to recent context only
            chat_history = []
            recent_messages = history[-6:-1] if len(history) > 6 else history[:-1]  # Only last 5 exchanges
            for msg in recent_messages:
                if msg["role"] == "user":
                    chat_history.append({"role": "user", "content": msg["content"]})
                elif msg["role"] == "assistant":
                    chat_history.append({"role": "assistant", "content": msg["content"]})
            
            # Get enhanced system prompt with training data
            enhanced_prompt = ai_trainer.get_enhanced_system_prompt(SYSTEM_PROMPT)
            training_context = ai_trainer.get_training_context(user_msg)
            
            # Add training context to user message if available
            enhanced_user_msg = f"{training_context}\n{user_msg}" if training_context else user_msg
            
            reply = langchain_client.generate_response(enhanced_user_msg, chat_history, image_url)
        except Exception:
            try:
                reply = call_openai_sync(user_msg, image_url) if client else "AI client not configured."
            except Exception as e2:
                reply = f"AI service error: {e2}"

    # Always ensure a string reply
    if reply is None:
        reply = "I'm sorry, I couldn't generate a response. Please try again."

    ChatMemoryManager.add_to_active_chat_history({"role": "assistant", "content": reply})
    return jsonify({"reply": reply})

@bp.post("/teach")
def teach():
    """Endpoint to teach the AI new information - Login required"""
    if not auth_manager.is_authenticated():
        return jsonify({"error": "Teaching requires login"}), 401
    
    data = request.get_json(force=True)
    lesson = (data or {}).get("lesson", "").strip()
    
    if not lesson:
        return jsonify({"error": "no lesson provided"}), 400
    
    from .helpers import teach_ai
    response = teach_ai(lesson)
    return jsonify({"response": response})

@bp.get("/memory")
def get_memory():
    """Get current user memory - Login required"""
    if not auth_manager.is_authenticated():
        return jsonify({"error": "Memory access requires login"}), 401
    
    memory = ChatMemoryManager.get_active_chat_memory()
    return jsonify({"memory": memory})

@bp.post("/stream")
def stream():
    data = request.get_json(force=True)
    user_msg = (data or {}).get("message", "").strip()
    image_url = (data or {}).get("image_url")

    if not user_msg and not image_url:
        return jsonify({"error": "empty message"}), 400

    # Add user message to history first
    ChatMemoryManager.add_to_active_chat_history({"role": "user", "content": user_msg, "image_url": image_url})
    history = ChatMemoryManager.get_active_chat_history()

    # Check for personal info or teaching commands first
    personal_response = extract_personal_info(user_msg)
    teaching_response = extract_teaching_command(user_msg)
    api_command = extract_api_command(user_msg)
    
    if personal_response:
        reply = personal_response
        ChatMemoryManager.add_to_active_chat_history({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})
    elif teaching_response:
        reply = teaching_response
        ChatMemoryManager.add_to_active_chat_history({"role": "assistant", "content": reply})
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
        
        ChatMemoryManager.add_to_active_chat_history({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    if not client:
        reply = "AI client not configured."
        ChatMemoryManager.add_to_active_chat_history({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    @stream_with_context
    def ollama_stream():
        full_chunks = []
        try:
            # Use LangChain for streaming - limit to recent context only
            chat_history = []
            recent_messages = history[-6:-1] if len(history) > 6 else history[:-1]  # Only last 5 exchanges
            for msg in recent_messages:
                if msg["role"] == "user":
                    chat_history.append({"role": "user", "content": msg["content"]})
                elif msg["role"] == "assistant":
                    chat_history.append({"role": "assistant", "content": msg["content"]})
            
            for chunk in langchain_client.generate_streaming_response(user_msg, chat_history, image_url):
                full_chunks.append(chunk)
                yield f"data: {json.dumps({'delta': chunk})}\n\n"
            
            final_text = "".join(full_chunks).strip()
            ChatMemoryManager.add_to_active_chat_history({"role": "assistant", "content": final_text})
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            err = f"AI stream error: {e}"
            ChatMemoryManager.add_to_active_chat_history({"role": "assistant", "content": err})
            yield f"data: {json.dumps({'delta': err})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
    return Response(ollama_stream(), mimetype="text/event-stream")

@bp.post("/api-fetch")
def api_fetch():
    """Direct endpoint to fetch and store API data - Login required"""
    if not auth_manager.is_authenticated():
        return jsonify({"error": "API fetch requires login"}), 401
    
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
    return jsonify({"ollama_present": bool(client)})

@bp.get("/config")
def config():
    model_name = OLLAMA_MODEL
    return jsonify({"using_openai": False, "model": model_name})

@bp.post("/set-ai-model")
def set_ai_model():
    """Set the current AI model"""
    data = request.get_json()
    model = data.get('model', '').strip()
    
    if not model:
        return jsonify({"error": "Model name required"}), 400
    
    session['selected_ai_model'] = model
    return jsonify({
        "success": True, 
        "model": model,
        "message": f"Switched to {model}"
    })

@bp.get("/available-models")
def get_available_models():
    """Get list of available AI models"""
    return jsonify({
        "models": ["ollama", "openai", "gemini"],
        "current": session.get('selected_ai_model', 'ollama'),
        "total": 3
    })




@bp.get("/ollama/models")
def get_ollama_models():
    """Get installed Ollama models"""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags')
        if response.status_code == 200:
            data = response.json()
            models = []
            for model in data.get('models', []):
                models.append({
                    'name': model['name'],
                    'size': f"{model['size'] // (1024**3):.1f}GB" if model['size'] > 0 else 'Unknown',
                    'modified': model['modified_at'][:10] if 'modified_at' in model else 'Unknown'
                })
            return jsonify({'success': True, 'models': models})
        else:
            return jsonify({'success': False, 'error': 'Ollama not running'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@bp.get("/ollama/info")
def get_ollama_info():
    """Get Ollama system info"""
    try:
        import psutil
        import shutil
        import requests
        
        # Get RAM info
        ram = psutil.virtual_memory()
        total_ram = f"{ram.total // (1024**3):.1f}GB"
        
        # Get disk info
        disk = shutil.disk_usage('/')
        free_storage = f"{disk.free // (1024**3):.1f}GB"
        
        # Calculate model storage usage
        model_storage = 0
        try:
            response = requests.get('http://localhost:11434/api/tags')
            if response.status_code == 200:
                data = response.json()
                for model in data.get('models', []):
                    model_storage += model.get('size', 0)
        except:
            pass
        
        used_storage = f"{model_storage // (1024**3):.1f}GB"
        usage_percent = int((model_storage / disk.total) * 100) if disk.total > 0 else 0
        
        return jsonify({
            'success': True,
            'ram': total_ram,
            'free': free_storage,
            'used': used_storage,
            'usagePercent': usage_percent
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@bp.post("/ollama/pull")
def pull_ollama_model():
    """Pull/update Ollama model"""
    data = request.get_json()
    model = data.get('model', '').strip()
    
    if not model:
        return jsonify({'success': False, 'error': 'Model name required'})
    
    try:
        import requests
        response = requests.post('http://localhost:11434/api/pull', 
                               json={'name': model}, 
                               timeout=300)
        if response.status_code == 200:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Pull failed'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@bp.post("/ollama/remove")
def remove_ollama_model():
    """Remove Ollama model"""
    data = request.get_json()
    model = data.get('model', '').strip()
    
    if not model:
        return jsonify({'success': False, 'error': 'Model name required'})
    
    try:
        import requests
        response = requests.delete(f'http://localhost:11434/api/delete', 
                                 json={'name': model})
        if response.status_code == 200:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Remove failed'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/favicon.ico')
def favicon():
    return '', 204
