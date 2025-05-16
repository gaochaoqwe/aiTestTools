"""
需求审查相关API路由
"""
from flask import Blueprint, request, jsonify, make_response
import logging
import traceback
from app.documentReview.ConfigurationItem.review.review_logic import review_requirements, generate_review_document
from app.documentReview.ConfigurationItem.review.review_validate import validate_model

review_bp = Blueprint('review', __name__)

@review_bp.route('/api/review_requirements', methods=['POST', 'OPTIONS'])
def review_requirements_api():
    """
    需求审查API端点
    对提取的需求进行AI评估和审查
    返回需求审查结果
    """
    logger = logging.getLogger(__name__)
    if request.method == "OPTIONS":
        return make_response('', 200)
    try:
        data = request.json
        requirements = data.get('requirements', [])
        session_id = data.get('session_id', '')
        review_results = review_requirements(requirements)
        session_data = {
            'requirements': requirements,
            'review_results': review_results
        }
        # 假设 save_session_data 已在主入口注册
        from app.documentReview.ConfigurationItem.api import save_session_data
        save_session_data(session_id, session_data)
        response_data = {
            "message": "需求审查完成",
            "review_results": review_results,
            "session_id": session_id
        }
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"需求审查时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"需求审查时出错: {str(e)}"}), 500


    """
    生成需求审查文档API
    生成需求审查结果的导出文档
    """
    if request.method == "OPTIONS":
        return make_response('', 200)
    try:
        data = request.json
        logging.debug(f"生成审查文档接收到的参数: {data}")
        review_results = data.get("review_results")
        session_id = data.get("session_id")
        output_folder = None
        if session_id:
            from app.documentReview.ConfigurationItem.api import get_session_data
            session_data = get_session_data(session_id)
            review_results = session_data.get("review_results", [])
        from app.documentReview.ConfigurationItem.api import app
        output_folder = app.config['OUTPUT_FOLDER']
        result = generate_review_document(review_results, output_folder)
        file_name = result.get("file_name", "")
        doc_id = file_name.replace("requirement_review_", "").replace(".txt", "")
        response_data = {
            "success": True,
            "file_id": doc_id,
            "message": result.get("message", "审查文档生成成功")
        }
        logging.debug(f"生成审查文档成功: {response_data}")
        return jsonify(response_data)
    except Exception as e:
        logging.error(f"生成审查文档时出错: {str(e)}", exc_info=True)
        return jsonify({"error": f"生成审查文档时出错: {str(e)}"}), 500
