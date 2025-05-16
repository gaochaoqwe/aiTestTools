"""
配置模块
用于存储应用程序的配置参数，包括模型设置等
"""
import os
import json
import logging
import copy

# 默认配置
DEFAULT_CONFIG = {
    # 模型提供商，可选: "openai", "ollama"
    "provider": "openai",
    
    # OpenAI配置
    "openai": {
        "api_key": "sk-kwmzlwamflklwslrcyunnvyuqveuuzesljlsjktnipekossw",  # 使用测试中验证成功的密钥
        "base_url": "https://api.siliconflow.cn/v1",  # 去掉端点路径
        "model_name": "THUDM/GLM-4-9B-0414"
    },
    
    # Ollama配置
    "ollama": {
        "base_url": os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        "model_name": "llama3",
    },
    
    # 模型参数
    "model_params": {
        "temperature": 0.1,
        "max_tokens": 2000,
    }
}

# 配置文件路径
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.json')

def load_config():
    """
    加载配置文件，如果不存在则创建默认配置
    
    返回:
        dict: 配置参数
    """
    # 如果配置文件存在，则加载
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logging.info(f"已加载配置文件: {CONFIG_PATH}")
            return copy.deepcopy(config)  # 返回深拷贝
        except Exception as e:
            logging.error(f"加载配置文件失败: {e}，将使用默认配置")
            
    # 创建默认配置文件
    save_config(DEFAULT_CONFIG)
    return copy.deepcopy(DEFAULT_CONFIG)  # 返回深拷贝

def save_config(config):
    """
    保存配置到文件
    
    参数:
        config: dict, 配置参数
        
    抛出:
        Exception: 保存失败时抛出异常
    """
    try:
        # 确保config是一个有效的字典
        if not isinstance(config, dict):
            raise ValueError(f"配置必须是字典类型，而不是 {type(config)}")
            
        # 创建父目录（如果不存在）
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        logging.info(f"已保存配置文件: {CONFIG_PATH}")
    except Exception as e:
        error_msg = f"保存配置文件失败: {str(e)}"
        logging.error(error_msg)
        # 重新抛出异常，让API端点能捕获到错误
        raise Exception(error_msg)

# 全局配置对象
config = load_config()

def get_config():
    """
    获取当前配置
    
    返回:
        dict: 配置参数
    """
    return config

def update_config(new_config):
    """
    更新配置
    
    参数:
        new_config: dict, 新配置参数
    
    返回:
        dict: 更新后的配置
    """
    global config
    # 递归更新配置
    def update_nested_dict(d, u):
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                update_nested_dict(d[k], v)
            else:
                d[k] = v
    
    update_nested_dict(config, new_config)
    save_config(config)
    return config
