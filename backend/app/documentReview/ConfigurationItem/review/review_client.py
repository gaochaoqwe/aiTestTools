"""
AI客户端与配置加载模块
"""
import os
import json
import logging
from openai import OpenAI
from app.documentReview.ConfigurationItem.config import get_config

def get_client():
    """
    根据配置获取相应的AI客户端
    返回: 客户端对象或None
    """
    env_api_key = os.environ.get("OPENAI_API_KEY", "")
    if env_api_key:
        logging.info("从环境变量中读取到OpenAI API密钥")
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.json')
    file_config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                logging.info(f"直接从文件读取配置: {config_path}")
        except Exception as e:
            logging.error(f"读取配置文件时出错: {str(e)}")
    config = get_config()
    logging.info(f"当前系统中的配置: {config}")
    file_api_key = ""
    if "openai" in file_config and "api_key" in file_config["openai"]:
        file_api_key = file_config["openai"]["api_key"]
    sys_api_key = ""
    if "openai" in config and "api_key" in config["openai"]:
        sys_api_key = config["openai"]["api_key"]
    if file_api_key != sys_api_key:
        logging.warning(f"文件配置与内存配置中的API密钥不一致！")
        logging.warning(f"文件密钥长度: {len(file_api_key)}, 内存密钥长度: {len(sys_api_key)}")
    if env_api_key:
        if "openai" not in config:
            config["openai"] = {}
        config["openai"]["api_key"] = env_api_key
    if not sys_api_key and file_api_key:
        logging.warning(f"配置对象中无API密钥，使用配置文件中的密钥代替")
        if "openai" not in config:
            config["openai"] = {}
        config["openai"]["api_key"] = file_api_key
    provider = config.get("provider", "openai")
    if provider == "openai":
        openai_config = config.get("openai", {})
        api_key = openai_config.get("api_key", "")
        base_url = openai_config.get("base_url", "")
        if not api_key:
            logging.error("OpenAI API密钥未设置")
            if file_api_key:
                logging.warning("使用配置文件中的API密钥作为最后尝试")
                api_key = file_api_key
                base_url = file_config.get("openai", {}).get("base_url", base_url)
            else:
                return None
        masked_key = "****"
        if api_key and len(api_key) > 8:
            masked_key = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]
        logging.debug(f"创建OpenAI客户端: API密钥: {masked_key}, 基础URL: {base_url}")
        try:
            is_third_party_api = ("siliconflow" in base_url or 
                                 "glm" in base_url.lower() or 
                                 "qwen" in base_url.lower() or 
                                 "zhipu" in base_url.lower())
            if is_third_party_api:
                logging.info(f"使用第三方API: {base_url}")
                if "chat/completions" in base_url:
                    logging.warning(f"base_url包含具体端点路径，这可能导致OpenAI库出现问题")
                    base_url = base_url.split("/chat/completions")[0]
                    logging.info(f"已提取基础URL: {base_url}")
            auth_header = f"Bearer {api_key}"
            logging.info(f"使用自定义认证头: {auth_header[:10]}...{auth_header[-4:]}")
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
