"""
AI客户端模块
用于创建和管理AI API客户端
"""
import os
import json
import logging
import requests
from openai import OpenAI

def get_client():
    """
    获取AI客户端
    为配置项测试提供AI客户端
    
    Returns:
        OpenAI客户端对象或None
    """
    # 从环境变量中获取API密钥（优先级最高）
    env_api_key = os.environ.get("OPENAI_API_KEY", "")
    if env_api_key:
        logging.info("从环境变量中读取到OpenAI API密钥")
    
    # 直接从配置文件中读取配置
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..', 'config.json')
    file_config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                logging.info(f"直接从文件读取配置: {config_path}")
        except Exception as e:
            logging.error(f"读取配置文件时出错: {str(e)}")
    
    # 使用文件中的配置作为主要配置
    config = file_config
    logging.info(f"当前系统中的配置: {config}")
    
    # 文件API密钥
    file_api_key = ""
    if "openai" in file_config and "api_key" in file_config["openai"]:
        file_api_key = file_config["openai"]["api_key"]
    
    # 如果环境变量中有API密钥，优先使用
    api_key = env_api_key if env_api_key else file_api_key
    
    # 确定要使用的API客户端类型（根据provider）
    provider = config.get("provider", "openai")
    if provider == "openai" and api_key:
        try:
            # 对API密钥进行部分隐藏，用于日志记录
            masked_key = "****"
            if api_key and len(api_key) > 8:
                masked_key = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]
            logging.debug(f"创建OpenAI客户端: API密钥: {masked_key}")
            
            # 获取基础URL（如果配置中有）
            openai_config = config.get("openai", {})
            base_url = openai_config.get("base_url")
            
            if not base_url:
                logging.info("使用OpenAI默认API端点")
                
                # 创建标准OpenAI客户端
                client = OpenAI(
                    api_key=api_key
                )
                
                return client
            
            # 检查是否为第三方API（非官方OpenAI端点）
            is_third_party_api = ("siliconflow" in base_url or 
                                 "glm" in base_url.lower() or 
                                 "qwen" in base_url.lower() or 
                                 "zhipu" in base_url.lower())
            
            if is_third_party_api:
                logging.info(f"使用第三方API: {base_url}")
                
                # 检查base_url是否包含完整路径
                if "chat/completions" in base_url:
                    logging.warning(f"base_url包含具体端点路径，这可能导致OpenAI库出现问题")
                    # 提取基础URL部分（去掉/chat/completions）
                    base_url = base_url.split("/chat/completions")[0]
                    logging.info(f"已提取基础URL: {base_url}")
            
            # 创建完整的授权头
            auth_header = f"Bearer {api_key}"
            logging.info(f"使用自定义认证头: {auth_header[:10]}...{auth_header[-4:]}")
            
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
    
    elif provider == "ollama":
        # Ollama不需要创建客户端，直接使用requests库调用
        logging.info("使用Ollama API，不需要创建客户端")
        return None
    else:
        logging.error(f"不支持的提供商: {provider}")
        return None
