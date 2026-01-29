from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
from app.core import get_db, get_current_admin, get_current_user
from app.models.user import User
from app.models.dataset import Dataset
from app.models.image import Image, ImageStatus
from app.models.category import Category
from app.core.config import settings

router = APIRouter(prefix="/api/datasets", tags=["数据集"])


class DatasetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    image_path: str
    label_path: Optional[str] = None


class DatasetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image_path: Optional[str] = None
    label_path: Optional[str] = None
    is_active: Optional[bool] = None


class DatasetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    image_path: str
    label_path: Optional[str]
    total_images: int
    labeled_images: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ScanResult(BaseModel):
    found_images: int
    imported_images: int
    skipped_images: int


@router.get("", response_model=List[DatasetResponse])
async def list_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取数据集列表"""
    if current_user.is_admin:
        datasets = db.query(Dataset).all()
    else:
        datasets = db.query(Dataset).filter(Dataset.is_active == True).all()
    return datasets


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个数据集详情"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")
    if not dataset.is_active and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权访问该数据集")
    return dataset


@router.post("", response_model=DatasetResponse)
async def create_dataset(
    dataset_data: DatasetCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """创建数据集"""
    # 检查路径是否存在
    if not os.path.isdir(dataset_data.image_path):
        raise HTTPException(status_code=400, detail="图片路径不存在")

    if dataset_data.label_path and not os.path.isdir(dataset_data.label_path):
        # 尝试创建标签目录
        try:
            os.makedirs(dataset_data.label_path, exist_ok=True)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"无法创建标签目录: {str(e)}")

    dataset = Dataset(
        name=dataset_data.name,
        description=dataset_data.description,
        image_path=dataset_data.image_path,
        label_path=dataset_data.label_path
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    return dataset


@router.put("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(
    dataset_id: int,
    dataset_data: DatasetUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """更新数据集"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")

    if dataset_data.name is not None:
        dataset.name = dataset_data.name
    if dataset_data.description is not None:
        dataset.description = dataset_data.description
    if dataset_data.image_path is not None:
        if not os.path.isdir(dataset_data.image_path):
            raise HTTPException(status_code=400, detail="图片路径不存在")
        dataset.image_path = dataset_data.image_path
    if dataset_data.label_path is not None:
        dataset.label_path = dataset_data.label_path
    if dataset_data.is_active is not None:
        dataset.is_active = dataset_data.is_active

    db.commit()
    db.refresh(dataset)
    return dataset


@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """删除数据集"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")

    db.delete(dataset)
    db.commit()
    return {"message": "删除成功"}


@router.post("/{dataset_id}/scan", response_model=ScanResult)
async def scan_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """扫描并导入图片"""
    from PIL import Image as PILImage

    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")

    if not os.path.isdir(dataset.image_path):
        raise HTTPException(status_code=400, detail="图片路径不存在")

    # 获取已存在的图片文件名
    existing_files = set(
        db.query(Image.filename).filter(Image.dataset_id == dataset_id).all()
    )
    existing_files = {f[0] for f in existing_files}

    found = 0
    imported = 0
    skipped = 0

    # 扫描目录
    for filename in os.listdir(dataset.image_path):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
            continue

        found += 1

        if filename in existing_files:
            skipped += 1
            continue

        file_path = os.path.join(dataset.image_path, filename)

        # 获取图片尺寸
        try:
            with PILImage.open(file_path) as img:
                width, height = img.size
        except Exception:
            width, height = None, None

        # 创建图片记录
        image = Image(
            dataset_id=dataset_id,
            filename=filename,
            file_path=file_path,
            width=width,
            height=height,
            status=ImageStatus.PENDING
        )
        db.add(image)
        imported += 1

    # 更新数据集统计
    dataset.total_images = db.query(Image).filter(Image.dataset_id == dataset_id).count()
    dataset.labeled_images = db.query(Image).filter(
        Image.dataset_id == dataset_id,
        Image.status == ImageStatus.LABELED
    ).count()

    db.commit()

    return ScanResult(
        found_images=found,
        imported_images=imported,
        skipped_images=skipped
    )
