from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Tuple
import os
import tempfile
import shutil
import zipfile
from app.core import get_db, get_current_admin
from app.models.user import User
from app.services.yolo_export import YOLOExporter

router = APIRouter(prefix="/api/export", tags=["导出"])


class ExportRequest(BaseModel):
    dataset_id: int
    output_name: Optional[str] = None
    train_ratio: float = 0.8
    val_ratio: float = 0.1
    test_ratio: float = 0.1
    include_unlabeled: bool = False


class ExportResponse(BaseModel):
    total_images: int
    train_images: int
    val_images: int
    test_images: int
    total_annotations: int
    categories: int
    download_url: str


# 存储导出任务状态
export_tasks = {}


@router.post("/yolo", response_model=ExportResponse)
async def export_yolo(
    request: ExportRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """导出数据集为YOLO格式"""
    # 验证比例
    total_ratio = request.train_ratio + request.val_ratio + request.test_ratio
    if abs(total_ratio - 1.0) > 0.01:
        raise HTTPException(status_code=400, detail="分割比例之和必须为1")

    # 创建临时目录
    export_dir = tempfile.mkdtemp(prefix="yolo_export_")
    output_name = request.output_name or f"dataset_{request.dataset_id}"
    output_path = os.path.join(export_dir, output_name)

    try:
        exporter = YOLOExporter(db)
        result = exporter.export_dataset(
            dataset_id=request.dataset_id,
            output_path=output_path,
            split_ratio=(request.train_ratio, request.val_ratio, request.test_ratio),
            include_unlabeled=request.include_unlabeled
        )

        # 创建ZIP文件
        zip_path = os.path.join(export_dir, f"{output_name}.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(output_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, export_dir)
                    zipf.write(file_path, arcname)

        # 存储导出任务信息
        task_id = f"export_{request.dataset_id}_{os.path.basename(export_dir)}"
        export_tasks[task_id] = {
            "zip_path": zip_path,
            "export_dir": export_dir
        }

        return ExportResponse(
            total_images=result["total_images"],
            train_images=result["train_images"],
            val_images=result["val_images"],
            test_images=result["test_images"],
            total_annotations=result["total_annotations"],
            categories=result["categories"],
            download_url=f"/api/export/download/{task_id}"
        )

    except Exception as e:
        # 清理临时目录
        shutil.rmtree(export_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{task_id}")
async def download_export(
    task_id: str,
    background_tasks: BackgroundTasks,
    current_admin: User = Depends(get_current_admin)
):
    """下载导出的文件"""
    if task_id not in export_tasks:
        raise HTTPException(status_code=404, detail="导出任务不存在或已过期")

    task = export_tasks[task_id]
    zip_path = task["zip_path"]

    if not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    # 下载后清理
    def cleanup():
        shutil.rmtree(task["export_dir"], ignore_errors=True)
        export_tasks.pop(task_id, None)

    background_tasks.add_task(cleanup)

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=os.path.basename(zip_path)
    )


@router.get("/preview/{dataset_id}/{image_id}")
async def preview_yolo_format(
    dataset_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """预览单张图片的YOLO格式标注"""
    exporter = YOLOExporter(db)
    result = exporter.export_single_image(image_id)

    if result is None:
        raise HTTPException(status_code=404, detail="图片不存在")

    return {"yolo_format": result}
