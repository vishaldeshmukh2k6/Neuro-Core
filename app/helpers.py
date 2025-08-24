import os, json
import requests
from urllib.parse import urlparse
from flask import request, session, current_app
from .pdf_utils import extract_pdf_text
from .config import UPLOAD_DIR
from datetime import datetime

# Global memory storage that persists across sessions
GLOBAL_MEMORY_FILE = os.path.join(UPLOAD_DIR, "global_memory.json")

def load_global_memory():
    """Load global memory from file"""
    try:
        if os.path.exists(GLOBAL_MEMORY_FILE):
            with open(GLOBAL_MEMORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading global memory: {e}")
    return {}

def save_global_memory(memory_data):
    """Save global memory to file"""
    try:
        with open(GLOBAL_MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(memory_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving global memory: {e}")

def ensure_history():
    if "history" not in session:
        session["history"] = []
    return session["history"]

def ensure_memory():
    """Ensure user memory exists in session and global storage"""
    # First check global memory
    global_memory = load_global_memory()
    
    # Then check session memory
    if "memory" not in session:
        session["memory"] = {}
    
    # Merge global memory with session memory
    merged_memory = {**global_memory, **session["memory"]}
    
    # Update session with merged memory
    session["memory"] = merged_memory
    session.modified = True
    
    return merged_memory

def update_memory(key: str, value: str):
    """Update user memory with new information"""
    print(f"DEBUG: update_memory called with key: {key}, value length: {len(value)}")
    
    # Update both global and session memory
    global_memory = load_global_memory()
    global_memory[key] = value
    save_global_memory(global_memory)
    
    # Also update session memory
    memory = ensure_memory()
    memory[key] = value
    session["memory"] = memory
    session.modified = True
    
    print(f"DEBUG: Updated global and session memory, keys: {list(memory.keys())}")
    return memory

def get_memory_context():
    """Get formatted memory context for AI"""
    memory = ensure_memory()
    if not memory:
        return ""
    
    context_parts = []
    for key, value in memory.items():
        if key != "files":  # Don't include files in general memory context
            context_parts.append(f"{key}: {value}")
    
    if context_parts:
        return f"[User Information: {', '.join(context_parts)}]\n\n"
    return ""

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

def extract_file_content_to_memory(file_path: str):
    """Extract content from file and store in memory"""
    try:
        print(f"DEBUG: Starting file extraction for {file_path}")
        print(f"DEBUG: File exists: {os.path.exists(file_path)}")
        print(f"DEBUG: File size: {os.path.getsize(file_path) if os.path.exists(file_path) else 'N/A'}")
        
        if file_path.lower().endswith('.pdf'):
            print(f"DEBUG: Processing PDF file")
            pdf_text = extract_pdf_text(file_path)
            print(f"DEBUG: PDF text length: {len(pdf_text)}")
            print(f"DEBUG: PDF text preview: {pdf_text[:100]}...")
            
            # Store the full PDF content in global memory
            global_memory = load_global_memory()
            if "files" not in global_memory:
                global_memory["files"] = {}
            
            file_name = os.path.basename(file_path)
            global_memory["files"][file_name] = {
                "type": "pdf",
                "content": pdf_text,
                "uploaded_at": str(datetime.now())
            }
            
            # Save to global storage
            save_global_memory(global_memory)
            print(f"DEBUG: Stored file {file_name} in global memory")
            
            # Also update session memory
            memory = ensure_memory()
            memory["files"] = global_memory["files"]
            session["memory"] = memory
            session.modified = True
            
            print(f"DEBUG: Memory updated in session and global storage")
            
            # Verify storage
            verify_memory = ensure_memory()
            print(f"DEBUG: Verification - files in memory: {list(verify_memory.get('files', {}).keys())}")
            
            return f"Successfully read and stored PDF content: {file_name}"
        else:
            print(f"DEBUG: Processing text file")
            # For other file types, try to read as text
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"DEBUG: Text content length: {len(content)}")
                
                # Store in global memory
                global_memory = load_global_memory()
                if "files" not in global_memory:
                    global_memory["files"] = {}
                
                file_name = os.path.basename(file_path)
                global_memory["files"][file_name] = {
                    "type": "text",
                    "content": content,
                    "uploaded_at": str(datetime.now())
                }
                
                save_global_memory(global_memory)
                
                # Update session memory
                memory = ensure_memory()
                memory["files"] = global_memory["files"]
                session["memory"] = memory
                session.modified = True
                
                return f"Successfully read and stored text content: {file_name}"
    except Exception as e:
        print(f"DEBUG: Error in extract_file_content_to_memory: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Error reading file: {str(e)}"

def get_file_context_for_question(question: str):
    """Get relevant file content based on the question"""
    # Use global memory for file content
    global_memory = load_global_memory()
    if "files" not in global_memory or not global_memory["files"]:
        print(f"DEBUG: No files found in global memory")
        return ""
    
    print(f"DEBUG: Found {len(global_memory['files'])} files in global memory")
    
    relevant_content = []
    question_lower = question.lower()
    
    for file_name, file_info in global_memory["files"].items():
        content = file_info["content"]
        print(f"DEBUG: Processing file: {file_name}, content length: {len(content)}")
        
        # Always include file content, but prioritize based on relevance
        if any(keyword in question_lower for keyword in content.lower().split()[:200]):
            # High relevance - include more content
            relevant_content.append(f"[Highly Relevant Content from {file_name}]:\n{content[:3000]}...")
            print(f"DEBUG: High relevance match for {file_name}")
        else:
            # Lower relevance but still include for context
            relevant_content.append(f"[Available Content from {file_name}]:\n{content[:1500]}...")
            print(f"DEBUG: Including {file_name} with lower relevance")
    
    if relevant_content:
        result = "\n\n".join(relevant_content)
        print(f"DEBUG: Returning file context with {len(result)} characters")
        return result
    else:
        print(f"DEBUG: No file context generated")
        return ""

def build_ollama_content(user_msg: str, image_url: str | None = None, system_prompt: str | None = None) -> list:
    messages = []
    
    print(f"DEBUG: build_ollama_content called with message: {user_msg[:100]}...")
    
    # Start with the base system prompt
    enhanced_prompt = system_prompt or ""
    
    # Add only the most relevant context, not everything
    relevant_contexts = []
    
    # Add file context if relevant to the question
    file_context = get_file_context_for_question(user_msg)
    if file_context:
        relevant_contexts.append(file_context)
        print(f"DEBUG: Added file context: {len(file_context)} chars")
    
    # Add API context if relevant to the question
    api_context = get_api_context_for_question(user_msg)
    if api_context:
        relevant_contexts.append(api_context)
        print(f"DEBUG: Added API context: {len(api_context)} chars")
    
    # Add memory context only if it's not too long
    memory_context = get_memory_context()
    if memory_context and len(memory_context) < 1000:  # Only add if memory is small
        relevant_contexts.append(memory_context)
        print(f"DEBUG: Added memory context: {len(memory_context)} chars")
    
    # Combine all relevant contexts
    if relevant_contexts:
        combined_context = "\n\n".join(relevant_contexts)
        enhanced_prompt += f"\n\n{combined_context}"
        enhanced_prompt += "\n\nIMPORTANT: Use the above stored data to answer the user's question accurately. If the answer is in the stored data, provide it. If not, use your general knowledge."
        print(f"DEBUG: Added combined context: {len(combined_context)} chars")
    
    print(f"DEBUG: Final enhanced prompt length: {len(enhanced_prompt)}")
    
    if enhanced_prompt:
        messages.append({"role": "system", "content": enhanced_prompt})

    # Add user message
    messages.append({"role": "user", "content": user_msg})
    
    print(f"DEBUG: Final messages structure: {len(messages)} messages")
    for i, msg in enumerate(messages):
        print(f"DEBUG: Message {i}: role={msg['role']}, content_length={len(msg['content'])}")
    
    return messages

def teach_ai(lesson: str):
    """Teach the AI new information"""
    memory = ensure_memory()
    if "lessons" not in memory:
        memory["lessons"] = []
    
    memory["lessons"].append(lesson)
    session["memory"] = memory
    session.modified = True
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
    """Fetch data from an API and return the response"""
    try:
        print(f"DEBUG: Fetching data from API: {api_url}")
        
        # Prepare headers
        request_headers = {
            'User-Agent': 'Neuro-Core AI Assistant/1.0',
            'Accept': 'application/json'
        }
        
        if headers:
            request_headers.update(headers)
        
        if api_key:
            request_headers['Authorization'] = f'Bearer {api_key}'
        
        # Make the API request
        response = requests.get(api_url, headers=request_headers, timeout=30)
        response.raise_for_status()
        
        # Try to parse JSON response
        try:
            data = response.json()
            print(f"DEBUG: Successfully fetched JSON data from API")
            return {
                'success': True,
                'data': data,
                'status_code': response.status_code,
                'content_type': response.headers.get('content-type', 'unknown')
            }
        except json.JSONDecodeError:
            # If not JSON, return text content
            text_data = response.text
            print(f"DEBUG: API returned text data, length: {len(text_data)}")
            return {
                'success': True,
                'data': text_data,
                'status_code': response.status_code,
                'content_type': 'text/plain'
            }
            
    except requests.exceptions.RequestException as e:
        print(f"DEBUG: API request failed: {str(e)}")
        return {
            'success': False,
            'error': f"API request failed: {str(e)}",
            'status_code': getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
        }
    except Exception as e:
        print(f"DEBUG: Unexpected error fetching API data: {str(e)}")
        return {
            'success': False,
            'error': f"Unexpected error: {str(e)}"
        }

def store_api_data(api_url: str, api_data: dict, api_key: str = None):
    """Store API data in global memory"""
    try:
        print(f"DEBUG: Storing API data from: {api_url}")
        
        global_memory = load_global_memory()
        if "apis" not in global_memory:
            global_memory["apis"] = {}
        
        # Create a unique key for this API
        api_key_name = f"api_{len(global_memory.get('apis', {})) + 1}"
        
        global_memory["apis"][api_key_name] = {
            "url": api_url,
            "data": api_data,
            "fetched_at": str(datetime.now()),
            "api_key_provided": bool(api_key)
        }
        
        # Save to global storage
        save_global_memory(global_memory)
        print(f"DEBUG: Successfully stored API data in global memory")
        
        # Also update session memory
        memory = ensure_memory()
        memory["apis"] = global_memory["apis"]
        session["memory"] = memory
        session.modified = True
        
        return f"Successfully fetched and stored data from API: {api_url}"
        
    except Exception as e:
        print(f"DEBUG: Error storing API data: {str(e)}")
        return f"Error storing API data: {str(e)}"

def get_api_context_for_question(question: str):
    """Get relevant API data based on the question"""
    # Use global memory for file content
    global_memory = load_global_memory()
    if "apis" not in global_memory or not global_memory["apis"]:
        print(f"DEBUG: No APIs found in global memory")
        return ""
    
    print(f"DEBUG: Found {len(global_memory['apis'])} APIs in global memory")
    
    relevant_content = []
    question_lower = question.lower()
    
    for api_key, api_info in global_memory["apis"].items():
        api_data = api_info["data"]
        api_url = api_info["url"]
        print(f"DEBUG: Processing API: {api_key}, URL: {api_url}")
        
        # Convert API data to string for searching
        if isinstance(api_data, dict):
            data_str = json.dumps(api_data, ensure_ascii=False)
        elif isinstance(api_data, str):
            data_str = api_data
        else:
            data_str = str(api_data)
        
        print(f"DEBUG: API data length: {len(data_str)}")
        
        # Always include API data, but prioritize based on relevance
        if any(keyword in question_lower for keyword in data_str.lower().split()[:200]):
            # High relevance - include more content
            relevant_content.append(f"[Highly Relevant API Data from {api_url}]:\n{data_str[:3000]}...")
            print(f"DEBUG: High relevance match for {api_key}")
        else:
            # Lower relevance but still include for context
            relevant_content.append(f"[Available API Data from {api_url}]:\n{data_str[:1500]}...")
            print(f"DEBUG: Including {api_key} with lower relevance")
    
    if relevant_content:
        result = "\n\n".join(relevant_content)
        print(f"DEBUG: Returning API context with {len(result)} characters")
        return result
    else:
        print(f"DEBUG: No API context generated")
        return ""

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
