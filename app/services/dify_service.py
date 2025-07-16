import requests
import time
from typing import Dict, Any, Optional
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

def call_dify_workflow(workflow_id: str, inputs: Dict[str, Any], user_id: str, conversation_id: Optional[str] = None) -> str:
    """
    调用指定的 Dify 工作流

    Args:
        workflow_id: Dify工作流ID
        inputs: 输入参数字典
        user_id: 用户唯一标识符
        conversation_id: 会话ID（可选）

    Returns:
        str: AI 生成的回答文本
    """
    # 设置请求头，包含认证信息
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json",
    }

    # 构建请求体
    body = {
        "inputs": inputs,
        "user": user_id,
        "response_mode": "blocking"
    }

    # 如果提供了会话ID，则添加到请求体中
    if conversation_id:
        body["conversation_id"] = conversation_id

    # 构建特定工作流的API URL（这里使用模拟URL，实际需要根据Dify API规范调整）
    workflow_url = f"{DIFY_API_URL.replace('/chat-messages', '')}/workflows/{workflow_id}/run"

    try:
        # 发送 POST 请求到 Dify 工作流 API
        response = requests.post(workflow_url, headers=headers, json=body)
        response.raise_for_status()

        # 解析 JSON 响应
        api_response = response.json()
        # 返回 AI 的回答，如果没有答案则返回默认消息
        return api_response.get("data", {}).get("outputs", {}).get("answer", "抱歉，我暂时无法回答。")

    except requests.exceptions.RequestException as e:
        # 处理网络请求异常
        print(f"调用 Dify 工作流 {workflow_id} 时发生错误: {e}")
        return "AI 服务当前不可用，请稍后再试。"

def generate_story_content(workflow_id: str, scene_config: Dict[str, Any], session_id: str, dialogue_history: str = "") -> str:
    """
    生成故事模式的场景内容

    Args:
        workflow_id: 故事生成工作流ID
        scene_config: 场景配置信息
        session_id: 游戏会话ID
        dialogue_history: 对话历史记录

    Returns:
        str: 生成的故事内容
    """
    # 如果Dify服务不可用或使用模拟工作流ID，返回模拟内容
    if not workflow_id or any(workflow_id.startswith(prefix) for prefix in ["story_", "victorian_", "locked_room_"]):
        return generate_mock_story_content(scene_config)

    inputs = {
        "scene_title": scene_config.get("title", ""),
        "scene_description": scene_config.get("description", ""),
        "characters_present": scene_config.get("scene_config", {}).get("characters_present", []),
        "mood": scene_config.get("scene_config", {}).get("mood", "neutral"),
        "dialogue_history": dialogue_history
    }

    return call_dify_workflow(workflow_id, inputs, session_id, session_id)

def generate_mock_story_content(scene_config: Dict[str, Any]) -> str:
    """
    生成模拟的故事内容（用于测试）

    Args:
        scene_config: 场景配置信息

    Returns:
        str: 模拟的故事内容
    """
    title = scene_config.get("title", "未知场景")
    description = scene_config.get("description", "")
    mood = scene_config.get("scene_config", {}).get("mood", "neutral")

    mood_descriptions = {
        "mysterious": "神秘的氛围笼罩着整个场景",
        "tense": "紧张的气氛让人不安",
        "investigative": "调查的时刻到了",
        "climactic": "关键时刻即将到来",
        "conclusive": "一切都将在此刻揭晓"
    }

    mood_text = mood_descriptions.get(mood, "平静的氛围")

    return f"""
【{title}】

{description}

{mood_text}。在这个场景中，你需要仔细观察周围的环境，注意每一个细节。
故事正在向前推进，每个选择都可能影响最终的结局。

请点击"继续"来推进故事情节。
    """.strip()

def generate_character_response(character_id: str, question: str, scene_context: str = "") -> str:
    """
    生成角色对话的模拟回答（用于测试）

    Args:
        character_id: 角色ID
        question: 玩家的问题
        scene_context: 场景上下文

    Returns:
        str: 模拟的角色回答
    """
    # 角色性格和背景设定
    character_profiles = {
        "librarian_ai": {
            "name": "图书管理员AI",
            "personality": "知识渊博但性格孤僻",
            "background": "对图书馆的每一个角落都了如指掌",
            "speech_style": "正式而谨慎"
        },
        "professor_ai": {
            "name": "文学教授AI",
            "personality": "优雅博学",
            "background": "对古籍和文学有深入研究",
            "speech_style": "文雅而深思熟虑"
        },
        "visitor_ai": {
            "name": "神秘访客AI",
            "personality": "神秘莫测",
            "background": "身份不明，似乎在寻找什么",
            "speech_style": "简洁而含糊"
        },
        "chief_inspector_ai": {
            "name": "首席探长AI",
            "personality": "经验丰富，直觉敏锐",
            "background": "处理过无数疑难案件",
            "speech_style": "直接而权威"
        },
        "forensic_expert_ai": {
            "name": "法医专家AI",
            "personality": "科学严谨",
            "background": "年轻但专业能力强",
            "speech_style": "专业而精确"
        }
    }

    profile = character_profiles.get(character_id, {
        "name": "未知角色",
        "personality": "普通",
        "background": "背景不明",
        "speech_style": "平常"
    })

    # 根据问题类型生成不同的回答
    if "介绍" in question or "你好" in question:
        return f"你好，我是{profile['name']}。{profile['background']}。有什么我可以帮助你的吗？"
    elif "管理员" in question and "librarian" in character_id:
        return "管理员...他昨晚确实表现得很奇怪。我注意到他一直在查看一些古老的记录，似乎在寻找什么重要的东西。"
    elif "图书馆" in question and "professor" in character_id:
        return "这座图书馆有着悠久的历史，建于19世纪初。据说这里曾经发生过一些...不寻常的事件。作为一名文学研究者，我对这里的古籍收藏非常感兴趣。"
    elif "为什么" in question and "visitor" in character_id:
        return "我...我有我的理由。有些事情必须在深夜才能进行。你不需要知道太多。"
    elif "案件" in question or "死者" in question:
        return f"根据我的{profile['background']}，这个案件确实很复杂。{scene_context}让我们需要更仔细地调查每一个细节。"
    else:
        return f"关于你的问题，以我的{profile['personality']}来看，这需要更深入的思考。{scene_context}可能包含了重要的线索。"