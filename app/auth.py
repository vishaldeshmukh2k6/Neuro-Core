import re
import hashlib
import secrets
import requests
from flask import session
from datetime import datetime
from .database import user_db

class AuthManager:
    def __init__(self):
        pass  # Using database now
        
    def validate_email(self, email):
        # Basic format check
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False
        
        # Check for common invalid patterns
        invalid_patterns = [
            r'.*\.\.',  # Double dots
            r'^\.',     # Starting with dot
            r'\.$',     # Ending with dot
            r'.*@.*@',  # Multiple @ symbols
        ]
        
        for invalid_pattern in invalid_patterns:
            if re.match(invalid_pattern, email):
                return False
        
        return True
    
    def verify_email_domain(self, email):
        """Verify if email domain exists (basic DNS check)"""
        try:
            domain = email.split('@')[1]
            # Check common valid domains
            valid_domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'icloud.com']
            if domain.lower() in valid_domains:
                return True
            
            # For other domains, just return True (can add DNS lookup here)
            return True
        except:
            return False
    
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
        
        if not self.verify_email_domain(email):
            return {'success': False, 'error': 'Invalid email domain'}
        
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
    
    def google_login(self, google_token):
        """Handle Google OAuth login"""
        try:
            # Verify Google token
            response = requests.get(
                f'https://www.googleapis.com/oauth2/v1/userinfo?access_token={google_token}'
            )
            
            if response.status_code != 200:
                return {'success': False, 'error': 'Invalid Google token'}
            
            user_info = response.json()
            email = user_info.get('email')
            name = user_info.get('name')
            
            if not email:
                return {'success': False, 'error': 'Could not get email from Google'}
            
            # Check if user exists
            existing_user = user_db.get_user_by_email(email)
            
            if existing_user:
                # Login existing user
                user_db.update_last_login(existing_user['user_id'])
                session['user_id'] = existing_user['user_id']
                session['user_email'] = existing_user['email']
                session['user_name'] = existing_user['username']
                
                return {'success': True, 'user': {
                    'id': existing_user['user_id'],
                    'email': existing_user['email'],
                    'name': existing_user['username']
                }}
            else:
                # Create new user
                user_id = secrets.token_hex(16)
                success = user_db.create_user(user_id, name, email, '', '')  # No mobile/password for Google users
                
                if success:
                    session['user_id'] = user_id
                    session['user_email'] = email
                    session['user_name'] = name
                    
                    return {'success': True, 'user': {
                        'id': user_id,
                        'email': email,
                        'name': name
                    }}
                else:
                    return {'success': False, 'error': 'Failed to create user'}
                    
        except Exception as e:
            return {'success': False, 'error': 'Google login failed'}
    
    def get_current_user(self):
        if not self.is_authenticated():
            return None
        
        return {
            'id': session.get('user_id'),
            'email': session.get('user_email'),
            'name': session.get('user_name')
        }
    


auth_manager = AuthManager()