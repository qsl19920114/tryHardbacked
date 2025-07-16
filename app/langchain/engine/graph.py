"""
LangGraph state graph definition for murder mystery game flow.

This module defines the state graph that orchestrates the game flow,
managing transitions between different game phases and coordinating
AI tool usage.
"""

import logging
from typing import Dict, Any, List, Literal
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

from app.langchain.state.models import GameState, GamePhase
from app.langchain.tools.dify_tools import create_dify_tools

logger = logging.getLogger(__name__)


class GameGraphState(Dict[str, Any]):
    """
    State dictionary for the game graph.
    
    This extends a regular dictionary to include specific fields
    that the LangGraph nodes will use and modify.
    """
    game_state: GameState
    messages: List[BaseMessage]
    current_action: Dict[str, Any]
    error_message: str
    next_phase: GamePhase


def create_game_graph() -> StateGraph:
    """
    Create and configure the LangGraph state graph for game flow.
    
    Returns:
        Configured StateGraph instance
    """
    # Initialize the state graph
    graph = StateGraph(GameGraphState)
    
    # Add nodes for each game phase
    graph.add_node("initialization", initialization_node)
    graph.add_node("monologue", monologue_node)
    graph.add_node("qna", qna_node)
    graph.add_node("mission_submit", mission_submit_node)
    graph.add_node("final_choice", final_choice_node)
    graph.add_node("completed", completed_node)
    graph.add_node("error_handler", error_handler_node)
    
    # Set the entry point
    graph.set_entry_point("initialization")
    
    # Define transitions from initialization
    graph.add_conditional_edges(
        "initialization",
        route_from_initialization,
        {
            "monologue": "monologue",
            "qna": "qna",
            "error": "error_handler",
            "end": END
        }
    )
    
    # Define transitions from monologue
    graph.add_conditional_edges(
        "monologue",
        route_from_monologue,
        {
            "qna": "qna",
            "mission_submit": "mission_submit",
            "final_choice": "final_choice",
            "completed": "completed",
            "error": "error_handler",
            "end": END
        }
    )
    
    # Define transitions from qna
    graph.add_conditional_edges(
        "qna",
        route_from_qna,
        {
            "qna": "qna",  # Stay in Q&A for multiple rounds
            "monologue": "monologue",
            "mission_submit": "mission_submit",
            "final_choice": "final_choice",
            "completed": "completed",
            "error": "error_handler",
            "end": END
        }
    )
    
    # Define transitions from mission_submit
    graph.add_conditional_edges(
        "mission_submit",
        route_from_mission_submit,
        {
            "qna": "qna",
            "final_choice": "final_choice",
            "completed": "completed",
            "error": "error_handler",
            "end": END
        }
    )
    
    # Define transitions from final_choice
    graph.add_conditional_edges(
        "final_choice",
        route_from_final_choice,
        {
            "completed": "completed",
            "error": "error_handler",
            "end": END
        }
    )
    
    # Completed and error nodes end the graph
    graph.add_edge("completed", END)
    graph.add_edge("error_handler", END)
    
    return graph


def initialization_node(state: GameGraphState) -> GameGraphState:
    """
    Handle game initialization phase.
    
    Args:
        state: Current game graph state
        
    Returns:
        Updated game graph state
    """
    try:
        logger.info(f"Initializing game {state['game_state'].game_id}")
        
        game_state = state["game_state"]
        
        # Set up initial game state
        game_state.current_phase = GamePhase.INITIALIZATION
        
        # Add initialization log entry
        game_state.add_public_log_entry(
            "game_start",
            f"游戏开始！剧本：{game_state.script_id}"
        )
        
        # Determine next phase based on game configuration
        if game_state.characters:
            state["next_phase"] = GamePhase.MONOLOGUE
        else:
            state["next_phase"] = GamePhase.QNA
        
        logger.info(f"Game {game_state.game_id} initialized, next phase: {state['next_phase']}")
        
        return state
        
    except Exception as e:
        logger.error(f"Error in initialization_node: {e}")
        state["error_message"] = f"初始化游戏时发生错误: {e}"
        state["next_phase"] = GamePhase.COMPLETED
        return state


