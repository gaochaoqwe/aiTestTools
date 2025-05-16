"""
AI需求审查包 - 回归测试专用
提供需求自动审查功能，支持多种AI模型API
"""

# 导出主要函数，方便直接从包导入
from .reviewer import review_requirement, review_requirements
from .document import generate_review_document, generate_review_doc
from .client import get_client
from .utils import validate_model

__all__ = [
    'review_requirement', 
    'review_requirements', 
    'generate_review_document', 
    'generate_review_doc',
    'get_client',
    'validate_model'
]
