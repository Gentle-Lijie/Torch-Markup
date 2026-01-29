from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
from app.core import get_db, get_current_user
from app.models.user import User
from app.models.dataset import Dataset
from app.models.image import Image, ImageStatus
from app.models.annotation import Annotation, AnnotationHistory, AnnotationAction
from app.models.category import Category
from app.models.statistics import WorkStatistics

router = APIRouter(prefix="/api/images", tags=["图片标注"])


class AnnotationCreate(BaseModel):
    category_id: int
    x_center: float
    y_center: float
    width: float
    height: float


class AnnotationUpdate(BaseModel):
    category_id: Optional[int] = None
    x_center: Optional[float] = None
    y_center: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None


class AnnotationResponse(BaseModel):
    id: int
    image_id: int
    category_id: int
    x_center: float
    y_center: float
    width: float
    height: float
    created_at: datetime

    class Config:
        from_attributes = True


class ImageResponse(BaseModel):
    id: int
    dataset_id: int
    filename: str
    width: Optional[int]
    height: Optional[int]
    status: str
    annotations: List[AnnotationResponse] = []

    class Config:
        from_attributes = True


class SaveAnnotationsRequest(BaseModel):
    annotations: List[AnnotationCreate]
    skip: bool = False


@router.get("/next/{dataset_id}", response_model=Optional[ImageResponse])
async def get_next_image(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取下一张待标注图片"""
    # 检查数据集
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.is_active == True).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在或未激活")

    # 优先返回当前用户已分配但未完成的图片
    assigned_image = db.query(Image).filter(
        Image.dataset_id == dataset_id,
        Image.assigned_to == current_user.id,
        Image.status == ImageStatus.ASSIGNED
    ).first()

    if assigned_image:
        return assigned_image

    # 获取一张新的待标注图片
    pending_image = db.query(Image).filter(
        Image.dataset_id == dataset_id,
        Image.status == ImageStatus.PENDING
    ).first()

    if not pending_image:
        return None

    # 分配给当前用户
    pending_image.assigned_to = current_user.id
    pending_image.assigned_at = datetime.utcnow()
    pending_image.status = ImageStatus.ASSIGNED
    db.commit()
    db.refresh(pending_image)

    return pending_image


@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取图片详情和标注"""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")

    return image


@router.get("/{image_id}/file")
async def get_image_file(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取图片文件"""
    import os

    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")

    if not os.path.exists(image.file_path):
        raise HTTPException(status_code=404, detail="图片文件不存在")

    return FileResponse(image.file_path)


@router.post("/{image_id}/annotations", response_model=AnnotationResponse)
async def create_annotation(
    image_id: int,
    annotation_data: AnnotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建标注"""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")

    # 验证类别
    category = db.query(Category).filter(
        Category.id == annotation_data.category_id,
        Category.dataset_id == image.dataset_id
    ).first()
    if not category:
        raise HTTPException(status_code=400, detail="无效的类别")

    annotation = Annotation(
        image_id=image_id,
        category_id=annotation_data.category_id,
        x_center=annotation_data.x_center,
        y_center=annotation_data.y_center,
        width=annotation_data.width,
        height=annotation_data.height,
        created_by=current_user.id
    )
    db.add(annotation)

    # 记录历史
    history = AnnotationHistory(
        image_id=image_id,
        user_id=current_user.id,
        action=AnnotationAction.CREATE,
        annotation_data={
            "category_id": annotation_data.category_id,
            "x_center": annotation_data.x_center,
            "y_center": annotation_data.y_center,
            "width": annotation_data.width,
            "height": annotation_data.height
        }
    )
    db.add(history)

    db.commit()
    db.refresh(annotation)

    return annotation


@router.put("/annotations/{annotation_id}", response_model=AnnotationResponse)
async def update_annotation(
    annotation_id: int,
    annotation_data: AnnotationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新标注"""
    annotation = db.query(Annotation).filter(Annotation.id == annotation_id).first()
    if not annotation:
        raise HTTPException(status_code=404, detail="标注不存在")

    if annotation_data.category_id is not None:
        annotation.category_id = annotation_data.category_id
    if annotation_data.x_center is not None:
        annotation.x_center = annotation_data.x_center
    if annotation_data.y_center is not None:
        annotation.y_center = annotation_data.y_center
    if annotation_data.width is not None:
        annotation.width = annotation_data.width
    if annotation_data.height is not None:
        annotation.height = annotation_data.height

    # 记录历史
    history = AnnotationHistory(
        image_id=annotation.image_id,
        user_id=current_user.id,
        action=AnnotationAction.UPDATE,
        annotation_data={
            "annotation_id": annotation_id,
            "category_id": annotation.category_id,
            "x_center": annotation.x_center,
            "y_center": annotation.y_center,
            "width": annotation.width,
            "height": annotation.height
        }
    )
    db.add(history)

    db.commit()
    db.refresh(annotation)
    return annotation


@router.delete("/annotations/{annotation_id}")
async def delete_annotation(
    annotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除标注"""
    annotation = db.query(Annotation).filter(Annotation.id == annotation_id).first()
    if not annotation:
        raise HTTPException(status_code=404, detail="标注不存在")

    # 记录历史
    history = AnnotationHistory(
        image_id=annotation.image_id,
        user_id=current_user.id,
        action=AnnotationAction.DELETE,
        annotation_data={
            "annotation_id": annotation_id,
            "category_id": annotation.category_id,
            "x_center": annotation.x_center,
            "y_center": annotation.y_center,
            "width": annotation.width,
            "height": annotation.height
        }
    )
    db.add(history)

    db.delete(annotation)
    db.commit()

    return {"message": "删除成功"}


@router.post("/{image_id}/save")
async def save_annotations(
    image_id: int,
    data: SaveAnnotationsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """保存图片的所有标注并完成"""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")

    # 删除旧标注
    db.query(Annotation).filter(Annotation.image_id == image_id).delete()

    annotation_count = 0
    if not data.skip:
        # 创建新标注
        for ann_data in data.annotations:
            annotation = Annotation(
                image_id=image_id,
                category_id=ann_data.category_id,
                x_center=ann_data.x_center,
                y_center=ann_data.y_center,
                width=ann_data.width,
                height=ann_data.height,
                created_by=current_user.id
            )
            db.add(annotation)
            annotation_count += 1

    # 更新图片状态
    image.status = ImageStatus.SKIPPED if data.skip else ImageStatus.LABELED
    image.labeled_by = current_user.id
    image.labeled_at = datetime.utcnow()

    # 更新数据集统计
    dataset = db.query(Dataset).filter(Dataset.id == image.dataset_id).first()
    if dataset:
        dataset.labeled_images = db.query(Image).filter(
            Image.dataset_id == dataset.id,
            Image.status == ImageStatus.LABELED
        ).count()

    # 更新工作量统计
    today = date.today()
    stats = db.query(WorkStatistics).filter(
        WorkStatistics.user_id == current_user.id,
        WorkStatistics.dataset_id == image.dataset_id,
        WorkStatistics.date == today
    ).first()

    if stats:
        stats.images_labeled += 1
        stats.annotations_created += annotation_count
    else:
        stats = WorkStatistics(
            user_id=current_user.id,
            dataset_id=image.dataset_id,
            date=today,
            images_labeled=1,
            annotations_created=annotation_count
        )
        db.add(stats)

    db.commit()

    return {"message": "保存成功", "status": image.status}


@router.get("/{image_id}/history")
async def get_annotation_history(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取标注历史 (用于撤销)"""
    history = db.query(AnnotationHistory).filter(
        AnnotationHistory.image_id == image_id,
        AnnotationHistory.user_id == current_user.id
    ).order_by(AnnotationHistory.created_at.desc()).limit(50).all()

    return [
        {
            "id": h.id,
            "action": h.action,
            "data": h.annotation_data,
            "created_at": h.created_at
        }
        for h in history
    ]


@router.get("/dataset/{dataset_id}/progress")
async def get_dataset_progress(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取数据集标注进度"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")

    total = db.query(func.count(Image.id)).filter(Image.dataset_id == dataset_id).scalar() or 0
    labeled = db.query(func.count(Image.id)).filter(
        Image.dataset_id == dataset_id,
        Image.status == ImageStatus.LABELED
    ).scalar() or 0
    skipped = db.query(func.count(Image.id)).filter(
        Image.dataset_id == dataset_id,
        Image.status == ImageStatus.SKIPPED
    ).scalar() or 0
    pending = db.query(func.count(Image.id)).filter(
        Image.dataset_id == dataset_id,
        Image.status == ImageStatus.PENDING
    ).scalar() or 0

    return {
        "total": total,
        "labeled": labeled,
        "skipped": skipped,
        "pending": pending,
        "progress": round(labeled / total * 100, 2) if total > 0 else 0
    }
