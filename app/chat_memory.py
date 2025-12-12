from flask import session
from .session_manager import ChatSessionManager
from .models import db, Message

class ChatMemoryManager:
    @staticmethod
    def get_active_chat_memory():
        user_id = session.get('user_id', 'guest')
        active_chat_id = ChatSessionManager.get_active_chat_id(user_id)
        if not active_chat_id:
            return {}
        chat_session = ChatSessionManager.get_chat_session(active_chat_id, user_id)
        return chat_session.get('memory', {})
    
    @staticmethod
    def update_active_chat_memory(key, value):
        user_id = session.get('user_id', 'guest')
        active_chat_id = ChatSessionManager.get_active_chat_id(user_id)
        if not active_chat_id:
            return {}
        
        chat_session = ChatSessionManager.get_chat_session(active_chat_id, user_id)
        if 'memory' not in chat_session:
            chat_session['memory'] = {}
        
        chat_session['memory'][key] = value
        ChatSessionManager.update_chat_session(active_chat_id, chat_session, user_id)
        return chat_session['memory']
    
    @staticmethod
    def get_active_chat_history():
        user_id = session.get('user_id', 'guest')
        active_chat_id = ChatSessionManager.get_active_chat_id(user_id)
        if not active_chat_id:
            return []
        
        # Get from database first
        messages = Message.query.filter_by(chat_id=active_chat_id).order_by(Message.timestamp).all()
        if messages:
            return [{
                'role': msg.role,
                'content': msg.content,
                'image_url': msg.image_url,
                'timestamp': msg.timestamp.isoformat()
            } for msg in messages]
        
        # Fallback to session storage
        chat_session = ChatSessionManager.get_chat_session(active_chat_id, user_id)
        return chat_session.get('history', [])
    
    @staticmethod
    def add_to_active_chat_history(message):
        user_id = session.get('user_id', 'guest')
        active_chat_id = ChatSessionManager.get_active_chat_id(user_id)
        
        # Always create a new chat if none exists
        if not active_chat_id:
            active_chat_id, _ = ChatSessionManager.create_new_chat(user_id)
        
        # Store in database
        try:
            db_message = Message(
                chat_id=active_chat_id,
                role=message['role'],
                content=message['content'],
                image_url=message.get('image_url')
            )
            db.session.add(db_message)
            db.session.commit()
        except Exception as e:
            print(f"Error saving message to DB: {e}")
            db.session.rollback()
        
        # Also store in session as backup
        chat_session = ChatSessionManager.get_chat_session(active_chat_id, user_id)
        if 'history' not in chat_session:
            chat_session['history'] = []
        
        chat_session['history'].append(message)
        ChatSessionManager.update_chat_session(active_chat_id, chat_session, user_id)
        return chat_session['history']
    
    @staticmethod
    def clear_active_chat_history():
        user_id = session.get('user_id', 'guest')
        active_chat_id = ChatSessionManager.get_active_chat_id(user_id)
        if not active_chat_id:
            return []
        
        # Clear from database
        try:
            Message.query.filter_by(chat_id=active_chat_id).delete()
            db.session.commit()
        except Exception as e:
            print(f"Error clearing messages from DB: {e}")
            db.session.rollback()
        
        # Clear from session
        chat_session = ChatSessionManager.get_chat_session(active_chat_id, user_id)
        chat_session['history'] = []
        ChatSessionManager.update_chat_session(active_chat_id, chat_session, user_id)
        return []