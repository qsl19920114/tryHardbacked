import requests
import time
import logging
from typing import Dict, Any, Optional
from enum import Enum
from app.core.config import (
    DIFY_API_URL, DIFY_API_KEY,
    DIFY_QNA_WORKFLOW_URL, DIFY_QNA_WORKFLOW_API_KEY,
    DIFY_MONOLOGUE_WORKFLOW_URL, DIFY_MONOLOGUE_WORKFLOW_API_KEY
)
from app.schemas.pydantic_schemas import DialogueRequest

logger = logging.getLogger(__name__)


class DifyWorkflowType(str, Enum):
    """Enumeration of available Dify workflows."""
    CHATFLOW = "chatflow"  # Original chat-messages API
    QNA_WORKFLOW = "qna_workflow"  # 查询并回答 workflow
    MONOLOGUE_WORKFLOW = "monologue_workflow"  # 简述自己的身世 workflow


class DifyServiceError(Exception):
    """Custom exception for Dify service errors."""
    pass


def call_dify_chatflow(request: DialogueRequest, user_id: str, formatted_prompt: str = "") -> str:
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
        logger.error(f"调用 Dify API 时发生错误: {e}")
        return "AI 服务当前不可用，请稍后再试。"


def call_dify_workflow(
    workflow_type: DifyWorkflowType,
    inputs: Dict[str, Any],
    user_id: str,
    max_retries: int = 3,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    调用 Dify 工作流 API

    Args:
        workflow_type: 工作流类型
        inputs: 输入参数字典
        user_id: 用户唯一标识符
        max_retries: 最大重试次数
        timeout: 请求超时时间（秒）

    Returns:
        Dict: API 响应数据

    Raises:
        DifyServiceError: 当 API 调用失败时
    """
    # 根据工作流类型选择配置
    if workflow_type == DifyWorkflowType.QNA_WORKFLOW:
        api_url = DIFY_QNA_WORKFLOW_URL
        api_key = DIFY_QNA_WORKFLOW_API_KEY
    elif workflow_type == DifyWorkflowType.MONOLOGUE_WORKFLOW:
        api_url = DIFY_MONOLOGUE_WORKFLOW_URL
        api_key = DIFY_MONOLOGUE_WORKFLOW_API_KEY
    else:
        raise DifyServiceError(f"Unsupported workflow type: {workflow_type}")

    # 设置请求头
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # 构建请求体
    body = {
        "inputs": inputs,
        "user": user_id,
        "response_mode": "blocking"
    }

    last_exception = None

    # 重试逻辑
    for attempt in range(max_retries):
        try:
            logger.info(f"Calling Dify workflow {workflow_type}, attempt {attempt + 1}")

            response = requests.post(
                api_url,
                headers=headers,
                json=body,
                timeout=timeout
            )
            response.raise_for_status()

            api_response = response.json()

            # 验证响应格式
            if not _validate_workflow_response(api_response):
                raise DifyServiceError(f"Invalid response format from {workflow_type}")

            logger.info(f"Successfully called Dify workflow {workflow_type}")
            return api_response

        except requests.exceptions.Timeout as e:
            last_exception = e
            logger.warning(f"Timeout on attempt {attempt + 1} for {workflow_type}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff

        except requests.exceptions.RequestException as e:
            last_exception = e
            logger.error(f"Request error on attempt {attempt + 1} for {workflow_type}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

        except Exception as e:
            last_exception = e
            logger.error(f"Unexpected error on attempt {attempt + 1} for {workflow_type}: {e}")
            break  # Don't retry on unexpected errors

    # All retries failed
    raise DifyServiceError(f"Failed to call {workflow_type} after {max_retries} attempts: {last_exception}")


def call_qna_workflow(
    char_id: str,
    act_num: int,
    query: str,
    model_name: str,
    user_id: str
) -> str:
    """
    调用查询并回答工作流

    Args:
        char_id: 角色ID
        act_num: 幕数
        query: 查询问题
        model_name: 模型名称
        user_id: 用户ID

    Returns:
        str: AI 生成的回答

    Raises:
        DifyServiceError: 当工作流调用失败时
    """
    inputs = {
        "char_id": char_id,
        "act_num": act_num,
        "query": query,
        "model_name": model_name
    }

    try:
        response = call_dify_workflow(
            DifyWorkflowType.QNA_WORKFLOW,
            inputs,
            user_id
        )

        # 从响应中提取答案
        answer = _extract_answer_from_response(response)
        return answer

    except DifyServiceError as e:
        logger.error(f"QnA workflow failed: {e}")
        return "抱歉，我暂时无法回答这个问题。"


def call_monologue_workflow(
    char_id: str,
    act_num: int,
    model_name: str,
    user_id: str
) -> str:
    """
    调用简述自己的身世工作流

    Args:
        char_id: 角色ID
        act_num: 幕数
        model_name: 模型名称
        user_id: 用户ID

    Returns:
        str: AI 生成的角色独白

    Raises:
        DifyServiceError: 当工作流调用失败时
    """
    inputs = {
        "char_id": char_id,
        "act_num": act_num,
        "model_name": model_name
    }

    try:
        response = call_dify_workflow(
            DifyWorkflowType.MONOLOGUE_WORKFLOW,
            inputs,
            user_id
        )

        # 从响应中提取独白内容
        monologue = _extract_answer_from_response(response)
        return monologue

    except DifyServiceError as e:
        logger.error(f"Monologue workflow failed: {e}")
        return "抱歉，我暂时无法生成角色独白。"


def _validate_workflow_response(response: Dict[str, Any]) -> bool:
    """
    验证工作流响应格式

    Args:
        response: API 响应数据

    Returns:
        bool: 响应格式是否有效
    """
    # 检查必要的字段
    if not isinstance(response, dict):
        return False

    # 工作流响应通常包含 data 字段
    if "data" not in response:
        return False

    data = response["data"]
    if not isinstance(data, dict):
        return False

    # 检查是否有输出数据
    if "outputs" not in data:
        return False

    return True


def _extract_answer_from_response(response: Dict[str, Any]) -> str:
    """
    从工作流响应中提取答案

    Args:
        response: API 响应数据

    Returns:
        str: 提取的答案文本
    """
    try:
        # 尝试从不同可能的字段中提取答案
        data = response.get("data", {})
        outputs = data.get("outputs", {})

        # 常见的输出字段名
        possible_fields = ["answer", "result", "output", "text", "content"]

        for field in possible_fields:
            if field in outputs and outputs[field]:
                return str(outputs[field])

        # 如果没有找到标准字段，返回第一个非空值
        for key, value in outputs.items():
            if value and isinstance(value, (str, int, float)):
                return str(value)

        # 最后的备选方案
        return "抱歉，无法解析AI响应。"

    except Exception as e:
        logger.error(f"Failed to extract answer from response: {e}")
        return "抱歉，响应解析失败。"