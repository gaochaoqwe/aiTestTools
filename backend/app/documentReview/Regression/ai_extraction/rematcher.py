"""
需求重新匹配模块
用于处理未匹配到的需求
"""
import logging
import tiktoken
from docx import Document
from ..ai_extraction.client import get_client
from ..ai_extraction.api import query_ai_model
from ..ai_extraction.utils import extract_json_from_text
from ..ai_extraction.chunking import count_tokens

def find_last_matched_position(paragraphs, last_requirement_content, fuzzy_match=True):
    """
    在文档中找到最后一个匹配到的需求的结束位置
    
    Args:
        paragraphs: 文档段落列表
        last_requirement_content: 最后一个匹配到的需求内容
        fuzzy_match: 是否使用模糊匹配
        
    Returns:
        最后一个匹配的需求结束位置的索引，如果未找到则返回0
    """
    if not last_requirement_content or not paragraphs:
        return 0
    
    # 为了提高鲁棒性，只使用内容的前200个字符进行匹配
    match_text = last_requirement_content[:200]
    
    # 从后向前搜索，找到最后一个包含匹配文本的段落
    for i in range(len(paragraphs) - 1, -1, -1):
        paragraph = paragraphs[i]
        
        if fuzzy_match:
            # 模糊匹配：如果段落包含匹配文本的大部分（至少30个字符）
            min_match_length = min(30, len(match_text))
            for j in range(len(match_text) - min_match_length + 1):
                if match_text[j:j+min_match_length] in paragraph:
                    return i + 1  # 返回下一个段落的索引
        else:
            # 精确匹配
            if match_text in paragraph:
                return i + 1  # 返回下一个段落的索引
    
    # 如果没有找到匹配，返回文档开头
    return 0

def rematch_requirements(file_path, matched_requirements, window_size=3000, model=None):
    """
    重新匹配未匹配到的需求
    
    Args:
        file_path: Word文档路径
        matched_requirements: 已匹配到的需求字典 {需求名称: 内容}
        window_size: 滑动窗口大小
        model: 使用的AI模型名称
        
    Returns:
        新匹配到的需求字典 {需求名称: 内容}
    """
    logging.info(f"开始重新匹配未匹配需求，已有{len(matched_requirements)}个已匹配需求")
    
    # 获取AI客户端
    client = get_client()
    if not client:
        logging.error("无法创建AI客户端，请检查配置")
        return {}
    
    # 加载文档
    doc = Document(file_path)
    paragraphs = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
    logging.debug(f"文档包含 {len(paragraphs)} 个段落")
    
    # 如果没有已匹配的需求，从头开始
    if not matched_requirements:
        logging.info("没有已匹配的需求，将从文档开头开始匹配")
        start_position = 0
    else:
        # 找到最后一个已匹配需求的内容
        last_requirement_content = list(matched_requirements.values())[-1]
        # 找到这个需求在文档中的位置
        start_position = find_last_matched_position(paragraphs, last_requirement_content)
        logging.info(f"从第 {start_position} 个段落开始重新匹配")
    
    # 如果已经到了文档末尾，无需再次匹配
    if start_position >= len(paragraphs):
        logging.info("已到达文档末尾，无需再次匹配")
        return {}
    
    # 构建从最后匹配位置开始的文本块
    remaining_paragraphs = paragraphs[start_position:]
    total_text = "\n".join(remaining_paragraphs)
    
    # 确保不超过token限制
    encoder = tiktoken.get_encoding("cl100k_base")
    tokens = encoder.encode(total_text)
    
    if len(tokens) > window_size:
        # 如果剩余内容超过窗口大小，截断
        tokens = tokens[:window_size]
        total_text = encoder.decode(tokens)
        logging.info(f"剩余内容已截断至 {window_size} 个token")
    else:
        logging.info(f"剩余内容包含 {len(tokens)} 个token")
    
    # 构建提示词
    prompt = f"""
    你是一个专业的需求文档分析专家，请从以下文档内容中识别并提取所有3.1.x和3.2.x格式的需求章节。
    
    文档的前面部分已经成功提取了一些需求，我们需要你继续提取剩余的未匹配需求。
    注意：只提取3.1.x和3.2.x格式开头的章节，忽略其他格式。
    
    以下是文档的剩余部分：
    ---
    {total_text}
    ---
    
    请按照以下JSON格式返回你找到的需求信息：
    ```json
    {{
      "chapters": [
        {{
          "chapter_number": "章节号，例如3.1.1",
          "title": "需求标题",
          "content": "需求全部内容，包括依据、标识号、说明等"
        }},
        ...
      ]
    }}
    ```
    
    如果在文档中没有找到任何需求，请返回空的chapters数组，但保持JSON格式完整。
    """
    
    # 调用AI模型
    try:
        logging.info("开始调用AI模型进行需求重新匹配")
        response = query_ai_model(client, prompt, model)
        
        # 解析JSON响应
        result = extract_json_from_text(response)
        
        if result and "chapters" in result:
            chapters = result["chapters"]
            if not isinstance(chapters, list):
                if isinstance(chapters, dict):
                    chapters = [chapters]
                else:
                    chapters = []
            
            # 转换为需求字典
            new_requirements = {}
            for chapter in chapters:
                try:
                    if chapter["chapter_number"].startswith("3.1.") or chapter["chapter_number"].startswith("3.2."):
                        requirement_name = chapter["title"]
                        # 检查是否已经在已匹配需求中
                        if requirement_name not in matched_requirements:
                            new_requirements[requirement_name] = chapter["content"]
                            logging.info(f"新匹配到需求: {requirement_name}")
                except KeyError as e:
                    logging.warning(f"章节缺少必要字段: {e}, 跳过此章节")
            
            logging.info(f"重新匹配完成，找到 {len(new_requirements)} 个新需求")
            return new_requirements
        else:
            logging.warning("未能从AI响应中解析出有效的需求")
            return {}
    except Exception as e:
        logging.error(f"调用AI模型失败: {str(e)}")
        return {}
