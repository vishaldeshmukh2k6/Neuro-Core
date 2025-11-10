from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from .config import OLLAMA_MODEL
from .helpers import get_memory_context, get_file_context_for_question, get_api_context_for_question

class LangChainClient:
    def __init__(self):
        self.llm = ChatOllama(
            model=OLLAMA_MODEL,
            base_url="http://localhost:11434",
            temperature=0.7
        )
        
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an AI assistant with memory and learning capabilities.

Context Information:
{memory_context}
{file_context}
{api_context}

Previous conversation:
{chat_history}

Current question: {question}"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
        
        self.chain = self.prompt_template | self.llm | StrOutputParser()
    
    def generate_response(self, user_message, chat_history=None, image_url=None):
        try:
            context_info = {
                "memory_context": get_memory_context() or "",
                "file_context": get_file_context_for_question(user_message) or "",
                "api_context": get_api_context_for_question(user_message) or "",
                "question": user_message,
                "chat_history": chat_history or []
            }
            
            return self.chain.invoke(context_info)
            
        except Exception as e:
            return f"Error processing request: {str(e)}"
    

    
    def generate_streaming_response(self, user_message, chat_history=None, image_url=None):
        try:
            context_info = {
                "memory_context": get_memory_context() or "",
                "file_context": get_file_context_for_question(user_message) or "",
                "api_context": get_api_context_for_question(user_message) or "",
                "question": user_message,
                "chat_history": chat_history or []
            }
            
            for chunk in self.chain.stream(context_info):
                yield chunk
                
        except Exception as e:
            yield f"Error: {str(e)}"

# Global instance
langchain_client = LangChainClient() 