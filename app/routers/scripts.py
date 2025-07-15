from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import database_models as models
from app.schemas import pydantic_schemas as schemas

# 创建剧本管理路由器
router = APIRouter(
    prefix="/api/v1/scripts",  # 路由前缀
    tags=["Scripts"],  # 在 API 文档中的标签分组
)

@router.get("", response_model=schemas.ScriptListResponse)
def get_scripts(db: Session = Depends(get_db)):
    """
    获取所有剧本列表
    
    Returns:
        ScriptListResponse: 包含所有剧本信息的响应对象
    """
    # 从数据库查询所有剧本
    scripts = db.query(models.Script).all()
    return {"scripts": scripts}

@router.get("/{script_id}", response_model=schemas.Script)
def get_script_details(script_id: str, db: Session = Depends(get_db)):
    """
    根据剧本ID获取特定剧本的详细信息

    Args:
        script_id: 剧本的唯一标识符
        db: 数据库会话（依赖注入）

    Returns:
        Script: 剧本详细信息对象

    Raises:
        HTTPException: 当剧本不存在时返回404错误
    """
    # 根据ID查询特定剧本
    script = db.query(models.Script).filter(models.Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script

@router.post("", response_model=schemas.Script, status_code=201)
def create_script(script_data: schemas.ScriptBase, db: Session = Depends(get_db)):
    """
    创建新的剧本

    Args:
        script_data: 剧本基础信息对象
        db: 数据库会话（依赖注入）

    Returns:
        Script: 新创建的剧本对象

    Raises:
        HTTPException: 当剧本ID已存在时返回400错误
    """
    # 检查剧本ID是否已存在
    existing_script = db.query(models.Script).filter(models.Script.id == script_data.id).first()
    if existing_script:
        raise HTTPException(status_code=400, detail="Script with this ID already exists")

    # 创建新的剧本对象
    new_script = models.Script(
        id=script_data.id,
        title=script_data.title,
        cover=script_data.cover,
        category=script_data.category,
        tags=script_data.tags,
        players=script_data.players,
        difficulty=script_data.difficulty,
        duration=script_data.duration,
        author=script_data.author,
        description=script_data.description,
        characters=[char.model_dump() for char in script_data.characters]  # 转换为字典格式存储
    )

    # 添加到数据库
    db.add(new_script)
    db.commit()
    db.refresh(new_script)  # 刷新对象以获取数据库生成的字段（如时间戳）

    return new_script