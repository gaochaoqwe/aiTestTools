"""
模型验证相关API路由
"""
from flask import Blueprint, request, jsonify, make_response
from app.documentReview.ConfigurationItem.review.review_validate import validate_model

validate_bp = Blueprint('validate', __name__)

@validate_bp.route('/api/validate_model', methods=['POST'])
def validate_model_api():
    """
    验证当前配置的模型是否可用
    返回验证结果
    """
    if request.method == 'OPTIONS':
        return make_response('', 200)
    try:
        result = validate_model()
        return jsonify({'success': True, 'response': result})
    except Exception as e:
        return jsonify({'success': False, 'error': f'模型验证失败: {str(e)}'})
