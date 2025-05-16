"""
API服务模块
提供HTTP API接口，处理前端请求
"""
import os
import tempfile
import uuid
import json
import logging
from flask import Flask, request, jsonify, send_file, make_response
from werkzeug.utils import secure_filename
from flask_cors import CORS


from app.documentReview.ConfigurationItem.requirement_extractor import (
    extract_requirements, 
    generate_requirement_excel
)

# 导入AI提取模块
from app.documentReview.ConfigurationItem.ai_extraction.extractor import ai_extract_requirements
from app.documentReview.ConfigurationItem.ai_extraction.rematcher import rematch_requirements

# 创建Flask应用
app = Flask(__name__)

# 配置CORS - 使用最简单的方式，允许任何来源的请求
CORS(app, resources={r"/*": {"origins": "*"}}, send_wildcard=True)

# 导入并注册AI目录提取Blueprint
from .ai_catalog.api import catalog_bp
app.register_blueprint(catalog_bp)

# 打印所有路由信息
logging.warning("=== 已注册的路由 ===")
for rule in app.url_map.iter_rules():
    logging.warning(f"  * {rule}")

# 记录所有请求信息
@app.before_request
def log_request_info():
    import logging
    logger = logging.getLogger(__name__)

# 测试端点，检查API是否正常工作
@app.route('/api/test', methods=['GET', 'POST'])
def test_api():
    """简单的测试接口来验证API是否正常工作"""
    import logging
    logger = logging.getLogger(__name__)
    
    if request.method == 'POST':
        if request.is_json:
            data = request.json
            return jsonify({"success": True, "message": "测试成功", "received": data})
        else:
            logger.warning("\u6536到的请求不是JSON格式")
            return jsonify({"success": False, "message": "请求不是JSON格式"})
    else:  # GET
        return jsonify({"success": True, "message": "API服务器工作正常"})

