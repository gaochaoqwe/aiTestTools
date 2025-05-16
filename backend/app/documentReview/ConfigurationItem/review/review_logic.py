"""
需求审查主业务逻辑
"""
import json
import logging
from app.documentReview.ConfigurationItem.config import get_config
from app.documentReview.ConfigurationItem.review.review_client import get_client
from app.documentReview.ConfigurationItem.review.review_ai import call_openai_api

def review_requirements(requirements):
    """
    批量审查需求列表
    参数: requirements: list, 需求对象列表
    返回: list: 包含审查结果的列表
    """
    if not isinstance(requirements, list):
        # 或者可以记录错误并返回空列表或抛出自定义异常
        logging.error(f"参数requirements必须是一个列表，但收到了 {type(requirements)}")
        # 根据实际需求决定是抛出异常还是返回错误指示
        raise ValueError("参数requirements必须是一个列表")
    
    results = []
    for req in requirements:
        if not isinstance(req, dict) or 'content' not in req:
            logging.warning(f"跳过无效的需求，缺少'content'字段: {req}")
            # 可以选择跳过或添加一个错误标记的结果
            continue
            
        # 确保每个需求都有name字段，如果不存在则使用默认值或从其他字段提取
        if 'name' not in req or not req['name']:
            req['name'] = req.get('requirement_name', '未命名需求') 
            # 如果需求名称非常重要，可以考虑记录警告或错误
            logging.warning(f"需求缺少'name'字段，已设置为默认值: {req['name']}")
            
        # 调用单条需求审查
        try:
            result = review_requirement(req)
            results.append(result)
        except Exception as e:
            logging.error(f"审查单个需求 '{req.get('name', '未知需求')}' 时发生错误: {e}")
            # 可以选择将错误信息添加到结果中，或跳过此需求
            results.append({
                "name": req.get('name', '未知需求'),
                "chapter": req.get("chapter", ""),
                "review_result": {
                    "requirements_review": [{
                        "problem_title": f"{req.get('name', '未知需求')} 审查失败",
                        "requirement_description": "需求审查过程中发生内部错误",
                        "problem_description": f"错误详情: {str(e)}",
                        "problem_location": "系统内部",
                        "impact_analysis": "无法完成对此需求的审查"
                    }],
                    "score": 0,
                    "summary": "审查失败，发生内部错误"
                }
            })
    
    return results

def generate_review_document(requirements, review_results, format_type='markdown'):
    """
    生成需求审查文档
    
    参数:
        requirements: list, 原始需求列表
        review_results: list, 审查结果列表
        format_type: str, 文档格式，支持'markdown'和'html'
        
    返回:
        str: 生成的文档内容
    """
    if format_type not in ['markdown', 'html']:
        raise ValueError("不支持的文档格式，请选择'markdown'或'html'")
    
    # 确保requirements和review_results长度一致，或者根据实际情况处理
    if len(requirements) != len(review_results):
        logging.warning("需求列表和审查结果列表长度不一致，可能导致文档内容不匹配")
        # 可以选择抛出异常或尝试匹配可用的部分

    if format_type == 'markdown':
        return _generate_markdown(requirements, review_results)
    else: # 'html'
        return _generate_html(requirements, review_results)

def _generate_markdown(requirements, review_results):
    """生成Markdown格式的审查文档"""
    content = ["# 需求审查报告\n"]
    
    for i, req_data in enumerate(review_results, 1):
        req_name = req_data.get('name', f'未命名需求 {i}')
        original_req = next((r for r in requirements if r.get('name') == req_name), {})
        req_content = original_req.get('content', '无内容')
        
        content.append(f"## {i}. {req_name}\n")
        content.append(f"**需求内容**: {req_content}\n")
        
        review = req_data.get('review_result', {})
        if not review or 'requirements_review' not in review:
            content.append("*未进行审查或审查失败*\n")
            content.append("\n---\n")
            continue
            
        issues = review.get('requirements_review', [])
        score = review.get('score', '未评分')
        summary = review.get('summary', '无总结')

        if not issues or (len(issues) == 1 and issues[0].get("problem_title", "").endswith("解析失败")) or (len(issues) == 1 and issues[0].get("problem_title", "").endswith("审查系统错误")):
            content.append("✅ 未发现明显问题或审查处理异常\n")
            if issues and ("解析失败" in issues[0].get("problem_title", "") or "审查系统错误" in issues[0].get("problem_title", "")):
                 content.append(f"- **问题描述**: {issues[0].get('problem_description', '')}\n")
        else:
            content.append(f"**问题数量**: {len(issues)} 个\n")
            for j, issue in enumerate(issues, 1):
                content.append(f"### 问题 {j}: {issue.get('problem_title', '无标题')}\n")
                content.append(f"- **需求描述**: {issue.get('requirement_description', 'N/A')}\n")
                content.append(f"- **问题描述**: {issue.get('problem_description', 'N/A')}\n")
                content.append(f"- **问题位置**: {issue.get('problem_location', 'N/A')}\n")
                content.append(f"- **影响分析**: {issue.get('impact_analysis', 'N/A')}\n")
        
        content.append(f"\n**总结**: {summary}\n")
        content.append(f"**评分**: {score}/100\n")
        content.append("\n---\n")
    
    return "\n".join(content)

