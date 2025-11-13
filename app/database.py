import sqlite3
import os
from datetime import datetime
from .config import UPLOAD_DIR

DATABASE_PATH = os.path.join(UPLOAD_DIR, 'users.db')

def init_database():
    """Initialize the database and create tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            mobile TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Create user_sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # Create user_memory table for storing AI memory per user
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            memory_key TEXT NOT NULL,
            memory_value TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            UNIQUE(user_id, memory_key)
        )
    ''')
    

    
    conn.commit()
    conn.close()

class UserDatabase:
    def __init__(self):
        init_database()
    
    def get_connection(self):
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    
    def create_user(self, user_id, username, email, mobile, password_hash):
        """Create a new user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (user_id, username, email, mobile, password_hash)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, email, mobile, password_hash))
            
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def get_user_by_email(self, email):
        """Get user by email"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE email = ? AND is_active = 1', (email,))
        user = cursor.fetchone()
        conn.close()
        
        return dict(user) if user else None
    
    def get_user_by_id(self, user_id):
        """Get user by user_id"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ? AND is_active = 1', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        return dict(user) if user else None
    
    def update_last_login(self, user_id):
        """Update user's last login timestamp"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET last_login = CURRENT_TIMESTAMP 
            WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
    
    def get_all_users(self):
        """Get all active users (admin function)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, username, email, mobile, created_at, last_login 
            FROM users WHERE is_active = 1 
            ORDER BY created_at DESC
        ''')
        
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return users
    
    def delete_user(self, user_id):
        """Soft delete user (set is_active to 0)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE users SET is_active = 0 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
    
    def save_user_memory(self, user_id, memory_key, memory_value):
        """Save user-specific memory"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_memory (user_id, memory_key, memory_value, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, memory_key, memory_value))
        
        conn.commit()
        conn.close()
    
    def get_user_memory(self, user_id):
        """Get all memory for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT memory_key, memory_value FROM user_memory 
            WHERE user_id = ? ORDER BY updated_at DESC
        ''', (user_id,))
        
        memory = {row['memory_key']: row['memory_value'] for row in cursor.fetchall()}
        conn.close()
        
        return memory
    


# Global database instance
user_db = UserDatabase()