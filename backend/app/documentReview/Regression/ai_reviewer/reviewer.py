"""
需求审查模块 - 核心功能
提供对需求的审查和分析功能
"""
import json
import logging
import re

from app.documentReview.Regression.config import get_config
from .api import call_openai_api, call_ollama_api

def review_requirement(requirement):
    """
    对单个需求进行审查
    
    参数:
        requirement: str or dict, 需要审查的需求，可以是字符串或字典
        
    返回:
        dict: 审查结果字典
    """
    # 记录需求详情
    if isinstance(requirement, dict):
        req_name = requirement.get('name', '未命名需求')
        req_chapter = requirement.get('chapter', '未知章节')
        req_content = requirement.get('content', '')
        content_length = len(req_content) if req_content else 0
        
        logging.debug(f"开始审查需求《{req_name}》，章节: {req_chapter}, 内容长度: {content_length} 字符")
        if content_length > 0:
            content_preview = req_content[:100] + '...' if content_length > 100 else req_content
            logging.debug(f"需求内容预览: {content_preview}")
        else:
            logging.debug("需求内容为空或未提供")
    else:
        logging.debug(f"审查需求: 非字典类型, 类型={type(requirement)}")
        if isinstance(requirement, str):
            preview = requirement[:100] + '...' if len(requirement) > 100 else requirement
            logging.debug(f"需求内容预览: {preview}")
    
    try:
        # 处理字符串类型的需求
        if isinstance(requirement, str):
            try:
                # 尝试解析为JSON
                requirement_dict = json.loads(requirement)
            except json.JSONDecodeError:
                # 如果无法解析，创建一个默认结构
                requirement_dict = {
                    "name": "未命名需求",
                    "chapter": "未知章节",
                    "content": requirement
                }
        else:
            requirement_dict = requirement
        
        # 确保requirement_dict至少包含必要的字段
        if "name" not in requirement_dict:
            requirement_dict["name"] = "未命名需求"
        if "content" not in requirement_dict:
            requirement_dict["content"] = "需求内容未提供"
        
        # 添加详细日志
        req_name = requirement_dict.get('name', '未命名需求')
        req_chapter = requirement_dict.get('chapter', '未知章节')
        req_content = requirement_dict.get('content', '')
        content_length = len(req_content) if req_content else 0
        
        logging.debug(f"开始审查需求《{req_name}》，章节: {req_chapter}, 内容长度: {content_length} 字符")
        if content_length > 0:
            content_preview = req_content[:100] + '...' if content_length > 100 else req_content
            logging.debug(f"需求内容预览: {content_preview}")
        else:
            logging.debug("需求内容为空或未提供")
        
        config = get_config()
        provider = config.get("provider", "openai")
        logging.debug(f"使用提供商: {provider}")
        
        # 准备提示词
        prompt = f"""
        请作为一名专业的需求审查专家，审查以下软件需求，找出潜在问题，严格按照要求的JSON格式返回结果：
        
        需求名称: {requirement_dict.get('name', '未命名需求')}
        需求内容:
        {requirement_dict.get('content', '需求内容未提供')}
        
        请仔细审查上述需求，找出所有潜在问题，例如：不明确的描述、不完整的约束条件、性能要求不具体、冲突的需求等。
        
        审查结果必须严格按照以下JSON格式返回（数组中可以包含多个问题）：
        {{
            "requirements_review": [
                {{
                    "problem_title": "问题的具体名称（包含功能名称和问题类型，不超过20个字）",
                    "requirement_description": "简要描述需求要点",
                    "problem_description": "详细描述发现的问题",
                    "problem_location": "指出问题在需求中的具体位置",
                    "impact_analysis": "分析此问题可能带来的影响"
                }}
            ],
            "score": 85,
            "summary": "审查总结"
        }}
        
        必须为每个发现的问题提供所有五个字段：problem_title、requirement_description、problem_description、problem_location和impact_analysis。
        
        其中problem_title是对问题的具体描述，必须包含需求的功能名称和具体问题类型，格式为"[功能名称]+[问题类型]"，如"用户身份验证功能约束不明确"、"用户身份验证功能性能要求不具体"等，不超过20个字。
        
        如果没有发现问题，请在requirements_review数组中返回一个对象，表明需求质量良好。
        请直接返回JSON对象，不要包含任何额外的文字。
        """
        
        model_params = config.get("model_params", {})
        temperature = model_params.get("temperature", 0.1)
        max_tokens = model_params.get("max_tokens", 2000)
        
        try:
            # 尝试使用OpenAI API
            from .client import get_client
            client = get_client()
            
            if client is None:
                # 如果无法创建API客户端，返回模拟数据
                logging.warning("无法创建OpenAI客户端，切换到模拟审查模式")
                review_item = {
                    "name": requirement_dict["name"],
                    "chapter": requirement_dict.get("chapter", ""),
                    "review_result": {
                        "requirements_review": [
                            {
                                "problem_title": f"{requirement_dict['name']}描述细节缺失",
                                "requirement_description": "需求完整性分析",
                                "problem_description": "需求描述缺乏具体细节，可能导致不同理解",
                                "problem_location": "需求说明部分",
                                "impact_analysis": "可能导致开发者对要求理解不一致，影响功能实现"
                            }
                        ],
                        "score": 85,
                        "summary": "需求总体质量良好，但存在一些可以改进的地方"
                    }
                }
                return review_item
            
            # 根据不同提供商调用API
            if provider == "openai":
                # 从配置获取正确的模型名称
                try:
                    openai_config = config.get("openai", {})
                    model_name = openai_config.get("model_name")
                    logging.info(f"使用OpenAI模型名称: {model_name}")
                except Exception as e:
                    logging.error(f"获取模型名称出错: {e}")
                    model_name = None
                    
                result = call_openai_api(prompt, temperature, max_tokens, model_name)
            elif provider == "ollama":
                # 从配置获取正确的模型名称
                try:
                    ollama_config = config.get("ollama", {})
                    model_name = ollama_config.get("model_name", "llama3")
                    logging.info(f"使用Ollama模型名称: {model_name}")
                except Exception as e:
                    logging.error(f"获取模型名称出错: {e}")
                    model_name = "llama3"
                    
                result = call_ollama_api(prompt, temperature, max_tokens, model_name)
            else:
                raise ValueError(f"不支持的模型提供商: {provider}")
            
            # 解析结果
            logging.debug(f"AI返回的原始结果:\n{result}")
            
            try:
                # 清理可能存在的Markdown代码块标记和其他非JSON字符
                # 尝试匹配并去除代码块标记
                import re
                cleaned_result = result
                
                # 匹配并删除```json和```
                json_pattern = re.compile(r'```json\s*\n(.*?)\n\s*```', re.DOTALL)
                match = json_pattern.search(cleaned_result)
                if match:
                    cleaned_result = match.group(1)
                    logging.info("检测到代码块标记，已提取其中的JSON")
                
                # 如果没有特定标记，尝试匹配任何代码块
                if cleaned_result == result:
                    code_block_pattern = re.compile(r'```.*?\n(.*?)\n\s*```', re.DOTALL)
                    match = code_block_pattern.search(cleaned_result)
                    if match:
                        cleaned_result = match.group(1)
                        logging.info("检测到一般代码块标记，已提取其中的内容")
                
                # 在解析前进行额外清理
                # 去除可能的前导和尾随空白
                cleaned_result = cleaned_result.strip()
                
                # 检查是否有额外的非JSON前缀或后缀文本
                if not cleaned_result.startswith('{'):
                    logging.warning("JSON不是以'{'开头，尝试查找JSON开始位置")
                    json_start = cleaned_result.find('{')
                    if json_start >= 0:
                        cleaned_result = cleaned_result[json_start:]
                        logging.info("已去除JSON前的额外文本")
                
                if not cleaned_result.endswith('}'):
                    logging.warning("JSON不是以'}'结尾，尝试查找JSON结束位置")
                    json_end = cleaned_result.rfind('}')
                    if json_end >= 0:
                        cleaned_result = cleaned_result[:json_end+1]
                        logging.info("已去除JSON后的额外文本")
                
                # 解析清理后的JSON结果
                logging.debug(f"清理后的结果:\n{cleaned_result}")
                logging.debug(f"结果字符类型: {type(cleaned_result).__name__}, 长度: {len(cleaned_result)}字符")
                result_json = json.loads(cleaned_result)
                
                # 添加原始需求信息
                review_result = {
                    "name": requirement_dict.get("name", "未命名需求"),
                    "chapter": requirement_dict.get("chapter", ""),
                    "review_result": result_json
                }
                
                logging.info(f"需求《{requirement_dict.get('name', '未命名需求')}》审查完成，发现 {len(result_json.get('requirements_review', []))} 个问题")
                return review_result
                
            except json.JSONDecodeError as e:
                logging.error(f"解析AI返回的JSON失败: {e}")
                # 返回错误信息
                return {
                    "name": requirement_dict.get("name", "未命名需求"),
                    "chapter": requirement_dict.get("chapter", ""),
                    "review_result": {
                        "requirements_review": [{
                            "problem_title": f"{requirement_dict.get('name', '未命名需求')}解析失败",
                            "requirement_description": "需求解析失败",
                            "problem_description": f"AI返回的结果无法解析为JSON: {e}",
                            "problem_location": "整个需求文档",
                            "impact_analysis": "无法进行有效的需求审查，可能导致需求问题被忽略"
                        }],
                        "score": 0,
                        "summary": "无法完成需求审查"
                    }
                }
        
        except Exception as e:
            logging.error(f"调用AI审查需求时出错: {e}")
            # 返回错误信息
            return {
                "name": requirement_dict.get("name", "未命名需求"),
                "chapter": requirement_dict.get("chapter", ""),
                "review_result": {
                    "requirements_review": [{
                        "problem_title": f"{requirement_dict.get('name', '未命名需求')}审查系统错误",
                        "requirement_description": "需求审查系统错误",
                        "problem_description": f"调用AI审查需求时出错: {str(e)}",
                        "problem_location": "系统调用过程",
                        "impact_analysis": "系统无法完成需求审查，可能导致需求缺陷无法发现和修复"
                    }],
                    "score": 0,
                    "summary": "无法完成需求审查"
                }
            }
    except Exception as e:
        logging.error(f"审查需求过程中发生未预期的错误: {str(e)}")
        return {
            "name": "审查过程错误",
            "chapter": "",
            "review_result": {
                "requirements_review": [{
                    "problem_title": "审查系统错误",
                    "requirement_description": "需求审查过程错误",
                    "problem_description": f"审查需求时发生错误: {str(e)}",
                    "problem_location": "审查系统",
                    "impact_analysis": "无法完成需求审查"
                }],
                "score": 0,
                "summary": "需求审查失败"
            }
        }