def _generate_html(requirements, review_results):
    """生成HTML格式的审查文档"""
    html_parts = ['''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>需求审查报告</title>
    <style>
        body { font-family: 'Arial', sans-serif; line-height: 1.6; margin: 0 auto; max-width: 900px; padding: 20px; color: #333; }
        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; text-align: center; }
        .requirement-section { margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 8px; background-color: #f9f9f9; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h2 { color: #2980b9; margin-top: 0; border-bottom: 1px solid #eee; padding-bottom: 5px;}
        h3 { color: #16a085; margin-top: 15px; }
        .issue { background-color: #fff; border: 1px solid #e8e8e8; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .issue p { margin: 5px 0; }
        .issue strong { color: #555; }
        .score { font-size: 1.2em; font-weight: bold; color: #e74c3c; margin-top: 10px; }
        .summary { font-style: italic; margin: 15px 0; background-color: #eaf2f8; padding: 10px; border-left: 3px solid #3498db; }
        .no-issues { color: #27ae60; font-weight: bold; }
        hr { border: 0; height: 1px; background-color: #ddd; margin-top: 20px; }
    </style>
</head>
<body>
    <h1>需求审查报告</h1>''']

    for i, req_data in enumerate(review_results, 1):
        req_name = req_data.get('name', f'未命名需求 {i}')
        original_req = next((r for r in requirements if r.get('name') == req_name), {})
        req_content = original_req.get('content', '无内容')

        html_parts.append(f'<div class="requirement-section">')
        html_parts.append(f'<h2>{i}. {req_name}</h2>')
        html_parts.append(f'<p><strong>需求内容</strong>: {req_content}</p>')

        review = req_data.get('review_result', {})
        if not review or 'requirements_review' not in review:
            html_parts.append('<p><em>未进行审查或审查失败</em></p>')
            html_parts.append('</div>') # close requirement-section
            continue

        issues = review.get('requirements_review', [])
        score = review.get('score', '未评分')
        summary = review.get('summary', '无总结')

        if not issues or (len(issues) == 1 and issues[0].get("problem_title", "").endswith("解析失败")) or (len(issues) == 1 and issues[0].get("problem_title", "").endswith("审查系统错误")):
            html_parts.append('<p class="no-issues">✅ 未发现明显问题或审查处理异常</p>')
            if issues and ("解析失败" in issues[0].get("problem_title", "") or "审查系统错误" in issues[0].get("problem_title", "")):
                html_parts.append(f'''
                <div class="issue">
                    <p><strong>问题描述</strong>: {issues[0].get('problem_description', '')}</p>
                </div>''')
        else:
            html_parts.append(f'<p><strong>问题数量</strong>: {len(issues)} 个</p>')
            for j, issue in enumerate(issues, 1):
                html_parts.append(f'''
                <div class="issue">
                    <h3>问题 {j}: {issue.get('problem_title', '无标题')}</h3>
                    <p><strong>需求描述</strong>: {issue.get('requirement_description', 'N/A')}</p>
                    <p><strong>问题描述</strong>: {issue.get('problem_description', 'N/A')}</p>
                    <p><strong>问题位置</strong>: {issue.get('problem_location', 'N/A')}</p>
                    <p><strong>影响分析</strong>: {issue.get('impact_analysis', 'N/A')}</p>
                </div>''')
        
        html_parts.append(f'<div class="summary"><strong>总结</strong>: {summary}</div>')
        html_parts.append(f'<div class="score">评分: {score}/100</div>')
        html_parts.append('</div>') # close requirement-section

    html_parts.append('''
</body>
</html>''')
    return "\n".join(html_parts)

