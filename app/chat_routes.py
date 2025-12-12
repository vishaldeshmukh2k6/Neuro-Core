from flask import Blueprint, request, jsonify
from app.models import db, Chat, Message
from datetime import datetime

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/api/chats', methods=['GET'])
def get_chats():
    chats = Chat.query.order_by(Chat.updated.desc()).all()
    return jsonify([chat.to_dict() for chat in chats])

@chat_bp.route('/api/chats', methods=['POST'])
def create_chat():
    data = request.get_json()
    chat = Chat(
        id=data['id'],
        name=data['name']
    )
    db.session.add(chat)
    db.session.commit()
    return jsonify(chat.to_dict())

@chat_bp.route('/api/chats/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    return jsonify(chat.to_dict())

@chat_bp.route('/api/chats/<chat_id>', methods=['PUT'])
def update_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    data = request.get_json()
    
    if 'name' in data:
        chat.name = data['name']
    
    chat.updated = datetime.utcnow()
    db.session.commit()
    return jsonify(chat.to_dict())

@chat_bp.route('/api/chats/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    db.session.delete(chat)
    db.session.commit()
    return jsonify({'success': True})

@chat_bp.route('/api/chats/<chat_id>/messages', methods=['POST'])
def add_message(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    data = request.get_json()
    
    message = Message(
        chat_id=chat_id,
        role=data['role'],
        content=data['content'],
        image_url=data.get('image_url')
    )
    
    db.session.add(message)
    chat.updated = datetime.utcnow()
    db.session.commit()
    
    return jsonify(message.to_dict())