def monologue_node(state: GameGraphState) -> GameGraphState:
    """
    Handle character monologue phase.
    
    Args:
        state: Current game graph state
        
    Returns:
        Updated game graph state
    """
    try:
        logger.info("Processing monologue phase")
        
        game_state = state["game_state"]
        game_state.current_phase = GamePhase.MONOLOGUE
        
        # Get current action details
        action = state.get("current_action", {})
        character_id = action.get("character_id")
        
        if not character_id:
            state["error_message"] = "角色ID未指定"
            state["next_phase"] = GamePhase.QNA
            return state
        
        # The actual monologue generation will be handled by the game engine
        # This node just manages the state transition
        
        # Add log entry
        game_state.add_public_log_entry(
            "monologue",
            f"角色 {character_id} 进行了自我介绍",
            related_character_id=character_id
        )
        
        # Determine next phase
        state["next_phase"] = GamePhase.QNA
        
        logger.info(f"Monologue phase completed for character {character_id}")
        
        return state
        
    except Exception as e:
        logger.error(f"Error in monologue_node: {e}")
        state["error_message"] = f"处理角色独白时发生错误: {e}"
        state["next_phase"] = GamePhase.QNA
        return state


def qna_node(state: GameGraphState) -> GameGraphState:
    """
    Handle Q&A phase.
    
    Args:
        state: Current game graph state
        
    Returns:
        Updated game graph state
    """
    try:
        logger.info("Processing Q&A phase")
        
        game_state = state["game_state"]
        game_state.current_phase = GamePhase.QNA
        
        # Get current action details
        action = state.get("current_action", {})
        
        # The actual Q&A processing will be handled by the game engine
        # This node just manages the state transition
        
        # Determine next phase based on game progress
        if action.get("action_type") == "advance_act":
            if game_state.current_act >= game_state.max_acts:
                state["next_phase"] = GamePhase.FINAL_CHOICE
            else:
                game_state.current_act += 1
                state["next_phase"] = GamePhase.MONOLOGUE
        elif action.get("action_type") == "submit_mission":
            state["next_phase"] = GamePhase.MISSION_SUBMIT
        else:
            # Stay in Q&A phase
            state["next_phase"] = GamePhase.QNA
        
        logger.info(f"Q&A phase processed, next phase: {state['next_phase']}")
        
        return state
        
    except Exception as e:
        logger.error(f"Error in qna_node: {e}")
        state["error_message"] = f"处理问答环节时发生错误: {e}"
        state["next_phase"] = GamePhase.QNA
        return state


def mission_submit_node(state: GameGraphState) -> GameGraphState:
    """
    Handle mission submission phase.
    
    Args:
        state: Current game graph state
        
    Returns:
        Updated game graph state
    """
    try:
        logger.info("Processing mission submission phase")
        
        game_state = state["game_state"]
        game_state.current_phase = GamePhase.MISSION_SUBMIT
        
        # Get current action details
        action = state.get("current_action", {})
        player_id = action.get("player_id")
        mission_type = action.get("mission_type", "general")
        content = action.get("content", "")
        
        if player_id and content:
            # Add mission submission
            submission = game_state.add_mission_submission(player_id, mission_type, content)
            
            # Add log entry
            game_state.add_public_log_entry(
                "mission_submission",
                f"玩家提交了{mission_type}任务",
                related_player_id=player_id
            )
            
            logger.info(f"Mission submitted by player {player_id}: {submission.id}")
        
        # Determine next phase
        if game_state.current_act >= game_state.max_acts:
            state["next_phase"] = GamePhase.FINAL_CHOICE
        else:
            state["next_phase"] = GamePhase.QNA
        
        return state
        
    except Exception as e:
        logger.error(f"Error in mission_submit_node: {e}")
        state["error_message"] = f"处理任务提交时发生错误: {e}"
        state["next_phase"] = GamePhase.QNA
        return state


def final_choice_node(state: GameGraphState) -> GameGraphState:
    """
    Handle final choice phase.
    
    Args:
        state: Current game graph state
        
    Returns:
        Updated game graph state
    """
    try:
        logger.info("Processing final choice phase")
        
        game_state = state["game_state"]
        game_state.current_phase = GamePhase.FINAL_CHOICE
        
        # Add log entry
        game_state.add_public_log_entry(
            "final_choice",
            "游戏进入最终选择阶段"
        )
        
        # The actual final choice processing will be handled by the game engine
        
        # Move to completed phase
        state["next_phase"] = GamePhase.COMPLETED
        
        logger.info("Final choice phase completed")
        
        return state
        
    except Exception as e:
        logger.error(f"Error in final_choice_node: {e}")
        state["error_message"] = f"处理最终选择时发生错误: {e}"
        state["next_phase"] = GamePhase.COMPLETED
        return state


