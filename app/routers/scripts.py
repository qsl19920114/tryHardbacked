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