# 配置上传文件存储目录
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'uploads', 'configuration_item')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 配置输出文件存储目录
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'outputs')
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'doc', 'docx'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({"status": "ok"})

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    文件上传接口
    接收前端上传的需求文档，保存到临时目录
    返回文件ID，用于后续处理
    """
    # 检查是否有文件
    if 'file' not in request.files:
        return jsonify({"error": "没有上传文件"}), 400
    
    file = request.files['file']
    
    # 检查文件名
    if file.filename == '':
        return jsonify({"error": "没有选择文件"}), 400
    
    # 检查文件类型
    if not allowed_file(file.filename):
        return jsonify({"error": "不支持的文件类型"}), 400
    
    # 生成安全的文件名并保存
    filename = secure_filename(file.filename)
    file_id = str(uuid.uuid4())
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{filename}")
    file.save(file_path)
    
    return jsonify({
        "message": "文件上传成功",
        "file_id": file_id,
        "file_name": filename,
        "file_path": file_path
    })

# ===================== 需求候选项自动发现接口 =====================
@app.route('/api/requirement_candidates', methods=['POST', 'OPTIONS'])
def requirement_candidates_api():
    """
    自动扫描文档生成需求名称候选列表，供前端选择。
    POST参数：file_id, file_name, catalog_file_id, catalog_file_name（目录参数是必需的）
    返回：{"candidates": [{name, chapter}...]}，将需求名称和章节号一起返回
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # 处理 OPTIONS 请求
    if request.method == "OPTIONS":
        return make_response('', 200)
    
    try:
        # 获取请求体
        if not request.is_json:
            logger.error("\u6536到的请求不是JSON格式")
            return jsonify({"error": "\u8bf7求必须是JSON格式"}), 400
            
        data = request.json
        file_id = data.get('file_id')
        file_name = data.get('file_name')
        catalog_file_id = data.get('catalog_file_id')
        catalog_file_name = data.get('catalog_file_name')
        
        if not file_id or not file_name:
            logger.error(f"\u7f3a少文件参数: file_id={file_id}, file_name={file_name}")
            return jsonify({"error": "缺少文件参数"}), 400
            
        # 检查是否使用AI自动提取目录
        use_ai_catalog = data.get('use_ai_catalog', False)
        
        # 如果不是使用AI自动提取，那么还是需要目录文件
        if not use_ai_catalog and (not catalog_file_id or not catalog_file_name):
            logger.error(f"\u7f3a少目录文件参数: catalog_file_id={catalog_file_id}, catalog_file_name={catalog_file_name}")
            return jsonify({"error": "缺少目录文件参数"}), 400
            
        # 首先尝试使用完整文件名
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{file_name}")
        # 如果找不到文件，尝试其他可能的格式
        if not os.path.exists(file_path):
            # 尝试 file_id_docx 格式
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_docx")
            if not os.path.exists(file_path):
                # 尝试只用file_id
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}")
                if not os.path.exists(file_path):
                    # 尝试在uploads根目录查找
                    root_upload_folder = os.path.dirname(app.config['UPLOAD_FOLDER'])
                    file_path = os.path.join(root_upload_folder, f"{file_id}_{file_name}")
                    if not os.path.exists(file_path):
                        file_path = os.path.join(root_upload_folder, f"{file_id}_docx")
                        if not os.path.exists(file_path):
                            file_path = os.path.join(root_upload_folder, f"{file_id}")
        
        logger.warning(f"使用文件路径: {file_path}")
            
        if not os.path.exists(file_path):
            # 记录更详细的错误信息
            logger.error(f"文件不存在: {file_path}")
            logger.error(f"请求参数: file_id={file_id}, file_name={file_name}")
            logger.error(f"上传目录: {app.config['UPLOAD_FOLDER']}")
            logger.error(f"尝试列出上传目录中的文件:")
            try:
                files = os.listdir(app.config['UPLOAD_FOLDER'])
                for f in files:
                    logger.error(f"  - {f}")
            except Exception as e:
                logger.error(f"无法列出目录文件: {str(e)}")
            
            return jsonify({"error": "文件不存在 - 请确保已正确上传"}), 404
            
        # 目录文件路径处理
        catalog_file_path = None
        if not use_ai_catalog:
            # 首先尝试使用完整文件名
            catalog_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{catalog_file_id}_{catalog_file_name}")
            # 如果找不到文件，尝试其他可能的格式
            if not os.path.exists(catalog_file_path):
                catalog_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{catalog_file_id}_docx")
                if not os.path.exists(catalog_file_path):
                    # 尝试只用catalog_file_id
                    catalog_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{catalog_file_id}")
                    if not os.path.exists(catalog_file_path):
                        # 尝试在uploads根目录查找
                        root_upload_folder = os.path.dirname(app.config['UPLOAD_FOLDER'])
                        catalog_file_path = os.path.join(root_upload_folder, f"{catalog_file_id}_{catalog_file_name}")
                        if not os.path.exists(catalog_file_path):
                            catalog_file_path = os.path.join(root_upload_folder, f"{catalog_file_id}_docx")
                            if not os.path.exists(catalog_file_path):
                                catalog_file_path = os.path.join(root_upload_folder, f"{catalog_file_id}")
            
            logger.warning(f"使用目录文件路径: {catalog_file_path}")
                
            if not os.path.exists(catalog_file_path):
                logger.error(f"目录文件不存在: {catalog_file_path}")
                logger.error(f"请求参数: catalog_file_id={catalog_file_id}, catalog_file_name={catalog_file_name}")
                return jsonify({"error": "目录文件不存在 - 请确保已正确上传"}), 404
    except Exception as e:
        logger.error(f"\u5904理请求时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"处理请求时出错: {str(e)}"}), 500
            
    import uuid
    candidates = None
    
    # 根据模式选择不同的提取方法
    if use_ai_catalog:
        # 使用AI自动提取目录
        
        try:
            # 导入AI目录提取模块
            from app.documentReview.ConfigurationItem.ai_catalog.extractor import ai_extract_catalog
            
            # 处理需求级别参数
            requirement_level = data.get('requirement_level', 3)  # 默认需求级别为3
            if requirement_level < 3 or requirement_level > 5:
                requirement_level = 3
                
            logger.warning(f"使用AI自动提取目录: file_path={file_path}, requirement_level={requirement_level}")
            
            # 调用AI目录提取功能
            candidates = ai_extract_catalog(file_path, requirement_level)
            logger.warning(f"AI目录提取完成，获取到 {len(candidates) if candidates else 0} 个需求项")
            
        except Exception as e:
            logger.error(f"AI目录提取时出错: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": f"AI目录提取时出错: {str(e)}"}), 500
    else:
        # 使用传统目录文件提取
        
        try:
            # 注意：这里使用包名的绝对导入
            from app.documentReview.ConfigurationItem.document_reader import extract_requirement_candidates
            candidates = extract_requirement_candidates(file_path, catalog_file_path)
            
        except Exception as e:
            logger.error(f"目录文件提取出错: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": f"提取需求候选项时出错: {str(e)}"}), 500
    
    # 检查提取结果
    if not candidates:
        error_msg = "未成功提取到需求条目" + ("从目录文件中" if not use_ai_catalog else "通过AI分析")
        return jsonify({"error": error_msg}), 400
    
    # 创建会话ID
    session_id = str(uuid.uuid4())
    print(f"[DEBUG] 创建新的会话ID: {session_id}")
    
    return jsonify({
        "candidates": candidates,
        "session_id": session_id
    })

