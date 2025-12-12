import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from flask import session
from .models import db, TrainingData, UserFeedback

class AITrainer:
    def __init__(self):
        self.training_data_file = "static/uploads/training_data.json"
        self.feedback_file = "static/uploads/feedback_data.json"
        
    def add_training_example(self, user_input: str, ai_response: str, 
                           expected_response: str = None, category: str = "general"):
        """Add a training example to improve AI responses"""
        training_entry = TrainingData(
            user_input=user_input,
            ai_response=ai_response,
            expected_response=expected_response,
            category=category,
            user_id=session.get('user_id', 'guest'),
            created_at=datetime.utcnow()
        )
        db.session.add(training_entry)
        db.session.commit()
        
        # Also store in JSON for quick access
        self._save_to_json_file(self.training_data_file, {
            'user_input': user_input,
            'ai_response': ai_response,
            'expected_response': expected_response,
            'category': category,
            'timestamp': datetime.now().isoformat()
        })
        
    def record_feedback(self, message_id: str, feedback_type: str, 
                       user_input: str, ai_response: str):
        """Record user feedback on AI responses"""
        feedback = UserFeedback(
            message_id=message_id,
            feedback_type=feedback_type,  # 'positive', 'negative', 'correction'
            user_input=user_input,
            ai_response=ai_response,
            user_id=session.get('user_id', 'guest'),
            created_at=datetime.utcnow()
        )
        db.session.add(feedback)
        db.session.commit()
        
    def get_training_context(self, user_input: str, limit: int = 5) -> str:
        """Get relevant training examples for context"""
        # Get similar training examples
        examples = TrainingData.query.filter(
            TrainingData.user_input.contains(user_input[:20])
        ).limit(limit).all()
        
        if not examples:
            return ""
            
        context = "Previous successful interactions:\n"
        for example in examples:
            if example.expected_response:
                context += f"User: {example.user_input}\n"
                context += f"Good Response: {example.expected_response}\n\n"
                
        return context
        
    def get_enhanced_system_prompt(self, base_prompt: str) -> str:
        """Enhance system prompt with learned behaviors"""
        # Get positive feedback patterns
        positive_feedback = UserFeedback.query.filter_by(
            feedback_type='positive'
        ).limit(10).all()
        
        enhancements = []
        if positive_feedback:
            enhancements.append("Based on user preferences, focus on:")
            for feedback in positive_feedback[:3]:
                enhancements.append(f"- Responses similar to: '{feedback.ai_response[:100]}...'")
                
        # Get negative feedback to avoid
        negative_feedback = UserFeedback.query.filter_by(
            feedback_type='negative'
        ).limit(5).all()
        
        if negative_feedback:
            enhancements.append("\nAvoid response patterns like:")
            for feedback in negative_feedback[:2]:
                enhancements.append(f"- '{feedback.ai_response[:100]}...'")
                
        enhancement_text = "\n".join(enhancements) if enhancements else ""
        
        return f"{base_prompt}\n\n{enhancement_text}"
        
    def _save_to_json_file(self, filename: str, data: dict):
        """Save data to JSON file for quick access"""
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        existing_data = []
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    existing_data = json.load(f)
            except:
                existing_data = []
                
        existing_data.append(data)
        
        # Keep only last 1000 entries
        if len(existing_data) > 1000:
            existing_data = existing_data[-1000:]
            
        with open(filename, 'w') as f:
            json.dump(existing_data, f, indent=2)

# Global trainer instance
ai_trainer = AITrainer()