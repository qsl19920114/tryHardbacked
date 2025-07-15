from app.database import SessionLocal, engine
from app.models.database_models import Base, Script

# 创建所有数据库表（如果不存在）
Base.metadata.create_all(bind=engine)

# 创建数据库会话
db = SessionLocal()

# 检查数据库中是否已有剧本数据，避免重复插入
if db.query(Script).first() is None:
    print("正在创建初始剧本数据...")
    
    # 创建第一个示例剧本：午夜图书馆（悬疑类）
    script1 = Script(
        id="1",
        title="午夜图书馆",
        cover="/images/scripts/1.jpg",
        category="Mystery",
        tags=["悬疑", "本格", "微恐"],
        players="6人 (3男3女)",
        difficulty=4,
        duration="约4小时",
        description="深夜的图书馆中，一位管理员神秘失踪...",
        author="神秘作者",
        characters=[
            {"name": "图书管理员", "avatar": "/images/characters/librarian.jpg", "description": "知识渊博但性格孤僻的管理员"},
            {"name": "文学教授", "avatar": "/images/characters/professor.jpg", "description": "优雅的中年教授，对古籍情有独钟"}
        ]
    )
    
    # 创建第二个示例剧本：校园青春物语（恋爱类）
    script2 = Script(
        id="2",
        title="校园青春物语",
        cover="/images/scripts/2.jpg",
        category="Romance",
        tags=["青春", "校园", "恋爱"],
        players="4人 (2男2女)",
        difficulty=2,
        duration="约2小时",
        description="高中时代的青涩恋爱故事...",
        author="青春作者",
        characters=[
            {"name": "学生会长", "avatar": "/images/characters/president.jpg", "description": "优秀的学生会长"},
            {"name": "转校生", "avatar": "/images/characters/transfer.jpg", "description": "神秘的转校生"}
        ]
    )
    
    # 将剧本数据添加到数据库会话
    db.add(script1)
    db.add(script2)
    db.commit()  # 提交事务，保存到数据库
    print("初始数据创建完成。")
else:
    print("数据已存在，跳过初始化。")

# 关闭数据库会话
db.close()

if __name__ == "__main__":
    print("数据库和表格创建完成。初始化数据脚本执行结束。")