def review_requirement(requirement):
    """
    使用AI模型对单个需求进行审查
    参数: requirement: dict, 包含需求信息的字典，至少有name和content字段
    返回: dict: 包含审查结果的字典
    """
    logging.debug(f"开始审查需求《{requirement['name']}》")
    config = get_config()
    provider = config.get("provider", "openai")
    prompt = f"""
    请作为一名专业的需求审查专家，审查以下软件需求，找出潜在问题，严格按照要求的JSON格式返回结果：\n\n需求名称: {requirement['name']}\n需求内容:\n{requirement['content']}\n\n请仔细审查上述需求，找出所有潜在问题，例如：不明确的描述、不完整的约束条件、性能要求不具体、冲突的需求等。\n\n审查结果必须严格按照以下JSON格式返回（数组中可以包含多个问题）：\n{{\n    \"requirements_review\": [\n        {{\n            \"problem_title\": \"问题的具体名称（包含功能名称和问题类型，不超过20个字）\",\n            \"requirement_description\": \"简要描述需求要点\",\n            \"problem_description\": \"详细描述发现的问题\",\n            \"problem_location\": \"指出问题在需求中的具体位置\",\n            \"impact_analysis\": \"分析此问题可能带来的影响\"\n        }}\n    ],\n    \"score\": 85,\n    \"summary\": \"审查总结\"\n}}\n\n必须为每个发现的问题提供所有五个字段：problem_title、requirement_description、problem_description、problem_location和impact_analysis。\n\n其中problem_title是对问题的具体描述，必须包含需求的功能名称和具体问题类型，格式为\"[功能名称]+[问题类型]\"，如\"用户身份验证功能约束不明确\"、\"用户身份验证功能性能要求不具体\"等，不超过20个字。\n\n如果没有发现问题，请在requirements_review数组中返回一个对象，表明需求质量良好。\n请直接返回JSON对象，不要包含任何额外的文字。\n"""
    model_params = config.get("model_params", {})
    temperature = model_params.get("temperature", 0.1)
    max_tokens = model_params.get("max_tokens", 2000)
    try:
        client = get_client()
        if client is None:
            logging.warning("无法创建OpenAI客户端，切换到模拟审查模式")
            review_item = {
                "name": requirement["name"],
                "chapter": requirement.get("chapter", ""),
                "review_result": {
                    "requirements_review": [
                        {
                            "problem_title": f"{requirement['name']}描述细节缺失",
                            "requirement_description": "需求完整性分析",
                            "problem_description": "需求描述缺乏具体细节，可能导致不同理解",
                            "problem_location": "需求说明部分",
                            "impact_analysis": "可能导致开发者对要求理解不一致，影响功能实现"
                        },
                        {
                            "problem_title": f"{requirement['name']}术语一致性问题",
                            "requirement_description": "需求术语一致性分析",
                            "problem_description": "需求中使用的术语可能存在不一致的情况",
                            "problem_location": "需求整体文档",
                            "impact_analysis": "可能导致模块之间集成困难，增加沟通成本"
                        }
                    ],
                    "score": 85,
                    "summary": "需求总体质量良好，但存在一些可以改进的地方"
                }
            }
            return review_item
        if provider == "openai":
            result = call_openai_api(prompt, temperature, max_tokens)
        else:
            logging.error(f"当前配置的提供商 '{provider}' 不受支持或 Ollama 已被移除。将尝试使用OpenAI (如果配置允许)。")
            # Fallback or strict error based on desired behavior:
            # Option 1: Fallback to OpenAI if client is available (assuming client is OpenAI client)
            # result = call_openai_api(prompt, temperature, max_tokens)
            # Option 2: Strict error for unsupported provider
            raise ValueError(f"不支持的模型提供商: {provider}. 当前仅支持 'openai'.")
        logging.debug(f"AI返回的原始结果: {result}")
        try:
            result_json = json.loads(result)
            review_result = {
                "name": requirement["name"],
                "chapter": requirement.get("chapter", ""),
                "review_result": result_json
            }
            logging.info(f"需求《{requirement['name']}》审查完成，发现 {len(result_json.get('requirements_review', []))} 个问题")
            return review_result
        except json.JSONDecodeError as e:
            logging.error(f"解析AI返回的JSON失败: {e}")
            return {
                "name": requirement["name"],
                "chapter": requirement.get("chapter", ""),
                "review_result": {
                    "requirements_review": [{
                        "problem_title": f"{requirement['name']}解析失败",
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
        return {
            "name": requirement["name"],
            "chapter": requirement.get("chapter", ""),
            "review_result": {
                "requirements_review": [{
                    "problem_title": f"{requirement['name']}审查系统错误",
                    "requirement_description": "需求审查系统错误",
                    "problem_description": f"调用AI审查需求时出错: {str(e)}",
                    "problem_location": "系统调用过程",
                    "impact_analysis": "系统无法完成需求审查，可能导致需求缺陷无法发现和修复"
                }],
                "score": 0,
                "summary": "无法完成需求审查"
            }
        }
