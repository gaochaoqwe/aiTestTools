import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

# Allowed extensions for upload
ALLOWED_EXTENSIONS = {'doc', 'docx'}

upload_bp = Blueprint('upload', __name__)

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    File upload endpoint.
    Receives a requirement document from the frontend, saves it, and returns a file ID.
    """
    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    if not upload_folder:
        # Default fallback if not set
        upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'uploads', 'configuration_item')
        os.makedirs(upload_folder, exist_ok=True)
    
    # Check if file part is present
    if 'file' not in request.files:
        return jsonify({"error": "没有上传文件"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "没有选择文件"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "不支持的文件类型"}), 400
    filename = secure_filename(file.filename)
    file_id = str(uuid.uuid4())
    file_path = os.path.join(upload_folder, f"{file_id}_{filename}")
    file.save(file_path)
    return jsonify({
        "message": "文件上传成功",
        "file_id": file_id,
        "file_name": filename,
        "file_path": file_path
    })