# ===================== 需求提取接口 =====================
@app.route('/api/extract', methods=['POST'])
def extract_requirements_api():
    """
    需求提取接口（修改版，根据用户确认的需求名称列表提取）
    接收文件ID、文件名和确认的需求名称列表，根据需求名称提取详细内容
    """
    data = request.json
    file_id = data.get('file_id')
    file_name = data.get('file_name')
    requirement_names = data.get('requirement_names', [])  # 新增参数：用户确认的需求名称列表
    catalog_file_id = data.get('catalog_file_id')  # 目录文件ID
    catalog_file_name = data.get('catalog_file_name')  # 目录文件名称
    
    print(f"[DEBUG] 提取需求请求参数: file_id={file_id}, catalog_file_id={catalog_file_id}")

    if not file_id or not file_name:
        return jsonify({"error": "缺少必要参数"}), 400

    # 构建file_path - 使用与候选项提取相同的逻辑
    # 首先尝试使用完整文件名
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{file_name}")
    # 如果不存在，再尝试只用扩展名
    if not os.path.exists(file_path):
        # 发现上传后的文件名是 file_id_docx 格式
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_docx")
    
    print(f"[DEBUG] 提取需求的文件路径: {file_path}")
    if not os.path.exists(file_path):
        return jsonify({"error": "文件不存在 - 请确保文件已正确上传"}), 404

    # 构建catalog_file_path
    catalog_file_path = None
    if catalog_file_id and catalog_file_name:
        catalog_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{catalog_file_id}_{catalog_file_name}")
        if not os.path.exists(catalog_file_path):
            catalog_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{catalog_file_id}_docx")
        print(f"[DEBUG] 目录文件路径: {catalog_file_path}")
        if not os.path.exists(catalog_file_path):
            print(f"[ERROR] 目录文件不存在: {catalog_file_path}")
            catalog_file_path = None

    # 调用需求提取函数，传入用户确认的需求名称列表和目录文件路径
    requirement_dict = extract_requirements(file_path, requirement_names, catalog_file_path)

    if not requirement_dict:
        return jsonify({"error": "无法从文档中提取需求"}), 400
        
    # 将字典转换为列表，以便于前端处理
    processed_requirements = []
    for name, content in requirement_dict.items():
        # 尝试从需求名称中提取章节号
        chapter = name.split(' ')[0] if ' ' in name else ''
        processed_requirements.append({
            "name": name,
            "content": content,
            "chapter": chapter
        })
        
    session_id = str(uuid.uuid4())
    print(f"[DEBUG] 创建需求提取会话ID: {session_id}")

    # 写入临时文件
    temp_file = os.path.join(app.config['OUTPUT_FOLDER'], f"{session_id}_requirements.txt")
    with open(temp_file, 'w', encoding='utf-8') as f:
        for req in processed_requirements:
            # 只保存 name 和 content 字段
            f.write(f"{req['name']}|{req['content']}\n")

    return jsonify({
        "message": "需求提取成功",
        "session_id": session_id,
        "requirements_count": len(processed_requirements),
        "requirements": processed_requirements
    })


