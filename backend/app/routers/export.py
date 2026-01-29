from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import tempfile
import shutil
import zipfile
from app.core import get_db_dependency, get_current_admin

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
    conn = Depends(get_db_dependency),
    current_admin = Depends(get_current_admin)
):
    """导出数据集为YOLO格式"""
    # 验证比例
    total_ratio = request.train_ratio + request.val_ratio + request.test_ratio
    if abs(total_ratio - 1.0) > 0.01:
        raise HTTPException(status_code=400, detail="分割比例之和必须为1")

    with conn.cursor() as cursor:
        # 获取数据集
        cursor.execute("SELECT * FROM datasets WHERE id = %s", (request.dataset_id,))
        dataset = cursor.fetchone()
        if not dataset:
            raise HTTPException(status_code=404, detail="数据集不存在")

        # 获取类别
        cursor.execute(
            "SELECT * FROM categories WHERE dataset_id = %s ORDER BY sort_order",
            (request.dataset_id,)
        )
        categories = cursor.fetchall()
        category_map = {cat['id']: idx for idx, cat in enumerate(categories)}

        # 获取图片
        if request.include_unlabeled:
            cursor.execute("SELECT * FROM images WHERE dataset_id = %s", (request.dataset_id,))
        else:
            cursor.execute("SELECT * FROM images WHERE dataset_id = %s AND status = 'labeled'", (request.dataset_id,))
        images = cursor.fetchall()

        total = len(images)
        if total == 0:
            raise HTTPException(status_code=400, detail="没有可导出的图片")

        # 创建临时目录
        export_dir = tempfile.mkdtemp(prefix="yolo_export_")
        output_name = request.output_name or f"dataset_{request.dataset_id}"
        output_path = os.path.join(export_dir, output_name)

        # 创建目录结构
        for split in ["train", "val", "test"]:
            os.makedirs(os.path.join(output_path, "images", split), exist_ok=True)
            os.makedirs(os.path.join(output_path, "labels", split), exist_ok=True)

        # 创建 data.yaml
        names = [cat['name'] for cat in categories]
        yaml_content = f"""path: {output_path}
train: images/train
val: images/val
test: images/test

nc: {len(names)}
names: {names}
"""
        with open(os.path.join(output_path, "data.yaml"), "w", encoding="utf-8") as f:
            f.write(yaml_content)

        # 计算分割点
        train_end = int(total * request.train_ratio)
        val_end = train_end + int(total * request.val_ratio)

        stats = {"train": 0, "val": 0, "test": 0, "annotations": 0}

        for idx, image in enumerate(images):
            # 确定分割
            if idx < train_end:
                split = "train"
            elif idx < val_end:
                split = "val"
            else:
                split = "test"

            # 复制图片
            src_path = image['file_path']
            dst_image_path = os.path.join(output_path, "images", split, image['filename'])

            if os.path.exists(src_path):
                shutil.copy2(src_path, dst_image_path)
                stats[split] += 1

            # 获取标注并创建标签文件
            cursor.execute("SELECT * FROM annotations WHERE image_id = %s", (image['id'],))
            annotations = cursor.fetchall()

            label_filename = os.path.splitext(image['filename'])[0] + ".txt"
            label_path = os.path.join(output_path, "labels", split, label_filename)

            with open(label_path, "w") as f:
                for ann in annotations:
                    if ann['category_id'] in category_map:
                        class_id = category_map[ann['category_id']]
                        line = f"{class_id} {ann['x_center']:.6f} {ann['y_center']:.6f} {ann['width']:.6f} {ann['height']:.6f}\n"
                        f.write(line)
                        stats["annotations"] += 1

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
        total_images=total,
        train_images=stats["train"],
        val_images=stats["val"],
        test_images=stats["test"],
        total_annotations=stats["annotations"],
        categories=len(categories),
        download_url=f"/api/export/download/{task_id}"
    )


@router.get("/download/{task_id}")
async def download_export(
    task_id: str,
    background_tasks: BackgroundTasks,
    current_admin = Depends(get_current_admin)
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
