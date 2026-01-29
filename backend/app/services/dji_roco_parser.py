"""DJI ROCO 数据集 XML 标注解析器"""

import os
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple


# DJI ROCO 默认类别（armor 类型统一为一个类别）
DJI_ROCO_CATEGORIES = [
    {'name': 'car', 'color': '#FF0000', 'shortcut_key': '1'},
    {'name': 'watcher', 'color': '#00FF00', 'shortcut_key': '2'},
    {'name': 'base', 'color': '#0000FF', 'shortcut_key': '3'},
    {'name': 'ignore', 'color': '#808080', 'shortcut_key': '4'},
    {'name': 'armor', 'color': '#FF00FF', 'shortcut_key': '5'},
]


def parse_xml_annotation(xml_path: str) -> Optional[Dict]:
    """
    解析 DJI ROCO XML 标注文件

    Args:
        xml_path: XML 文件路径

    Returns:
        解析后的标注数据，包含图片尺寸和边界框列表
    """
    if not os.path.exists(xml_path):
        return None

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # 获取图片尺寸
        size_elem = root.find('size')
        if size_elem is None:
            return None

        width = int(size_elem.find('width').text)
        height = int(size_elem.find('height').text)

        # 解析所有对象
        objects = []
        for obj in root.findall('object'):
            name = obj.find('name').text

            # armor 类型统一处理（armor_0, armor_1 等都归为 armor）
            if name.startswith('armor'):
                category_name = 'armor'
            else:
                category_name = name

            # 获取边界框
            bndbox = obj.find('bndbox')
            if bndbox is None:
                continue

            xmin = float(bndbox.find('xmin').text)
            ymin = float(bndbox.find('ymin').text)
            xmax = float(bndbox.find('xmax').text)
            ymax = float(bndbox.find('ymax').text)

            # 转换为 YOLO 格式（归一化中心点和宽高）
            x_center = (xmin + xmax) / 2 / width
            y_center = (ymin + ymax) / 2 / height
            box_width = (xmax - xmin) / width
            box_height = (ymax - ymin) / height

            objects.append({
                'category_name': category_name,
                'x_center': x_center,
                'y_center': y_center,
                'width': box_width,
                'height': box_height,
                # 保留原始像素坐标用于调试
                'original': {
                    'xmin': xmin,
                    'ymin': ymin,
                    'xmax': xmax,
                    'ymax': ymax
                }
            })

        return {
            'width': width,
            'height': height,
            'objects': objects
        }

    except ET.ParseError as e:
        print(f"XML 解析错误: {xml_path}, {e}")
        return None
    except Exception as e:
        print(f"解析失败: {xml_path}, {e}")
        return None


def find_xml_for_image(image_path: str, annotation_dir: Optional[str] = None) -> Optional[str]:
    """
    根据图片路径查找对应的 XML 标注文件

    DJI ROCO 目录结构通常为:
    - image/xxx.jpg
    - image_annotation/xxx.xml

    Args:
        image_path: 图片文件路径
        annotation_dir: 标注目录路径（可选）

    Returns:
        XML 文件路径，如果不存在返回 None
    """
    image_dir = os.path.dirname(image_path)
    image_name = os.path.basename(image_path)
    base_name = os.path.splitext(image_name)[0]

    # 尝试的标注目录列表
    possible_dirs = []

    if annotation_dir:
        possible_dirs.append(annotation_dir)

    # 常见的 DJI ROCO 目录结构
    parent_dir = os.path.dirname(image_dir)
    possible_dirs.extend([
        os.path.join(parent_dir, 'image_annotation'),
        os.path.join(parent_dir, 'annotations'),
        os.path.join(parent_dir, 'xml'),
        os.path.join(image_dir, '..', 'image_annotation'),
        image_dir.replace('/image', '/image_annotation'),
    ])

    for ann_dir in possible_dirs:
        xml_path = os.path.join(ann_dir, f"{base_name}.xml")
        if os.path.exists(xml_path):
            return xml_path

    return None


def import_dji_roco_annotations(
    image_id: int,
    image_path: str,
    category_map: Dict[str, int],
    annotation_dir: Optional[str] = None
) -> List[Dict]:
    """
    导入 DJI ROCO 格式的标注

    Args:
        image_id: 图片 ID
        image_path: 图片文件路径
        category_map: 类别名称到 ID 的映射
        annotation_dir: 标注目录路径（可选）

    Returns:
        可以直接插入数据库的标注列表
    """
    xml_path = find_xml_for_image(image_path, annotation_dir)
    if not xml_path:
        return []

    parsed = parse_xml_annotation(xml_path)
    if not parsed:
        return []

    annotations = []
    for obj in parsed['objects']:
        category_name = obj['category_name']
        category_id = category_map.get(category_name)

        if category_id is None:
            # 未知类别，跳过
            continue

        annotations.append({
            'image_id': image_id,
            'category_id': category_id,
            'x_center': obj['x_center'],
            'y_center': obj['y_center'],
            'width': obj['width'],
            'height': obj['height']
        })

    return annotations


def get_default_categories() -> List[Dict]:
    """获取 DJI ROCO 默认类别列表"""
    return DJI_ROCO_CATEGORIES.copy()
