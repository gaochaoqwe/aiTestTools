"""
AI目录提取API接口
提供AI目录提取服务的API接口
"""
import os
import logging
import json
import traceback
from flask import Blueprint, request, jsonify

from .extractor import ai_extract_catalog

# 创建Blueprint
catalog_bp = Blueprint('catalog', __name__, url_prefix='/catalog')

@catalog_bp.route('/extract', methods=['POST', 'OPTIONS'])
def catalog_extract_api():
    """
    从文档中自动提取目录的API接口
    
    请求参数:
        file_id: 文件ID
        file_name: 文件名
        requirement_level: 需求级别(3-5)
        model: 可选的AI模型名称
        
    返回:
        包含需求名称和章节号的列表
    """
    try:
        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify({"error": "未提供请求数据"}), 400
        
        # 提取必要参数
        file_id = data.get("file_id")
        file_name = data.get("file_name")
        requirement_level = int(data.get("requirement_level", 3))
        model = data.get("model")
        
        # 验证必要参数
        if not file_id or not file_name:
            return jsonify({"error": "缺少必要参数: file_id 或 file_name"}), 400
            
        # 验证需求级别范围
        if requirement_level < 3 or requirement_level > 5:
            logging.warning(f"需求级别({requirement_level})超出范围，将使用默认值3")
            requirement_level = 3
        
        # 构建文件路径 - 使用应用配置
        from flask import current_app
        # 仅对OPTIONS请求做特殊处理
        if request.method == "OPTIONS":
            headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
            return ('', 200, headers)
            
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{file_id}_{file_name}")
        # 如果文件不存在，尝试其他命名格式
        if not os.path.exists(file_path):
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{file_id}_docx")
            if not os.path.exists(file_path):
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{file_id}")
                if not os.path.exists(file_path):
                    # 尝试在uploads根目录查找
                    root_upload_folder = os.path.dirname(current_app.config['UPLOAD_FOLDER'])
                    file_path = os.path.join(root_upload_folder, f"{file_id}_{file_name}")
                    if not os.path.exists(file_path):
                        file_path = os.path.join(root_upload_folder, f"{file_id}_docx")
                        if not os.path.exists(file_path):
                            file_path = os.path.join(root_upload_folder, f"{file_id}")
        
        logging.warning(f"使用文件路径: {file_path}")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            logging.error(f"文件不存在: {file_path}")
            return jsonify({"error": f"找不到指定文件: {file_name}"}), 404
        
        # 调用AI提取目录
        logging.info(f"开始AI提取目录: 文件={file_name}, 需求级别={requirement_level}")
        requirements = ai_extract_catalog(file_path, requirement_level, model)
        
        # 返回结果
        result = {
            "success": True,
            "catalog": requirements,
            "count": len(requirements)
        }
        
        # 记录请求正常完成
        logging.info(f"AI目录提取成功，共提取 {len(requirements)} 个需求条目")
        
        return jsonify(result)
    
    except Exception as e:
        # 记录详细错误信息
        error_msg = f"AI目录提取失败: {str(e)}"
        logging.error(error_msg)
        logging.error(traceback.format_exc())
        
        # 返回错误响应
        return jsonify({"error": error_msg}), 500
