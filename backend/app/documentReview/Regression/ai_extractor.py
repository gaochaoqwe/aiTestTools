"""
基于AI的需求提取模块
使用大型语言模型直接从文档中识别和提取需求章节

兼容层：此文件现在是一个向后兼容的包装器，实际实现已移至ai_extraction包
"""
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

# 设置日志配置
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def get_client():
    """
    获取AI客户端 - 兼容层
    基于requirement_reviewer.py中的get_client实现
    """
    # 直接委托给新模块的实现
    from .ai_extraction.client import get_client as new_get_client
    return new_get_client()

def chunk_document(paragraphs, max_tokens=2000):
    """
    将文档分成若干个块，每个块不超过max_tokens个token - 兼容层
    
    Args:
        paragraphs: 段落列表
        max_tokens: 每个块的最大token数
        
    Returns:
        文档块列表
    """
    # 委托给新模块实现
    from .ai_extraction.chunking import chunk_document as new_chunk_document
    return new_chunk_document(paragraphs, max_tokens)

def chunk_document_with_overlap(paragraphs, window_size=3000, overlap=500):
    """
    使用滑动窗口将文档分成若干个块 - 兼容层
    
    Args:
        paragraphs: 段落列表
        window_size: 每个块的最大token数
        overlap: 与前一个块重叠的token数
        
    Returns:
        文档块列表和每块最后包含的章节标识列表
    """
    # 委托给新模块实现
    from .ai_extraction.chunking import chunk_document_with_overlap as new_chunk_with_overlap
    return new_chunk_with_overlap(paragraphs, window_size, overlap)

def extract_json_from_text(text):
    """
    从AI响应中提取JSON部分 - 兼容层
    
    Args:
        text: AI响应文本
        
    Returns:
        解析后的JSON对象或None
    """
    # 委托给新模块实现
    from .ai_extraction.utils import extract_json_from_text as new_extract_json
    return new_extract_json(text)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def query_ai_model(client, prompt, model=None):
    """
    向AI模型发送请求 - 兼容层
    
    Args:
        client: OpenAI客户端
        prompt: 提示文本
        model: 模型名称
        
    Returns:
        AI的响应文本
    """
    # 委托给新模块实现
    from .ai_extraction.api import query_ai_model as new_query_ai_model
    return new_query_ai_model(client, prompt, model)

def ai_extract_requirements(file_path, model=None):
    """
    使用AI提取需求内容，支持滑动窗口和上下文回溯 - 兼容层
    
    Args:
        file_path: Word文档路径
        model: 使用的AI模型名称
        
    Returns:
        提取的需求字典 {需求名称: 内容}
    """
    # 委托给新模块实现
    logging.debug(f"AI提取需求原始传入模型: {model}, 调用兼容层")
    from .ai_extraction.extractor import ai_extract_requirements as new_extract
    return new_extract(file_path, model)

def ai_extract_specific_requirement(file_path, requirement_name, model=None):
    """
    使用AI提取特定需求的内容 - 兼容层
    
    Args:
        file_path: Word文档路径
        requirement_name: 需求名称
        model: 使用的AI模型名称
        
    Returns:
        需求内容字符串或None
    """
    # 记录原始传入的模型名称以方便调试
    logging.debug(f"特定AI提取需求原始传入模型: {model}, 调用兼容层")
    # 委托给新模块实现
    from .ai_extraction.extractor import ai_extract_specific_requirement as new_extract_specific
    return new_extract_specific(file_path, requirement_name, model)

def ai_extract_named_requirements(file_path, requirement_names, model="gpt-3.5-turbo"):
    """
    使用AI提取指定需求名称的内容 - 兼容层
    
    Args:
        file_path: Word文档路径
        requirement_names: 需求名称列表
        model: 使用的AI模型名称
        
    Returns:
        提取的需求字典 {需求名称: 内容}
    """
    # 记录原始传入的模型名称以方便调试
    logging.debug(f"命名需求提取，原始传入模型: {model}, 调用兼容层")
    # 委托给新模块实现
    from .ai_extraction.extractor import ai_extract_named_requirements as new_extract_named
    return new_extract_named(file_path, requirement_names, model)

def ai_rematch_requirements(file_path, matched_requirements, model=None):
    """
    重新匹配未匹配到的需求 - 兼容层
    
    Args:
        file_path: Word文档路径
        matched_requirements: 已匹配到的需求字典 {需求名称: 内容}
        model: 使用的AI模型名称
        
    Returns:
        合并后的需求字典 {需求名称: 内容}，包含原有的匹配需求和新匹配的需求
    """
    # 记录原始传入的模型名称以方便调试
    logging.debug(f"AI重新匹配需求原始传入模型: {model}, 调用兼容层")
    # 委托给新模块实现
    from .ai_extraction.extractor import ai_rematch_requirements as new_rematch
    return new_rematch(file_path, matched_requirements, model)
