"""数据集配置 API"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.core import get_db_dependency, get_current_user, get_current_admin
from app.services.dji_roco_parser import (
    get_default_categories,
    import_dji_roco_annotations,
    find_xml_for_image
)

router = APIRouter(prefix="/api/dataset-configs", tags=["数据集配置"])


class DatasetConfigCreate(BaseModel):
    dataset_id: int
    format_type: str = 'yolo'
    annotation_path: Optional[str] = None
    source_width: int = 1920
    source_height: int = 1080
    auto_import_annotations: bool = True


class DatasetConfigUpdate(BaseModel):
    format_type: Optional[str] = None
    annotation_path: Optional[str] = None
    source_width: Optional[int] = None
    source_height: Optional[int] = None
    auto_import_annotations: Optional[bool] = None


class DatasetConfigResponse(BaseModel):
    id: int
    dataset_id: int
    format_type: str
    annotation_path: Optional[str]
    source_width: int
    source_height: int
    auto_import_annotations: bool
    created_at: datetime
    updated_at: datetime


@router.get("/{dataset_id}")
async def get_dataset_config(
    dataset_id: int,
    conn=Depends(get_db_dependency),
    current_user=Depends(get_current_user)
):
    """获取数据集配置"""
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM dataset_configs WHERE dataset_id = %s",
            (dataset_id,)
        )
        config = cursor.fetchone()

    if not config:
        # 返回默认配置
        return {
            "dataset_id": dataset_id,
            "format_type": "yolo",
            "annotation_path": None,
            "source_width": 1920,
            "source_height": 1080,
            "auto_import_annotations": True
        }

    return config


@router.post("/")
async def create_or_update_config(
    data: DatasetConfigCreate,
    conn=Depends(get_db_dependency),
    current_user=Depends(get_current_admin)
):
    """创建或更新数据集配置"""
    with conn.cursor() as cursor:
        # 检查数据集是否存在
        cursor.execute(
            "SELECT id FROM datasets WHERE id = %s",
            (data.dataset_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="数据集不存在")

        # 检查是否已有配置
        cursor.execute(
            "SELECT id FROM dataset_configs WHERE dataset_id = %s",
            (data.dataset_id,)
        )
        existing = cursor.fetchone()

        if existing:
            # 更新
            cursor.execute(
                """UPDATE dataset_configs
                   SET format_type = %s, annotation_path = %s,
                       source_width = %s, source_height = %s,
                       auto_import_annotations = %s
                   WHERE dataset_id = %s""",
                (data.format_type, data.annotation_path,
                 data.source_width, data.source_height,
                 data.auto_import_annotations, data.dataset_id)
            )
        else:
            # 插入
            cursor.execute(
                """INSERT INTO dataset_configs
                   (dataset_id, format_type, annotation_path, source_width, source_height, auto_import_annotations)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (data.dataset_id, data.format_type, data.annotation_path,
                 data.source_width, data.source_height, data.auto_import_annotations)
            )

        cursor.execute(
            "SELECT * FROM dataset_configs WHERE dataset_id = %s",
            (data.dataset_id,)
        )
        config = cursor.fetchone()

    return config


@router.put("/{dataset_id}")
async def update_config(
    dataset_id: int,
    data: DatasetConfigUpdate,
    conn=Depends(get_db_dependency),
    current_user=Depends(get_current_admin)
):
    """更新数据集配置"""
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM dataset_configs WHERE dataset_id = %s",
            (dataset_id,)
        )
        config = cursor.fetchone()

        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")

        updates = []
        values = []

        if data.format_type is not None:
            updates.append("format_type = %s")
            values.append(data.format_type)
        if data.annotation_path is not None:
            updates.append("annotation_path = %s")
            values.append(data.annotation_path)
        if data.source_width is not None:
            updates.append("source_width = %s")
            values.append(data.source_width)
        if data.source_height is not None:
            updates.append("source_height = %s")
            values.append(data.source_height)
        if data.auto_import_annotations is not None:
            updates.append("auto_import_annotations = %s")
            values.append(data.auto_import_annotations)

        if updates:
            values.append(dataset_id)
            cursor.execute(
                f"UPDATE dataset_configs SET {', '.join(updates)} WHERE dataset_id = %s",
                tuple(values)
            )

        cursor.execute(
            "SELECT * FROM dataset_configs WHERE dataset_id = %s",
            (dataset_id,)
        )
        config = cursor.fetchone()

    return config


