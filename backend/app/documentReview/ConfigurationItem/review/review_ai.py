"""
AI模型API调用模块
"""
import json
import logging
from app.documentReview.ConfigurationItem.config import get_config
from app.documentReview.ConfigurationItem.review.review_client import get_client

def call_openai_api(prompt, temperature, max_tokens):
    """
    调用OpenAI API
    参数: prompt: str, temperature: float, max_tokens: int
    返回: str: 模型响应内容
    """
    config = get_config()
    openai_config = config.get("openai", {})
    model_name = openai_config.get("model_name", "gpt-4o")
    api_key = openai_config.get("api_key", "")
    base_url = openai_config.get("base_url", "")
    is_third_party_api = ("siliconflow" in base_url or 
                          "glm" in base_url.lower() or 
                          "qwen" in base_url.lower() or 
                          "zhipu" in base_url.lower())
    masked_key = "****"
    if api_key and len(api_key) > 8:
        masked_key = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]
    request_params = {
        "provider": "openai",
        "model": model_name,
        "api_key_prefix": api_key[:4] if len(api_key) > 4 else "无效",
        "api_key_length": len(api_key),
        "base_url": base_url,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "prompt_length": len(prompt),
        "prompt_preview": prompt[:50] + "..." if len(prompt) > 50 else prompt,
        "is_third_party_api": is_third_party_api
    }
    logging.info(f"OpenAI请求参数: {json.dumps(request_params, ensure_ascii=False)}")
    if is_third_party_api:
        try:
            return call_direct_http_api(prompt, temperature, max_tokens)
        except Exception as e:
            logging.warning(f"直接HTTP请求失败，尝试使用OpenAI库: {str(e)}")
    try:
        client = get_client()
        if not client:
            raise ValueError("无法创建OpenAI客户端")
        request_args = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "你是一名专业的需求分析专家，擅长发现需求文档中的问题。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if "验证模型" not in prompt:
            request_args["response_format"] = {"type": "json_object"}
        logging.info(f"OpenAI API请求参数: {json.dumps(request_args, ensure_ascii=False)}")
        response = client.chat.completions.create(**request_args)
        return response.choices[0].message.content
    except Exception as e:
        error_message = str(e)
        if hasattr(e, 'response'):
            try:
                response_json = e.response.json()
                logging.error(f"OpenAI API完整错误响应: {json.dumps(response_json, ensure_ascii=False)}")
                if 'error' in response_json:
                    error_message = f"{response_json['error'].get('message', error_message)}"
            except Exception as parse_err:
                logging.error(f"解析错误响应失败: {parse_err}")
                pass
        if not is_third_party_api and ("401" in error_message or "unauthorized" in error_message.lower()):
            try:
                logging.info(f"尝试使用直接HTTP请求方式作为备选")
                return call_direct_http_api(prompt, temperature, max_tokens)
            except Exception as http_err:
                logging.error(f"直接HTTP请求也失败: {str(http_err)}")
        if "401" in error_message or "unauthorized" in error_message.lower() or "authentication" in error_message.lower():
            raise ValueError(f"Error code: 401 - API密钥无效或认证失败, 请检查API密钥和基础URL设置。详细信息: {error_message}")
        elif "model" in error_message.lower() and ("not found" in error_message.lower() or "does not exist" in error_message.lower()):
            raise ValueError(f"指定的模型 '{model_name}' 不存在或不可用，请检查模型名称")
        else:
            raise ValueError(f"调用OpenAI API时出错: {error_message}")

def call_direct_http_api(prompt, temperature, max_tokens):
    """
    使用直接HTTP请求调用兼容OpenAI的API
    """
    import requests
    import logging
    config = get_config()
    openai_config = config.get("openai", {})
    model_name = openai_config.get("model_name", "gpt-4o")
    api_key = openai_config.get("api_key", "")
    base_url = openai_config.get("base_url", "")
    if "chat/completions" in base_url:
        url = base_url
        logging.info(f"使用预配置的完整端点URL: {url}")
    else:
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        url = f"{base_url}/chat/completions"
        logging.info(f"构建端点URL: {url}")
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "response_format": {"type": "text"}
    }
    auth_header = f"Bearer {api_key}"
    headers = {
        "Authorization": auth_header,
        "Content-Type": "application/json"
    }
    logging.info(f"直接HTTP请求 - URL: {url}")
    logging.info(f"直接HTTP请求 - 模型: {model_name}")
    logging.info(f"直接HTTP请求 - 认证头格式: {auth_header[:10]}...{auth_header[-4:]}")
    try:
        # 实际请求已注释，防止误调用
        # response = requests.post(url, json=payload, headers=headers)
        raise Exception("直接HTTP请求已被禁用")
        # if response.status_code != 200:
        #     logging.error(f"API请求失败: 状态码 {response.status_code}")
        #     logging.error(f"响应内容: {response.text}")
        #     raise ValueError(f"API请求失败: 状态码 {response.status_code}, 响应: {response.text}")
        # result = response.json()
        # if "choices" in result and len(result["choices"]) > 0:
        #     message = result["choices"][0].get("message", {})
        #     content = message.get("content", "")
        #     return content
        # else:
        #     logging.error(f"API响应格式不符合预期: {json.dumps(result, ensure_ascii=False)}")
        #     raise ValueError(f"API响应格式不符合预期")
    except requests.RequestException as e:
        logging.error(f"HTTP请求错误: {str(e)}")
        raise ValueError(f"HTTP请求错误: {str(e)}")
    except json.JSONDecodeError as e:
        logging.error(f"响应不是有效的JSON: {str(e)}")
        raise ValueError(f"响应不是有效的JSON: {str(e)}")
    except Exception as e:
        logging.error(f"调用API时发生错误: {str(e)}")
        raise ValueError(f"调用API时发生错误: {str(e)}")

# 其它API调用函数（如call_ollama_api）可在此继续实现
