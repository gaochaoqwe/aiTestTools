"""
测试直接使用OpenAI库的认证和请求方式
"""
import sys
import os
import json
from openai import OpenAI

# 设置API参数 - 与成功的测试保持完全一致
API_KEY = "sk-kwmzlwamflklwslrcyunnvyuqveuuzesljlsjktnipekossw"  # 使用提供的密钥
BASE_URL = "https://api.siliconflow.cn/v1"  # 基础URL，不包含端点
MODEL_NAME = "THUDM/GLM-4-32B-0414"  # 使用提供的模型

def test_openai_lib():
    """使用OpenAI库测试API调用"""
    print("\n==== 开始OpenAI库API调用测试 ====\n")
    
    try:
        # 创建OpenAI客户端
        print(f"创建OpenAI客户端 - API密钥: {API_KEY[:4]}...{API_KEY[-4:]}")
        print(f"基础URL: {BASE_URL}")
        
        # 直接设置完整的认证头，不依赖库的处理
        client = OpenAI(
            api_key=API_KEY,
            base_url=BASE_URL,
            default_headers={"Authorization": f"Bearer {API_KEY}"}
        )
        
        messages = [
            {
                "role": "user", 
                "content": "你好，请简单回复一句问候语,用英文，验证模型连接正常。"
            }
        ]
        
        print(f"请求模型: {MODEL_NAME}")
        print(f"开始发送请求...")
        
        # 创建聊天完成
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.1,
            max_tokens=100
        )
        
        # 打印完整响应
        print(f"\n成功! 响应内容:\n{response.model_dump_json(indent=2)}")
        
        # 提取文本内容
        content = response.choices[0].message.content
        print(f"\n回复内容: {content}")
        
    except Exception as e:
        print(f"\n发生错误: {str(e)}")
        # 尝试提取更多错误详情
        if hasattr(e, 'response'):
            try:
                print(f"错误响应: {e.response.text}")
            except:
                print(f"错误响应对象: {e.response}")

if __name__ == "__main__":
    test_openai_lib()
