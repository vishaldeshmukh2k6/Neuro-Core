import os, json, requests
from urllib.parse import urlparse
from flask import request, session, current_app
from .pdf_utils import extract_pdf_text
from .config import UPLOAD_DIR
from datetime import datetime
from .chat_memory import ChatMemoryManager

def get_memory_context():
    """Get formatted memory context for AI - only persistent info, not conversation topics"""
    memory = ChatMemoryManager.get_active_chat_memory()
    if not memory:
        return ""
    
    context_parts = []
    # Only include basic personal info, not conversation topics
    persistent_keys = ["name"]  # Only name persists across conversations
    
    for key, value in memory.items():
        if key in persistent_keys:
            context_parts.append(f"{key}: {value}")
    
    if context_parts:
        return f"[User Info: {', '.join(context_parts)}]\n\n"
    return ""

def update_memory(key: str, value: str):
    """Update memory for active chat"""
    return ChatMemoryManager.update_active_chat_memory(key, value)


def extract_personal_info(user_msg: str):
    """Extract personal information from user message"""
    user_msg_lower = user_msg.lower()
    
    # Extract name information
    if "mera naam" in user_msg_lower or "my name is" in user_msg_lower or "i am" in user_msg_lower:
        # Simple extraction - can be improved with regex
        if "mera naam" in user_msg_lower:
            name_start = user_msg_lower.find("mera naam") + 9
        elif "my name is" in user_msg_lower:
            name_start = user_msg_lower.find("my name is") + 11
        elif "i am" in user_msg_lower:
            name_start = user_msg_lower.find("i am") + 4
        else:
            name_start = 0
            
        if name_start > 0:
            name_part = user_msg[name_start:].strip()
            if name_part:
                # Clean up the name (remove punctuation, extra words)
                name = name_part.split()[0].strip(".,!?")
                if name and len(name) > 1:
                    update_memory("name", name)
                    return f"Nice to meet you, {name}! I'll remember your name."
    
    # Extract other personal info patterns
    if "mera age" in user_msg_lower or "my age is" in user_msg_lower:
        # Extract age
        pass
    
    return None


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


def _tokenize_query_for_json(query: str) -> list:
    q = query.lower()
    # basic tokenization: words of length >= 3
    tokens = [t.strip(".,:;!?()[]{}\"'`)\n\t ") for t in q.split()]
    tokens = [t for t in tokens if len(t) >= 3]
    return list(dict.fromkeys(tokens))


def _search_json_relevant_slices(data, query: str, max_hits: int = 6, max_chars_per_hit: int = 800):
    """Traverse JSON and pick small relevant slices based on query tokens."""
    tokens = _tokenize_query_for_json(query)
    hits = []

    def add_hit(path, snippet):
        if len(hits) >= max_hits:
            return
        try:
            text = json.dumps(snippet, ensure_ascii=False)
        except Exception:
            text = str(snippet)
        hits.append({
            "path": "/" + "/".join(map(str, path)),
            "json": (text[:max_chars_per_hit] + ("..." if len(text) > max_chars_per_hit else ""))
        })

    def traverse(node, path):
        if len(hits) >= max_hits:
            return
        # Match at dict level
        if isinstance(node, dict):
            # key or value contains token
            for k, v in node.items():
                key_match = any(t in str(k).lower() for t in tokens)
                val_str = None
                if isinstance(v, (str, int, float)):
                    val_str = str(v).lower()
                elif isinstance(v, (dict, list)):
                    # For nested, we still traverse but also check stringified for quick match
                    try:
                        val_str = json.dumps(v, ensure_ascii=False)[:3000].lower()
                    except Exception:
                        val_str = str(v).lower()
                else:
                    val_str = str(v).lower()
                val_match = any(t in val_str for t in tokens) if val_str else False
                if key_match or val_match:
                    add_hit(path + [k], v)
                traverse(v, path + [k])
        elif isinstance(node, list):
            for i, item in enumerate(node):
                if len(hits) >= max_hits:
                    break
                # Quick match on item string
                try:
                    item_str = json.dumps(item, ensure_ascii=False)[:1500].lower()
                except Exception:
                    item_str = str(item).lower()
                if any(t in item_str for t in tokens):
                    add_hit(path + [i], item)
                traverse(item, path + [i])
        else:
            # primitive
            return

    traverse(data, [])

    if not hits and isinstance(data, (dict, list)):
        # fallback: top-level preview
        add_hit([], data)
    return hits


