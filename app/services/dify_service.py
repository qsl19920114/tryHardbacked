import requests
import time
from app.core.config import DIFY_API_URL, DIFY_API_KEY
from app.schemas.pydantic_schemas import DialogueRequest

def call_dify_chatflow(request: DialogueRequest, user_id: str) -> str:
    """
    调用 Dify 的 Chat Message API
    """
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json",
    }

    body = {
        "inputs": {},
        "query": request.question,
        "user": user_id,
        "conversation_id": request.session_id,
        "response_mode": "blocking"
    }
    
    try:
        response = requests.post(DIFY_API_URL, headers=headers, json=body)
        response.raise_for_status()

        api_response = response.json()
        return api_response.get("answer", "抱歉，我暂时无法回答。")

    except requests.exceptions.RequestException as e:
        print(f"Error calling Dify API: {e}")
        return "AI 服务当前不可用，请稍后再试。"