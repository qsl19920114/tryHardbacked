"""
场景数据初始化脚本
从剧本清单文件中读取场景配置并插入到数据库中
支持24场景的完整剧本配置
"""

from app.database import SessionLocal, engine
from app.models.database_models import Base, ScriptScene, SceneType
from app.services.script_service import script_manifest_service

# 创建所有数据库表（如果不存在）
Base.metadata.create_all(bind=engine)

# 创建数据库会话
db = SessionLocal()

def clear_existing_scenes(script_id: str):
    """
    清除指定剧本的现有场景数据
    
    Args:
        script_id: 剧本ID
    """
    existing_scenes = db.query(ScriptScene).filter(ScriptScene.script_id == script_id).all()
    if existing_scenes:
        for scene in existing_scenes:
            db.delete(scene)
        db.commit()
        print(f"已清除剧本 {script_id} 的 {len(existing_scenes)} 个现有场景")

def create_scenes_from_manifest(script_id: str):
    """
    从剧本清单创建场景数据
    
    Args:
        script_id: 剧本ID
    """
    # 先清除现有数据
    clear_existing_scenes(script_id)
    
    # 加载剧本清单
    manifest = script_manifest_service.load_script_manifest(script_id)
    if not manifest:
        print(f"无法加载剧本 {script_id} 的清单文件。")
        return
    
    scenes_data = manifest.get("scenes", [])
    print(f"正在为剧本 {script_id} 创建 {len(scenes_data)} 个场景...")
    
    story_count = 0
    investigation_count = 0
    
    for scene_data in scenes_data:
        # 统计场景类型
        scene_type = scene_data.get("scene_type")
        if scene_type == "story":
            story_count += 1
        elif scene_type == "investigation":
            investigation_count += 1
        
        # 创建场景对象
        scene = ScriptScene(
            script_id=script_id,
            scene_index=scene_data.get("scene_index"),
            scene_type=SceneType(scene_type),
            title=scene_data.get("title"),
            description=scene_data.get("description"),
            dify_workflow_id=scene_data.get("dify_workflow_id"),
            scene_config=scene_data.get("scene_config")
        )
        db.add(scene)
    
    db.commit()
    print(f"✅ 成功创建了剧本 {script_id} 的 {len(scenes_data)} 个场景")
    print(f"   - 故事场景: {story_count} 个")
    print(f"   - 调查场景: {investigation_count} 个")
    
    # 显示场景概览
    print(f"\n📋 剧本 {script_id} 场景概览:")
    for i, scene_data in enumerate(scenes_data[:5]):  # 显示前5个场景
        print(f"   {i}: {scene_data.get('title')} ({scene_data.get('scene_type')})")
    if len(scenes_data) > 5:
        print(f"   ... 还有 {len(scenes_data) - 5} 个场景")

def validate_scene_data(script_id: str):
    """
    验证场景数据的完整性
    
    Args:
        script_id: 剧本ID
    """
    print(f"\n🔍 验证剧本 {script_id} 的场景数据...")
    
    scenes = db.query(ScriptScene).filter(ScriptScene.script_id == script_id).order_by(ScriptScene.scene_index).all()
    
    if not scenes:
        print(f"❌ 剧本 {script_id} 没有场景数据")
        return False
    
    # 检查场景索引连续性
    expected_index = 0
    for scene in scenes:
        if scene.scene_index != expected_index:
            print(f"❌ 场景索引不连续: 期望 {expected_index}, 实际 {scene.scene_index}")
            return False
        expected_index += 1
    
    # 统计场景类型
    story_scenes = [s for s in scenes if s.scene_type == SceneType.STORY]
    investigation_scenes = [s for s in scenes if s.scene_type == SceneType.INVESTIGATION]
    
    print(f"✅ 场景数据验证通过:")
    print(f"   - 总场景数: {len(scenes)}")
    print(f"   - 故事场景: {len(story_scenes)}")
    print(f"   - 调查场景: {len(investigation_scenes)}")
    
    # 检查调查场景的角色配置
    investigation_characters = 0
    for scene in investigation_scenes:
        if scene.scene_config and 'available_characters' in scene.scene_config:
            chars = scene.scene_config['available_characters']
            investigation_characters += len(chars)
            print(f"   - 场景 {scene.scene_index} ({scene.title}): {len(chars)} 个角色")
    
    print(f"   - 调查场景总角色数: {investigation_characters}")
    
    return True

def main():
    """主函数"""
    try:
        print("🚀 开始初始化场景数据")
        print("=" * 50)
        
        # 初始化剧本数据
        script_ids = ["1", "2"]  # 可以添加更多剧本ID
        
        for script_id in script_ids:
            print(f"\n📚 处理剧本 {script_id}")
            create_scenes_from_manifest(script_id)
            validate_scene_data(script_id)
        
        print(f"\n🎉 场景数据初始化完成！")
        print(f"现在可以通过以下方式测试:")
        print(f"1. 启动服务器: python run.py")
        print(f"2. 创建游戏会话并测试场景推进")
        print(f"3. 测试调查模式的角色对话")
        
    except Exception as e:
        print(f"❌ 初始化场景数据时发生错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
