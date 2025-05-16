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
