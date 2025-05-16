"""
工具模块
提供JSON解析和其他辅助功能
"""
import re
import json
import logging

def extract_json_from_text(text):
    """
    从AI响应中提取JSON部分
    
    Args:
        text: AI响应文本
        
    Returns:
        解析后的JSON对象或None
    """
    # 若text不是字符串类型，返回原始值
    if not isinstance(text, str):
        logging.warning(f"提取JSON时收到非字符串值: {type(text)}")
        if isinstance(text, dict):
            return text  # 如果以及是字典，直接返回
        return None
    
    # 记录原始响应文本的前100个字符（调试用）
    logging.debug(f"尝试解析JSON响应: {text[:100]}...")
    
    # 尝试多种JSON提取模式
    # 模式1: ```json ... ```
    json_match = re.search(r'```json\s*(.+?)```', text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1).strip()
        try:
            return json.loads(json_str)
        except Exception as e:
            logging.warning(f"无法解析JSON模式1: {e}，尝试下一种模式")
    
    # 模式2: { ... }
    json_match = re.search(r'(\{.+\})', text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1).strip()
        try:
            return json.loads(json_str)
        except Exception as e:
            logging.warning(f"无法解析JSON模式2: {e}，尝试下一种模式")
    
    # 模式3: 尝试提取文本中的任何JSON对象
    try:
        # 去除可能的前缀和后缀文本
        cleaned_text = re.sub(r'^[^{]*', '', text)
        cleaned_text = re.sub(r'[^}]*$', '', cleaned_text)
        return json.loads(cleaned_text)
    except Exception as e:
        logging.error(f"无法从响应中提取有效的JSON: {e}")
        
        # 最后尝试将整个文本包装成JSON格式
        try:
            # 将无法解析的文本包装成简单的JSON
            return {"error": "Failed to parse JSON", "text": text}
        except:
            return None

def get_config():
    """
    获取全局配置信息
    
    Returns:
        配置字典
    """
    import os
    import json
    
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..', 'config.json')
    config = {}
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logging.debug(f"从文件读取到配置: {config_path}")
        except Exception as e:
            logging.error(f"读取配置文件出错: {str(e)}")
    
    return config

def merge_requirement_contents(contents, max_length=None):
    """
    合并多个需求内容片段，可能来自不同窗口
    
    Args:
        contents: 内容片段列表
        max_length: 最大合并长度，None表示不限制
        
    Returns:
        合并后的内容
    """
    if not contents:
        return ""
    
    # 如果只有一个内容，直接返回
    if len(contents) == 1:
        return contents[0]
        
    # 合并多个内容
    merged = contents[0]
    
    for content in contents[1:]:
        # 避免内容重复
        if content in merged:
            continue
            
        # 查找最佳合并点
        overlap = find_overlap(merged, content)
        if overlap > 10:  # 有明显重叠
            merged = merged + content[overlap:]
        else:
            merged = merged + "\n\n" + content
            
        # 如果超过最大长度，截断
        if max_length and len(merged) > max_length:
            merged = merged[:max_length]
            break
            
    return merged

def find_overlap(s1, s2, min_overlap=10, max_overlap=200):
    """
    查找两个字符串之间的最大重叠部分
    
    Args:
        s1: 第一个字符串
        s2: 第二个字符串
        min_overlap: 最小重叠长度
        max_overlap: 最大重叠长度，用于限制搜索范围
        
    Returns:
        重叠的字符数量
    """
    # 限制搜索范围，提高效率
    s1_end = s1[-min(len(s1), max_overlap):]
    s2_start = s2[:min(len(s2), max_overlap)]
    
    max_overlap_len = 0
    
    # 尝试不同的重叠长度
    for i in range(min_overlap, min(len(s1_end), len(s2_start)) + 1):
        if s1_end[-i:] == s2_start[:i]:
            max_overlap_len = i
    
    return max_overlap_len