def review_requirements(requirements):
    """
    批量审查多个需求
    
    参数:
        requirements: list, 需求列表，每个元素可以是字典或字符串
    
    返回:
        list: 包含所有需求审查结果的列表
    """
    logging.info(f"开始批量审查 {len(requirements)} 个需求")
    
    # 记录输入的需求数据详情
    logging.debug(f"需求参数类型: {type(requirements)}")
    
    if len(requirements) > 0:
        sample_req = requirements[0]
        logging.debug(f"第一个需求类型: {type(sample_req)}")
        if isinstance(sample_req, dict):
            logging.debug(f"第一个需求结构: {', '.join(sample_req.keys())}")
            if 'content' in sample_req:
                content_preview = sample_req['content'][:100] + '...' if len(sample_req['content']) > 100 else sample_req['content']
                logging.debug(f"第一个需求内容预览: {content_preview}")
    
    # 检查输入类型
    if not isinstance(requirements, list):
        logging.warning(f"需求参数不是列表类型，而是 {type(requirements)}，尝试转换")
        if isinstance(requirements, str):
            try:
                # 尝试将字符串解析为JSON列表
                requirements = json.loads(requirements)
                logging.debug(f"将字符串解析为JSON列表，解析后长度: {len(requirements)}")
            except json.JSONDecodeError:
                # 如果无法解析，将其作为单个需求处理
                requirements = [requirements]
                logging.debug("无法解析为JSON，将作为单个字符串需求处理")
        else:
            # 如果不是字符串，直接包装为列表
            requirements = [requirements]
            logging.debug(f"将类型{type(requirements[0])}的单个对象包装为列表")
    
    review_results = []
    for i, requirement in enumerate(requirements):
        logging.debug(f"开始审查第 {i+1}/{len(requirements)} 个需求")
        req_name = requirement.get('name', '未命名') if isinstance(requirement, dict) else f'需求{i+1}'
        logging.debug(f"审查需求: {req_name}")
        
        review_result = review_requirement(requirement)
        
        # 记录审查结果的基本信息
        result_name = review_result.get('name', '未命名')
        review_data = review_result.get('review_result', {})
        problems_count = len(review_data.get('requirements_review', []))
        logging.debug(f"需求《{result_name}》审查完成，发现 {problems_count} 个问题")
        
        review_results.append(review_result)
    
    logging.info(f"完成批量审查，共审查 {len(review_results)} 个需求")
    return review_results
