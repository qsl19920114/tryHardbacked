import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_ # 1. 导入 or_ 用于实现多字段搜索
from typing import Optional, List # 导入 Optional

from app.database import get_db
from app.models import database_models as models
from app.schemas import pydantic_schemas as schemas

router = APIRouter(
    prefix="/api/v1/scripts",
    tags=["Scripts"],
)

@router.get("", response_model=schemas.ScriptListResponse)
def get_scripts(
    db: Session = Depends(get_db),
    page: int = Query(1, gt=0, description="页码，从1开始"),
    page_size: int = Query(8, gt=0, le=100, description="每页数量"),
    # 2. 添加 category 和 search 参数
    category: Optional[str] = Query(None, description="按分类筛选，例如：Mystery, Horror"),
    search: Optional[str] = Query(None, description="搜索关键词，将匹配标题和描述")
):
    # 3. 开始构建基础查询
    scripts_query = db.query(models.Script)
    
    # 4. 根据参数动态添加过滤条件
    if category:
        # 如果提供了 category 参数，添加分类过滤
        scripts_query = scripts_query.filter(models.Script.category == category)
        
    if search:
        # 如果提供了 search 参数，添加搜索过滤
        # 使用 or_ 来同时搜索 title 和 description 字段
        # 使用 ilike 来进行不区分大小写的模糊匹配
        search_term = f"%{search}%"
        scripts_query = scripts_query.filter(
            or_(
                models.Script.title.ilike(search_term),
                models.Script.description.ilike(search_term)
            )
        )
    
    # 5. 在过滤后的查询上计算总数 (非常重要)
    total_count = scripts_query.count()
    
    # 6. 应用分页
    offset = (page - 1) * page_size
    scripts = scripts_query.offset(offset).limit(page_size).all()
    
    # 计算总页数
    total_pages = math.ceil(total_count / page_size)
    
    # 按照 ScriptListResponse 格式返回
    return {
        "scripts": scripts,
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }




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

    # 创建新的剧本对象（cover字段会通过SQLAlchemy事件监听器自动生成）
    new_script = models.Script(
        id=script_data.id,
        title=script_data.title,
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