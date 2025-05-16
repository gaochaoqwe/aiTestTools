"""
文档分块模块
提供文档分块和滑动窗口功能
"""
import re
import logging
import tiktoken

def count_tokens(text, model="gpt-3.5-turbo"):
    """
    计算文本的token数量
    
    Args:
        text: 要计算的文本
        model: 使用的模型名称
        
    Returns:
        token数量
    """
    try:
        enc = tiktoken.encoding_for_model(model)
    except:
        enc = tiktoken.get_encoding("cl100k_base")  # 默认编码
    
    return len(enc.encode(text))

def chunk_document(paragraphs, max_tokens=2000):
    """
    将文档分成若干个块，每个块不超过max_tokens个token
    
    Args:
        paragraphs: 段落列表
        max_tokens: 每个块的最大token数
        
    Returns:
        文档块列表
    """
    # 使用tiktoken估算token数量
    try:
        enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
    except:
        enc = tiktoken.get_encoding("cl100k_base")  # 默认编码
    
    chunks = []
    current_chunk = []
    current_chunk_tokens = 0
    
    for para in paragraphs:
        para_tokens = len(enc.encode(para))
        
        # 如果当前段落加上已有内容会超过限制，开始新的块
        if current_chunk_tokens + para_tokens > max_tokens and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = []
            current_chunk_tokens = 0
        
        current_chunk.append(para)
        current_chunk_tokens += para_tokens
    
    # 添加最后一个块（如果有内容）
    if current_chunk:
        chunks.append("\n".join(current_chunk))
    
    return chunks

def chunk_document_with_overlap(paragraphs, window_size=3000, overlap=500):
    """
    使用滑动窗口将文档分成若干个块，每个块不超过window_size个token，并与前一个块有overlap个token重叠
    
    Args:
        paragraphs: 段落列表
        window_size: 每个块的最大token数
        overlap: 与前一个块重叠的token数
        
    Returns:
        文档块列表和每块最后包含的章节标识列表
    """
    # 使用tiktoken估算token数量
    try:
        enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
    except:
        enc = tiktoken.get_encoding("cl100k_base")  # 默认编码
    
    # 计算每个段落的token数和累计token数
    paras_with_tokens = []
    cumulative_tokens = 0
    
    for para in paragraphs:
        tokens = enc.encode(para)
        token_count = len(tokens)
        paras_with_tokens.append((para, tokens, token_count, cumulative_tokens))
        cumulative_tokens += token_count
    
    # 创建滑动窗口
    chunks = []
    last_chapters = []
    
    start_idx = 0
    while start_idx < len(paras_with_tokens):
        # 初始化当前窗口
        current_window = []
        current_tokens = 0
        end_idx = start_idx
        
        # 向前填充窗口直到达到window_size或文档结束
        while end_idx < len(paras_with_tokens) and current_tokens + paras_with_tokens[end_idx][2] <= window_size:
            current_window.append(paras_with_tokens[end_idx][0])
            current_tokens += paras_with_tokens[end_idx][2]
            end_idx += 1
        
        # 如果窗口为空（段落太长），至少包含一个段落
        if not current_window and start_idx < len(paras_with_tokens):
            current_window.append(paras_with_tokens[start_idx][0])
            end_idx = start_idx + 1
        
        # 生成当前块文本
        current_text = "\n".join(current_window)
        chunks.append(current_text)
        
        # 查找当前窗口中最后一个章节标识
        last_chapter = None
        for para in reversed(current_window):
            # 匹配配置项测试中常见的章节号格式: 3.2.1, 3.2.2.1等
            match = re.search(r'(3\.[1-9]\.[0-9]+(?:\.[0-9]+)?)\s', para + " ")
            if match:
                chapter_start = match.start(1)
                # 找到章节标题结束位置（下一个换行或段落结束）
                title_end = para.find("\n", chapter_start)
                if title_end == -1:
                    title_end = len(para)
                
                # 提取章节号和标题
                title_text = para[chapter_start:title_end].strip()
                last_chapter = title_text
                break
        
        last_chapters.append(last_chapter)
        
        # 如果已经处理完所有段落，退出循环
        if end_idx >= len(paras_with_tokens):
            break
        
        # 计算下一个窗口的起始位置（考虑重叠）
        next_start_idx = start_idx
        overlap_tokens = 0
        
        while next_start_idx < end_idx and overlap_tokens < overlap:
            overlap_tokens += paras_with_tokens[next_start_idx][2]
            next_start_idx += 1
        
        # 确保至少前进了一个位置，避免死循环
        start_idx = max(start_idx + 1, end_idx - max(1, next_start_idx - start_idx))
    
    logging.debug(f"使用滑动窗口分割文档: 生成{len(chunks)}个块，窗口大小={window_size}, 重叠={overlap}")
    return chunks, last_chapters
