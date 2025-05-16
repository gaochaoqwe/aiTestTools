"""
工具函数模块 - 提供各种辅助功能
"""
import logging
from app.documentReview.Regression.config import get_config
from .api import call_openai_api, call_ollama_api

def validate_model():
    """
    验证当前配置的模型是否可以正常使用
    
    返回:
        str: 模型的响应内容
    """
    try:
        config = get_config()
        provider = config.get("provider", "openai")
        
        # 准备测试提示词
        test_prompt = """
        请回复"模型验证成功"来验证API调用正常工作。
        """
        
        # 设置轻量级的模型参数
        model_params = config.get("model_params", {})
        temperature = 0.1
        max_tokens = 50
        
        # 根据提供商调用不同的API
        if provider == "openai":
            openai_config = config.get("openai", {})
            model_name = openai_config.get("model_name")
            logging.info(f"验证OpenAI模型: {model_name}")
            
            # 判断是否是第三方API
            is_third_party = False
            if "base_url" in openai_config:
                base_url = openai_config.get("base_url", "")
                if base_url:
                    is_third_party = (
                        "siliconflow" in base_url.lower() or 
                        "dashscope" in base_url.lower() or 
                        "qwen" in base_url.lower() or 
                        "zhipu" in base_url.lower()
                    )
            
            try:
                result = call_openai_api(test_prompt, temperature, max_tokens, is_third_party, model_name)
                logging.info(f"OpenAI模型验证成功，响应: {result}")
                return f"模型 {model_name} 验证成功，响应: {result}"
            except Exception as e:
                logging.error(f"OpenAI模型验证失败: {str(e)}")
                raise ValueError(f"OpenAI模型验证失败: {str(e)}")
                
        elif provider == "ollama":
            ollama_config = config.get("ollama", {})
            model_name = ollama_config.get("model_name", "llama3")
            logging.info(f"验证Ollama模型: {model_name}")
            
            try:
                result = call_ollama_api(test_prompt, temperature, max_tokens)
                logging.info(f"Ollama模型验证成功，响应: {result}")
                return f"模型 {model_name} 验证成功，响应: {result}"
            except Exception as e:
                logging.error(f"Ollama模型验证失败: {str(e)}")
                raise ValueError(f"Ollama模型验证失败: {str(e)}")
        
        else:
            raise ValueError(f"不支持的提供商: {provider}")
    
    except Exception as e:
        logging.error(f"模型验证失败: {e}")
        raise

def extract_json_from_text(text):
    """
    从文本中提取JSON对象
    
    参数:
        text: str, 可能包含JSON的文本
    
    返回:
        dict or None: 提取的JSON对象，如果未找到则返回None
    """
    import json
    import re
    
    # 清理文本，尝试提取JSON部分
    text = text.strip()
    
    try:
        # 先尝试直接解析整个文本
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # 尝试从Markdown代码块中提取JSON
    json_pattern = re.compile(r'```(?:json)?\s*\n(.*?)\n\s*```', re.DOTALL)
    match = json_pattern.search(text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    
    # 尝试查找文本中的第一个有效JSON对象
    # 查找可能的JSON开始和结束位置
    start_pos = text.find('{')
    if start_pos >= 0:
        # 找到左括号，现在尝试找到匹配的右括号
        open_brackets = 0
        for i in range(start_pos, len(text)):
            if text[i] == '{':
                open_brackets += 1
            elif text[i] == '}':
                open_brackets -= 1
                if open_brackets == 0:
                    # 找到了完整的JSON对象
                    try:
                        json_text = text[start_pos:i+1]
                        return json.loads(json_text)
                    except json.JSONDecodeError:
                        pass
    
    # 如果以上方法都失败，返回None
    return None

def count_tokens(text):
    """
    计算文本中的token数量
    
    参数:
        text: str, 要计算的文本
    
    返回:
        int: token数量
    """
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        # 如果没有tiktoken，使用简单的估算方法
        words = text.split()
        return len(words) * 1.3  # 简单估算：每个单词约1.3个token

def merge_dicts(dict1, dict2):
    """
    合并两个字典，保留所有键，对于重复的键，使用dict2的值
    
    参数:
        dict1: dict, 第一个字典
        dict2: dict, 第二个字典
    
    返回:
        dict: 合并后的字典
    """
    result = dict1.copy()
    result.update(dict2)
    return result
