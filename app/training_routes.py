from flask import Blueprint, request, jsonify, session
from .ai_trainer import ai_trainer
from .models import db

training_bp = Blueprint('training', __name__)

@training_bp.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Submit feedback on AI response"""
    data = request.get_json()
    message_id = data.get('message_id')
    feedback_type = data.get('type')  # 'positive', 'negative'
    user_input = data.get('user_input')
    ai_response = data.get('ai_response')
    
    ai_trainer.record_feedback(message_id, feedback_type, user_input, ai_response)
    
    return jsonify({'success': True, 'message': 'Feedback recorded'})

@training_bp.route('/api/train', methods=['POST'])
def add_training_data():
    """Add training example"""
    data = request.get_json()
    user_input = data.get('user_input')
    ai_response = data.get('ai_response')
    expected_response = data.get('expected_response')
    category = data.get('category', 'general')
    
    ai_trainer.add_training_example(user_input, ai_response, expected_response, category)
    
    return jsonify({'success': True, 'message': 'Training data added'})

@training_bp.route('/api/training-stats', methods=['GET'])
def get_training_stats():
    """Get training statistics"""
    from .models import TrainingData, UserFeedback
    
    training_count = TrainingData.query.count()
    feedback_count = UserFeedback.query.count()
    positive_feedback = UserFeedback.query.filter_by(feedback_type='positive').count()
    
    return jsonify({
        'training_examples': training_count,
        'total_feedback': feedback_count,
        'positive_feedback': positive_feedback,
        'success_rate': round((positive_feedback / feedback_count * 100) if feedback_count > 0 else 0, 1)
    })