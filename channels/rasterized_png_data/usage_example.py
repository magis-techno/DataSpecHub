#!/usr/bin/env python3
"""
Rasterized PNG Data 使用示例

展示如何读取和解析栅格化PNG数据，包括像素值的语义解码
"""

import cv2
import numpy as np
from typing import Dict, Tuple, List, Optional
from PIL import Image
import json

# 示例：语义分割类别映射
SEMANTIC_CLASSES = {
    0: {"label": "background", "description": "背景/无效区域", "color": [0, 0, 0]},
    1: {"label": "road", "description": "道路区域", "color": [128, 64, 128]},
    2: {"label": "vehicle", "description": "车辆", "color": [0, 0, 142]},
    3: {"label": "pedestrian", "description": "行人", "color": [220, 20, 60]},
    4: {"label": "obstacle", "description": "障碍物", "color": [119, 11, 32]},
}

def load_rasterized_png(file_path: str, load_method: str = "cv2") -> np.ndarray:
    """
    加载栅格化PNG文件
    
    Args:
        file_path: PNG文件路径
        load_method: 加载方法，"cv2" 或 "pil"
        
    Returns:
        np.ndarray: 加载的图像数据
    """
    if load_method == "cv2":
        # 使用OpenCV加载（推荐用于灰度图）
        image = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError(f"无法加载文件: {file_path}")
    elif load_method == "pil":
        # 使用PIL加载
        image = Image.open(file_path)
        if image.mode != 'L':  # 转换为灰度图
            image = image.convert('L')
        image = np.array(image)
    else:
        raise ValueError("load_method 必须是 'cv2' 或 'pil'")
    
    return image

def decode_semantic_pixels(image: np.ndarray, 
                          class_mapping: Dict[int, Dict] = None) -> Dict:
    """
    解码语义像素值
    
    Args:
        image: 栅格化图像
        class_mapping: 类别映射字典
        
    Returns:
        Dict: 包含统计信息和掩码的字典
    """
    if class_mapping is None:
        class_mapping = SEMANTIC_CLASSES
    
    result = {
        "image_shape": image.shape,
        "unique_values": np.unique(image).tolist(),
        "class_statistics": {},
        "masks": {},
        "coverage_percentage": {}
    }
    
    total_pixels = image.size
    
    # 为每个类别生成统计信息和掩码
    for class_id, class_info in class_mapping.items():
        mask = (image == class_id)
        pixel_count = np.sum(mask)
        coverage = (pixel_count / total_pixels) * 100
        
        result["class_statistics"][class_id] = {
            "label": class_info["label"],
            "pixel_count": int(pixel_count),
            "coverage_percentage": round(coverage, 2),
            "description": class_info["description"]
        }
        result["masks"][class_id] = mask
        result["coverage_percentage"][class_info["label"]] = round(coverage, 2)
    
    return result

def pixel_to_world_coords(pixel_coords: Tuple[int, int], 
                         resolution: float = 0.1,
                         origin_offset: Tuple[float, float] = (0.0, 0.0)) -> Tuple[float, float]:
    """
    将像素坐标转换为世界坐标
    
    Args:
        pixel_coords: (x, y) 像素坐标
        resolution: 米/像素的分辨率
        origin_offset: 世界坐标系原点偏移
        
    Returns:
        Tuple[float, float]: (x, y) 世界坐标
    """
    x_pixel, y_pixel = pixel_coords
    x_world = x_pixel * resolution + origin_offset[0]
    y_world = y_pixel * resolution + origin_offset[1]
    return (x_world, y_world)

def find_objects_by_class(image: np.ndarray, 
                         target_class: int,
                         min_area: int = 10) -> List[Dict]:
    """
    在栅格图中查找特定类别的对象
    
    Args:
        image: 栅格化图像
        target_class: 目标类别ID
        min_area: 最小面积阈值（像素数）
        
    Returns:
        List[Dict]: 检测到的对象列表
    """
    # 创建目标类别的二值掩码
    mask = (image == target_class).astype(np.uint8)
    
    # 查找轮廓
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    objects = []
    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        if area >= min_area:
            # 计算边界框
            x, y, w, h = cv2.boundingRect(contour)
            
            # 计算质心
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
            else:
                cx, cy = x + w//2, y + h//2
            
            objects.append({
                "object_id": i,
                "class_id": target_class,
                "area": int(area),
                "bounding_box": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
                "centroid": {"x": int(cx), "y": int(cy)},
                "contour_points": contour.squeeze().tolist() if len(contour.squeeze().shape) == 2 else []
            })
    
    return objects

