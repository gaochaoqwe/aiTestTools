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
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..', 'config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 记录完整的配置信息
                    logging.info(f"从配置文件读取到的完整配置: {json.dumps(config, ensure_ascii=False)}")
                    
                    provider = config.get("provider", "openai")
                    if provider == "openai" and "openai" in config:
                        if not model:  # 只有在未指定模型时才从配置读取
                            # 直接使用与configuration文件同样的model_name字段
                            model = config["openai"].get("model_name")
                            logging.info(f"使用OpenAI配置模型: {model}")
                    elif provider == "ollama" and "ollama" in config:
                        if not model:  # 只有在未指定模型时才从配置读取
                            model = config["ollama"].get("model_name", "llama3")
                            logging.info(f"使用Ollama配置模型: {model}")
                    
                    # 如果没有设置模型名称，使用默认值
                    if not model:
                        logging.warning("配置文件中没有设置模型名称，使用默认值gpt-3.5-turbo")
                        model = "gpt-3.5-turbo"  # 默认回退模型
            except Exception as e:
                logging.error(f"读取配置文件中的模型名称失败: {str(e)}")
                model = "gpt-3.5-turbo"  # 默认回退模型
        else:
            model = "gpt-3.5-turbo"  # 默认回退模型
    
    logging.info(f"查询AI模型: {model}, 提示长度: {len(prompt)}")
    
    try:
        # 确保model参数正确，记录最终使用的模型名称
        if not model or model == "gpt-3.5-turbo":  
            # 再次尝试从配置文件获取正确的模型名称
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..', 'config.json')
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        openai_config = config.get("openai", {})
                        model_from_config = openai_config.get("model_name")
                        if model_from_config:
                            model = model_from_config
                            logging.info(f"最终从配置获取到的模型名称: {model}")
                except Exception as e:
                    logging.error(f"尝试读取配置模型时出错: {e}")
        
        logging.info(f"开始API调用，使用模型: {model}")
        
        # 记录详细的API调用参数
        api_params = {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是一个专业的需求文档分析专家，擅长结构化提取文档内容。"},
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
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "你是一个专业的需求文档分析专家，擅长结构化提取文档内容。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=2000
    )
    
    # 提取文本响应
    return response.choices[0].message.content

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
    
    return result.get("response", "")
