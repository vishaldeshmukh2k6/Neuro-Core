import re
import hashlib
import secrets
from flask import session
from datetime import datetime
from .database import user_db

class AuthManager:
    def __init__(self):
        pass  # Using database now
        
    def validate_email(self, email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_mobile(self, mobile):
        pattern = r'^[+]?[1-9]\d{1,14}$'
        return re.match(pattern, mobile.replace(' ', '').replace('-', '')) is not None
    
    def hash_password(self, password):
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return salt + pwd_hash.hex()
    
    def verify_password(self, password, hashed):
        salt = hashed[:32]
        stored_hash = hashed[32:]
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return pwd_hash.hex() == stored_hash
    
    def register_user(self, email, mobile, password, name):
        if not self.validate_email(email):
            return {'success': False, 'error': 'Invalid email format'}
        
        if not self.validate_mobile(mobile):
            return {'success': False, 'error': 'Invalid mobile number format'}
        
        if len(password) < 6:
            return {'success': False, 'error': 'Password must be at least 6 characters'}
        
        # Check if email already exists
        existing_user = user_db.get_user_by_email(email)
        if existing_user:
            return {'success': False, 'error': 'Email already registered'}
        
        user_id = secrets.token_hex(16)
        password_hash = self.hash_password(password)
        
        # Create user in database
        success = user_db.create_user(user_id, name, email, mobile, password_hash)
        
        if success:
            return {'success': True, 'user_id': user_id}
        else:
            return {'success': False, 'error': 'Failed to create user'}
    
    def login_user(self, email, password):
        user = user_db.get_user_by_email(email)
        if not user:
            return {'success': False, 'error': 'Email not found'}
        
        if not self.verify_password(password, user['password_hash']):
            return {'success': False, 'error': 'Invalid password'}
        
        # Update last login
        user_db.update_last_login(user['user_id'])
        
        # Set session
        session['user_id'] = user['user_id']
        session['user_email'] = user['email']
        session['user_name'] = user['username']
        
        return {'success': True, 'user': {
            'id': user['user_id'],
            'email': user['email'],
            'name': user['username']
        }}
    
    def logout_user(self):
        session.pop('user_id', None)
        session.pop('user_email', None)
        session.pop('user_name', None)
        return {'success': True}
    
    def is_authenticated(self):
        return 'user_id' in session
    
    def get_current_user(self):
        if not self.is_authenticated():
            return None
        
        return {
            'id': session.get('user_id'),
            'email': session.get('user_email'),
            'name': session.get('user_name')
        }
    


auth_manager = AuthManager()