def extract_file_content_to_memory(file_path: str):
    try:
        lower = file_path.lower()
        file_name = os.path.basename(file_path)
        
        # Get current memory for the active chat
        memory = ChatMemoryManager.get_active_chat_memory()
        if "files" not in memory:
            memory["files"] = {}
        
        file_data = {}
        if lower.endswith('.pdf'):
            pdf_text = extract_pdf_text(file_path)
            file_data = {
                "type": "pdf",
                "content": pdf_text,
                "uploaded_at": str(datetime.now())
            }
        elif lower.endswith('.json'):
            with open(file_path, 'r', encoding='utf-8') as f:
                parsed = json.load(f)
            pretty = json.dumps(parsed, ensure_ascii=False, indent=2)
            file_data = {
                "type": "json",
                "content": pretty,
                "json": parsed,
                "uploaded_at": str(datetime.now())
            }
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            file_data = {
                "type": "text",
                "content": content,
                "uploaded_at": str(datetime.now())
            }
        
        memory["files"][file_name] = file_data
        ChatMemoryManager.update_active_chat_memory("files", memory["files"])
        
        return f"Successfully read and stored {file_data['type']} content: {file_name}"
    except Exception as e:
        return f"Error reading file: {str(e)}"


def get_file_context_for_question(question: str):
    memory = ChatMemoryManager.get_active_chat_memory()
    if "files" not in memory or not memory["files"]:
        return ""
    
    relevant_content = []
    question_lower = question.lower()
    
    for file_name, file_info in memory["files"].items():
        content = file_info["content"]
        ftype = file_info.get("type")
        
        if ftype == "json" and isinstance(file_info.get("json"), (dict, list)):
            slices = _search_json_relevant_slices(file_info["json"], question_lower)
            if slices:
                for s in slices:
                    relevant_content.append(f"[Relevant JSON from {file_name} at {s['path']}]:\n{s['json']}")
            else:
                relevant_content.append(f"[Available JSON from {file_name}]:\n{content[:1500]}...")
        else:
            if any(keyword in question_lower for keyword in content.lower().split()[:200]):
                relevant_content.append(f"[Highly Relevant Content from {file_name}]:\n{content[:3000]}...")
            else:
                relevant_content.append(f"[Available Content from {file_name}]:\n{content[:1500]}...")
    
    return "\n\n".join(relevant_content) if relevant_content else ""


def build_ollama_content(user_msg: str, image_url: str | None = None, system_prompt: str | None = None) -> list:
    messages = []
    enhanced_prompt = system_prompt or ""
    
    relevant_contexts = []
    
    file_context = get_file_context_for_question(user_msg)
    if file_context:
        relevant_contexts.append(file_context)
    
    api_context = get_api_context_for_question(user_msg)
    if api_context:
        relevant_contexts.append(api_context)
    
    memory_context = get_memory_context()
    if memory_context and len(memory_context) < 1000:
        relevant_contexts.append(memory_context)
    
    if relevant_contexts:
        combined_context = "\n\n".join(relevant_contexts)
        enhanced_prompt += f"\n\n{combined_context}"
    
    if enhanced_prompt:
        messages.append({"role": "system", "content": enhanced_prompt})
    
    messages.append({"role": "user", "content": user_msg})
    
    return messages


def teach_ai(lesson: str):
    """Teach the AI new information"""
    memory = ChatMemoryManager.get_active_chat_memory()
    if "lessons" not in memory:
        memory["lessons"] = []
    
    memory["lessons"].append(lesson)
    ChatMemoryManager.update_active_chat_memory("lessons", memory["lessons"])
    return f"I've learned: {lesson}"


