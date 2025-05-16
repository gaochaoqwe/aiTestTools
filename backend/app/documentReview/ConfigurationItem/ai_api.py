"""
配置项测试AI提取API接口
用于连接前端和AI提取模块
"""
import os
import logging
import json
import uuid
from datetime import datetime
from flask import jsonify, request, send_file
from docx import Document

from .ai_extraction.extractor import (
    ai_extract_requirements,
    ai_extract_specific_requirement,
    ai_extract_named_requirements,
    ai_rematch_requirements
)

# 导入AI目录提取模块
from .ai_catalog.api import ai_catalog_extraction_api

def register_ai_extraction_apis(app, upload_folder):
    """
    注册AI需求提取相关的API
    
    Args:
        app: Flask应用实例
        upload_folder: 上传文件夹路径
    """
    
    @app.route('/api/ai_extract', methods=['POST'])
    def ai_extract_api():
        """
        AI提取特定需求
        
        JSON参数:
            file_id: 文件ID
            file_name: 文件名
            requirement_names: 需求名称列表
            model: 可选，使用的AI模型名称
            
        返回:
            提取的需求字典 {session_id, requirements: {name: content}}
        """
        try:
            data = request.json
            file_id = data.get('file_id')
            file_name = data.get('file_name')
            requirement_names = data.get('requirement_names', [])
            model = data.get('model')
            
            if not file_id or not file_name:
                return jsonify({'success': False, 'error': '缺少必要参数'}), 400
            
            # 构建文件路径
            file_path = os.path.join(upload_folder, file_id)
            if not os.path.exists(file_path):
                return jsonify({'success': False, 'error': '文件不存在'}), 404
            
            logging.info(f"配置项测试AI提取需求: {file_id}, 需求数量: {len(requirement_names)}")
            
            # 创建会话ID
            session_id = str(uuid.uuid4())
            
            # 提取需求
            requirements = []
            if requirement_names:
                # 提取特定需求
                requirements_data = ai_extract_named_requirements(file_path, requirement_names, model)
            else:
                # 提取所有需求
                requirements_data = ai_extract_requirements(file_path, model)
                
            # 转换格式以适应前端需求
            requirements = []
            if isinstance(requirements_data, list):
                # 如果已经是列表格式，确保字段名称正确
                for req in requirements_data:
                    if isinstance(req, dict):
                        # 处理content可能是对象的情况
                        content = req.get("content", "")
                        content_str = ""
                        
                        # 如果content是字典，将其转换为格式化字符串
                        if isinstance(content, dict):
                            content_parts = []
                            # 处理多种字段格式
                            if 'b' in content:
                                content_parts.append(content['b'])
                            if 'c' in content:
                                content_parts.append(f"\n\n进入条件: {content['c']}")
                            if 'd' in content:
                                content_parts.append(f"\n\n输入: {content['d']}")
                            if 'e' in content:
                                content_parts.append(f"\n\n输出: {content['e']}")
                            if 'f' in content:
                                content_parts.append(f"\n\n处理: {content['f']}")
                            if 'g' in content:
                                content_parts.append(f"\n\n性能: {content['g']}")
                            if 'h' in content:
                                content_parts.append(f"\n\n约束与限制: {content['h']}")
                            content_str = "\n".join(content_parts)
                        elif isinstance(content, str):
                            content_str = content
                            
                        # 确保有内容
                        if not content_str.strip():
                            content_str = f"需求: {req.get('title', '')}" 
                            
                        # 确保在日志中显示标题和章节号信息，便于调试
                        title = req.get("title", "")
                        chapter = req.get("chapter_number", "")
                        logging.info(f"提取到需求：{title}，章节号：{chapter}")
                        
                        requirements.append({
                            "name": title,  # 确保前端收到name字段
                            "chapter": chapter,  # 确保前端收到chapter字段
                            "content": content_str
                            # 移除identifier字段
                        })
            elif isinstance(requirements_data, dict):
                # 如果是字典格式，转换为前端所需的列表格式
                for title, data in requirements_data.items():
                    if isinstance(data, dict):
                        # 提取内容
                        content = data.get("content", "")
                        content_str = ""
                        
                        # 如果content是字典，将其转换为格式化字符串
                        if isinstance(content, dict):
                            content_parts = []
                            # 处理多种字段格式
                            if 'b' in content:
                                content_parts.append(content['b'])
                            if 'c' in content:
                                content_parts.append(f"\n\n进入条件: {content['c']}")
                            if 'd' in content:
                                content_parts.append(f"\n\n输入: {content['d']}")
                            if 'e' in content:
                                content_parts.append(f"\n\n输出: {content['e']}")
                            if 'f' in content:
                                content_parts.append(f"\n\n处理: {content['f']}")
                            if 'g' in content:
                                content_parts.append(f"\n\n性能: {content['g']}")
                            if 'h' in content:
                                content_parts.append(f"\n\n约束与限制: {content['h']}")
                            content_str = "\n".join(content_parts)
                        elif isinstance(content, str):
                            content_str = content
                        
                        # 确保有内容
                        if not content_str.strip():
                            content_str = f"需求: {title}" 
                            
                        # 提取并记录标题和章节号
                        req_title = data.get("title", title)
                        req_chapter = data.get("chapter_number", "")
                        logging.info(f"提取到需求：{req_title}，章节号：{req_chapter}")
                        
                        requirements.append({
                            "name": req_title,  # 确保前端收到name字段
                            "chapter": req_chapter,  # 确保前端收到chapter字段
                            "content": content_str
                            # 移除identifier字段
                        })
                    else:
                        # 纯文本内容的情况
                        # 纯文本情况下的需求处理
                        logging.info(f"纯文本需求：{title}")
                        # 手动提取的需求在utils.py中返回的是title/chapter_number格式，需要转换
                        # 显示每个提取的需求的名称和章节号，便于调试
                        for i, req in enumerate(requirements):
                            logging.info(f"需求{i+1}: name='{req.get('name', '')}', chapter='{req.get('chapter', '')}'")
                        
                        logging.info(f"共提取到{len(requirements)}个需求")
                        
            # 如果处理完后没有提取到任何需求，尝试其他方式解析
            if not requirements and isinstance(requirements_data, dict):
                logging.info("未能提取到需求，尝试其他解析方式")
                # 可能是返回了错误信息或特殊格式
                if 'error' in requirements_data:
                    logging.error(f"AI提取返回错误: {requirements_data['error']}")
                # 尝试直接将requirements_data字典中的其他字段作为需求
                for key, value in requirements_data.items():
                    if key != 'error' and key != 'text' and key != 'requirements':
                        logging.info(f"尝试将键 '{key}' 作为需求名称")
                        requirements.append({
                            "name": key,
                            "chapter": "",
                            "content": str(value)
                        })
            
            # 最后确认每个需求都有正确的字段名
            for req in requirements:
                # 确保字段名称一致
                if 'title' in req and 'name' not in req:
                    req['name'] = req.pop('title')
                if 'chapter_number' in req and 'chapter' not in req:
                    req['chapter'] = req.pop('chapter_number')
            
            # 记录处理结果
            result_folder = os.path.join(upload_folder, 'results')
            os.makedirs(result_folder, exist_ok=True)
            
            result_path = os.path.join(result_folder, f"{session_id}.json")
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'session_id': session_id,
                    'file_id': file_id,
                    'file_name': file_name,
                    'requirements': requirements,
                    'timestamp': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            
            # 输出日志以便调试
            logging.debug(f"准备返回前端的需求数据: {requirements[:2] if len(requirements) >= 2 else requirements}")
            logging.info(f"配置项测试AI提取完成，共找到 {len(requirements)} 个需求")
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'requirements': requirements
            })
            
        except Exception as e:
            logging.exception(f"配置项测试AI提取需求出错: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/rematch_requirements', methods=['POST'])
    def rematch_requirements_api():
        """
        一键重新匹配未匹配需求
        
        JSON参数:
            file_id: 文件ID
            file_name: 文件名
            session_id: 会话ID
            model: 可选，使用的AI模型名称
            
        返回:
            重新匹配的需求字典 {requirements: {name: content}}
        """
        try:
            data = request.json
            file_id = data.get('file_id')
            file_name = data.get('file_name', '')
            session_id = data.get('session_id', '')
            model = data.get('model')
            
            if not file_id:
                return jsonify({'success': False, 'error': '缺少文件ID'}), 400
            
            # 构建文件路径
            file_path = os.path.join(upload_folder, file_id)
            if not os.path.exists(file_path):
                return jsonify({'success': False, 'error': '文件不存在'}), 404
            
            # 获取已匹配需求
            matched_requirements = {}
            if session_id:
                result_path = os.path.join(upload_folder, 'results', f"{session_id}.json")
                if os.path.exists(result_path):
                    try:
                        with open(result_path, 'r', encoding='utf-8') as f:
                            result_data = json.load(f)
                            matched_requirements = result_data.get('requirements', {})
                    except Exception as e:
                        logging.error(f"读取已匹配需求失败: {str(e)}")
            
            logging.info(f"配置项测试重新匹配需求: {file_id}, 已有需求数量: {len(matched_requirements)}")
            
            # 重新匹配需求
            all_requirements_data = ai_rematch_requirements(file_path, matched_requirements, model)
            
            # 转换格式以适应前端需求
            all_requirements = []
            if isinstance(all_requirements_data, list):
                # 如果已经是列表格式，确保字段名称正确
                for req in all_requirements_data:
                    if isinstance(req, dict):
                        # 处理content可能是对象的情况
                        content = req.get("content", "")
                        content_str = ""
                        
                        # 如果content是字典，将其转换为格式化字符串
                        if isinstance(content, dict):
                            content_parts = []
                            # 处理多种字段格式
                            if 'b' in content:
                                content_parts.append(content['b'])
                            if 'c' in content:
                                content_parts.append(f"\n\n进入条件: {content['c']}")
                            if 'd' in content:
                                content_parts.append(f"\n\n输入: {content['d']}")
                            if 'e' in content:
                                content_parts.append(f"\n\n输出: {content['e']}")
                            if 'f' in content:
                                content_parts.append(f"\n\n处理: {content['f']}")
                            if 'g' in content:
                                content_parts.append(f"\n\n性能: {content['g']}")
                            if 'h' in content:
                                content_parts.append(f"\n\n约束与限制: {content['h']}")
                            content_str = "\n".join(content_parts)
                        elif isinstance(content, str):
                            content_str = content
                            
                        # 确保有内容
                        if not content_str.strip():
                            content_str = f"需求: {req.get('title', '')}" 
                            
                        # 提取且记录标题和章节号
                        req_title = req.get("title", "")
                        req_chapter = req.get("chapter_number", "")
                        logging.info(f"重新匹配需求：{req_title}，章节号：{req_chapter}")
                        
                        all_requirements.append({
                            "name": req_title,  # 确保前端收到name字段
                            "chapter": req_chapter,  # 确保前端收到chapter字段
                            "content": content_str
                            # 移除identifier字段
                        })
            elif isinstance(all_requirements_data, dict):
                # 如果是字典格式，转换为前端所需的列表格式
                for title, data in all_requirements_data.items():
                    if isinstance(data, dict):
                        # 提取内容
                        content = data.get("content", "")
                        content_str = ""
                        
                        # 如果content是字典，将其转换为格式化字符串
                        if isinstance(content, dict):
                            content_parts = []
                            # 处理多种字段格式
                            if 'b' in content:
                                content_parts.append(content['b'])
                            if 'c' in content:
                                content_parts.append(f"\n\n进入条件: {content['c']}")
                            if 'd' in content:
                                content_parts.append(f"\n\n输入: {content['d']}")
                            if 'e' in content:
                                content_parts.append(f"\n\n输出: {content['e']}")
                            if 'f' in content:
                                content_parts.append(f"\n\n处理: {content['f']}")
                            if 'g' in content:
                                content_parts.append(f"\n\n性能: {content['g']}")
                            if 'h' in content:
                                content_parts.append(f"\n\n约束与限制: {content['h']}")
                            content_str = "\n".join(content_parts)
                        elif isinstance(content, str):
                            content_str = content
                        
                        # 确保有内容
                        if not content_str.strip():
                            content_str = f"需求: {title}" 
                            
                        # 提取并记录标题和章节号
                        req_title = data.get("title", title)
                        req_chapter = data.get("chapter_number", "")
                        logging.info(f"重新匹配需求：{req_title}，章节号：{req_chapter}")
                        
                        all_requirements.append({
                            "name": req_title,  # 确保前端收到name字段
                            "chapter": req_chapter,  # 确保前端收到chapter字段
                            "content": content_str
                            # 移除identifier字段
                        })
                    else:
                        # 纯文本内容的情况
                        # 纯文本情况下必须确保指定name和chapter
                        logging.info(f"纯文本需求：{title}")
                        all_requirements.append({
                            "name": title,  # 确保前端收到name字段
                            "chapter": "",  # 确保前端收到chapter字段
                            "content": data if isinstance(data, str) else f"需求: {title}"
                            # 无identifier字段
                        })
            
            # 更新会话文件
            if session_id:
                result_folder = os.path.join(upload_folder, 'results')
                os.makedirs(result_folder, exist_ok=True)
                
                result_path = os.path.join(result_folder, f"{session_id}.json")
                with open(result_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'session_id': session_id,
                        'file_id': file_id,
                        'file_name': file_name,
                        'requirements': all_requirements,
                        'timestamp': datetime.now().isoformat()
                    }, f, ensure_ascii=False, indent=2)
            
            # 输出日志以便调试
            logging.debug(f"重新匹配后返回前端的需求数据: {all_requirements[:2] if len(all_requirements) >= 2 else all_requirements}")
            logging.info(f"配置项测试需求重新匹配完成，共找到 {len(all_requirements)} 个需求")
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'requirements': all_requirements
            })
            
        except Exception as e:
            logging.exception(f"配置项测试重新匹配需求出错: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # 注册AI目录提取API
    @app.route('/api/ai_catalog', methods=['POST'])
    def ai_catalog_api():
        return ai_catalog_extraction_api()
