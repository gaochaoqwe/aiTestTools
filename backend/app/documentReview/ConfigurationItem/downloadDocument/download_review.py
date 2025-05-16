"""
需求审查文档下载接口
"""
import os
from flask import Blueprint, send_file, abort

download_review_bp = Blueprint('download_review', __name__)

@download_review_bp.route('/api/download_review/<doc_id>', methods=['GET'])
def download_review_document(doc_id):
    """
    下载生成的审查文档（Excel或TXT）
    """
    outputs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../outputs'))
    # 查找以doc_id为标识的文件
    for ext in ('.xlsx', '.txt', '.json'):
        file_path = os.path.join(outputs_dir, f"requirement_review_{doc_id}{ext}")
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
    abort(404, description="未找到对应的审查文档")
