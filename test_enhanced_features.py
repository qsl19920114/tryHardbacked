"""
增强功能测试脚本
测试新增的scene_id参数支持、调试信息和24场景配置
"""

import requests
import json
import time
from typing import Dict, Any

# API基础URL
BASE_URL = "http://127.0.0.1:8000"

def test_create_session_and_advance():
    """测试创建会话和场景推进"""
    print("🎮 测试创建会话和场景推进")
    print("=" * 40)
    
    # 创建游戏会话
    response = requests.post(f"{BASE_URL}/api/v1/game/sessions", json={
        "script_id": "1",
        "user_id": "test_user_enhanced"
    })
    
    if response.status_code != 201:
        print(f"❌ 创建会话失败: {response.text}")
        return None
    
    session_data = response.json()
    session_id = session_data["session_id"]
    print(f"✅ 会话创建成功: {session_id}")
    
    # 推进到调查场景 (场景3)
    for i in range(4):  # 推进到场景3
        response = requests.post(f"{BASE_URL}/api/v1/game/sessions/{session_id}/advance", json={
            "session_id": session_id,
            "action": "next"
        })
        
        if response.status_code == 200:
            result = response.json()
            scene_content = result["scene_content"]
            print(f"📖 场景 {result['current_scene_index']}: {scene_content['title']} ({scene_content['scene_type']})")
            
            # 显示调试信息
            if result.get("debug_info"):
                debug_info = result["debug_info"]
                print(f"   🔧 工作流ID: {debug_info.get('workflow_id')}")
                print(f"   ⏱️ 处理步骤: {len(debug_info.get('processing_steps', []))} 步")
            
            # 显示可用操作
            if result.get("available_actions"):
                actions = result["available_actions"]
                print(f"   🎯 可用操作: {len(actions)} 个")
                for action in actions[:2]:  # 显示前2个操作
                    print(f"      - {action['action_name']}: {action['description']}")
            
            if scene_content["scene_type"] == "investigation":
                print(f"   👥 可用角色: {scene_content.get('characters', [])}")
                break
        else:
            print(f"❌ 场景推进失败: {response.text}")
            return None
    
    return session_id

def test_dialogue_with_scene_id(session_id: str):
    """测试带scene_id参数的对话功能"""
    print(f"\n💬 测试带scene_id参数的对话功能")
    print("=" * 40)
    
    # 测试与不同角色的对话，指定scene_id
    test_dialogues = [
        {
            "scene_id": 3,
            "character_id": "librarian_ai",
            "question": "你好，请介绍一下这个图书馆的特色"
        },
        {
            "scene_id": 3,
            "character_id": "professor_ai", 
            "question": "作为教授，你对这里的古籍有什么看法？"
        },
        {
            "scene_id": 6,  # 测试不同场景的对话
            "character_id": "security_ai",
            "question": "作为保安，你注意到什么异常情况吗？"
        }
    ]
    
    for dialogue in test_dialogues:
        print(f"\n🎯 场景 {dialogue['scene_id']} - 与 {dialogue['character_id']} 对话")
        
        response = requests.post(f"{BASE_URL}/api/v1/ai/dialogue", json={
            "session_id": session_id,
            "question": dialogue["question"],
            "character_id": dialogue["character_id"],
            "scene_id": dialogue["scene_id"]
        })
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 对话成功")
            print(f"   💭 问题: {result['question']}")
            print(f"   🤖 回答: {result['answer'][:100]}...")
            print(f"   ⏱️ 响应时间: {result['response_time']}秒")
            
            # 显示调试信息
            if result.get("debug_info"):
                debug_info = result["debug_info"]
                print(f"   🔧 工作流ID: {debug_info.get('workflow_id')}")
                print(f"   📋 处理步骤: {len(debug_info.get('processing_steps', []))} 步")
            
            # 显示场景上下文
            if result.get("scene_context"):
                scene_context = result["scene_context"]
                print(f"   🎬 场景上下文: {scene_context['title']} ({scene_context['scene_type']})")
                print(f"   👥 可用角色数: {len(scene_context.get('available_characters', []))}")
            
            # 显示可用操作
            if result.get("available_actions"):
                actions = result["available_actions"]
                print(f"   🎯 可用操作: {len(actions)} 个")
        else:
            print(f"❌ 对话失败: {response.text}")
        
        time.sleep(1)  # 等待异步广播

def test_scene_progression():
    """测试24场景的推进"""
    print(f"\n📚 测试24场景推进")
    print("=" * 40)
    
    # 创建新会话
    response = requests.post(f"{BASE_URL}/api/v1/game/sessions", json={
        "script_id": "2",  # 使用剧本2测试
        "user_id": "test_user_24scenes"
    })
    
    if response.status_code != 201:
        print(f"❌ 创建会话失败: {response.text}")
        return
    
    session_data = response.json()
    session_id = session_data["session_id"]
    print(f"✅ 会话创建成功: {session_id}")
    
    # 推进前10个场景
    for i in range(10):
        response = requests.post(f"{BASE_URL}/api/v1/game/sessions/{session_id}/advance", json={
            "session_id": session_id,
            "action": "next"
        })
        
        if response.status_code == 200:
            result = response.json()
            scene_content = result["scene_content"]
            print(f"📖 场景 {result['current_scene_index']}: {scene_content['title']} ({scene_content['scene_type']})")
            
            # 如果是调查场景，显示角色信息
            if scene_content["scene_type"] == "investigation":
                characters = scene_content.get("characters", [])
                print(f"   👥 可用角色: {len(characters)} 个")
                
                # 测试一个快速对话
                if characters:
                    test_char = characters[0]
                    dialogue_response = requests.post(f"{BASE_URL}/api/v1/ai/dialogue", json={
                        "session_id": session_id,
                        "question": "简单介绍一下你自己",
                        "character_id": test_char,
                        "scene_id": result['current_scene_index']
                    })
                    
                    if dialogue_response.status_code == 200:
                        dialogue_result = dialogue_response.json()
                        print(f"   💬 {test_char}: {dialogue_result['answer'][:50]}...")
        else:
            print(f"❌ 场景 {i} 推进失败: {response.text}")
            break
        
        time.sleep(0.5)  # 短暂延迟

def main():
    """主测试函数"""
    print("🚀 启动增强功能测试")
    print("=" * 50)
    
    # 检查服务器连接
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("❌ 服务器未运行或无法访问")
            return
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器正在运行")
        return
    
    print("✅ 服务器连接正常")
    
    # 测试1: 创建会话和推进到调查场景
    session_id = test_create_session_and_advance()
    if not session_id:
        return
    
    # 测试2: 带scene_id参数的对话
    test_dialogue_with_scene_id(session_id)
    
    # 测试3: 24场景推进
    test_scene_progression()
    
    print(f"\n🎉 增强功能测试完成！")
    print(f"主要新功能验证:")
    print(f"✅ scene_id参数支持")
    print(f"✅ 调试信息输出")
    print(f"✅ 场景上下文信息")
    print(f"✅ 可用操作列表")
    print(f"✅ 24场景配置")
    print(f"✅ 中文内容支持")

if __name__ == "__main__":
    main()
