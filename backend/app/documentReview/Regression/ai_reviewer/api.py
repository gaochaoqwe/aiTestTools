"""
API调用模块 - 处理与不同AI服务提供商的API交互
"""
import json
import logging
import requests
import re

from app.documentReview.Regression.config import get_config

def call_openai_api(prompt, temperature, max_tokens, is_third_party_api=False, model_name=None):
    """
    调用OpenAI API
    
    参数:
        prompt: str, 提示词
        temperature: float, 温度参数
        max_tokens: int, 最大令牌数
        is_third_party_api: bool, 是否是第三方API
        model_name: str, 模型名称，默认为None
    
    返回:
        str: 模型响应内容
    """
    config = get_config()
    openai_config = config.get("openai", {})
    
    # 如果没有指定model_name，从配置中获取
    if not model_name:
        model_name = openai_config.get("model_name")
        if not model_name:
            model_name = "gpt-3.5-turbo"  # 默认模型
    
    # 获取API密钥和基础URL
    api_key = openai_config.get("api_key", "")
    base_url = openai_config.get("base_url", "")
    
    if not api_key:
        raise ValueError("未找到有效的API密钥")
    
    # 记录API请求信息（敏感信息部分掩码）
    api_key_prefix = api_key[:4] if len(api_key) > 8 else ""
    api_key_suffix = api_key[-4:] if len(api_key) > 8 else ""
    api_key_length = len(api_key)
    
    # 构建请求参数
    request_params = {
        "provider": "openai",
        "model": model_name,
        "api_key_prefix": api_key_prefix,
        "api_key_length": api_key_length,
        "base_url": base_url,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "prompt_length": len(prompt),
        "prompt_preview": prompt[:50] + "..." if len(prompt) > 50 else prompt,
        "is_third_party_api": is_third_party_api
    }
    
    logging.info(f"OpenAI请求参数: {json.dumps(request_params, ensure_ascii=False)}")
    
    # 对于第三方API，优先使用直接HTTP请求
    if is_third_party_api:
        try:
            return call_direct_http_api(prompt, temperature, max_tokens)
        except Exception as e:
            logging.warning(f"直接HTTP请求失败，尝试使用OpenAI库: {str(e)}")
            # 如果直接请求失败，回退到OpenAI库
    
    try:
        from .client import get_client
        client = get_client()
        if not client:
            raise ValueError("无法创建OpenAI客户端")
            
        # 构建请求参数
        request_args = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "你是一名专业的需求分析专家，擅长发现需求文档中的问题。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # 如果不是验证模型，则添加JSON响应格式
        if "验证模型" not in prompt:
            request_args["response_format"] = {"type": "json_object"}
            
        # 打印实际请求参数
        logging.info(f"OpenAI API请求参数: {json.dumps(request_args, ensure_ascii=False)}")
        
        response = client.chat.completions.create(**request_args)
        
        # 提取响应内容
        return response.choices[0].message.content
    
    except Exception as e:
        error_message = str(e)
        # 提取更详细的错误信息
        if hasattr(e, 'response'):
            try:
                # 尝试从响应中提取更多错误信息
                response_json = e.response.json()
                logging.error(f"OpenAI API完整错误响应: {json.dumps(response_json, ensure_ascii=False)}")
                if 'error' in response_json:
                    error_message = f"{response_json['error'].get('message', error_message)}"
            except Exception:
                pass
        
        # 对于常见错误，提供更友好的错误消息
        if "rate limit" in error_message.lower():
            raise ValueError(f"API调用频率超过限制，请稍后再试: {error_message}")
        elif "maximum context length" in error_message.lower():
            raise ValueError(f"提示词过长，超过了模型上下文长度限制: {error_message}")
        elif "does not exist" in error_message.lower() and model_name:
            raise ValueError(f"指定的模型 '{model_name}' 不存在或不可用，请检查模型名称")
        
        # 其他错误
        else:
            raise ValueError(f"调用OpenAI API时出错: {error_message}")