def extract_teaching_command(user_msg: str):
    """Extract teaching commands from user message"""
    user_msg_lower = user_msg.lower()
    
    # Check for teaching patterns
    if any(phrase in user_msg_lower for phrase in ["sikhao", "teach me", "yaad rakh", "remember this"]):
        # Extract the lesson content
        if "sikhao" in user_msg_lower:
            lesson_start = user_msg_lower.find("sikhao") + 6
        elif "teach me" in user_msg_lower:
            lesson_start = user_msg_lower.find("teach me") + 8
        elif "yaad rakh" in user_msg_lower:
            lesson_start = user_msg_lower.find("yaad rakh") + 9
        elif "remember this" in user_msg_lower:
            lesson_start = user_msg_lower.find("remember this") + 13
        else:
            lesson_start = 0
            
        if lesson_start > 0:
            lesson = user_msg[lesson_start:].strip()
            if lesson:
                return teach_ai(lesson)
    
    return None


def fetch_api_data(api_url: str, api_key: str = None, headers: dict = None):
    try:
        request_headers = {
            'User-Agent': 'Neuro-Core AI Assistant/1.0',
            'Accept': 'application/json'
        }
        
        if headers:
            request_headers.update(headers)
        
        if api_key:
            request_headers['Authorization'] = f'Bearer {api_key}'
        
        response = requests.get(api_url, headers=request_headers, timeout=30)
        response.raise_for_status()
        
        try:
            data = response.json()
            return {
                'success': True,
                'data': data,
                'status_code': response.status_code,
                'content_type': response.headers.get('content-type', 'unknown')
            }
        except json.JSONDecodeError:
            text_data = response.text
            return {
                'success': True,
                'data': text_data,
                'status_code': response.status_code,
                'content_type': 'text/plain'
            }
            
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f"API request failed: {str(e)}",
            'status_code': getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"Unexpected error: {str(e)}"
        }


def store_api_data(api_url: str, api_data: dict, api_key: str = None):
    try:
        memory = ChatMemoryManager.get_active_chat_memory()
        if "apis" not in memory:
            memory["apis"] = {}
        
        api_key_name = f"api_{len(memory.get('apis', {})) + 1}"
        
        memory["apis"][api_key_name] = {
            "url": api_url,
            "data": api_data,
            "fetched_at": str(datetime.now()),
            "api_key_provided": bool(api_key)
        }
        
        ChatMemoryManager.update_active_chat_memory("apis", memory["apis"])
        
        return f"Successfully fetched and stored data from API: {api_url}"
        
    except Exception as e:
        return f"Error storing API data: {str(e)}"


def get_api_context_for_question(question: str):
    memory = ChatMemoryManager.get_active_chat_memory()
    if "apis" not in memory or not memory["apis"]:
        return ""
    
    relevant_content = []
    question_lower = question.lower()
    
    for api_key, api_info in memory["apis"].items():
        api_data = api_info["data"]
        api_url = api_info["url"]
        
        if isinstance(api_data, (dict, list)):
            slices = _search_json_relevant_slices(api_data, question_lower)
            if slices:
                for s in slices:
                    relevant_content.append(f"[Relevant API JSON from {api_url} at {s['path']}]:\n{s['json']}")
            else:
                preview = json.dumps(api_data, ensure_ascii=False)[:1500]
                relevant_content.append(f"[Available API JSON from {api_url}]:\n{preview}...")
        else:
            data_str = str(api_data)
            if any(keyword in question_lower for keyword in data_str.lower().split()[:200]):
                relevant_content.append(f"[Highly Relevant API Data from {api_url}]:\n{data_str[:3000]}...")
            else:
                relevant_content.append(f"[Available API Data from {api_url}]:\n{data_str[:1500]}...")
    
    return "\n\n".join(relevant_content) if relevant_content else ""


def extract_api_command(user_msg: str):
    """Extract API commands from user message"""
    user_msg_lower = user_msg.lower()
    
    # Check for API patterns
    api_patterns = [
        "api fetch", "fetch api", "api data", "get api", "call api",
        "api call", "fetch data", "get data from", "api endpoint"
    ]
    
    if any(pattern in user_msg_lower for pattern in api_patterns):
        # Extract the API URL
        # Look for URLs in the message
        words = user_msg.split()
        for word in words:
            if word.startswith(('http://', 'https://', 'www.')):
                return word.strip('.,!?')
        
        # If no URL found, ask for one
        return "URL_NOT_FOUND"
    
    return None
