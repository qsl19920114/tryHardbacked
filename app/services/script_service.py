import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
from app.schemas.pydantic_schemas import ScriptScene, SceneType

class ScriptManifestService:
    """剧本清单服务 - 处理剧本场景配置的加载和管理"""
    
    def __init__(self, data_root: str = "data/scripts"):
        """
        初始化剧本清单服务
        
        Args:
            data_root: 剧本数据根目录路径
        """
        self.data_root = Path(data_root)
    
    def load_script_manifest(self, script_id: str) -> Optional[Dict[str, Any]]:
        """
        加载指定剧本的场景清单
        
        Args:
            script_id: 剧本ID
            
        Returns:
            Dict: 剧本清单数据，如果文件不存在则返回None
        """
        manifest_path = self.data_root / script_id / "scenes.json"
        
        if not manifest_path.exists():
            return None
            
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载剧本清单失败 {script_id}: {e}")
            return None
    
    def get_scene_config(self, script_id: str, scene_index: int) -> Optional[Dict[str, Any]]:
        """
        获取指定场景的配置信息
        
        Args:
            script_id: 剧本ID
            scene_index: 场景索引
            
        Returns:
            Dict: 场景配置数据，如果不存在则返回None
        """
        manifest = self.load_script_manifest(script_id)
        if not manifest:
            return None
            
        scenes = manifest.get("scenes", [])
        for scene in scenes:
            if scene.get("scene_index") == scene_index:
                return scene
                
        return None
    
    def get_total_scenes(self, script_id: str) -> int:
        """
        获取剧本的总场景数
        
        Args:
            script_id: 剧本ID
            
        Returns:
            int: 总场景数，如果清单不存在则返回0
        """
        manifest = self.load_script_manifest(script_id)
        if not manifest:
            return 0
            
        return manifest.get("metadata", {}).get("total_scenes", 0)
    
    def get_scene_workflow_id(self, script_id: str, scene_index: int) -> Optional[str]:
        """
        获取指定场景对应的Dify工作流ID
        
        Args:
            script_id: 剧本ID
            scene_index: 场景索引
            
        Returns:
            str: Dify工作流ID，如果不存在则返回None
        """
        scene_config = self.get_scene_config(script_id, scene_index)
        if not scene_config:
            return None
            
        return scene_config.get("dify_workflow_id")
    
    def get_character_workflow_id(self, script_id: str, scene_index: int, character_id: str) -> Optional[str]:
        """
        获取调查模式下指定角色的Dify工作流ID
        
        Args:
            script_id: 剧本ID
            scene_index: 场景索引
            character_id: 角色ID
            
        Returns:
            str: 角色对应的Dify工作流ID，如果不存在则返回None
        """
        scene_config = self.get_scene_config(script_id, scene_index)
        if not scene_config or scene_config.get("scene_type") != "investigation":
            return None
            
        available_characters = scene_config.get("scene_config", {}).get("available_characters", [])
        for character in available_characters:
            if character.get("character_id") == character_id:
                return character.get("dify_workflow_id")
                
        return None
    
    def get_available_characters(self, script_id: str, scene_index: int) -> List[Dict[str, Any]]:
        """
        获取调查模式下可用的角色列表
        
        Args:
            script_id: 剧本ID
            scene_index: 场景索引
            
        Returns:
            List[Dict]: 可用角色列表
        """
        scene_config = self.get_scene_config(script_id, scene_index)
        if not scene_config or scene_config.get("scene_type") != "investigation":
            return []
            
        return scene_config.get("scene_config", {}).get("available_characters", [])
    
    def is_final_scene(self, script_id: str, scene_index: int) -> bool:
        """
        检查指定场景是否为最终场景

        Args:
            script_id: 剧本ID
            scene_index: 场景索引

        Returns:
            bool: 是否为最终场景
        """
        scene_config = self.get_scene_config(script_id, scene_index)
        if not scene_config:
            return False

        return scene_config.get("scene_config", {}).get("is_final", False)

    def get_scene_by_id(self, script_id: str, scene_id: int) -> Optional[Dict[str, Any]]:
        """
        通过场景ID获取场景配置（scene_id等同于scene_index）

        Args:
            script_id: 剧本ID
            scene_id: 场景ID

        Returns:
            Dict: 场景配置数据，如果不存在则返回None
        """
        return self.get_scene_config(script_id, scene_id)

    def get_scene_context_info(self, script_id: str, scene_id: int) -> Optional[Dict[str, Any]]:
        """
        获取场景的完整上下文信息，用于API响应

        Args:
            script_id: 剧本ID
            scene_id: 场景ID

        Returns:
            Dict: 场景上下文信息
        """
        scene_config = self.get_scene_config(script_id, scene_id)
        if not scene_config:
            return None

        context_info = {
            "scene_id": scene_id,
            "scene_type": scene_config.get("scene_type"),
            "title": scene_config.get("title", ""),
            "description": scene_config.get("description", ""),
            "available_characters": [],
            "scene_metadata": scene_config.get("scene_config", {})
        }

        # 如果是调查场景，添加可用角色信息
        if scene_config.get("scene_type") == "investigation":
            context_info["available_characters"] = scene_config.get("scene_config", {}).get("available_characters", [])

        return context_info

    def get_available_actions_for_scene(self, script_id: str, scene_id: int, current_scene_index: int) -> List[Dict[str, Any]]:
        """
        获取当前场景下可用的操作列表

        Args:
            script_id: 剧本ID
            scene_id: 场景ID
            current_scene_index: 当前场景索引

        Returns:
            List[Dict]: 可用操作列表
        """
        scene_config = self.get_scene_config(script_id, scene_id)
        if not scene_config:
            return []

        actions = []
        scene_type = scene_config.get("scene_type")

        if scene_type == "story":
            # 故事场景：可以推进到下一场景
            if not self.is_final_scene(script_id, scene_id):
                actions.append({
                    "action_type": "advance",
                    "action_name": "推进故事",
                    "description": "点击继续推进到下一个场景",
                    "parameters": {"action": "next"}
                })

        elif scene_type == "investigation":
            # 调查场景：可以与角色对话
            available_characters = scene_config.get("scene_config", {}).get("available_characters", [])
            for character in available_characters:
                actions.append({
                    "action_type": "dialogue",
                    "action_name": f"与{character.get('name', character.get('character_id'))}对话",
                    "description": f"向{character.get('description', '角色')}提问",
                    "parameters": {
                        "character_id": character.get("character_id"),
                        "scene_id": scene_id
                    }
                })

            # 调查场景也可以推进（如果不是最终场景）
            if not self.is_final_scene(script_id, scene_id):
                actions.append({
                    "action_type": "advance",
                    "action_name": "结束调查",
                    "description": "结束当前调查阶段，推进到下一场景",
                    "parameters": {"action": "next"}
                })

        return actions

# 创建全局服务实例
script_manifest_service = ScriptManifestService()