@app.route('/api/generate_excel', methods=['POST'])
def generate_excel_api():
    """
    生成CSV文件接口
    接收会话 ID，生成 CSV 文件
    返回文件下载链接
    """
    data = request.json
    session_id = data.get('session_id')
    excel_type = data.get('excel_type', 'requirement')  # 默认生成需求分析表
    
    if not session_id:
        return jsonify({"error": "缺少必要参数"}), 400
    
    # 读取临时文件中的需求数据
    temp_file = os.path.join(app.config['OUTPUT_FOLDER'], f"{session_id}_requirements.txt")
    
    if not os.path.exists(temp_file):
        return jsonify({"error": "会话已过期"}), 404
    
    # 从临时文件恢复需求数据
    processed_requirements = []
    with open(temp_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('|')
            if len(parts) >= 4:  # 现在只有四个字段
                req = {
                    "identifier": parts[0],
                    "name": parts[1],
                    "chapter": parts[2],
                    "content": parts[3]
                }
                processed_requirements.append(req)
    
    # 直接打印当前配置信息
    config = get_config()
    # 调试模式：显示完整API密钥信息
    safe_config = json.loads(json.dumps(config))
    if "openai" in safe_config and "api_key" in safe_config["openai"]:
        api_key = safe_config["openai"]["api_key"]
        print(f"[DEBUG] 完整API密钥（调试用）: '{api_key}'")
    
    # 根据类型生成不同的Excel文件
    if excel_type == 'requirement':
        output_file = os.path.join(app.config['OUTPUT_FOLDER'], f"{session_id}_requirement_analysis.xlsx")
        success = generate_requirement_excel(processed_requirements, output_file)
    elif excel_type == 'test_case':
        output_file = os.path.join(app.config['OUTPUT_FOLDER'], f"{session_id}_test_cases.xlsx")
        success = generate_requirement_excel(processed_requirements, output_file, "test_case")
    else:
        return jsonify({"error": "不支持的Excel类型"}), 400
    
    if not success:
        return jsonify({"error": "生成Excel文件失败"}), 500
    
    # 返回文件下载链接
    download_url = f"/api/download/{session_id}/{excel_type}"
    
    return jsonify({
        "message": "Excel文件生成成功",
        "download_url": download_url
    })

@app.route('/api/download/<session_id>/<excel_type>', methods=['GET'])
def download_excel(session_id, excel_type):
    """
    文件下载接口
    根据会话 ID 和 Excel 类型，返回生成的 Excel 文件
    """
    if excel_type == 'requirement':
        file_name = f"{session_id}_requirement_analysis.xlsx"
        display_name = "需求分析表.xlsx"
    elif excel_type == 'test_case':
        file_name = f"{session_id}_test_cases.xlsx"
        display_name = "测试用例表.xlsx"
    else:
        return jsonify({"error": "不支持的Excel类型"}), 400
    
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], file_name)
    
    if not os.path.exists(file_path):
        return jsonify({"error": "文件不存在"}), 404
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=display_name,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# ===================== 模型配置API =====================
@app.route('/api/model_config', methods=['GET', 'POST'])
def model_config_api():
    """
    获取或更新模型配置
    GET: 获取当前配置
    POST: 更新配置
    """
    from app.documentReview.ConfigurationItem.config import get_config, save_config
    
    if request.method == 'OPTIONS':
        return make_response('', 200)
    
    # 获取当前配置
    if request.method == 'GET':
        config = get_config()
        # 安全起见，不返回完整API密钥
        safe_config = json.loads(json.dumps(config))
        if 'openai' in safe_config and 'api_key' in safe_config['openai']:
            api_key = safe_config['openai']['api_key']
            # 掩码API密钥
            if api_key and len(api_key) > 8:
                masked_key = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]
                safe_config['openai']['api_key'] = masked_key
        
        return jsonify(safe_config)
    
    # 更新配置
    if request.method == 'POST':
        try:
            new_config = request.json
            save_config(new_config)
            # 返回前端期望的success字段而非status
            return jsonify({'success': True, 'message': '配置已更新'})
        except Exception as e:
            # 不返回400状态码，而是使用200状态码与success=False
            return jsonify({'success': False, 'error': str(e)})

# ===================== 需求审查API =====================
@app.route('/api/review_requirements', methods=['POST', 'OPTIONS'])
def review_requirements_api():
    """
    需求审查API端点
    对提取的需求进行AI评估和审查
    返回需求审查结果
    """
    import logging
    import traceback
    from app.documentReview.ConfigurationItem.requirement_reviewer import review_requirements
    
    logger = logging.getLogger(__name__)
    
    # 处理 OPTIONS 请求
    if request.method == "OPTIONS":
        return make_response('', 200)
    
    try:
        data = request.json
        requirements = data.get('requirements', [])
        session_id = data.get('session_id', 'default')
        
        if not requirements:
            logger.warning("未提供需求数据")
            return jsonify({"error": "未提供需求数据"}), 400
        
        
        review_results = review_requirements(requirements)
        
        # 保存审查结果到会话缓存，以便后续导出文档
        session_data = {
            'requirements': requirements,
            'review_results': review_results
        }
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

