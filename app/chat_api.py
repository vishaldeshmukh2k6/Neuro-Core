import uuid
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from .models import db, Chat, Message
from .auth import auth_manager
from .langchain_client import langchain_client
from .config import OLLAMA_MODEL

chat_api_bp = Blueprint('chat_api', __name__)

def get_user_id():
    """Get user_id from session, create guest ID if needed"""
    if 'user_id' not in session:
        if auth_manager.is_authenticated():
            user = auth_manager.get_current_user()
            session['user_id'] = user['id']
        else:
            # Create a formal guest user
            auth_manager.create_guest_user()
            
    return session['user_id']



def validate_chat_ownership(chat_id, user_id):
    """Validate that user owns the chat"""
    chat = Chat.query.filter_by(id=chat_id, user_id=user_id).first()
    return chat is not None

@chat_api_bp.route('/start_chat', methods=['POST'])
def start_chat():
    """Create a new chat and return chat_id"""
    user_id = get_user_id()
    
    chat_id = str(uuid.uuid4())
    chat = Chat(
        id=chat_id,
        user_id=user_id,
        name="New Chat",
        created=datetime.utcnow(),
        updated=datetime.utcnow()
    )
    
    db.session.add(chat)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'chat_id': chat_id,
        'message': 'Chat created successfully'
    })

@chat_api_bp.route('/chat/<chat_id>/message', methods=['POST'])
def save_message(chat_id):
    """Save a message to specific chat"""
    user_id = get_user_id()
    
    if not validate_chat_ownership(chat_id, user_id):
        return jsonify({'error': 'Chat not found or access denied'}), 404
    
    data = request.get_json()
    role = data.get('role')  # 'user' or 'assistant'
    content = data.get('content')
    image_url = data.get('image_url')
    
    if not role or not content:
        return jsonify({'error': 'Role and content required'}), 400
    
    message = Message(
        chat_id=chat_id,
        role=role,
        content=content,
        image_url=image_url,
        timestamp=datetime.utcnow()
    )
    
    db.session.add(message)
    
    # Update chat timestamp
    chat = Chat.query.get(chat_id)
    chat.updated = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message_id': message.id
    })

@chat_api_bp.route('/chat/<chat_id>/history', methods=['GET'])
def get_chat_history(chat_id):
    """Get chat history for specific chat"""
    user_id = get_user_id()
    
    if not validate_chat_ownership(chat_id, user_id):
        return jsonify({'error': 'Chat not found or access denied'}), 404
    
    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
    
    history = []
    for msg in messages:
        history.append({
            'id': msg.id,
            'role': msg.role,
            'content': msg.content,
            'image_url': msg.image_url,
            'timestamp': msg.timestamp.isoformat()
        })
    
    return jsonify({
        'success': True,
        'chat_id': chat_id,
        'history': history
    })

@chat_api_bp.route('/chats', methods=['GET'])
def get_user_chats():
    """Get all chats for current user (excluding datetime-named chats)"""
    user_id = get_user_id()
    
    chats = Chat.query.filter_by(user_id=user_id).order_by(Chat.updated.desc()).all()
    
    chat_list = []
    for chat in chats:
        # Hide chats with datetime pattern names (e.g., "Chat 12/14 11:59")
        import re
        datetime_pattern = r'^Chat \d{1,2}/\d{1,2} \d{1,2}:\d{2}$'
        
        if not re.match(datetime_pattern, chat.name):
            chat_list.append({
                'id': chat.id,
                'name': chat.name,
                'created': chat.created.isoformat(),
                'updated': chat.updated.isoformat()
            })
    
    return jsonify({
        'success': True,
        'chats': chat_list
    })

@chat_api_bp.route('/chat/<chat_id>', methods=['PUT'])
def update_chat(chat_id):
    """Update chat details (name, etc.)"""
    user_id = get_user_id()
    
    if not validate_chat_ownership(chat_id, user_id):
        return jsonify({'error': 'Chat not found or access denied'}), 404
    
    data = request.get_json()
    chat = Chat.query.get(chat_id)
    
    if 'name' in data:
        chat.name = data['name']
    
    chat.updated = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Chat updated successfully'
    })

@chat_api_bp.route('/chat/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    """Delete a chat and all its messages"""
    user_id = get_user_id()
    
    if not validate_chat_ownership(chat_id, user_id):
        return jsonify({'error': 'Chat not found or access denied'}), 404
    
    # Delete messages first
    Message.query.filter_by(chat_id=chat_id).delete()
    
    # Delete chat
    Chat.query.filter_by(id=chat_id, user_id=user_id).delete()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Chat deleted successfully'
    })

@chat_api_bp.route('/chat/<chat_id>/clear', methods=['POST'])
def clear_chat_history(chat_id):
    """Clear all messages from a chat but keep the chat"""
    user_id = get_user_id()
    
    if not validate_chat_ownership(chat_id, user_id):
        return jsonify({'error': 'Chat not found or access denied'}), 404
    
    Message.query.filter_by(chat_id=chat_id).delete()
    
    # Update chat timestamp
    chat = Chat.query.get(chat_id)
    chat.updated = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Chat history cleared'
    })

@chat_api_bp.route('/chat/<chat_id>/generate_title', methods=['POST'])
def generate_title(chat_id):
    """Generate a title for the chat using AI"""
    user_id = get_user_id()
    
    if not validate_chat_ownership(chat_id, user_id):
        return jsonify({'error': 'Chat not found or access denied'}), 404
    
    # Get chat history
    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
    if not messages:
        return jsonify({'success': False, 'error': 'No messages to generate title from'})
    
    history = [{'role': msg.role, 'content': msg.content} for msg in messages]
    
    # Generate title
    new_title = langchain_client.generate_title(history)
    
    # Update chat
    chat = Chat.query.get(chat_id)
    chat.name = new_title
    db.session.commit()
    
    return jsonify({
        'success': True,
        'title': new_title
    })

