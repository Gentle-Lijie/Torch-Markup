from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime, timedelta
from app.core import get_db_dependency, get_current_admin, get_password_hash

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


class UserUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


class PasswordReset(BaseModel):
    new_password: str


@router.get("/users", response_model=List[UserListResponse])
async def list_users(
    conn = Depends(get_db_dependency),
    current_admin = Depends(get_current_admin)
):
    """获取用户列表"""
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT u.id, u.username, u.email, u.is_admin, u.is_active, u.created_at,
                   COALESCE(COUNT(i.id), 0) as images_labeled
            FROM users u
            LEFT JOIN images i ON i.labeled_by = u.id
            GROUP BY u.id
        """)
        users = cursor.fetchall()

    return users


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    conn = Depends(get_db_dependency),
    current_admin = Depends(get_current_admin)
):
    """更新用户状态"""
    with conn.cursor() as cursor:
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="用户不存在")

        # 不能禁用自己
        if user_id == current_admin['id'] and user_update.is_active == False:
            raise HTTPException(status_code=400, detail="不能禁用自己的账户")

        updates = []
        params = []
        if user_update.is_active is not None:
            updates.append("is_active = %s")
            params.append(user_update.is_active)
        if user_update.is_admin is not None:
            updates.append("is_admin = %s")
            params.append(user_update.is_admin)

        if updates:
            params.append(user_id)
            cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = %s", params)

    return {"message": "更新成功"}


@router.post("/users/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    password_data: PasswordReset,
    conn = Depends(get_db_dependency),
    current_admin = Depends(get_current_admin)
):
    """重置用户密码"""
    with conn.cursor() as cursor:
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="用户不存在")

        hashed_password = get_password_hash(password_data.new_password)
        cursor.execute("UPDATE users SET hashed_password = %s WHERE id = %s", (hashed_password, user_id))

    return {"message": "密码重置成功"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    conn = Depends(get_db_dependency),
    current_admin = Depends(get_current_admin)
):
    """删除用户"""
    if user_id == current_admin['id']:
        raise HTTPException(status_code=400, detail="不能删除自己的账户")

    with conn.cursor() as cursor:
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="用户不存在")

        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))

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
    conn = Depends(get_db_dependency),
    current_admin = Depends(get_current_admin)
):
    """获取整体统计概览"""
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM users")
        total_users = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM datasets WHERE is_active = TRUE")
        total_datasets = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM images")
        total_images = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM images WHERE status = 'labeled'")
        labeled_images = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM images WHERE status = 'pending'")
        pending_images = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM annotations")
        total_annotations = cursor.fetchone()['count']

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
    conn = Depends(get_db_dependency),
    current_admin = Depends(get_current_admin)
):
    """获取每日统计数据"""
    start_date = date.today() - timedelta(days=days)

    with conn.cursor() as cursor:
        sql = """
            SELECT date, SUM(images_labeled) as images_labeled, SUM(annotations_created) as annotations_created
            FROM work_statistics
            WHERE date >= %s
        """
        params = [start_date]

        if dataset_id:
            sql += " AND dataset_id = %s"
            params.append(dataset_id)

        sql += " GROUP BY date ORDER BY date"
        cursor.execute(sql, params)
        results = cursor.fetchall()

    return [
        DailyStatistics(
            date=r['date'],
            images_labeled=r['images_labeled'] or 0,
            annotations_created=r['annotations_created'] or 0
        )
        for r in results
    ]


@router.get("/statistics/users", response_model=List[UserStatistics])
async def get_user_statistics(
    dataset_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    conn = Depends(get_db_dependency),
    current_admin = Depends(get_current_admin)
):
    """获取用户工作量统计"""
    with conn.cursor() as cursor:
        sql = """
            SELECT ws.user_id, u.username,
                   SUM(ws.images_labeled) as images_labeled,
                   SUM(ws.annotations_created) as annotations_created
            FROM work_statistics ws
            JOIN users u ON ws.user_id = u.id
            WHERE 1=1
        """
        params = []

        if dataset_id:
            sql += " AND ws.dataset_id = %s"
            params.append(dataset_id)
        if start_date:
            sql += " AND ws.date >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND ws.date <= %s"
            params.append(end_date)

        sql += " GROUP BY ws.user_id, u.username"
        cursor.execute(sql, params)
        results = cursor.fetchall()

    return [
        UserStatistics(
            user_id=r['user_id'],
            username=r['username'],
            images_labeled=r['images_labeled'] or 0,
            annotations_created=r['annotations_created'] or 0
        )
        for r in results
    ]


@router.get("/statistics/export")
async def export_statistics(
    format: str = Query(default="csv", pattern="^(csv|json)$"),
    dataset_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    conn = Depends(get_db_dependency),
    current_admin = Depends(get_current_admin)
):
    """导出统计数据"""
    from fastapi.responses import StreamingResponse
    import io
    import csv

    with conn.cursor() as cursor:
        sql = """
            SELECT ws.date, u.username, d.name as dataset_name,
                   ws.images_labeled, ws.annotations_created, ws.time_spent
            FROM work_statistics ws
            JOIN users u ON ws.user_id = u.id
            JOIN datasets d ON ws.dataset_id = d.id
            WHERE 1=1
        """
        params = []

        if dataset_id:
            sql += " AND ws.dataset_id = %s"
            params.append(dataset_id)
        if start_date:
            sql += " AND ws.date >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND ws.date <= %s"
            params.append(end_date)

        sql += " ORDER BY ws.date DESC"
        cursor.execute(sql, params)
        results = cursor.fetchall()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["日期", "用户", "数据集", "标注图片数", "标注框数", "花费时间(秒)"])
        for r in results:
            writer.writerow([r['date'], r['username'], r['dataset_name'], r['images_labeled'], r['annotations_created'], r['time_spent']])

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=statistics.csv"}
        )
    else:
        return [
            {
                "date": str(r['date']),
                "username": r['username'],
                "dataset_name": r['dataset_name'],
                "images_labeled": r['images_labeled'],
                "annotations_created": r['annotations_created'],
                "time_spent": r['time_spent']
            }
            for r in results
        ]