def completed_node(state: GameGraphState) -> GameGraphState:
    """
    Handle game completion.
    
    Args:
        state: Current game graph state
        
    Returns:
        Updated game graph state
    """
    try:
        logger.info("Processing game completion")
        
        game_state = state["game_state"]
        game_state.current_phase = GamePhase.COMPLETED
        
        # Set completion timestamp
        from datetime import datetime, timezone
        game_state.completed_at = datetime.now(timezone.utc)
        
        # Add final log entry
        game_state.add_public_log_entry(
            "game_completed",
            "游戏结束！"
        )
        
        logger.info(f"Game {game_state.game_id} completed")
        
        return state
        
    except Exception as e:
        logger.error(f"Error in completed_node: {e}")
        state["error_message"] = f"完成游戏时发生错误: {e}"
        return state


def error_handler_node(state: GameGraphState) -> GameGraphState:
    """
    Handle errors in the game flow.
    
    Args:
        state: Current game graph state
        
    Returns:
        Updated game graph state
    """
    logger.error(f"Error handler activated: {state.get('error_message', 'Unknown error')}")
    
    game_state = state["game_state"]
    
    # Add error log entry
    game_state.add_public_log_entry(
        "error",
        f"游戏发生错误: {state.get('error_message', '未知错误')}"
    )
    
    return state


# Routing functions for conditional edges

def route_from_initialization(state: GameGraphState) -> Literal["monologue", "qna", "error", "end"]:
    """Route from initialization phase."""
    if state.get("error_message"):
        return "error"
    
    next_phase = state.get("next_phase")
    if next_phase == GamePhase.MONOLOGUE:
        return "monologue"
    elif next_phase == GamePhase.QNA:
        return "qna"
    else:
        return "end"


def route_from_monologue(state: GameGraphState) -> Literal["qna", "mission_submit", "final_choice", "completed", "error", "end"]:
    """Route from monologue phase."""
    if state.get("error_message"):
        return "error"
    
    next_phase = state.get("next_phase")
    if next_phase == GamePhase.QNA:
        return "qna"
    elif next_phase == GamePhase.MISSION_SUBMIT:
        return "mission_submit"
    elif next_phase == GamePhase.FINAL_CHOICE:
        return "final_choice"
    elif next_phase == GamePhase.COMPLETED:
        return "completed"
    else:
        return "end"


def route_from_qna(state: GameGraphState) -> Literal["qna", "monologue", "mission_submit", "final_choice", "completed", "error", "end"]:
    """Route from Q&A phase."""
    if state.get("error_message"):
        return "error"
    
    next_phase = state.get("next_phase")
    if next_phase == GamePhase.QNA:
        return "qna"
    elif next_phase == GamePhase.MONOLOGUE:
        return "monologue"
    elif next_phase == GamePhase.MISSION_SUBMIT:
        return "mission_submit"
    elif next_phase == GamePhase.FINAL_CHOICE:
        return "final_choice"
    elif next_phase == GamePhase.COMPLETED:
        return "completed"
    else:
        return "end"


def route_from_mission_submit(state: GameGraphState) -> Literal["qna", "final_choice", "completed", "error", "end"]:
    """Route from mission submission phase."""
    if state.get("error_message"):
        return "error"
    
    next_phase = state.get("next_phase")
    if next_phase == GamePhase.QNA:
        return "qna"
    elif next_phase == GamePhase.FINAL_CHOICE:
        return "final_choice"
    elif next_phase == GamePhase.COMPLETED:
        return "completed"
    else:
        return "end"


def route_from_final_choice(state: GameGraphState) -> Literal["completed", "error", "end"]:
    """Route from final choice phase."""
    if state.get("error_message"):
        return "error"
    
    next_phase = state.get("next_phase")
    if next_phase == GamePhase.COMPLETED:
        return "completed"
    else:
        return "end"
