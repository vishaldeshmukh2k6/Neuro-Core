import re
import hashlib
import secrets
import uuid
from flask import session
from datetime import datetime
from .models import db, User

class AuthManager:
    def __init__(self):
        pass
        
    def validate_email(self, email):
        # Basic format check
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
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
            return True
        except:
            return False
    
    def validate_mobile(self, mobile):
        if not mobile: return True
        pattern = r'^[+]?[1-9]\d{1,14}$'
        return re.match(pattern, mobile.replace(' ', '').replace('-', '')) is not None
    
    def hash_password(self, password):
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return salt + pwd_hash.hex()
    
    def verify_password(self, password, hashed):
        if not hashed: return False
        try:
            salt = hashed[:32]
            stored_hash = hashed[32:]
            pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return pwd_hash.hex() == stored_hash
        except:
            return False
    
    def register_user(self, email, mobile, password, name):
        if not self.validate_email(email):
            return {'success': False, 'error': 'Invalid email format'}
        
        if len(password) < 6:
            return {'success': False, 'error': 'Password must be at least 6 characters'}
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return {'success': False, 'error': 'Email already registered'}
        
        user_id = str(uuid.uuid4())
        password_hash = self.hash_password(password)
        
        new_user = User(
            id=user_id,
            username=name,
            email=email,
            mobile=mobile,
            password_hash=password_hash,
            is_guest=False
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            return {'success': True, 'user_id': user_id}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Failed to create user: {str(e)}'}
    
    def login_user(self, email, password):
        user = User.query.filter_by(email=email).first()
        if not user:
            return {'success': False, 'error': 'Email not found'}
        
        if not self.verify_password(password, user.password_hash):
            return {'success': False, 'error': 'Invalid password'}
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Set session
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['user_name'] = user.username
        session['is_guest'] = False
        
        return {'success': True, 'user': user.to_dict()}
    
    def create_guest_user(self):
        """Create a temporary guest user"""
        user_id = f"guest_{uuid.uuid4().hex[:8]}"
        
        # We don't necessarily need to save guests to DB unless we want to track them
        # But to be consistent, let's save them with a flag
        guest_user = User(
            id=user_id,
            username="Guest",
            email=f"{user_id}@guest.local", # Dummy email
            password_hash="",
            is_guest=True
        )
        
        try:
            db.session.add(guest_user)
            db.session.commit()
            
            session['user_id'] = user_id
            session['user_name'] = "Guest"
            session['is_guest'] = True
            
            return user_id
        except Exception as e:
            print(f"Error creating guest: {e}")
            # Fallback to just session
            session['user_id'] = user_id
            return user_id

    def logout_user(self):
        session.clear()
        return {'success': True}
    
    def is_authenticated(self):
        return 'user_id' in session
    
    def get_current_user(self):
        if not self.is_authenticated():
            return None
        
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        if user:
            return user.to_dict()
        
        # Fallback for session-only guests
        return {
            'id': user_id,
            'name': session.get('user_name', 'Guest'),
            'email': session.get('user_email'),
            'is_guest': session.get('is_guest', True)
        }

auth_manager = AuthManager()