def call_direct_http_api(prompt, temperature, max_tokens):
    """
    使用直接HTTP请求调用兼容OpenAI的API
    针对第三方API可能需要不同的认证方式
    
    参数:
        prompt: str, 提示词
        temperature: float, 温度参数
        max_tokens: int, 最大令牌数
    
    返回:
        str: 模型响应内容
    """
    import requests
    
    config = get_config()
    openai_config = config.get("openai", {})
    model_name = openai_config.get("model_name", "gpt-4o")
    api_key = openai_config.get("api_key", "")
    base_url = openai_config.get("base_url", "")
    
    # 判断并构建正确的URL
    if "chat/completions" in base_url:
        # 如果base_url已经包含了端点路径，则直接使用
        url = base_url
        logging.info(f"使用预配置的完整端点URL: {url}")
    else:
        # 确保base_url不以/结尾
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        # 构建完整URL
        url = f"{base_url}/chat/completions"
        logging.info(f"构建端点URL: {url}")
    
    # 准备请求数据 - 与成功的测试案例完全一致
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "response_format": {"type": "text"}
    }
    
    # 准备认证头 - 直接使用Bearer前缀，与成功案例保持一致
    auth_header = f"Bearer {api_key}"
    
    headers = {
        "Authorization": auth_header,
        "Content-Type": "application/json"
    }
    
    logging.info(f"直接HTTP请求 - URL: {url}")
    logging.info(f"直接HTTP请求 - 模型: {model_name}")
    logging.info(f"直接HTTP请求 - 认证头格式: {auth_header[:10]}...{auth_header[-4:]}")
    
    # 发送请求
    try:
        # 启用直接HTTP请求
        response = requests.post(url, json=payload, headers=headers)
        
        # 检查响应状态码
        response.raise_for_status()
        
        # 解析JSON响应
        result = response.json()
        logging.info(f"直接HTTP请求成功，响应状态码: {response.status_code}")
        
        # 提取回复内容
        if 'choices' in result and len(result['choices']) > 0:
            message_content = result['choices'][0]['message']['content']
            return message_content
        else:
            logging.error(f"API响应格式不正确: {json.dumps(result, ensure_ascii=False)}")
            raise ValueError(f"API响应格式不正确")
            
    except requests.RequestException as e:
        logging.error(f"HTTP请求错误: {str(e)}")
        raise ValueError(f"HTTP请求错误: {str(e)}")
    except json.JSONDecodeError as e:
        logging.error(f"响应不是有效的JSON: {str(e)}")
        raise ValueError(f"响应不是有效的JSON: {str(e)}")
    except Exception as e:
        logging.error(f"调用API时发生错误: {str(e)}")
        raise ValueError(f"调用API时发生错误: {str(e)}")

def call_ollama_api(prompt, temperature, max_tokens):
    """
    调用Ollama API
    
    参数:
        prompt: str, 提示词
        temperature: float, 温度参数
        max_tokens: int, 最大令牌数
    
    返回:
        str: 模型响应内容
    """
    config = get_config()
    ollama_config = config.get("ollama", {})
    base_url = ollama_config.get("base_url", "http://localhost:11434")
    model_name = ollama_config.get("model_name", "llama3")
    
    # 打印请求详情
    logging.info(f"Ollama API请求 - 基础URL: {base_url}")
    logging.info(f"Ollama API请求 - 模型: {model_name}")
    logging.info(f"Ollama API请求 - 温度: {temperature}")
    logging.info(f"Ollama API请求 - 最大令牌数: {max_tokens}")
    
    # 构建API URL
    if base_url.endswith('/'):
        api_url = f"{base_url}api/generate"
    else:
        api_url = f"{base_url}/api/generate"
    
    # 准备请求数据
    payload = {
        "model": model_name,
        "prompt": prompt,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }
    
    # 打印请求详情
    logging.info(f"Ollama API URL: {api_url}")
    request_params = {**payload}
    request_params["prompt"] = request_params["prompt"][:50] + "..." if len(request_params["prompt"]) > 50 else request_params["prompt"]
    logging.info(f"Ollama API请求参数: {json.dumps(request_params, ensure_ascii=False)}")
    
    # 发送请求
    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        
        # 解析响应
        result = response.json()
        
        if "response" in result:
            return result["response"]
        else:
            logging.error(f"Ollama API响应没有包含response字段: {json.dumps(result, ensure_ascii=False)}")
            raise ValueError("Ollama API响应格式不正确")
    
    except requests.RequestException as e:
        logging.error(f"Ollama HTTP请求错误: {str(e)}")
        raise ValueError(f"Ollama HTTP请求错误: {str(e)}")
    except json.JSONDecodeError as e:
        logging.error(f"Ollama响应不是有效的JSON: {str(e)}")
        raise ValueError(f"Ollama响应不是有效的JSON: {str(e)}")
    except Exception as e:
        logging.error(f"调用Ollama API时发生错误: {str(e)}")
        raise ValueError(f"调用Ollama API时发生错误: {str(e)}")
