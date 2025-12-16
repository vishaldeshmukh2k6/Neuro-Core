import uuid
from datetime import datetime
from flask import Blueprint, session, request, jsonify
from .models import db, Chat

session_bp = Blueprint('session_manager', __name__)

class ChatSessionManager:
    @staticmethod
    def get_user_session_key(user_id=None):
        return f"user_{user_id or session.get('user_id', 'guest')}"
    
    @staticmethod
    def get_chat_session_key(chat_id, user_id=None):
        return f"{ChatSessionManager.get_user_session_key(user_id)}_chat_{chat_id}"
    
    @staticmethod
    def create_new_chat(user_id=None, chat_name=None):
        user_id = user_id or session.get('user_id', 'guest')
        chat_id = str(uuid.uuid4())
        chat_name = chat_name or f"Chat {datetime.now().strftime('%m/%d %H:%M')}"
        
        chat = Chat(id=chat_id, user_id=user_id, name=chat_name)
        db.session.add(chat)
        db.session.commit()
        
        chat_key = ChatSessionManager.get_chat_session_key(chat_id, user_id)
        session[chat_key] = {
            'chat_id': chat_id,
            'history': [],
            'memory': {},
            'user_id': user_id
        }
        
        user_key = ChatSessionManager.get_user_session_key(user_id)
        if user_key not in session:
            session[user_key] = {}
        session[user_key]['active_chat_id'] = chat_id
        session.modified = True
        
        return chat_id, chat_name
    
    @staticmethod
    def get_active_chat_id(user_id=None):
        user_key = ChatSessionManager.get_user_session_key(user_id)
        return session.get(user_key, {}).get('active_chat_id')
    
    @staticmethod
    def set_active_chat(chat_id, user_id=None):
        user_key = ChatSessionManager.get_user_session_key(user_id)
        if user_key not in session:
            session[user_key] = {}
        session[user_key]['active_chat_id'] = chat_id
        session.modified = True
    
    @staticmethod
    def get_chat_session(chat_id, user_id=None):
        chat_key = ChatSessionManager.get_chat_session_key(chat_id, user_id)
        return session.get(chat_key, {})
    
    @staticmethod
    def update_chat_session(chat_id, data, user_id=None):
        chat_key = ChatSessionManager.get_chat_session_key(chat_id, user_id)
        if chat_key not in session:
            session[chat_key] = {}
        session[chat_key].update(data)
        session.modified = True
    
    @staticmethod
    def get_user_chats(user_id=None):
        user_id = user_id or session.get('user_id', 'guest')
        chats = Chat.query.filter_by(user_id=user_id).order_by(Chat.updated.desc()).all()
        
        return [{
            'id': chat.id,
            'name': chat.name,
            'is_active': chat.id == ChatSessionManager.get_active_chat_id(user_id)
        } for chat in chats]
    
    @staticmethod
    def delete_chat(chat_id, user_id=None):
        chat = Chat.query.get(chat_id)
        if chat:
            db.session.delete(chat)
            db.session.commit()
        
        chat_key = ChatSessionManager.get_chat_session_key(chat_id, user_id)
        if chat_key in session:
            del session[chat_key]
        
        if ChatSessionManager.get_active_chat_id(user_id) == chat_id:
            user_key = ChatSessionManager.get_user_session_key(user_id)
            if user_key in session:
                session[user_key]['active_chat_id'] = None
        
        session.modified = True
    
    @staticmethod
    def clear_active_chat(user_id=None):
        """Clear the active chat ID to force new chat creation"""
        user_key = ChatSessionManager.get_user_session_key(user_id)
        if user_key not in session:
            session[user_key] = {}
        session[user_key]['active_chat_id'] = None
        session.modified = True

# API Routes
@session_bp.route('/api/chats/new', methods=['POST'])
def create_new_chat():
    data = request.get_json() or {}
    user_id = session.get('user_id', 'guest')
    chat_id, chat_name = ChatSessionManager.create_new_chat(user_id, data.get('name'))
    return jsonify({'success': True, 'chat_id': chat_id, 'chat_name': chat_name})

@session_bp.route('/api/chats/list', methods=['GET'])
def list_user_chats():
    user_id = session.get('user_id', 'guest')
    return jsonify({
        'success': True,
        'chats': ChatSessionManager.get_user_chats(user_id),
        'active_chat_id': ChatSessionManager.get_active_chat_id(user_id)
    })

@session_bp.route('/api/chats/<chat_id>/activate', methods=['POST'])
def activate_chat(chat_id):
    ChatSessionManager.set_active_chat(chat_id, session.get('user_id', 'guest'))
    return jsonify({'success': True, 'active_chat_id': chat_id})

@session_bp.route('/api/chats/<chat_id>/delete', methods=['DELETE'])
def delete_chat(chat_id):
    ChatSessionManager.delete_chat(chat_id, session.get('user_id', 'guest'))
    return jsonify({'success': True})

@session_bp.route('/api/chats/<chat_id>/history', methods=['GET'])
def get_chat_history(chat_id):
    chat_session = ChatSessionManager.get_chat_session(chat_id, session.get('user_id', 'guest'))
    return jsonify({
        'success': True,
        'history': chat_session.get('history', []),
        'memory': chat_session.get('memory', {})
    })