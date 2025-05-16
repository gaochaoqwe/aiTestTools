"""
模型可用性验证相关业务逻辑
"""
import logging
import json
from app.documentReview.ConfigurationItem.config import get_config
from app.documentReview.ConfigurationItem.review.review_client import get_client

def validate_model():
    """
    验证当前配置的模型是否可以正常使用
    返回: dict: {"success": bool, "response"/"error": str}
    """
    logging.info("开始验证模型配置")
    config = get_config()
    provider = config.get("provider", "openai")
    prompt = "你好，请简单回复一句问候语，验证模型连接正常。"
    model_params = config.get("model_params", {})
    temperature = model_params.get("temperature", 0.7)
    max_tokens = 100
    try:
        if provider == "openai":
            openai_config = config.get("openai", {})
            model_name = openai_config.get("model_name", "gpt-4o")
            api_key = openai_config.get("api_key", "")
            base_url = openai_config.get("base_url", "")
            logging.info(f"OpenAI配置 - 模型: {model_name}")
            logging.info(f"完整API密钥【调试用】: '{api_key}'")
            logging.info(f"基础URL: {base_url}")
            logging.info(f"模型参数 - 温度: {temperature}, 最大令牌数: {max_tokens}")
            is_third_party_api = (
                "siliconflow" in base_url or 
                "glm" in base_url.lower() or 
                "qwen" in base_url.lower() or 
                "zhipu" in base_url.lower()
            )
            request_info = {
                "provider": provider,
                "model": model_name,
                "api_key_prefix": api_key[:4] if api_key else "",
                "api_key_length": len(api_key) if api_key else 0,
                "base_url": base_url,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "prompt_length": len(prompt),
                "prompt_preview": prompt[:30],
                "is_third_party_api": is_third_party_api
            }
            logging.info(f"OpenAI请求参数: {json.dumps(request_info, ensure_ascii=False)}")
            try:
                logging.info("使用OpenAI库进行验证")
                client = get_client()
                if not client:
                    raise ValueError("无法创建OpenAI客户端")
                system_message = "你是一名专业的需求分析专家，擅长发现需求文档中的问题。"
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ]
                request_params = {
                    'model': model_name,
                    'messages': messages,
                    'temperature': temperature,
                    'max_tokens': max_tokens
                }
                logging.info(f"OpenAI API请求参数: {json.dumps(request_params, ensure_ascii=False)}")
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                content = response.choices[0].message.content
                logging.info(f"OpenAI模型验证成功，返回: {content}")
                return {"success": True, "response": content}
            except Exception as e:
                error_str = str(e)
                full_error = getattr(e, 'response', None)
                if full_error:
                    try:
                        response_json = full_error.json()
                        logging.error(f"OpenAI API完整错误响应: {json.dumps(response_json, ensure_ascii=False)}")
                        if 'error' in response_json:
                            error_str = f"{response_json['error'].get('message', error_str)}"
                    except Exception as parse_err:
                        logging.error(f"解析错误响应失败: {str(parse_err)}")
                if "401" in error_str:
                    err_msg = f"Error code: 401 - API密钥无效或认证失败, 请检查API密钥和基础URL设置。详细信息: {error_str}"
                elif "404" in error_str:
                    err_msg = f"Error code: 404 - 请求的资源不存在, 请检查API基础URL和模型名称设置。详细信息: {error_str}"
                elif "429" in error_str:
                    err_msg = f"Error code: 429 - 请求过于频繁或超出配额, 请稍后再试。详细信息: {error_str}"
                elif "500" in error_str or "502" in error_str or "503" in error_str:
                    err_msg = f"Error code: {error_str[:3]} - 服务器错误, 请稍后再试。详细信息: {error_str}"
                else:
                    err_msg = f"模型请求失败: {error_str}"
                logging.error(f"模型验证失败: {err_msg}")
                return {"success": False, "error": err_msg}
        elif provider == "ollama":
            # Ollama API调用逻辑
            pass
        else:
            raise ValueError(f"不支持的模型提供商: {provider}")
    except Exception as e:
        logging.error(f"模型验证失败: {e}")
        raise
