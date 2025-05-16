"""
AI目录提取器
实现从文档自动提取目录结构的核心功能
"""
import os
import time
import json
import logging
from docx import Document

from ..ai_extraction.api import query_ai_model
from ..ai_extraction.client import get_client
from ..ai_extraction.utils import extract_json_from_text
from .chunking import split_document
from .prompts import CATALOG_EXTRACTION_PROMPT, CATALOG_CONTINUATION_PROMPT

def ai_extract_catalog(file_path, requirement_level=3, model=None):
    """
    使用AI从文档中提取目录结构
    
    Args:
        file_path: Word文档路径
        requirement_level: 需求级别(3-5)，决定提取的章节层级
            3 - 提取类似 3.2.1 这一级别
            4 - 提取类似 3.2.1.1 这一级别
            5 - 提取类似 3.2.1.1.1 这一级别
        model: AI模型名称，默认使用配置文件中指定的模型
        
    Returns:
        提取的需求条目列表 [{name, chapter}, ...]
    """
    start_time = time.time()
    logging.info(f"开始使用AI提取目录结构，文件路径: {file_path}，需求级别: {requirement_level}")
    
    # 获取AI客户端
    client = get_client()
    if not client:
        logging.error("无法创建AI客户端，请检查配置")
        return []
    
    # 从配置文件获取参数
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..', 'config.json')
    max_chars = 100000  # 默认每块最大10万字符
    overlap = 10000  # 默认重叠1万字符
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                catalog_params = config.get("catalog_extraction", {})
                max_chars = catalog_params.get("max_chars", 100000)
                overlap = catalog_params.get("overlap", 10000)
                logging.info(f"使用配置的分块参数: 最大块大小={max_chars}, 重叠={overlap}")
        except Exception as e:
            logging.warning(f"读取配置参数失败: {str(e)}，使用默认配置")
    
    # 加载文档
    doc_load_start = time.time()
    try:
        doc = Document(file_path)
        logging.debug(f"文档加载耗时: {time.time() - doc_load_start:.2f}秒")
    except Exception as e:
        logging.error(f"加载文档失败: {str(e)}")
        return []
    
    # 提取文本内容
    text_start_time = time.time()
    paragraphs = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
    logging.debug(f"文档包含 {len(paragraphs)} 个段落，文本提取耗时: {time.time() - text_start_time:.2f}秒")
    
    # 检查文档大小决定是否需要分块
    doc_size = sum(len(p) for p in paragraphs)
    if doc_size > max_chars:
        logging.info(f"文档大小({doc_size}字符)超过阈值({max_chars}字符)，将进行分块处理")
        chunks = split_document(paragraphs, max_chars, overlap)
    else:
        logging.info(f"文档大小({doc_size}字符)未超过阈值，作为单一块处理")
        chunks = [paragraphs]
    
    # 处理每个块并收集结果
    all_requirements = []
    for i, chunk in enumerate(chunks):
        logging.info(f"处理块 {i+1}/{len(chunks)}")
        
        # 将段落列表合并为文本
        chunk_text = "\n".join(chunk)
        
        # 构建提示
        if i == 0:
            # 第一个块使用初始提示
            prompt = CATALOG_EXTRACTION_PROMPT.format(
                document_content=chunk_text,
                requirement_level=requirement_level
            )
        else:
            # 后续块使用续取提示
            prompt = CATALOG_CONTINUATION_PROMPT.format(
                document_content=chunk_text,
                requirement_level=requirement_level,
                chunk_number=i+1
            )
        
        try:
            # 查询AI模型前详细打印
            print(f"[AI目录提取] 块 {i+1} 请求模型: {model if model else '默认'}, prompt前200字: {prompt[:200]}")
            try:
                response = query_ai_model(client, prompt, model)
                print(f"[AI目录提取] 块 {i+1} 模型原始响应前500字: {str(response)[:500]}")
            except Exception as e:
                import traceback
                print(f"[AI目录提取] 块 {i+1} 调用模型异常: {type(e).__name__}: {e}")
                print(traceback.format_exc())
                raise
            # 解析响应
            result = extract_json_from_text(response)
            if not result:
                logging.warning(f"块 {i+1} 解析失败，跳过")
                continue
                
            # 提取需求列表
            if "requirements" in result and isinstance(result["requirements"], list):
                requirements = result["requirements"]
                
                # 验证每个需求条目
                for req in requirements:
                    if isinstance(req, dict) and "chapter" in req and "name" in req:
                        # 验证章节号
                        chapter = req["chapter"]
                        name = req["name"]
                        
                        # 确保符合需求级别
                        chapter_level = len(chapter.split('.'))
                        if chapter_level >= requirement_level:
                            # 从需求名称中去除章节号前缀
                            # 例如 "3.1.1 用户身份验证功能" -> "用户身份验证功能"
                            requirement_name = name
                            
                            # 检查当前名称是否包含章节号前缀
                            if name.startswith(chapter):
                                # 去除章节号前缀和可能的空格
                                requirement_name = name[len(chapter):].strip()
                            
                            # 检查是否已存在该章节
                            if not any(r["chapter"] == chapter for r in all_requirements):
                                # 添加level字段 - 根据章节号计算级别
                                requirement_level_num = len(chapter.split('.'))
                                
                                all_requirements.append({
                                    "chapter": chapter,
                                    "name": requirement_name,
                                    "level": requirement_level_num  # 添加level字段
                                })
                                logging.debug(f"提取到新需求: 章节={chapter}, 名称={requirement_name}, 级别={requirement_level_num}")
                
                logging.info(f"块 {i+1} 提取到 {len(requirements)} 个需求条目")
            else:
                logging.warning(f"块 {i+1} 未找到需求列表，跳过")
                
        except Exception as e:
            logging.error(f"处理块 {i+1} 时出错: {str(e)}")
    
    # 按章节号排序
    all_requirements.sort(key=lambda x: [int(n) if n.isdigit() else n for n in x["chapter"].split('.')])
    
    # 添加"level"属性
    for req in all_requirements:
        req["level"] = len(req["chapter"].split('.'))
    
    logging.info(f"AI目录提取完成，共提取 {len(all_requirements)} 个需求条目，总耗时: {time.time() - start_time:.2f}秒")
    
    # 记录一些提取的需求作为示例，便于调试
    if all_requirements:
        log_count = min(5, len(all_requirements))
        for i in range(log_count):
            logging.debug(f"示例需求 {i+1}: {all_requirements[i]}")
    
    return all_requirements