@router.post("/{dataset_id}/copy-from/{source_id}")
async def copy_config_from(
    dataset_id: int,
    source_id: int,
    conn=Depends(get_db_dependency),
    current_user=Depends(get_current_admin)
):
    """从另一个数据集复制配置"""
    with conn.cursor() as cursor:
        # 检查源数据集配置
        cursor.execute(
            "SELECT * FROM dataset_configs WHERE dataset_id = %s",
            (source_id,)
        )
        source_config = cursor.fetchone()

        if not source_config:
            raise HTTPException(status_code=404, detail="源数据集配置不存在")

        # 检查目标数据集是否存在
        cursor.execute(
            "SELECT id FROM datasets WHERE id = %s",
            (dataset_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="目标数据集不存在")

        # 删除现有配置
        cursor.execute(
            "DELETE FROM dataset_configs WHERE dataset_id = %s",
            (dataset_id,)
        )

        # 复制配置
        cursor.execute(
            """INSERT INTO dataset_configs
               (dataset_id, format_type, annotation_path, source_width, source_height, auto_import_annotations)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (dataset_id, source_config['format_type'], source_config['annotation_path'],
             source_config['source_width'], source_config['source_height'],
             source_config['auto_import_annotations'])
        )

        cursor.execute(
            "SELECT * FROM dataset_configs WHERE dataset_id = %s",
            (dataset_id,)
        )
        new_config = cursor.fetchone()

    return {"message": "配置复制成功", "config": new_config}


@router.get("/{dataset_id}/default-categories")
async def get_format_default_categories(
    dataset_id: int,
    conn=Depends(get_db_dependency),
    current_user=Depends(get_current_user)
):
    """获取数据集格式的默认类别"""
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT format_type FROM dataset_configs WHERE dataset_id = %s",
            (dataset_id,)
        )
        config = cursor.fetchone()

    format_type = config['format_type'] if config else 'yolo'

    if format_type == 'dji_roco':
        return get_default_categories()
    else:
        return []


@router.post("/{dataset_id}/import-default-categories")
async def import_default_categories(
    dataset_id: int,
    conn=Depends(get_db_dependency),
    current_user=Depends(get_current_admin)
):
    """导入数据集格式的默认类别"""
    with conn.cursor() as cursor:
        # 获取配置
        cursor.execute(
            "SELECT format_type FROM dataset_configs WHERE dataset_id = %s",
            (dataset_id,)
        )
        config = cursor.fetchone()

        if not config or config['format_type'] != 'dji_roco':
            raise HTTPException(status_code=400, detail="仅支持 DJI ROCO 格式")

        categories = get_default_categories()
        imported = 0

        for cat in categories:
            # 检查是否已存在
            cursor.execute(
                "SELECT id FROM categories WHERE dataset_id = %s AND name = %s",
                (dataset_id, cat['name'])
            )
            if cursor.fetchone():
                continue

            cursor.execute(
                """INSERT INTO categories (dataset_id, name, color, shortcut_key)
                   VALUES (%s, %s, %s, %s)""",
                (dataset_id, cat['name'], cat['color'], cat['shortcut_key'])
            )
            imported += 1

    return {"message": f"成功导入 {imported} 个类别", "imported": imported}


@router.post("/{dataset_id}/import-annotations")
async def import_annotations_for_dataset(
    dataset_id: int,
    conn=Depends(get_db_dependency),
    current_user=Depends(get_current_admin)
):
    """为数据集中的图片导入标注"""
    with conn.cursor() as cursor:
        # 获取配置
        cursor.execute(
            "SELECT * FROM dataset_configs WHERE dataset_id = %s",
            (dataset_id,)
        )
        config = cursor.fetchone()

        if not config or config['format_type'] != 'dji_roco':
            raise HTTPException(status_code=400, detail="仅支持 DJI ROCO 格式")

        # 获取类别映射
        cursor.execute(
            "SELECT id, name FROM categories WHERE dataset_id = %s",
            (dataset_id,)
        )
        categories = cursor.fetchall()
        category_map = {c['name']: c['id'] for c in categories}

        # 获取待处理的图片
        cursor.execute(
            "SELECT id, file_path FROM images WHERE dataset_id = %s AND status = 'pending'",
            (dataset_id,)
        )
        images = cursor.fetchall()

        imported_count = 0
        for image in images:
            annotations = import_dji_roco_annotations(
                image['id'],
                image['file_path'],
                category_map,
                config['annotation_path']
            )

            for ann in annotations:
                cursor.execute(
                    """INSERT INTO annotations
                       (image_id, category_id, x_center, y_center, width, height, created_by)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (ann['image_id'], ann['category_id'],
                     ann['x_center'], ann['y_center'],
                     ann['width'], ann['height'], current_user['id'])
                )
                imported_count += 1

    return {
        "message": f"成功导入 {imported_count} 个标注",
        "imported": imported_count,
        "images_processed": len(images)
    }
