import ollama
from .config import OLLAMA_MODEL
from .helpers import get_memory_context, get_file_context_for_question, get_api_context_for_question

class LangChainClient:
    def __init__(self):
        self.model = OLLAMA_MODEL
        self.available = True
        try:
            ollama.list()
        except:
            self.available = False
    
    def generate_response(self, user_message, chat_history=None, image_url=None):
        if not self.available:
            return "Ollama client not available"
        
        try:
            context = f"{get_memory_context()}{get_file_context_for_question(user_message)}{get_api_context_for_question(user_message)}"
            
            messages = []
            if context:
                messages.append({"role": "system", "content": f"You are Neuro-Core, an advanced AI assistant. Context: {context}"})
            else:
                messages.append({"role": "system", "content": "You are Neuro-Core, an advanced AI assistant."})
            
            if chat_history:
                for msg in chat_history[-5:]:  # Last 5 messages for context
                    messages.append(msg)
            
            messages.append({"role": "user", "content": user_message})
            
            response = ollama.chat(model=self.model, messages=messages)
            return response['message']['content']
        except Exception as e:
            return f"Error: {str(e)}"
    
    def generate_streaming_response(self, user_message, chat_history=None, image_url=None):
        if not self.available:
            yield "Ollama client not available"
            return
        
        try:
            context = f"{get_memory_context()}{get_file_context_for_question(user_message)}{get_api_context_for_question(user_message)}"
            
            messages = []
            if context:
                messages.append({"role": "system", "content": f"You are Neuro-Core, an advanced AI assistant. Context: {context}"})
            else:
                messages.append({"role": "system", "content": "You are Neuro-Core, an advanced AI assistant."})
            
            if chat_history:
                for msg in chat_history[-5:]:
                    messages.append(msg)
            
            messages.append({"role": "user", "content": user_message})
            
            for chunk in ollama.chat(model=self.model, messages=messages, stream=True):
                yield chunk['message']['content']
        except Exception as e:
            yield f"Error: {str(e)}"

    def generate_title(self, chat_history):
        if not self.available:
            return "New Chat"
        
        try:
            # Create a summary prompt
            messages = []
            messages.append({"role": "system", "content": "You are a specialized title generator. Your task is to create a concise, professional, and descriptive title (max 5 words) for a chat conversation. \nRules:\n1. Output ONLY the title text.\n2. Do NOT use quotes, markdown, or special characters.\n3. Keep it under 5 words.\n4. Focus on the main topic or intent.\n5. Do not include 'Title:' or 'Subject:'."})
            
            # Focus mainly on the first user message as it usually sets the topic
            first_user_msg = next((msg['content'] for msg in chat_history if msg['role'] == 'user'), "")
            if not first_user_msg:
                return "New Chat"

            # Add a bit of context from the response if available, but keep it short
            first_ai_msg = next((msg['content'] for msg in chat_history if msg['role'] == 'assistant'), "")
            context_str = f"User: {first_user_msg[:200]}\nAI: {first_ai_msg[:100]}"
            
            messages.append({"role": "user", "content": f"Generate a title for this conversation:\n\n{context_str}"})
            
            response = ollama.chat(model=self.model, messages=messages)
            title = response['message']['content'].strip()
            
            # Aggressive cleaning
            import re
            # Remove any markdown headers or bolding
            title = re.sub(r'[#*`]', '', title)
            # Remove common prefixes
            title = re.sub(r'^(Title|Subject|Topic|Here is):?\s*', '', title, flags=re.IGNORECASE)
            # Remove quotes
            title = title.strip('"\'')
            # Truncate if still too long (fallback)
            if len(title) > 50:
                title = title[:47] + "..."
            
            return title
        except Exception as e:
            print(f"Error generating title: {e}")
            return "New Chat"

langchain_client = LangChainClient()