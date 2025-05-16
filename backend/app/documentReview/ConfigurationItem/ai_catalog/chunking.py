"""
文档分块模块
用于大文档分块处理，支持滑动窗口，确保能有效处理超大规格说明书
"""
import logging

def split_document(paragraphs, max_chars=100000, overlap=10000):
    """
    将文档按照最大字符数进行分块，支持滑动窗口提高提取准确性
    
    Args:
        paragraphs: 段落列表
        max_chars: 每块最大字符数，默认10万字符
        overlap: 重叠字符数，默认1万字符
        
    Returns:
        chunks: 分块后的段落列表的列表
    """
    chunks = []
    current_chunk = []
    current_length = 0
    overlap_start = None
    
    logging.info(f"开始分块处理文档，共 {len(paragraphs)} 个段落，最大块大小 {max_chars}，重叠大小 {overlap}")
    
    for para in paragraphs:
        para_length = len(para)
        
        # 如果当前段落加入后超过最大长度，则开始新的块
        if current_length + para_length > max_chars and current_chunk:
            chunks.append(current_chunk)
            
            # 创建重叠部分
            if overlap > 0 and overlap_start is not None:
                # 复制重叠部分到新块
                overlap_paragraphs = current_chunk[overlap_start:]
                current_chunk = overlap_paragraphs.copy()
                current_length = sum(len(p) for p in current_chunk)
            else:
                current_chunk = []
                current_length = 0
                
            overlap_start = None
        
        current_chunk.append(para)
        current_length += para_length
        
        # 记录可能成为重叠起始部分的位置
        # 当积累的字符数接近(max_chars - overlap)时，标记为重叠起始点
        if overlap_start is None and current_length >= (max_chars - overlap):
            overlap_start = len(current_chunk) - 1
    
    # 添加最后一块（如果有内容）
    if current_chunk:
        chunks.append(current_chunk)
    
    logging.info(f"文档分块完成，共生成 {len(chunks)} 个块")
    
    # 记录各块的大小信息用于调试
    for i, chunk in enumerate(chunks):
        chunk_size = sum(len(p) for p in chunk)
        logging.debug(f"块 {i+1}: {len(chunk)} 个段落，{chunk_size} 个字符")
    
    return chunks
