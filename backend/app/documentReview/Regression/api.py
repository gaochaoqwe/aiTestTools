"""
API服务模块 - 回归测试专用
提供HTTP API接口，处理前端回归测试请求
"""
import os
import tempfile
import uuid
import json
import logging
import re
from flask import Flask, request, jsonify, send_file, make_response
from werkzeug.utils import secure_filename
from flask_cors import CORS


from app.documentReview.Regression.requirement_extractor import (
    extract_requirements, 
    generate_requirement_excel
)

# 导入AI提取模块
from app.documentReview.Regression.ai_extractor import (
    ai_extract_requirements,
    ai_extract_named_requirements,
    ai_rematch_requirements
)

# 导入文档读取模块
from app.documentReview.Regression.document_reader import (
    check_word_document, 
    extract_requirement_candidates
)

# 创建Flask应用
app = Flask(__name__)

# 配置CORS - 修改为匹配/api/*
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

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
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'uploads', 'regression')
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

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({"status": "ok"})

@app.route('/api/upload', methods=['POST'])
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
    import traceback
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
            
        if not catalog_file_id or not catalog_file_name:
            logger.error(f"\u7f3a少目录文件参数: catalog_file_id={catalog_file_id}, catalog_file_name={catalog_file_name}")
            return jsonify({"error": "必须提供目录文件！"}), 400
            
        # 首先尝试使用完整文件名
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{file_name}")
        # 如果不存在，再尝试只用扩展名
        if not os.path.exists(file_path):
            # 发现上传后的文件名是 file_id_docx 格式
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_docx")
            
        if not os.path.exists(file_path):
            logger.error(f"\u6587件不存在: {file_path}")
            return jsonify({"error": "文件不存在 - 请确保已正确上传"}), 404
            
        # 目录文件也用同样的逻辑
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
        
        logging.warning(f"使用目录文件路径: {catalog_file_path}")
        
        if not os.path.exists(catalog_file_path):
            logging.error(f"目录文件不存在: {catalog_file_path}")
            logging.error(f"请求参数: catalog_file_id={catalog_file_id}, catalog_file_name={catalog_file_name}")
            return jsonify({"error": "目录文件不存在 - 请确保已正确上传"}), 404
    except Exception as e:
        logger.error(f"\u5904理请求时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"处理请求时出错: {str(e)}"}), 500
            
    # 注意：这里使用包名的绝对导入
    from app.documentReview.ConfigurationItem.document_reader import extract_requirement_candidates
    import uuid
    
    try:
        # 使用目录文件提取需求候选项
        candidates = extract_requirement_candidates(file_path, catalog_file_path)
    except Exception as e:
        print(f"[ERROR] 调用extract_requirement_candidates函数时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"提取需求候选项时出错: {str(e)}"}), 500
    
    if not candidates:
        return jsonify({"error": "从目录文件中未能提取出任何需求条目"}), 400
    
    # 创建会话ID
    session_id = str(uuid.uuid4())
        
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
    try:
        data = request.json
        file_id = data.get('file_id')
        file_name = data.get('file_name')
        requirement_names = data.get('requirement_names', [])  # 用户确认的需求名称列表
        catalog_file_id = data.get('catalog_file_id')  # 目录文件ID
        catalog_file_name = data.get('catalog_file_name')  # 目录文件名称
        
        logging.debug(f"提取需求请求参数: file_id={file_id}, catalog_file_id={catalog_file_id}")
        logging.debug(f"开始提取需求，共{len(requirement_names)}个需求名称")
        
        # 清除需求名称中的章节号前缀
        cleaned_requirement_names = []
        for req_name in requirement_names:
            # 移除前面的章节号部分 (如 "3.1.1 ")
            if re.match(r'^\d+(\.\d+)*\s+', req_name):
                clean_name = re.sub(r'^\d+(\.\d+)*\s+', '', req_name)
                cleaned_requirement_names.append(clean_name)
            else:
                cleaned_requirement_names.append(req_name)
                
        if not file_id or not file_name:
            return jsonify({"error": "缺少必要参数"}), 400

        # 构建file_path - 使用与候选项提取相同的逻辑
        # 首先尝试使用完整文件名
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{file_name}")
        # 如果不存在，再尝试只用扩展名
        if not os.path.exists(file_path):
            # 发现上传后的文件名是 file_id_docx 格式
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_docx")
        
        if not os.path.exists(file_path):
            logging.error(f"文件不存在: {file_path}")
            return jsonify({"error": "文件不存在 - 请确保文件已正确上传"}), 404

        # 构建catalog_file_path
        catalog_file_path = None
        if catalog_file_id and catalog_file_name:
            catalog_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{catalog_file_id}_{catalog_file_name}")
            if not os.path.exists(catalog_file_path):
                catalog_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{catalog_file_id}_docx")
            if not os.path.exists(catalog_file_path):
                logging.warning(f"目录文件不存在: {catalog_file_path}")
                catalog_file_path = None

        # 调用requirement_extractor中的extract_requirements函数
        from app.documentReview.Regression.requirement_extractor import extract_requirements
        
        # 提取需求内容
        requirement_dict = extract_requirements(file_path, cleaned_requirement_names, catalog_file_path)

        # 处理提取结果
        processed_requirements = []
        
        if not requirement_dict:
            logging.warning("提取需求返回空字典，将为所有需求名创建占位符")
            # 创建占位符 - 为所有需求创建默认项
            for name in cleaned_requirement_names:
                chapter = name.split(' ')[0] if ' ' in name else ''
                processed_requirements.append({
                    "name": name,
                    "content": f"未能从文档中提取「{name}」的需求内容",
                    "chapter": chapter
                })
        else:
            # 将字典转换为列表，以便于前端处理
            for name, content in requirement_dict.items():
                # 尝试从需求名称中提取章节号
                chapter = name.split(' ')[0] if ' ' in name else ''
                processed_requirements.append({
                    "name": name,
                    "content": content,
                    "chapter": chapter
                })
            
            # 确保所有需求都有内容
            for name in cleaned_requirement_names:
                if name not in requirement_dict:
                    chapter = name.split(' ')[0] if ' ' in name else ''
                    processed_requirements.append({
                        "name": name,
                        "content": f"未能从文档中提取「{name}」的需求内容",
                        "chapter": chapter
                    })
        
        # 按章节号排序
        processed_requirements.sort(key=lambda x: x["chapter"])
        
        # 确保即使没有提取到需求也创建会话ID
        session_id = str(uuid.uuid4())
        
        # 保存至会话缓存
        save_session_data(session_id, {
            "requirements": processed_requirements,
            "file_path": file_path
        })

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
    
    except Exception as e:
        logging.error(f"提取需求时出现异常: {str(e)}", exc_info=True)
        
        # 即使出现异常，也尝试返回部分结果或占位符
        if 'requirement_names' in locals():
            # 为所有需求创建占位符
            processed_requirements = []
            for name in requirement_names:
                chapter = name.split(' ')[0] if ' ' in name else ''
                processed_requirements.append({
                    "name": name,
                    "content": f"提取需求时出错: {str(e)}",
                    "chapter": chapter
                })
            
            # 创建会话ID
            session_id = str(uuid.uuid4())
            
            return jsonify({
                "message": f"需求提取过程中出现错误，但仍返回占位符结果: {str(e)}",
                "session_id": session_id,
                "requirements_count": len(processed_requirements),
                "requirements": processed_requirements
            })
        else:
            return jsonify({"error": f"需求提取失败: {str(e)}"}), 500

@app.route('/api/ai_extract', methods=['POST'])
def ai_extract_requirements_api():
    """
    AI驱动的需求提取接口
    使用大型语言模型分析文档并提取需求内容
    """
    try:
        data = request.json
        file_id = data.get('file_id')
        file_name = data.get('file_name')
        requirement_names = data.get('requirement_names', [])  # 用户确认的需求名称列表
        model = data.get('model', 'gpt-3.5-turbo')  # 默认使用gpt-3.5-turbo
        
        if not file_id or not file_name:
            return jsonify({"error": "缺少必要参数"}), 400

        # 构建file_path
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{file_name}")
        if not os.path.exists(file_path):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_docx")
        
        if not os.path.exists(file_path):
            logging.error(f"文件不存在: {file_path}")
            return jsonify({"error": "文件不存在 - 请确保文件已正确上传"}), 404

        # 调用AI提取模块提取需求内容
        requirement_dict = ai_extract_named_requirements(file_path, cleaned_requirement_names, model)

        # 处理提取结果
        processed_requirements = []
        
        if not requirement_dict:
            logging.warning("AI提取需求返回空字典，将为所有需求名创建占位符")
            # 创建占位符 - 为所有需求创建默认项
            for name in cleaned_requirement_names:
                chapter = name.split(' ')[0] if ' ' in name else ''
                processed_requirements.append({
                    "name": name,
                    "content": f"AI未能从文档中提取「{name}」的需求内容",
                    "chapter": chapter
                })
        else:
            # 将字典转换为列表，以便于前端处理
            for name, content in requirement_dict.items():
                # 尝试从需求名称中提取章节号
                chapter = name.split(' ')[0] if ' ' in name else ''
                processed_requirements.append({
                    "name": name,
                    "content": content,
                    "chapter": chapter,
                    "extraction_method": "AI"  # 标记为AI提取
                })
            
            # 确保所有需求都有内容
            for name in cleaned_requirement_names:
                if name not in requirement_dict:
                    chapter = name.split(' ')[0] if ' ' in name else ''
                    processed_requirements.append({
                        "name": name,
                        "content": f"AI未能从文档中提取「{name}」的需求内容",
                        "chapter": chapter
                    })
        
        # 创建一个新的会话ID用于后续操作
        session_id = str(uuid.uuid4())
        
        # 存储会话数据，包括提取的需求和原始文件ID
        session_data = {
            "requirements": processed_requirements,
            "file_id": file_id,
            "file_name": file_name
        }
        
        # 保存会话数据
        save_session_data(session_id, session_data)
        
        return jsonify({
            "success": True,
            "requirements": processed_requirements,
            "session_id": session_id,
            "message": f"成功使用AI提取了{len(processed_requirements)}个需求"
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": f"AI需求提取失败: {str(e)}"
        }), 500

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
    from app.documentReview.Regression.ai_reviewer import review_requirements
    
    logger = logging.getLogger(__name__)
    
    # 处理 OPTIONS 请求
    if request.method == "OPTIONS":
        return make_response('', 200)
    
    try:
        data = request.json
        requirements = data.get('requirements', [])
        session_id = data.get('session_id', 'default')
        
        # 处理嵌套的需求数据结构 - 检查是否有嵌套的requirements结构
        if requirements and isinstance(requirements, list) and len(requirements) > 0:
            if isinstance(requirements[0], dict) and 'requirements' in requirements[0]:
                logger.info("检测到嵌套的需求数据结构，正在提取内部需求")
                # 提取内部的requirements
                nested_requirements = []
                for item in requirements:
                    if isinstance(item, dict) and 'requirements' in item:
                        nested_requirements.extend(item.get('requirements', []))
                        # 如果内部有session_id并且外部是默认值，则使用内部的
                        if session_id == 'default' and 'session_id' in item:
                            session_id = item.get('session_id')
                            
                requirements = nested_requirements
                
        
        if not requirements:
            logger.warning("未提供需求数据")
            return jsonify({"error": "未提供需求数据"}), 400
        
        
        
        
        # 添加更详细的调试信息
        logger.debug("需求数据详情:")
        for i, req in enumerate(requirements):
            req_name = req.get('name', '未命名') if isinstance(req, dict) else '非字典类型需求'
            req_content = req.get('content', '无内容') if isinstance(req, dict) else str(req)[:100] + '...' if len(str(req)) > 100 else str(req)
            logger.debug(f"需求[{i}]: 名称={req_name}, 内容长度={len(req_content) if req_content else 0}字符")
            if req_content and len(req_content) > 0:
                logger.debug(f"需求[{i}]内容预览: {req_content[:100]}...")
            else:
                logger.debug(f"需求[{i}]内容为空")
        
        # 记录请求类型和完整数据
        logger.debug(f"需求数据类型: {type(requirements)}, 元素类型: {type(requirements[0]) if requirements else 'N/A'}")
        
        # 输出完整的请求数据，但不截断
        try:
            full_data_str = json.dumps(data, ensure_ascii=False)
            logger.debug(f"请求完整数据: {full_data_str}")
        except Exception as e:
            logger.warning(f"序列化请求数据失败: {e}")
            logger.debug(f"请求数据的键: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
        
        try:
            logger.debug("开始调用review_requirements函数")
            
            # 修改处理方式，确保需求是一个一个处理的
            if len(requirements) > 1:
                
                review_results = []
                for idx, req in enumerate(requirements):
                    logger.debug(f"单独处理需求[{idx+1}/{len(requirements)}]")
                    # 将单个需求包装为列表发送给审查函数
                    single_result = review_requirements([req])
                    if single_result and len(single_result) > 0:
                        review_results.append(single_result[0])
                    else:
                        logger.warning(f"需求[{idx+1}]审查失败，返回结果为空")
            else:
                # 如果只有一个需求，直接处理
                
                review_results = review_requirements(requirements)
                
            logger.debug(f"审查完成，结果长度: {len(review_results)}")
            if len(review_results) != len(requirements):
                logger.warning(f"警告: 结果数量({len(review_results)})与需求数量({len(requirements)})不匹配")
            
            # 记录审查结果的基本信息
            for i, result in enumerate(review_results):
                result_name = result.get('name', '未命名')
                review_data = result.get('review_result', {})
                problems_count = len(review_data.get('requirements_review', []))
                logger.debug(f"审查结果[{i}]: 需求名称={result_name}, 发现问题数={problems_count}")
                
                # 记录问题详情
                if problems_count > 0:
                    for j, problem in enumerate(review_data.get('requirements_review', [])):
                        logger.debug(f"问题[{j}]: {problem.get('problem_title', '未知问题')}")
        except Exception as inner_e:
            logger.error(f"审查过程中发生错误: {str(inner_e)}", exc_info=True)
            return jsonify({"error": f"需求审查失败: {str(inner_e)}"}), 500
        
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

# ===================== 需求重新匹配API =====================
@app.route('/api/rematch_requirements', methods=['POST'])
def rematch_requirements_api():
    """
    需求重新匹配API端点
    对未匹配的需求进行再次匹配
    返回合并后的完整需求列表
    """
    try:
        # 获取请求数据
        data = request.get_json()
        file_id = data.get('file_id')
        file_name = data.get('file_name')
        session_id = data.get('session_id', 'default')
        
        # 检查必要参数
        if not file_id or not file_name:
            return jsonify({"error": "缺少文件ID或文件名"}), 400
            
        # 检查文件存在
        file_path = os.path.join(UPLOAD_FOLDER, file_id)
        if not os.path.exists(file_path):
            return jsonify({"error": "文件不存在"}), 404
        
        # 检查文件格式
        if not file_name.lower().endswith(('.doc', '.docx')):
            return jsonify({"error": "文件格式不支持，仅支持.doc和.docx"}), 400
            
        # 获取当前会话数据中的已匹配需求
        session_data = get_session_data(session_id)
        if not session_data or "requirements" not in session_data:
            # 如果没有已匹配需求，则直接调用提取函数
            logging.info("未找到已匹配需求，执行完整提取")
            requirements = ai_extract_requirements(file_path)
        else:
            # 已有匹配需求，调用重新匹配函数
            matched_requirements = session_data.get("requirements", {})
            logging.info(f"开始重新匹配需求，当前已有 {len(matched_requirements)} 个已匹配需求")
            requirements = ai_rematch_requirements(file_path, matched_requirements)
            
        # 保存提取结果到会话
        if not session_data:
            session_data = {}
        session_data["requirements"] = requirements
        save_session_data(session_id, session_data)
        
        # 返回结果
        return jsonify({
            "success": True,
            "message": "需求重新匹配成功",
            "requirements": requirements,
            "count": len(requirements)
        })
    except Exception as e:
        logging.error(f"需求重新匹配失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"需求重新匹配失败: {str(e)}"}), 500

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