# ===================== 生成审查文档API =====================
@app.route('/api/generate_review_document', methods=['POST', 'OPTIONS'])
def generate_review_document_api():
    """
    生成需求审查文档API
    生成需求审查结果的导出文档
    """
    from app.documentReview.ConfigurationItem.requirement_reviewer import generate_review_document
    
    # 处理 OPTIONS 请求
    if request.method == "OPTIONS":
        return make_response('', 200)
    
    try:
        data = request.json
        logging.debug(f"生成审查文档接收到的参数: {data}")
        
        # 支持两种方式: 直接提供review_results或提供session_id
        review_results = data.get('review_results', [])
        session_id = data.get('session_id')
        
        # 如果提供了session_id但没有review_results,则尝试从会话中获取
        if not review_results and session_id:
            logging.debug(f"尝试从会话 {session_id} 中获取审查结果")
            # 从会话缓存中获取审查结果
            session_data = get_session_data(session_id)
            if session_data and 'review_results' in session_data:
                review_results = session_data['review_results']
                logging.debug(f"从会话缓存中获取到 {len(review_results)} 条审查结果")
        
        if not review_results:
            logging.error(f"未提供审查结果且无法从会话中获取: {data}")
            return jsonify({"error": "未提供审查结果且无法从会话中获取"}), 400
        
        # 调用需求审查模块生成文档
        result = generate_review_document(review_results, app.config['OUTPUT_FOLDER'])
        
        # 修改文件ID，只保留文件名的UUID部分
        file_name = result.get("file_name", "")
        doc_id = file_name.replace("requirement_review_", "").replace(".txt", "")
        
        # 构建响应数据格式，适配前端预期
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

