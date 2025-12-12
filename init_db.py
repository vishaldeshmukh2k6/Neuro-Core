#!/usr/bin/env python3
"""
Database initialization script for Neuro-Core AI Assistant
Run this script to create all required database tables
"""

import os
import sys
from app import create_app
from app.models import db

def init_database():
    """Initialize the database with all tables"""
    app = create_app()
    
    with app.app_context():
        # Drop all tables (if they exist)
        db.drop_all()
        print("🗑️  Dropped existing tables")
        
        # Create all tables
        db.create_all()
        print("✅ Created all database tables")
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"📋 Created tables: {', '.join(tables)}")

if __name__ == "__main__":
    init_database()
    print("🎉 Database initialization complete!")