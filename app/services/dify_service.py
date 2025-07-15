import requests
import time
from app.core.config import DIFY_API_URL, DIFY_API_KEY
from app.schemas.pydantic_schemas import DialogueRequest

def call_dify_chatflow(request: DialogueRequest, user_id: str) -> str:
    """
    调用 Dify AI 平台的聊天消息 API
    
    Args:
        request: 对话请求对象，包含会话ID和用户问题
        user_id: 用户唯一标识符
    
    Returns:
        str: AI 生成的回答文本
    """
    # 设置请求头，包含认证信息
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",  # Bearer Token 认证
        "Content-Type": "application/json",  # JSON 格式请求
    }

    # 构建请求体，符合 Dify API 规范
    body = {
        "inputs": {},  # 输入参数（当前为空）
        "query": request.question,  # 用户的问题
        "user": user_id,  # 用户标识符
        "conversation_id": request.session_id,  # 会话ID，用于保持对话上下文
        "response_mode": "blocking"  # 阻塞模式，等待完整响应
    }
    
    try:
        # 发送 POST 请求到 Dify API
        response = requests.post(DIFY_API_URL, headers=headers, json=body)
        response.raise_for_status()  # 检查 HTTP 状态码，如有错误则抛出异常

        # 解析 JSON 响应
        api_response = response.json()
        # 返回 AI 的回答，如果没有答案则返回默认消息
        return api_response.get("answer", "抱歉，我暂时无法回答。")

    except requests.exceptions.RequestException as e:
        # 处理网络请求异常（连接超时、网络错误等）
        print(f"调用 Dify API 时发生错误: {e}")
        return "AI 服务当前不可用，请稍后再试。"