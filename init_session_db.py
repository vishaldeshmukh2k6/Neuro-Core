#!/usr/bin/env python3
"""Initialize session database tables"""

from app import create_app
from app.models import db

def init_db():
    app = create_app()
    with app.app_context():
        db.create_all()
        print("✅ Session database tables created successfully")

if __name__ == "__main__":
    init_db()