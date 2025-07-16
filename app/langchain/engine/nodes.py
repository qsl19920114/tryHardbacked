"""
Game phase nodes for LangGraph workflow.

This module provides the GamePhaseNodes class that contains utility methods
for the game phase nodes defined in graph.py.
"""

import logging
from typing import Dict, Any, Optional
from app.langchain.state.models import GameState, GamePhase

logger = logging.getLogger(__name__)


class GamePhaseNodes:
    """
    Utility class for game phase node operations.
    
    This class provides helper methods and utilities that can be used
    by the game phase nodes in the LangGraph workflow.
    """
    
    @staticmethod
    def validate_action(action: Dict[str, Any], required_fields: list) -> Optional[str]:
        """
        Validate that an action contains required fields.
        
        Args:
            action: Action dictionary to validate
            required_fields: List of required field names
            
        Returns:
            Error message if validation fails, None if valid
        """
        for field in required_fields:
            if field not in action or not action[field]:
                return f"Missing required field: {field}"
        return None
    
    @staticmethod
    def can_advance_to_phase(game_state: GameState, target_phase: GamePhase) -> tuple[bool, str]:
        """
        Check if the game can advance to a specific phase.
        
        Args:
            game_state: Current game state
            target_phase: Target phase to advance to
            
        Returns:
            Tuple of (can_advance, reason)
        """
        current_phase = game_state.current_phase
        
        # Define valid phase transitions
        valid_transitions = {
            GamePhase.INITIALIZATION: [GamePhase.MONOLOGUE, GamePhase.QNA],
            GamePhase.MONOLOGUE: [GamePhase.QNA, GamePhase.MISSION_SUBMIT, GamePhase.FINAL_CHOICE],
            GamePhase.QNA: [GamePhase.MONOLOGUE, GamePhase.MISSION_SUBMIT, GamePhase.FINAL_CHOICE, GamePhase.COMPLETED],
            GamePhase.MISSION_SUBMIT: [GamePhase.QNA, GamePhase.FINAL_CHOICE, GamePhase.COMPLETED],
            GamePhase.FINAL_CHOICE: [GamePhase.COMPLETED],
            GamePhase.COMPLETED: [],
            GamePhase.PAUSED: [GamePhase.MONOLOGUE, GamePhase.QNA, GamePhase.MISSION_SUBMIT, GamePhase.FINAL_CHOICE]
        }
        
        if target_phase in valid_transitions.get(current_phase, []):
            return True, "Valid transition"
        else:
            return False, f"Cannot transition from {current_phase.value} to {target_phase.value}"
    
    @staticmethod
    def should_advance_act(game_state: GameState) -> bool:
        """
        Determine if the game should advance to the next act.
        
        Args:
            game_state: Current game state
            
        Returns:
            True if should advance act, False otherwise
        """
        # Check if all characters have been questioned enough times
        min_questions_per_character = 2  # Configurable threshold
        
        for character_id in game_state.characters.keys():
            current_count = game_state.get_qna_count_for_character_act(
                character_id, 
                game_state.current_act
            )
            if current_count < min_questions_per_character:
                return False
        
        return True
    
    @staticmethod
    def get_next_player_turn(game_state: GameState) -> Optional[str]:
        """
        Get the next player in turn order.
        
        Args:
            game_state: Current game state
            
        Returns:
            Player ID of next player, or None if no players
        """
        if not game_state.turn_order:
            return None
        
        current_player = game_state.get_current_player()
        if not current_player:
            return game_state.turn_order[0] if game_state.turn_order else None
        
        game_state.advance_turn()
        return game_state.get_current_player().player_id if game_state.get_current_player() else None
    
    @staticmethod
    def calculate_game_progress(game_state: GameState) -> Dict[str, Any]:
        """
        Calculate overall game progress metrics.
        
        Args:
            game_state: Current game state
            
        Returns:
            Dictionary with progress metrics
        """
        total_acts = game_state.max_acts
        current_act = game_state.current_act
        
        # Calculate act progress (0-100%)
        act_progress = ((current_act - 1) / total_acts) * 100
        
        # Calculate Q&A progress for current act
        total_possible_qna = len(game_state.characters) * game_state.max_qna_per_character_per_act
        current_act_qna = sum(
            game_state.get_qna_count_for_character_act(char_id, current_act)
            for char_id in game_state.characters.keys()
        )
        qna_progress = (current_act_qna / total_possible_qna * 100) if total_possible_qna > 0 else 0
        
        # Overall progress
        phase_weights = {
            GamePhase.INITIALIZATION: 5,
            GamePhase.MONOLOGUE: 15,
            GamePhase.QNA: 60,
            GamePhase.MISSION_SUBMIT: 15,
            GamePhase.FINAL_CHOICE: 5,
            GamePhase.COMPLETED: 100
        }
        
        phase_progress = phase_weights.get(game_state.current_phase, 0)
        overall_progress = min(100, act_progress + (qna_progress * 0.6) + phase_progress)
        
        return {
            "overall_progress": round(overall_progress, 1),
            "act_progress": round(act_progress, 1),
            "qna_progress": round(qna_progress, 1),
            "current_act": current_act,
            "total_acts": total_acts,
            "current_phase": game_state.current_phase.value,
            "total_qna_current_act": current_act_qna,
            "max_qna_current_act": total_possible_qna
        }
    
    @staticmethod
    def get_available_actions(game_state: GameState, player_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of available actions for the current game state.
        
        Args:
            game_state: Current game state
            player_id: Optional specific player ID
            
        Returns:
            List of available action dictionaries
        """
        actions = []
        current_phase = game_state.current_phase
        
        if current_phase == GamePhase.INITIALIZATION:
            actions.append({
                "action_type": "advance_phase",
                "target_phase": GamePhase.MONOLOGUE.value,
                "description": "开始角色介绍阶段"
            })
        
        elif current_phase == GamePhase.MONOLOGUE:
            # Add monologue actions for each character
            for character_id in game_state.characters.keys():
                actions.append({
                    "action_type": "monologue",
                    "character_id": character_id,
                    "description": f"让{character_id}进行自我介绍"
                })
            
            actions.append({
                "action_type": "advance_phase",
                "target_phase": GamePhase.QNA.value,
                "description": "进入问答阶段"
            })
        
        elif current_phase == GamePhase.QNA:
            # Add Q&A actions for each character
            for character_id in game_state.characters.keys():
                remaining_questions = (
                    game_state.max_qna_per_character_per_act - 
                    game_state.get_qna_count_for_character_act(character_id, game_state.current_act)
                )
                if remaining_questions > 0:
                    actions.append({
                        "action_type": "qna",
                        "character_id": character_id,
                        "remaining_questions": remaining_questions,
                        "description": f"向{character_id}提问 (剩余{remaining_questions}次)"
                    })
            
            # Mission submission action
            actions.append({
                "action_type": "mission_submit",
                "description": "提交任务或线索"
            })
            
            # Phase advancement options
            if game_state.current_act < game_state.max_acts:
                actions.append({
                    "action_type": "advance_act",
                    "description": f"进入第{game_state.current_act + 1}幕"
                })
            else:
                actions.append({
                    "action_type": "advance_phase",
                    "target_phase": GamePhase.FINAL_CHOICE.value,
                    "description": "进入最终选择阶段"
                })
        
        elif current_phase == GamePhase.MISSION_SUBMIT:
            actions.append({
                "action_type": "advance_phase",
                "target_phase": GamePhase.QNA.value,
                "description": "返回问答阶段"
            })
            
            if game_state.current_act >= game_state.max_acts:
                actions.append({
                    "action_type": "advance_phase",
                    "target_phase": GamePhase.FINAL_CHOICE.value,
                    "description": "进入最终选择阶段"
                })
        
        elif current_phase == GamePhase.FINAL_CHOICE:
            actions.append({
                "action_type": "final_choice",
                "description": "做出最终选择"
            })
            
            actions.append({
                "action_type": "advance_phase",
                "target_phase": GamePhase.COMPLETED.value,
                "description": "结束游戏"
            })
        
        return actions
    
    @staticmethod
    def format_game_summary(game_state: GameState) -> str:
        """
        Format a human-readable game summary.
        
        Args:
            game_state: Current game state
            
        Returns:
            Formatted summary string
        """
        progress = GamePhaseNodes.calculate_game_progress(game_state)
        
        summary_lines = [
            f"游戏ID: {game_state.game_id}",
            f"剧本: {game_state.script_id}",
            f"当前阶段: {game_state.current_phase.value}",
            f"第{game_state.current_act}幕 (共{game_state.max_acts}幕)",
            f"整体进度: {progress['overall_progress']}%",
            f"玩家数量: {len(game_state.players)}",
            f"角色数量: {len(game_state.characters)}",
            f"问答记录: {len(game_state.qna_history)}条",
            f"任务提交: {len(game_state.mission_submissions)}个",
            f"公开日志: {len(game_state.public_log)}条"
        ]
        
        if game_state.turn_order:
            current_player = game_state.get_current_player()
            if current_player:
                summary_lines.append(f"当前轮次: {current_player.player_id}")
        
        return "\n".join(summary_lines)
