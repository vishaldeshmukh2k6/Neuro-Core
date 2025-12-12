import pytest
import json
from app import create_app
from app.models import db, Chat, Message

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_start_chat(client):
    """Test creating a new chat"""
    response = client.post('/start_chat')
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['success'] == True
    assert 'chat_id' in data
    assert len(data['chat_id']) > 0

def test_save_message(client):
    """Test saving messages to chat"""
    # Create chat first
    response = client.post('/start_chat')
    chat_data = json.loads(response.data)
    chat_id = chat_data['chat_id']
    
    # Save user message
    response = client.post(f'/chat/{chat_id}/message', 
                          json={'role': 'user', 'content': 'Hello'})
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['success'] == True
    assert 'message_id' in data

def test_get_chat_history(client):
    """Test retrieving chat history"""
    # Create chat and add messages
    response = client.post('/start_chat')
    chat_data = json.loads(response.data)
    chat_id = chat_data['chat_id']
    
    # Add messages
    client.post(f'/chat/{chat_id}/message', 
               json={'role': 'user', 'content': 'Hello'})
    client.post(f'/chat/{chat_id}/message', 
               json={'role': 'assistant', 'content': 'Hi there!'})
    
    # Get history
    response = client.get(f'/chat/{chat_id}/history')
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['success'] == True
    assert len(data['history']) == 2
    assert data['history'][0]['role'] == 'user'
    assert data['history'][1]['role'] == 'assistant'

def test_get_user_chats(client):
    """Test getting all user chats"""
    # Create multiple chats
    client.post('/start_chat')
    client.post('/start_chat')
    
    response = client.get('/chats')
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['success'] == True
    assert len(data['chats']) == 2

def test_delete_chat(client):
    """Test deleting a chat"""
    # Create chat
    response = client.post('/start_chat')
    chat_data = json.loads(response.data)
    chat_id = chat_data['chat_id']
    
    # Delete chat
    response = client.delete(f'/chat/{chat_id}')
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['success'] == True

def test_clear_chat_history(client):
    """Test clearing chat messages"""
    # Create chat and add message
    response = client.post('/start_chat')
    chat_data = json.loads(response.data)
    chat_id = chat_data['chat_id']
    
    client.post(f'/chat/{chat_id}/message', 
               json={'role': 'user', 'content': 'Hello'})
    
    # Clear history
    response = client.post(f'/chat/{chat_id}/clear')
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['success'] == True
    
    # Verify history is empty
    response = client.get(f'/chat/{chat_id}/history')
    data = json.loads(response.data)
    assert len(data['history']) == 0

def test_chat_ownership_validation(client):
    """Test that users can only access their own chats"""
    # This would require proper session management in tests
    # For now, just test that invalid chat_id returns 404
    response = client.get('/chat/invalid-id/history')
    assert response.status_code == 404