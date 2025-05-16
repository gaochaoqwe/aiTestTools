"""
工具模块
提供JSON解析和其他辅助功能
"""
import re
import json
import logging
import os

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
            return text  # 如果已经是字典，直接返回
        return None
    
    # 记录原始响应文本的前100个字符（调试用）
    logging.info(f"尝试解析JSON响应，原始文本长度: {len(text)}")
    
    # 尝试多种JSON提取模式
    # 模式1: ```json ... ```
    json_match = re.search(r'```(?:json)?\s*(.+?)```', text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1).strip()
        logging.info(f"发现JSON代码块模式1，长度: {len(json_str)}")
        try:
            result = json.loads(json_str)
            logging.info(f"模式1解析成功，结果类型: {type(result)}，内容预览: {str(result)[:200]}")
            logging.info(f"模式1解析结果详情: {json.dumps(result, ensure_ascii=False)}")
            
            # 特别检查requirements字段
            if isinstance(result, dict) and 'requirements' in result:
                requirements = result['requirements']
                logging.info(f"解析到{len(requirements)}个需求，前2个: {requirements[:2] if len(requirements) >= 2 else requirements}")
            
            return result
        except Exception as e:
            logging.warning(f"无法解析JSON模式1: {e}，尝试下一种模式")
            logging.warning(f"模式1问题JSON内容片段: {json_str[:200]}")
    else:
        logging.info("未找到```json```代码块模式")
    
    # 模式2: 直接匹配完整JSON对象 { ... }
    json_matches = re.findall(r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})', text, re.DOTALL)
    if json_matches:
        for i, json_str in enumerate(json_matches):
            logging.info(f"发现JSON对象模式2-{i+1}，长度: {len(json_str)}")
            try:
                result = json.loads(json_str)
                logging.info(f"模式2-{i+1}解析成功，结果: {str(result)[:200]}")
                
                # 检查是否包含requirements
                if isinstance(result, dict) and 'requirements' in result:
                    requirements = result['requirements']
                    logging.info(f"模式2-{i+1}解析到{len(requirements)}个需求")
                    logging.info(f"模式2-{i+1}需求列表详情: {json.dumps(requirements, ensure_ascii=False)}")
                    return result
            except Exception as e:
                logging.warning(f"无法解析JSON模式2-{i+1}: {e}")
    else:
        logging.info("未找到完整JSON对象模式")
    
    # 模式3: 手动提取requirements部分并构建JSON
    requirements_match = re.search(r'"requirements"\s*:\s*\[(.*?)\]', text, re.DOTALL)
    if requirements_match:
        logging.info("找到requirements数组部分，尝试手动解析")
        try:
            # 尝试手动包装为完整JSON
            requirements_str = requirements_match.group(1).strip()
            json_str = '{"requirements": [' + requirements_str + ']}'
            result = json.loads(json_str)
            logging.info(f"模式3解析成功，需求数量: {len(result.get('requirements', []))}")
            logging.info(f"模式3需求列表详情: {json.dumps(result, ensure_ascii=False)}")
            return result
        except Exception as e:
            logging.warning(f"无法解析requirements部分: {e}")
    
    # 模式4: 尝试提取文本中的所有完整需求项
    requirements = []
    requirement_blocks = re.findall(r'\{\s*"chapter_number"[^{}]+?\}', text, re.DOTALL)
    if requirement_blocks:
        logging.info(f"模式4: 找到{len(requirement_blocks)}个需求块")
        for i, block in enumerate(requirement_blocks):
            try:
                req = json.loads(block)
                if isinstance(req, dict) and 'title' in req:
                    logging.info(f"模式4: 成功解析需求{i+1}: {req.get('title', 'unknown')}")
                    requirements.append(req)
            except Exception as e:
                logging.warning(f"模式4: 无法解析需求块{i+1}: {e}")
        
        if requirements:
            logging.info(f"模式4: 共提取到{len(requirements)}个需求")
            return {"requirements": requirements}
    
    # 模式5: 尝试提取文本中的任何JSON对象
    try:
        # 去除可能的前缀和后缀文本
        cleaned_text = re.sub(r'^[^{]*', '', text)
        cleaned_text = re.sub(r'[^}]*$', '', cleaned_text)
        logging.info(f"模式5: 清理后的文本长度: {len(cleaned_text)}")
        result = json.loads(cleaned_text)
        logging.info(f"模式5解析成功，结果: {str(result)[:200]}")
        return result
    except Exception as e:
        logging.error(f"模式5: 无法从响应中提取有效的JSON: {e}")
        
    # 如果所有JSON解析方式失败，尝试手动提取需求信息
    logging.info("所有JSON解析方式失败，尝试手动提取需求信息")
    try:
        # 创建一个手动提取的需求列表
        requirements = []
        
        # 提取标题和章节号模式
        title_chapter_matches = []
        
        # 尝试不同的模式匹配标题和章节号
        pattern1 = re.findall(r'"chapter_number"\s*:\s*"([^"]+)"\s*,\s*"title"\s*:\s*"([^"]+)"', text, re.DOTALL)
        pattern2 = re.findall(r'"title"\s*:\s*"([^"]+)"\s*,\s*"chapter_number"\s*:\s*"([^"]+)"', text, re.DOTALL)
        
        for chapter, title in pattern1:
            title_chapter_matches.append((title, chapter))
            
        for title, chapter in pattern2:
            title_chapter_matches.append((title, chapter))
            
        # 继续尝试其他模式
        pattern3 = re.findall(r'\d+\.\d+\.\d+\s+([^\n]+)', text)
        pattern4 = re.findall(r'\d+\.\d+\s+([^\n]+)', text)
        
        # 提取所有标识符
        all_identifiers = re.findall(r'\bREQ-\d+\.\d+\b', text)
        
        if title_chapter_matches:
            logging.info(f"手动提取: 找到{len(title_chapter_matches)}个标题和章节号匹配")
            
            for i, (title, chapter) in enumerate(title_chapter_matches):
                # 尝试获取标识符
                identifier = f"REQ-{i+1}.1"  # 默认标识符
                if i < len(all_identifiers):
                    identifier = all_identifiers[i]
                    
                # 添加需求
                logging.info(f"手动提取: 成功添加需求 {i+1}: {title}, 章节: {chapter}")
                requirements.append({
                    "title": title,
                    "chapter_number": chapter,
                    "content": f"标识号: {identifier}\n\n需求: {title}" 
                })
                
        # 添加来自模式3和模式4的标题，如果无匹配章节号
        if not requirements and (pattern3 or pattern4):
            for i, title in enumerate(pattern3 + pattern4):
                chapter = f"3.{i+1}"
                identifier = f"REQ-{i+1}.1"
                requirements.append({
                    "title": title,
                    "chapter_number": chapter,
                    "content": f"标识号: {identifier}\n\n需求: {title}"
                })
                logging.info(f"手动提取: 成功添加需求 {i+1}: {title}, 章节: {chapter}, 标识: {identifier}")
                
        if requirements:
            logging.info(f"手动提取: 共提取到{len(requirements)}个需求")
            return {"requirements": requirements}
        else:
            logging.warning("手动提取: 未找到标题和章节号匹配")
        
        # 最后尝试将整个文本包装成JSON格式
        return {"error": "Failed to parse JSON", "text": text[:1000]}
    except Exception as e:
        logging.error(f"手动提取需求失败: {e}")
        return {"error": "Failed to extract requirements", "message": str(e)}

def get_config():
    """
    获取全局配置信息
    
    Returns:
        配置字典
    """
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

def extract_req_identifier(text):
    """
    从文本中提取需求标识符(如REQ-1.1)
    
    Args:
        text: 需求文本
        
    Returns:
        需求标识符或None
    """
    if not text:
        return None
        
    # 匹配REQ-x.x格式
    match = re.search(r'REQ-\d+\.\d+', text)
    if match:
        return match.group(0)
    
    # 也匹配其他可能的格式
    match = re.search(r'标识号[：:]\s*(\S+)', text)
    if match:
        return match.group(1)
        
    return None