def create_visualization(image: np.ndarray, 
                        class_mapping: Dict[int, Dict] = None,
                        output_path: Optional[str] = None) -> np.ndarray:
    """
    创建彩色可视化图像
    
    Args:
        image: 栅格化图像
        class_mapping: 类别映射
        output_path: 输出文件路径（可选）
        
    Returns:
        np.ndarray: RGB可视化图像
    """
    if class_mapping is None:
        class_mapping = SEMANTIC_CLASSES
    
    # 创建RGB图像
    height, width = image.shape
    rgb_image = np.zeros((height, width, 3), dtype=np.uint8)
    
    # 为每个类别分配颜色
    for class_id, class_info in class_mapping.items():
        mask = (image == class_id)
        color = class_info["color"]
        rgb_image[mask] = color
    
    if output_path:
        cv2.imwrite(output_path, cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR))
    
    return rgb_image

def validate_rasterized_data(image: np.ndarray, 
                           expected_classes: List[int] = None,
                           max_resolution: Tuple[int, int] = (2048, 2048)) -> Dict:
    """
    验证栅格化数据的有效性
    
    Args:
        image: 栅格化图像
        expected_classes: 期望的类别列表
        max_resolution: 最大分辨率限制
        
    Returns:
        Dict: 验证结果
    """
    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "image_info": {
            "shape": image.shape,
            "dtype": str(image.dtype),
            "value_range": [int(image.min()), int(image.max())],
            "unique_values": len(np.unique(image))
        }
    }
    
    # 检查分辨率
    if image.shape[0] > max_resolution[0] or image.shape[1] > max_resolution[1]:
        validation_result["errors"].append(f"图像分辨率 {image.shape} 超过最大限制 {max_resolution}")
        validation_result["is_valid"] = False
    
    # 检查像素值范围
    if image.min() < 0 or image.max() > 255:
        validation_result["errors"].append(f"像素值范围 [{image.min()}, {image.max()}] 超出有效范围 [0, 255]")
        validation_result["is_valid"] = False
    
    # 检查期望的类别
    if expected_classes:
        unique_values = set(np.unique(image).tolist())
        expected_set = set(expected_classes)
        unexpected_classes = unique_values - expected_set
        missing_classes = expected_set - unique_values
        
        if unexpected_classes:
            validation_result["warnings"].append(f"发现意外的类别值: {list(unexpected_classes)}")
        
        if missing_classes:
            validation_result["warnings"].append(f"缺失期望的类别值: {list(missing_classes)}")
    
    return validation_result

# 使用示例
if __name__ == "__main__":
    # 示例用法
    png_file = "path/to/your/rasterized_data.png"
    
    try:
        # 1. 加载栅格化PNG数据
        image = load_rasterized_png(png_file)
        print(f"加载图像成功，尺寸: {image.shape}")
        
        # 2. 验证数据
        validation = validate_rasterized_data(image, list(SEMANTIC_CLASSES.keys()))
        if validation["is_valid"]:
            print("数据验证通过")
        else:
            print(f"数据验证失败: {validation['errors']}")
            
        # 3. 解码语义像素
        semantic_result = decode_semantic_pixels(image)
        print("\n类别统计:")
        for class_id, stats in semantic_result["class_statistics"].items():
            print(f"  {stats['label']}: {stats['pixel_count']} 像素 ({stats['coverage_percentage']}%)")
        
        # 4. 查找特定对象（例如车辆）
        vehicles = find_objects_by_class(image, target_class=2, min_area=50)
        print(f"\n检测到 {len(vehicles)} 个车辆对象")
        
        # 5. 创建可视化
        rgb_vis = create_visualization(image, output_path="visualization.png")
        print("已生成可视化图像: visualization.png")
        
        # 6. 坐标转换示例
        pixel_coord = (100, 200)
        world_coord = pixel_to_world_coords(pixel_coord, resolution=0.1)
        print(f"像素坐标 {pixel_coord} -> 世界坐标 {world_coord}")
        
    except Exception as e:
        print(f"处理失败: {e}") 