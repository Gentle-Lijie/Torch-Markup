import os
import shutil
from typing import Optional
from sqlalchemy.orm import Session
from app.models.dataset import Dataset
from app.models.image import Image, ImageStatus
from app.models.annotation import Annotation
from app.models.category import Category


class YOLOExporter:
    """YOLO格式数据导出器"""

    def __init__(self, db: Session):
        self.db = db

    def export_dataset(
        self,
        dataset_id: int,
        output_path: str,
        split_ratio: tuple = (0.8, 0.1, 0.1),
        include_unlabeled: bool = False
    ) -> dict:
        """
        导出数据集为YOLO格式

        Args:
            dataset_id: 数据集ID
            output_path: 输出目录路径
            split_ratio: (train, val, test) 分割比例
            include_unlabeled: 是否包含未标注图片

        Returns:
            导出统计信息
        """
        dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise ValueError("数据集不存在")

        # 创建目录结构
        dirs = {
            "images/train": os.path.join(output_path, "images", "train"),
            "images/val": os.path.join(output_path, "images", "val"),
            "images/test": os.path.join(output_path, "images", "test"),
            "labels/train": os.path.join(output_path, "labels", "train"),
            "labels/val": os.path.join(output_path, "labels", "val"),
            "labels/test": os.path.join(output_path, "labels", "test"),
        }

        for dir_path in dirs.values():
            os.makedirs(dir_path, exist_ok=True)

        # 获取类别映射
        categories = self.db.query(Category).filter(
            Category.dataset_id == dataset_id
        ).order_by(Category.sort_order).all()

        category_map = {cat.id: idx for idx, cat in enumerate(categories)}

        # 创建 data.yaml
        yaml_content = self._create_data_yaml(output_path, categories)
        with open(os.path.join(output_path, "data.yaml"), "w", encoding="utf-8") as f:
            f.write(yaml_content)

        # 获取图片
        query = self.db.query(Image).filter(Image.dataset_id == dataset_id)
        if not include_unlabeled:
            query = query.filter(Image.status == ImageStatus.LABELED)

        images = query.all()
        total = len(images)

        # 计算分割点
        train_end = int(total * split_ratio[0])
        val_end = train_end + int(total * split_ratio[1])

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
            src_path = image.file_path
            dst_image_path = os.path.join(dirs[f"images/{split}"], image.filename)

            if os.path.exists(src_path):
                shutil.copy2(src_path, dst_image_path)
                stats[split] += 1

            # 创建标签文件
            annotations = self.db.query(Annotation).filter(
                Annotation.image_id == image.id
            ).all()

            label_filename = os.path.splitext(image.filename)[0] + ".txt"
            label_path = os.path.join(dirs[f"labels/{split}"], label_filename)

            with open(label_path, "w") as f:
                for ann in annotations:
                    if ann.category_id in category_map:
                        class_id = category_map[ann.category_id]
                        line = f"{class_id} {ann.x_center:.6f} {ann.y_center:.6f} {ann.width:.6f} {ann.height:.6f}\n"
                        f.write(line)
                        stats["annotations"] += 1

        return {
            "total_images": total,
            "train_images": stats["train"],
            "val_images": stats["val"],
            "test_images": stats["test"],
            "total_annotations": stats["annotations"],
            "categories": len(categories),
            "output_path": output_path
        }

    def _create_data_yaml(self, output_path: str, categories: list) -> str:
        """创建YOLO data.yaml配置文件"""
        names = [cat.name for cat in categories]

        yaml_lines = [
            f"path: {output_path}",
            "train: images/train",
            "val: images/val",
            "test: images/test",
            "",
            f"nc: {len(names)}",
            f"names: {names}",
        ]

        return "\n".join(yaml_lines)

    def export_single_image(self, image_id: int) -> Optional[str]:
        """
        导出单张图片的标注为YOLO格式字符串

        Returns:
            YOLO格式标注字符串
        """
        image = self.db.query(Image).filter(Image.id == image_id).first()
        if not image:
            return None

        # 获取类别映射
        categories = self.db.query(Category).filter(
            Category.dataset_id == image.dataset_id
        ).order_by(Category.sort_order).all()

        category_map = {cat.id: idx for idx, cat in enumerate(categories)}

        # 获取标注
        annotations = self.db.query(Annotation).filter(
            Annotation.image_id == image_id
        ).all()

        lines = []
        for ann in annotations:
            if ann.category_id in category_map:
                class_id = category_map[ann.category_id]
                line = f"{class_id} {ann.x_center:.6f} {ann.y_center:.6f} {ann.width:.6f} {ann.height:.6f}"
                lines.append(line)

        return "\n".join(lines)
