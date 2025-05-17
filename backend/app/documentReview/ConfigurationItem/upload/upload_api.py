"""
文件上传API，仅保留/upload接口
"""
from flask import Blueprint, request, jsonify, current_app
import os
import uuid
from werkzeug.utils import secure_filename
import logging
import json

ALLOWED_EXTENSIONS = {'doc', 'docx'}

upload_bp = Blueprint('upload', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    文件上传接口
    """
    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    if not upload_folder:
        # 修正为项目根目录下 uploads/configuration_item
        project_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
        upload_folder = os.path.join(project_root, 'uploads', 'configuration_item')
        os.makedirs(upload_folder, exist_ok=True)
    
    # Use current_app's logger if available, otherwise default to root logger
    logger = current_app.logger if hasattr(current_app, 'logger') else logging.getLogger()
    logger.info("--- UPLOAD_API: Entered upload_file function ---")
    print("--- UPLOAD_API: Entered upload_file function ---", flush=True)

    if 'file' not in request.files:
        logger.error("--- UPLOAD_API: 'file' not in request.files ---")
        print("--- UPLOAD_API: 'file' not in request.files ---", flush=True)
        return jsonify({"error": "没有上传文件"}), 400
    file = request.files['file']
    if file.filename == '':
        logger.error("--- UPLOAD_API: file.filename is empty ---")
        print("--- UPLOAD_API: file.filename is empty ---", flush=True)
        return jsonify({"error": "没有选择文件"}), 400
    if not allowed_file(file.filename):
        logger.error(f"--- UPLOAD_API: File type not allowed for {file.filename} ---")
        print(f"--- UPLOAD_API: File type not allowed for {file.filename} ---", flush=True)
        return jsonify({"error": "不支持的文件类型"}), 400
    
    file_id = str(uuid.uuid4())
    original_filename = file.filename
    filename = secure_filename(original_filename)
    ext = os.path.splitext(original_filename)[-1]  # 包含点，如'.docx'
    # 如果secure_filename结果为空或仅为扩展名，则用file_id+原始扩展名
    if not filename or filename == ext.lstrip('.') or filename == ext:
        filename_on_disk = f"{file_id}{ext}"
    else:
        filename_on_disk = f"{file_id}_{filename}"
    file_path = os.path.join(upload_folder, filename_on_disk)

    logger.info(f"--- UPLOAD_API: Attempting to save to: {file_path} ---")
    print(f"--- UPLOAD_API: Attempting to save to: {file_path} ---", flush=True)
    try:
        file.save(file_path)
        logger.info(f"--- UPLOAD_API: File saved successfully to {file_path} ---")
        print(f"--- UPLOAD_API: File saved successfully to {file_path} ---", flush=True)
    except Exception as e:
        logger.exception(f"--- UPLOAD_API: Error saving file to {file_path} ---")
        print(f"--- UPLOAD_API: Error saving file: {e} ---", flush=True)
        return jsonify({"error": f"保存文件失败: {str(e)}"}), 500

    # Detailed logging before returning
    logger.info(f"[UPLOAD_API_DEBUG] Original filename from werkzeug: {original_filename}")
    logger.info(f"[UPLOAD_API_DEBUG] Secured filename: {filename}")
    logger.info(f"[UPLOAD_API_DEBUG] File ID created: {file_id}")
    logger.info(f"[UPLOAD_API_DEBUG] File actually saved as: {filename_on_disk}")
    logger.info(f"[UPLOAD_API_DEBUG] Full file path on disk: {file_path}")
    print(f"[UPLOAD_API_DEBUG] Original filename from werkzeug: {original_filename}", flush=True)
    print(f"[UPLOAD_API_DEBUG] Secured filename: {filename}", flush=True)
    print(f"[UPLOAD_API_DEBUG] File ID created: {file_id}", flush=True)
    print(f"[UPLOAD_API_DEBUG] File actually saved as: {filename_on_disk}", flush=True)
    print(f"[UPLOAD_API_DEBUG] Full file path on disk: {file_path}", flush=True)

    response_data = {
        "message": "文件上传成功",
        "file_id": file_id,
        "file_name": original_filename,  # 返回原始名
        "file_path": file_path
    }
    logger.info(f"[UPLOAD_API_DEBUG] Returning JSON: {response_data}")
    print(f"[UPLOAD_API_DEBUG] Returning JSON: {json.dumps(response_data, ensure_ascii=False)}", flush=True)

    return jsonify(response_data)
