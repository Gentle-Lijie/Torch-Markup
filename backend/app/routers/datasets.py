from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
from app.core import get_db_dependency, get_current_admin, get_current_user, settings

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


class ScanResult(BaseModel):
    found_images: int
    imported_images: int
    skipped_images: int


@router.get("", response_model=List[DatasetResponse])
async def list_datasets(
    conn = Depends(get_db_dependency),
    current_user = Depends(get_current_user)
):
    """获取数据集列表"""
    with conn.cursor() as cursor:
        if current_user['is_admin']:
            cursor.execute("SELECT * FROM datasets")
        else:
            cursor.execute("SELECT * FROM datasets WHERE is_active = TRUE")
        datasets = cursor.fetchall()

    return datasets


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: int,
    conn = Depends(get_db_dependency),
    current_user = Depends(get_current_user)
):
    """获取单个数据集详情"""
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM datasets WHERE id = %s", (dataset_id,))
        dataset = cursor.fetchone()

    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")
    if not dataset['is_active'] and not current_user['is_admin']:
        raise HTTPException(status_code=403, detail="无权访问该数据集")

    return dataset


@router.post("", response_model=DatasetResponse)
async def create_dataset(
    dataset_data: DatasetCreate,
    conn = Depends(get_db_dependency),
    current_admin = Depends(get_current_admin)
):
    """创建数据集"""
    # 检查路径是否存在
    if not os.path.isdir(dataset_data.image_path):
        raise HTTPException(status_code=400, detail="图片路径不存在")

    if dataset_data.label_path and not os.path.isdir(dataset_data.label_path):
        try:
            os.makedirs(dataset_data.label_path, exist_ok=True)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"无法创建标签目录: {str(e)}")

    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO datasets (name, description, image_path, label_path) VALUES (%s, %s, %s, %s)",
            (dataset_data.name, dataset_data.description, dataset_data.image_path, dataset_data.label_path)
        )
        dataset_id = cursor.lastrowid

        cursor.execute("SELECT * FROM datasets WHERE id = %s", (dataset_id,))
        dataset = cursor.fetchone()

    return dataset


@router.put("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(
    dataset_id: int,
    dataset_data: DatasetUpdate,
    conn = Depends(get_db_dependency),
    current_admin = Depends(get_current_admin)
):
    """更新数据集"""
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM datasets WHERE id = %s", (dataset_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="数据集不存在")

        updates = []
        params = []

        if dataset_data.name is not None:
            updates.append("name = %s")
            params.append(dataset_data.name)
        if dataset_data.description is not None:
            updates.append("description = %s")
            params.append(dataset_data.description)
        if dataset_data.image_path is not None:
            if not os.path.isdir(dataset_data.image_path):
                raise HTTPException(status_code=400, detail="图片路径不存在")
            updates.append("image_path = %s")
            params.append(dataset_data.image_path)
        if dataset_data.label_path is not None:
            updates.append("label_path = %s")
            params.append(dataset_data.label_path)
        if dataset_data.is_active is not None:
            updates.append("is_active = %s")
            params.append(dataset_data.is_active)

        if updates:
            params.append(dataset_id)
            cursor.execute(f"UPDATE datasets SET {', '.join(updates)} WHERE id = %s", params)

        cursor.execute("SELECT * FROM datasets WHERE id = %s", (dataset_id,))
        dataset = cursor.fetchone()

    return dataset


@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: int,
    conn = Depends(get_db_dependency),
    current_admin = Depends(get_current_admin)
):
    """删除数据集"""
    with conn.cursor() as cursor:
        cursor.execute("SELECT id FROM datasets WHERE id = %s", (dataset_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="数据集不存在")

        cursor.execute("DELETE FROM datasets WHERE id = %s", (dataset_id,))

    return {"message": "删除成功"}


@router.post("/{dataset_id}/scan", response_model=ScanResult)
async def scan_dataset(
    dataset_id: int,
    conn = Depends(get_db_dependency),
    current_admin = Depends(get_current_admin)
):
    """扫描并导入图片"""
    from PIL import Image as PILImage

    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM datasets WHERE id = %s", (dataset_id,))
        dataset = cursor.fetchone()

        if not dataset:
            raise HTTPException(status_code=404, detail="数据集不存在")

        if not os.path.isdir(dataset['image_path']):
            raise HTTPException(status_code=400, detail="图片路径不存在")

        # 获取已存在的图片文件名
        cursor.execute("SELECT filename FROM images WHERE dataset_id = %s", (dataset_id,))
        existing_files = set(row['filename'] for row in cursor.fetchall())

        found = 0
        imported = 0
        skipped = 0

        # 扫描目录
        for filename in os.listdir(dataset['image_path']):
            ext = os.path.splitext(filename)[1].lower()
            if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
                continue

            found += 1

            if filename in existing_files:
                skipped += 1
                continue

            file_path = os.path.join(dataset['image_path'], filename)

            # 获取图片尺寸
            try:
                with PILImage.open(file_path) as img:
                    width, height = img.size
            except Exception:
                width, height = None, None

            # 创建图片记录
            cursor.execute(
                "INSERT INTO images (dataset_id, filename, file_path, width, height, status) VALUES (%s, %s, %s, %s, %s, %s)",
                (dataset_id, filename, file_path, width, height, 'pending')
            )
            imported += 1

        # 更新数据集统计
        cursor.execute("SELECT COUNT(*) as count FROM images WHERE dataset_id = %s", (dataset_id,))
        total = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM images WHERE dataset_id = %s AND status = 'labeled'", (dataset_id,))
        labeled = cursor.fetchone()['count']

        cursor.execute("UPDATE datasets SET total_images = %s, labeled_images = %s WHERE id = %s", (total, labeled, dataset_id))

    return ScanResult(
        found_images=found,
        imported_images=imported,
        skipped_images=skipped
    )
