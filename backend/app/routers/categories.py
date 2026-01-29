from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.core import get_db, get_current_admin, get_current_user
from app.models.user import User
from app.models.dataset import Dataset
from app.models.category import Category

router = APIRouter(prefix="/api/categories", tags=["类别"])


class CategoryCreate(BaseModel):
    dataset_id: int
    name: str
    shortcut_key: Optional[str] = None
    color: Optional[str] = "#FF0000"
    sort_order: Optional[int] = 0


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    shortcut_key: Optional[str] = None
    color: Optional[str] = None
    sort_order: Optional[int] = None


class CategoryResponse(BaseModel):
    id: int
    dataset_id: int
    name: str
    shortcut_key: Optional[str]
    color: str
    sort_order: int
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/dataset/{dataset_id}", response_model=List[CategoryResponse])
async def list_categories(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取数据集的类别列表"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")

    categories = db.query(Category).filter(
        Category.dataset_id == dataset_id
    ).order_by(Category.sort_order).all()

    return categories


@router.post("", response_model=CategoryResponse)
async def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """创建类别"""
    # 检查数据集是否存在
    dataset = db.query(Dataset).filter(Dataset.id == category_data.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")

    # 检查类别名是否重复
    existing = db.query(Category).filter(
        Category.dataset_id == category_data.dataset_id,
        Category.name == category_data.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="类别名已存在")

    # 检查快捷键是否重复
    if category_data.shortcut_key:
        existing_key = db.query(Category).filter(
            Category.dataset_id == category_data.dataset_id,
            Category.shortcut_key == category_data.shortcut_key
        ).first()
        if existing_key:
            raise HTTPException(status_code=400, detail="快捷键已被使用")

    category = Category(
        dataset_id=category_data.dataset_id,
        name=category_data.name,
        shortcut_key=category_data.shortcut_key,
        color=category_data.color,
        sort_order=category_data.sort_order
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    return category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """更新类别"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="类别不存在")

    if category_data.name is not None:
        # 检查名称是否重复
        existing = db.query(Category).filter(
            Category.dataset_id == category.dataset_id,
            Category.name == category_data.name,
            Category.id != category_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="类别名已存在")
        category.name = category_data.name

    if category_data.shortcut_key is not None:
        # 检查快捷键是否重复
        if category_data.shortcut_key:
            existing_key = db.query(Category).filter(
                Category.dataset_id == category.dataset_id,
                Category.shortcut_key == category_data.shortcut_key,
                Category.id != category_id
            ).first()
            if existing_key:
                raise HTTPException(status_code=400, detail="快捷键已被使用")
        category.shortcut_key = category_data.shortcut_key

    if category_data.color is not None:
        category.color = category_data.color

    if category_data.sort_order is not None:
        category.sort_order = category_data.sort_order

    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """删除类别"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="类别不存在")

    db.delete(category)
    db.commit()
    return {"message": "删除成功"}


@router.post("/batch", response_model=List[CategoryResponse])
async def batch_create_categories(
    categories: List[CategoryCreate],
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """批量创建类别"""
    if not categories:
        raise HTTPException(status_code=400, detail="类别列表不能为空")

    # 检查数据集是否存在
    dataset_id = categories[0].dataset_id
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")

    created = []
    for cat_data in categories:
        if cat_data.dataset_id != dataset_id:
            raise HTTPException(status_code=400, detail="所有类别必须属于同一数据集")

        category = Category(
            dataset_id=cat_data.dataset_id,
            name=cat_data.name,
            shortcut_key=cat_data.shortcut_key,
            color=cat_data.color,
            sort_order=cat_data.sort_order
        )
        db.add(category)
        created.append(category)

    db.commit()
    for cat in created:
        db.refresh(cat)

    return created
