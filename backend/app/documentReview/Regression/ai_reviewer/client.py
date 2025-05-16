"""
AI客户端模块 - 处理与AI服务提供商的连接
"""
import os
import logging
import json
from openai import OpenAI

# 导入配置模块
from app.documentReview.Regression.config import get_config

def get_client():
    """
    根据配置获取相应的AI客户端
    
    返回:
        客户端对象或None
    """
    # 从环境变量中获取API密钥（优先级最高）
    env_api_key = os.environ.get("OPENAI_API_KEY", "")
    if env_api_key:
        logging.info("从环境变量中读取到OpenAI API密钥")
    
    # 直接从配置文件中读取配置（辅助方法）
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..', 'config.json')
    file_config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                logging.info(f"直接从文件读取配置: {config_path}")
        except Exception as e:
            logging.error(f"读取配置文件时出错: {str(e)}")
    
    # 从配置系统获取配置（原始方法）
    config = get_config()
    logging.info(f"当前系统中的配置: {config}")
    
    # 比较配置文件和配置对象中的API密钥（调试所用）
    file_api_key = ""
    if "openai" in file_config and "api_key" in file_config["openai"]:
        file_api_key = file_config["openai"]["api_key"]
        
    # 确定最终使用的API密钥
    if env_api_key:
        api_key = env_api_key
    elif "openai" in config and "api_key" in config["openai"]:
        api_key = config["openai"]["api_key"]
    else:
        logging.error("未找到有效的OpenAI API密钥")
        return None
        
    # 对于OpenAI，检查是否配置了base_url
    if "openai" in config and "base_url" in config["openai"]:
        base_url = config["openai"]["base_url"]
        
        # 检查是否是第三方API提供商
        is_third_party_api = False
        if base_url:
            is_third_party_api = (
                "siliconflow" in base_url.lower() or 
                "dashscope" in base_url.lower() or 
                "qwen" in base_url.lower() or 
                "zhipu" in base_url.lower()
            )
            
            if is_third_party_api:
                logging.info(f"使用第三方API: {base_url}")
                
                # 检查base_url是否包含完整路径
                if "chat/completions" in base_url:
                    logging.warning(f"base_url包含具体端点路径，这可能导致OpenAI库出现问题")
                    # 提取基础URL部分（去掉/chat/completions）
                    base_url = base_url.split("/chat/completions")[0]
                    logging.info(f"已提取基础URL: {base_url}")
            
        # 重要修复: 与成功的测试案例保持一致，显式设置认证头
        # 创建完整的授权头，与成功测试一致
        auth_header = f"Bearer {api_key}"
        logging.info(f"使用自定义认证头: {auth_header[:10]}...{auth_header[-4:]}")
        
        try:
            # 构建OpenAI客户端
            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                default_headers={"Authorization": auth_header}
            )
                
            return client
        except Exception as e:
            logging.error(f"创建OpenAI客户端失败: {str(e)}")
            raise ValueError(f"创建OpenAI客户端失败: {str(e)}")
    
    # Ollama不需要创建客户端，直接使用requests库调用
    return None
