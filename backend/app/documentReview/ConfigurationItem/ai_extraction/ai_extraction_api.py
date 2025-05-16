"""
AI需求提取相关API路由
"""
from flask import Blueprint, request, jsonify
import logging
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from .extractor import ai_extract_requirements
from .utils import get_config

ai_extraction_bp = Blueprint('ai_extraction', __name__)

@ai_extraction_bp.route('/ai_extract', methods=['POST'])
def ai_extract_requirements_api():
    """
    AI需求提取接口
    使用AI技术提取需求详情
    接收：file_id, file_name, [model]
    返回：提取的需求详情
    """
    try:
        data = request.json
        file_id = data.get('file_id')
        original_file_name_from_request = data.get('file_name') # This is the original filename
        model = data.get('model')
        
        if not original_file_name_from_request:
            logging.error(f"AI Extraction: 'file_name' is missing in the request. file_id='{file_id}'")
            return jsonify({'success': False, 'error': "'file_name' is required."}), 400

        # Apply secure_filename to the received filename to match the on-disk version
        secured_request_filename = secure_filename(original_file_name_from_request)
        if not secured_request_filename:
            # This might happen if secure_filename removes all characters (e.g. if filename was just '..')
            logging.error(f"AI Extraction: secure_filename resulted in empty string for '{original_file_name_from_request}'. file_id='{file_id}'")
            return jsonify({'success': False, 'error': 'Invalid file_name resulting in empty secure name.'}), 400

        # Determine the base upload folder, consistent with upload_api.py's potential default
        default_base_uploads = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'uploads')
        base_upload_folder = get_config().get('UPLOAD_FOLDER', default_base_uploads)
        
        # Target the 'configuration_item' subfolder
        config_item_upload_folder = os.path.join(base_upload_folder, 'configuration_item')
        
        # Construct the expected filename as saved by upload_api.py
        expected_filename_on_disk = f"{file_id}_{secured_request_filename}"
        file_path = os.path.join(config_item_upload_folder, expected_filename_on_disk)
        
        logging.info(f"AI Extraction: Attempting to access file at: {file_path}")

        if not os.path.exists(file_path):
            logging.error(f"AI Extraction: File not found at {file_path}. Original request filename='{original_file_name_from_request}', secured='{secured_request_filename}', file_id='{file_id}'")
            return jsonify({'success': False, 'error': f'File not found on server. Path: {file_path}'}), 404

        logging.info(f"正在使用AI提取文档需求: {original_file_name_from_request} ({file_id}) from path {file_path}")
        session_id = str(uuid.uuid4())
        requirements_data = ai_extract_requirements(file_path, model)
        requirements = []
        if isinstance(requirements_data, list):
            for req in requirements_data:
                if isinstance(req, dict):
                    name = req.get("name", req.get("title", ""))
                    chapter = req.get("chapter", req.get("chapter_number", ""))
                    content = req.get("content", "")
                    if isinstance(content, dict):
                        content_str = ""
                        if 'b' in content:
                            content_str += content['b'] + "\n\n"
                        if 'c' in content:
                            content_str += f"进入条件: {content['c']}\n\n"
                        if 'd' in content:
                            content_str += f"输入: {content['d']}\n\n"
                        if 'e' in content:
                            content_str += f"输出: {content['e']}\n\n"
                        if 'f' in content:
                            content_str += f"处理: {content['f']}\n\n"
                        if 'g' in content:
                            content_str += f"性能: {content['g']}\n\n"
                        if 'h' in content:
                            content_str += f"约束与限制: {content['h']}"
                    elif isinstance(content, str):
                        content_str = content
                    else:
                        content_str = str(content)
                    if not content_str.strip():
                        content_str = f"需求: {name}" if name else "未提取到需求内容"
                    requirements.append({
                        "name": name,
                        "chapter": chapter,
                        "content": content_str
                    })
                elif isinstance(req, str):
                    requirements.append({
                        "name": f"需求_{len(requirements)+1}",
                        "chapter": "",
                        "content": req
                    })
        if not requirements:
            logging.warning(f"没有从文件 {original_file_name_from_request} 中提取到需求")
            return jsonify({
                'success': False, 
                'error': '未提取到需求，请检查文档格式或内容'
            }), 400
        # 记录处理结果
        result_folder = os.path.join(base_upload_folder, 'results')
        os.makedirs(result_folder, exist_ok=True)
        result_path = os.path.join(result_folder, f"{session_id}.json")
        with open(result_path, 'w', encoding='utf-8') as f:
            import json
            json.dump({
                'session_id': session_id,
                'file_id': file_id,
                'file_name': original_file_name_from_request,
                'requirements': requirements,
                'timestamp': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        logging.info(f"配置项测试需求提取完成，共找到 {len(requirements)} 个需求")
        return jsonify({
            'success': True,
            'session_id': session_id,
            'requirements': requirements
        })
    except Exception as e:
        logging.exception(f"配置项测试提取需求出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
