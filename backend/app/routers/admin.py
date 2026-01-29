from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime, timedelta
from app.core import get_db, get_current_admin, get_password_hash
from app.models.user import User
from app.models.dataset import Dataset
from app.models.image import Image, ImageStatus
from app.models.annotation import Annotation
from app.models.statistics import WorkStatistics

router = APIRouter(prefix="/api/admin", tags=["管理后台"])


# ===================== 用户管理 =====================

class UserListResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    is_admin: bool
    is_active: bool
    created_at: datetime
    images_labeled: int = 0

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


class PasswordReset(BaseModel):
    new_password: str


@router.get("/users", response_model=List[UserListResponse])
async def list_users(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """获取用户列表"""
    users = db.query(User).all()

    result = []
    for user in users:
        # 统计该用户标注的图片数
        labeled_count = db.query(func.count(Image.id)).filter(
            Image.labeled_by == user.id
        ).scalar() or 0

        user_data = UserListResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_admin=user.is_admin,
            is_active=user.is_active,
            created_at=user.created_at,
            images_labeled=labeled_count
        )
        result.append(user_data)

    return result


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """更新用户状态"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 不能禁用自己
    if user_id == current_admin.id and user_update.is_active == False:
        raise HTTPException(status_code=400, detail="不能禁用自己的账户")

    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    if user_update.is_admin is not None:
        user.is_admin = user_update.is_admin

    db.commit()
    return {"message": "更新成功"}


@router.post("/users/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    password_data: PasswordReset,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """重置用户密码"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    return {"message": "密码重置成功"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """删除用户"""
    if user_id == current_admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己的账户")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    db.delete(user)
    db.commit()
    return {"message": "删除成功"}


# ===================== 统计功能 =====================

class StatisticsResponse(BaseModel):
    total_users: int
    total_datasets: int
    total_images: int
    labeled_images: int
    pending_images: int
    total_annotations: int


class DailyStatistics(BaseModel):
    date: date
    images_labeled: int
    annotations_created: int


class UserStatistics(BaseModel):
    user_id: int
    username: str
    images_labeled: int
    annotations_created: int


@router.get("/statistics/overview", response_model=StatisticsResponse)
async def get_overview_statistics(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """获取整体统计概览"""
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_datasets = db.query(func.count(Dataset.id)).filter(Dataset.is_active == True).scalar() or 0
    total_images = db.query(func.count(Image.id)).scalar() or 0
    labeled_images = db.query(func.count(Image.id)).filter(Image.status == ImageStatus.LABELED).scalar() or 0
    pending_images = db.query(func.count(Image.id)).filter(Image.status == ImageStatus.PENDING).scalar() or 0
    total_annotations = db.query(func.count(Annotation.id)).scalar() or 0

    return StatisticsResponse(
        total_users=total_users,
        total_datasets=total_datasets,
        total_images=total_images,
        labeled_images=labeled_images,
        pending_images=pending_images,
        total_annotations=total_annotations
    )


@router.get("/statistics/daily", response_model=List[DailyStatistics])
async def get_daily_statistics(
    days: int = Query(default=30, le=365),
    dataset_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """获取每日统计数据"""
    start_date = date.today() - timedelta(days=days)

    query = db.query(
        WorkStatistics.date,
        func.sum(WorkStatistics.images_labeled).label("images_labeled"),
        func.sum(WorkStatistics.annotations_created).label("annotations_created")
    ).filter(WorkStatistics.date >= start_date)

    if dataset_id:
        query = query.filter(WorkStatistics.dataset_id == dataset_id)

    results = query.group_by(WorkStatistics.date).order_by(WorkStatistics.date).all()

    return [
        DailyStatistics(
            date=r.date,
            images_labeled=r.images_labeled or 0,
            annotations_created=r.annotations_created or 0
        )
        for r in results
    ]


@router.get("/statistics/users", response_model=List[UserStatistics])
async def get_user_statistics(
    dataset_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """获取用户工作量统计"""
    query = db.query(
        WorkStatistics.user_id,
        User.username,
        func.sum(WorkStatistics.images_labeled).label("images_labeled"),
        func.sum(WorkStatistics.annotations_created).label("annotations_created")
    ).join(User, WorkStatistics.user_id == User.id)

    if dataset_id:
        query = query.filter(WorkStatistics.dataset_id == dataset_id)
    if start_date:
        query = query.filter(WorkStatistics.date >= start_date)
    if end_date:
        query = query.filter(WorkStatistics.date <= end_date)

    results = query.group_by(WorkStatistics.user_id, User.username).all()

    return [
        UserStatistics(
            user_id=r.user_id,
            username=r.username,
            images_labeled=r.images_labeled or 0,
            annotations_created=r.annotations_created or 0
        )
        for r in results
    ]


@router.get("/statistics/export")
async def export_statistics(
    format: str = Query(default="csv", regex="^(csv|json)$"),
    dataset_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """导出统计数据"""
    from fastapi.responses import StreamingResponse
    import io
    import csv
    import json

    query = db.query(
        WorkStatistics.date,
        User.username,
        Dataset.name.label("dataset_name"),
        WorkStatistics.images_labeled,
        WorkStatistics.annotations_created,
        WorkStatistics.time_spent
    ).join(User, WorkStatistics.user_id == User.id
    ).join(Dataset, WorkStatistics.dataset_id == Dataset.id)

    if dataset_id:
        query = query.filter(WorkStatistics.dataset_id == dataset_id)
    if start_date:
        query = query.filter(WorkStatistics.date >= start_date)
    if end_date:
        query = query.filter(WorkStatistics.date <= end_date)

    results = query.order_by(WorkStatistics.date.desc()).all()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["日期", "用户", "数据集", "标注图片数", "标注框数", "花费时间(秒)"])
        for r in results:
            writer.writerow([r.date, r.username, r.dataset_name, r.images_labeled, r.annotations_created, r.time_spent])

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=statistics.csv"}
        )
    else:
        data = [
            {
                "date": str(r.date),
                "username": r.username,
                "dataset_name": r.dataset_name,
                "images_labeled": r.images_labeled,
                "annotations_created": r.annotations_created,
                "time_spent": r.time_spent
            }
            for r in results
        ]
        return data