@app.route('/api/download_review/<doc_id>', methods=['GET'])
def download_review_document(doc_id):
    """下载生成的审查文档"""
    try:
        # 检查doc_id是否已经包含扩展名
        has_extension = doc_id.lower().endswith('.xlsx') or doc_id.lower().endswith('.txt')
        
        if has_extension:
            # 如果已包含扩展名，直接使用
            base_name = doc_id  # 包含扩展名的文件名
            file_path = os.path.join(app.config['OUTPUT_FOLDER'], f"requirement_review_{base_name}")
            
            # 确定正确的MIME类型
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if doc_id.lower().endswith('.xlsx') else 'text/plain'
            download_name = "需求审查报告" + ('.xlsx' if doc_id.lower().endswith('.xlsx') else '.txt')
            
            logging.debug(f"尝试下载已含扩展名的文件: {file_path}")
            
            if os.path.exists(file_path):
                return send_file(
                    file_path, 
                    as_attachment=True, 
                    download_name=download_name,
                    mimetype=mimetype
                )
            else:
                logging.error(f"文件不存在: {file_path}")
        else:
            # 不包含扩展名，尝试两种可能的格式
            xlsx_file_name = f"requirement_review_{doc_id}.xlsx"
            xlsx_file_path = os.path.join(app.config['OUTPUT_FOLDER'], xlsx_file_name)
            
            txt_file_name = f"requirement_review_{doc_id}.txt"
            txt_file_path = os.path.join(app.config['OUTPUT_FOLDER'], txt_file_name)
            
            # 优先检查xlsx格式
            if os.path.exists(xlsx_file_path):
                logging.debug(f"找到Excel审查文档: {xlsx_file_path}")
                return send_file(
                    xlsx_file_path, 
                    as_attachment=True, 
                    download_name="需求审查报告.xlsx",
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            elif os.path.exists(txt_file_path):
                logging.debug(f"找到文本审查文档: {txt_file_path}")
                return send_file(
                    txt_file_path, 
                    as_attachment=True, 
                    download_name="需求审查报告.txt"
                )
            else:
                logging.error(f"文件不存在: {xlsx_file_path} 或 {txt_file_path}")
                return jsonify({"error": "文件不存在"}), 404
    
    except Exception as e:
        logging.error(f"下载审查文档时出错: {str(e)}", exc_info=True)
        return jsonify({"error": f"下载审查文档时出错: {str(e)}"}), 500

# ===================== AI需求提取API =====================
@app.route('/api/ai_extract', methods=['POST'])
def ai_extract_requirements_api():
    """
    AI需求提取接口
    使用AI技术提取需求详情
    接收：file_id, file_name, [requirement_names], [model]
    返回：提取的需求详情
    """
    import logging
    import traceback
    logger = logging.getLogger(__name__)
    
    if request.method == 'OPTIONS':
        return make_response('', 200)
    
    try:
        # 获取请求数据
        data = request.json
        file_id = data.get('file_id')
        file_name = data.get('file_name')
        requirement_names = data.get('requirement_names', [])
        model = data.get('model')
        
        
        
        # 构建文件路径
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{file_name}")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({"error": "文件不存在"}), 404
        
        # 调用AI提取需求函数
        extracted_requirements = ai_extract_requirements(file_path, model=model)
        
        # 生成会话ID
        session_id = str(uuid.uuid4())
        
        # 保存会话数据
        save_session_data(session_id, {
            "requirements": extracted_requirements,
            "file_id": file_id,
            "file_name": file_name
        })
        
        # 返回结果
        return jsonify({
            "success": True,
            "session_id": session_id,
            "requirements": extracted_requirements,
            "count": len(extracted_requirements)
        })
    
    except Exception as e:
        logger.error(f"AI提取需求时出错: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"AI提取需求时出错: {str(e)}"}), 500

# ===================== 需求重新匹配API =====================
@app.route('/api/rematch_requirements', methods=['POST'])
def rematch_requirements_api():
    """
    需求重新匹配接口
    重新匹配未匹配的需求
    接收：file_id, file_name, session_id, [model]
    返回：重新匹配的需求详情
    """
    import logging
    import traceback
    logger = logging.getLogger(__name__)
    
    if request.method == 'OPTIONS':
        return make_response('', 200)
    
    try:
        # 获取请求数据
        data = request.json
        file_id = data.get('file_id')
        file_name = data.get('file_name')
        session_id = data.get('session_id')
        model = data.get('model')
        
        
        
        # 构建文件路径
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{file_name}")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({"error": "文件不存在"}), 404
        
        # 获取会话数据
        session_data = get_session_data(session_id)
        if not session_data or 'requirements' not in session_data:
            return jsonify({"error": "会话数据不存在或无效"}), 400
        
        matched_requirements = session_data.get('requirements', [])
        
        # 调用需求重新匹配函数
        rematch_result = rematch_requirements(file_path, matched_requirements, model=model)
        
        # 更新会话数据
        if rematch_result and isinstance(rematch_result, list):
            session_data['requirements'] = rematch_result
            save_session_data(session_id, session_data)
        
        # 返回结果
        return jsonify({
            "success": True,
            "session_id": session_id,
            "requirements": rematch_result,
            "count": len(rematch_result) if rematch_result else 0
        })
    
    except Exception as e:
        logger.error(f"重新匹配需求时出错: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"重新匹配需求时出错: {str(e)}"}), 500

# ===================== 模型验证API =====================
@app.route('/api/validate_model', methods=['POST'])
def validate_model_api():
    """
    验证当前配置的模型是否可用
    返回验证结果
    """
    # 导入必要模块
    from app.documentReview.ConfigurationItem.requirement_reviewer import validate_model
    
    if request.method == 'OPTIONS':
        return make_response('', 200)
    
    try:
        # 输出当前配置信息用于调试
        from app.documentReview.ConfigurationItem.config import get_config
        config = get_config()
        
        # 记录收到的请求内容（如果有）
        request_data = request.json if request.is_json else {}
        
        
        # 调试信息：显示完整API密钥
        safe_config = json.loads(json.dumps(config))
        if 'openai' in safe_config and 'api_key' in safe_config['openai']:
            api_key = safe_config['openai']['api_key']
            
            
        # 记录配置参数，便于调试
        
        
            
        # 调用模型验证函数
        result = validate_model()
        # 使用success字段替代status，与response字段替代message
        return jsonify({'success': True, 'response': result})
    except Exception as e:
        error_message = f'模型验证失败: {str(e)}'
        logging.error(error_message)
        # 使用success=False和error字段
        return jsonify({'success': False, 'error': error_message})

# 添加会话数据存储
session_cache = {}

def get_session_data(session_id):
    """
    获取会话数据
    """
    if not session_id:
        return None
    
    
    if session_id in session_cache:
        return session_cache[session_id]
    
    
    return None

def save_session_data(session_id, data):
    """
    保存会话数据
    """
    if not session_id:
        return
    
    
    session_cache[session_id] = data

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
