"""
API模块
处理AI API调用相关功能
"""
import os
import json
import time
import logging
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from .client import get_client
from .utils import get_config

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def query_ai_model(client, prompt, model=None):
    """
    向AI模型发送请求
    
    Args:
        client: OpenAI客户端
        prompt: 提示文本
        model: 模型名称
        
    Returns:
        AI的响应文本
    """
    # 如果没有指定模型，从配置文件获取
    if model is None:
        # 从配置文件获取模型名称
        config = get_config()
        provider = config.get("provider", "openai")
        
        if provider == "openai" and "openai" in config:
            model = config["openai"].get("model_name", "gpt-3.5-turbo")
            logging.info(f"使用OpenAI配置模型: {model}")
        elif provider == "ollama" and "ollama" in config:
            model = config["ollama"].get("model_name", "llama3")
            logging.info(f"使用Ollama配置模型: {model}")
        
        # 如果没有设置模型名称，使用默认值
        if not model:
            logging.warning("配置文件中没有设置模型名称，使用默认值gpt-3.5-turbo")
            model = "gpt-3.5-turbo"  # 默认回退模型
    
    logging.info(f"查询AI模型: {model}, 提示长度: {len(prompt)}")
    
    try:
        # 再次记录最终使用的模型名称
        logging.info(f"开始API调用，使用模型: {model}")
        
        # 记录详细的API调用参数
        api_params = {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是一个专业的需求文档分析专家，擅长从软件需求规格说明中提取结构化需求内容。"},
                {"role": "user", "content": prompt[:100] + "..." if len(prompt) > 100 else prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 2000
        }
        logging.info(f"完整API调用参数: {json.dumps(api_params, ensure_ascii=False)}")
        
        # 根据provider选择不同的API调用方式
        provider = get_config().get("provider", "openai")
        
        if provider == "openai":
            # 使用OpenAI客户端
            return call_openai_api(client, prompt, model)
        elif provider == "ollama":
            # 使用Ollama API
            return call_ollama_api(prompt, model)
        else:
            logging.error(f"不支持的提供商: {provider}")
            raise ValueError(f"不支持的提供商: {provider}")
            
    except Exception as e:
        logging.error(f"AI模型查询失败: {str(e)}")
        raise

def call_openai_api(client, prompt, model):
    """
    调用OpenAI API
    
    Args:
        client: OpenAI客户端
        prompt: 提示文本
        model: 模型名称
        
    Returns:
        API响应文本
    """
    # 获取模型参数
    config = get_config()
    model_params = config.get("model_params", {})
    temperature = model_params.get("temperature", 0.2)
    max_tokens = model_params.get("max_tokens", 2000)
    
    logging.info("准备调用OpenAI API，使用模型: %s", model)
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "你是一个专业的需求文档分析专家，擅长从软件需求规格说明中提取结构化需求内容。"},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature,
        max_tokens=max_tokens
    )
    
    # 记录完整原始响应，不省略内容
    full_response = response.choices[0].message.content
    logging.info("===== 模型完整原始响应开始 =====\n%s\n===== 模型完整原始响应结束 =====", full_response)
    
    # 提取文本响应
    return full_response

def call_ollama_api(prompt, model="llama3", temperature=0.2, max_tokens=2000):
    """
    调用Ollama API
    
    Args:
        prompt: 提示文本
        model: 模型名称
        temperature: 温度参数
        max_tokens: 最大token数
        
    Returns:
        API响应文本
    """
    config = get_config()
    if "ollama" not in config:
        raise ValueError("配置中未找到Ollama设置")
    
    base_url = config["ollama"].get("base_url", "http://localhost:11434")
    
    # 构建API URL
    if base_url.endswith("/"):
        api_url = f"{base_url}api/generate"
    else:
        api_url = f"{base_url}/api/generate"
    
    # 使用配置文件中的模型参数，如果存在
    model_params = config.get("model_params", {})
    if model_params:
        temperature = model_params.get("temperature", temperature)
        max_tokens = model_params.get("max_tokens", max_tokens)
    
    # 设置请求参数
    payload = {
        "model": model,
        "prompt": prompt,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    # 发送请求
    response = requests.post(api_url, json=payload)
    response.raise_for_status()
    
    # 解析响应
    result = response.json()
    extracted_requirements = result.get("requirements", [])
    
    return result.get("response", "")


def register_ai_extraction_apis(app, upload_folder):
    """
    注册AI需求提取相关的API，只保留直接提取需求功能
    Args:
        app: Flask应用实例
        upload_folder: 上传文件夹路径
    """
    from flask import jsonify, request
    import logging
    import uuid
    from datetime import datetime
    import os
    import json

    @app.route('/api/requirement_candidates', methods=['POST'])
    def ai_extract_api():
        """
        AI直接提取文档中的所有需求
        JSON参数:
            file_id: 文件ID
            file_name: 文件名
            model: 可选，使用的AI模型名称
        返回:
            提取的需求列表 {session_id, requirements: [{name, chapter, content}, ...]}
        """
        try:
            data = request.json
            file_id = data.get('file_id')
            file_name = data.get('file_name')
            model = data.get('model')
            if not file_id or not file_name:
                return jsonify({'success': False, 'error': '缺少必要参数'}), 400
            # 构建文件路径
            file_path = os.path.join(upload_folder, file_id)
            if not os.path.exists(file_path):
                return jsonify({'success': False, 'error': '文件不存在'}), 404
            logging.info(f"正在使用AI提取文档需求: {file_name} ({file_id})")
            # 创建会话ID
            session_id = str(uuid.uuid4())
            # 直接提取所有需求
            from .extractor import ai_extract_requirements
            requirements_data = ai_extract_requirements(file_path, model)
            # 处理提取结果
            requirements = []
            if isinstance(requirements_data, list):
                for req in requirements_data:
                    if isinstance(req, dict):
                        name = req.get("name", req.get("title", ""))
                        chapter = req.get("chapter", req.get("chapter_number", ""))
                        content = req.get("content", "")
                        # 处理内容字段
                        if isinstance(content, dict):
                            content_str = ""
                            if 'b' in content:  # 基本描述
                                content_str += content['b'] + "\n\n"
                            if 'c' in content:  # 条件
                                content_str += f"进入条件: {content['c']}\n\n"
                            if 'd' in content:  # 输入
                                content_str += f"输入: {content['d']}\n\n"
                            if 'e' in content:  # 输出
                                content_str += f"输出: {content['e']}\n\n"
                            if 'f' in content:  # 处理
                                content_str += f"处理: {content['f']}\n\n"
                            if 'g' in content:  # 性能
                                content_str += f"性能: {content['g']}\n\n"
                            if 'h' in content:  # 限制
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
                logging.warning(f"没有从文件 {file_name} 中提取到需求")
                return jsonify({
                    'success': False, 
                    'error': '未提取到需求，请检查文档格式或内容'
                }), 400
            # 记录处理结果
            result_folder = os.path.join(upload_folder, 'results')
            os.makedirs(result_folder, exist_ok=True)
            result_path = os.path.join(result_folder, f"{session_id}.json")
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'session_id': session_id,
                    'file_id': file_id,
                    'file_name': file_name,
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
    return app
