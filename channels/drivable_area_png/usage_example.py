#!/usr/bin/env python3
"""
Drivable Area PNG Data 使用示例

展示如何读取和处理基于车体坐标系的可行驶域PNG数据
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass

@dataclass
class DrivableAreaConfig:
    """可行驶域配置参数"""
    voxel_size: float = 0.1  # 米/像素
    vehicle_center_pixel: Tuple[int, int] = (512, 512)  # 车体中心像素坐标
    coverage_range: Dict[str, float] = None  # 覆盖范围
    
    def __post_init__(self):
        if self.coverage_range is None:
            self.coverage_range = {
                'forward': 50.0,   # 向前50米
                'backward': 10.0,  # 向后10米  
                'left': 25.0,      # 向左25米
                'right': 25.0      # 向右25米
            }

# 可行驶域类别定义
DRIVABLE_CLASSES = {
    0: {"label": "unknown", "description": "未知区域", "color": [128, 128, 128]},
    1: {"label": "drivable", "description": "可行驶区域", "color": [0, 255, 0]},
    2: {"label": "restricted", "description": "受限制行驶区域", "color": [255, 255, 0]},
    3: {"label": "non_drivable", "description": "不可行驶区域", "color": [255, 0, 0]}
}

class DrivableAreaProcessor:
    """可行驶域数据处理器"""
    
    def __init__(self, config: DrivableAreaConfig):
        self.config = config
        self.center_x, self.center_y = config.vehicle_center_pixel
        
    def load_drivable_area(self, file_path: str) -> np.ndarray:
        """
        加载可行驶域PNG文件
        
        Args:
            file_path: PNG文件路径
            
        Returns:
            np.ndarray: 可行驶域图像数据
        """
        image = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError(f"无法加载文件: {file_path}")
        
        # 验证数据
        self._validate_image(image)
        return image
        
    def _validate_image(self, image: np.ndarray) -> None:
        """验证图像数据的有效性"""
        unique_values = np.unique(image)
        valid_values = set(DRIVABLE_CLASSES.keys())
        
        # 检查像素值是否在有效范围内
        invalid_values = set(unique_values) - valid_values
        if invalid_values:
            print(f"警告: 发现无效的像素值: {invalid_values}")
            
        # 检查是否包含必需的可行驶域状态
        required_values = {1, 2, 3}  # 必须包含可行驶域分类
        missing_values = required_values - set(unique_values)
        if missing_values:
            print(f"警告: 缺失可行驶域状态: {missing_values}")
    
    def pixel_to_vehicle_coords(self, pixel_x: int, pixel_y: int) -> Tuple[float, float]:
        """
        将像素坐标转换为车体坐标
        
        Args:
            pixel_x, pixel_y: 像素坐标
            
        Returns:
            Tuple[float, float]: 车体坐标 (x_vehicle, y_vehicle)
        """
        x_vehicle = (pixel_x - self.center_x) * self.config.voxel_size
        y_vehicle = (self.center_y - pixel_y) * self.config.voxel_size  # 图像y轴向下
        return x_vehicle, y_vehicle
    
    def vehicle_to_pixel_coords(self, x_vehicle: float, y_vehicle: float) -> Tuple[int, int]:
        """
        将车体坐标转换为像素坐标
        
        Args:
            x_vehicle, y_vehicle: 车体坐标
            
        Returns:
            Tuple[int, int]: 像素坐标 (pixel_x, pixel_y)
        """
        pixel_x = int(x_vehicle / self.config.voxel_size + self.center_x)
        pixel_y = int(self.center_y - y_vehicle / self.config.voxel_size)
        return pixel_x, pixel_y
    
    def extract_regions(self, image: np.ndarray) -> Dict[str, np.ndarray]:
        """
        提取不同的可行驶域区域
        
        Args:
            image: 可行驶域图像
            
        Returns:
            Dict: 各区域的掩码
        """
        regions = {}
        for class_id, class_info in DRIVABLE_CLASSES.items():
            regions[class_info['label']] = (image == class_id)
        return regions
    
    def analyze_drivable_statistics(self, image: np.ndarray) -> Dict:
        """
        分析可行驶域统计信息
        
        Args:
            image: 可行驶域图像
            
        Returns:
            Dict: 统计信息
        """
        total_pixels = image.size
        stats = {
            "image_shape": image.shape,
            "total_pixels": total_pixels,
            "class_statistics": {},
            "coverage_area_m2": {}
        }
        
        pixel_area_m2 = self.config.voxel_size ** 2  # 每个像素的实际面积
        
        for class_id, class_info in DRIVABLE_CLASSES.items():
            mask = (image == class_id)
            pixel_count = np.sum(mask)
            coverage_percentage = (pixel_count / total_pixels) * 100
            area_m2 = pixel_count * pixel_area_m2
            
            stats["class_statistics"][class_id] = {
                "label": class_info["label"],
                "pixel_count": int(pixel_count),
                "coverage_percentage": round(coverage_percentage, 2),
                "area_m2": round(area_m2, 2),
                "description": class_info["description"]
            }
            stats["coverage_area_m2"][class_info["label"]] = round(area_m2, 2)
        
        return stats
    
    def find_drivable_path_candidates(self, image: np.ndarray, 
                                    start_vehicle_coords: Tuple[float, float],
                                    target_vehicle_coords: Tuple[float, float]) -> Dict:
        """
        在可行驶域中查找路径候选区域
        
        Args:
            image: 可行驶域图像
            start_vehicle_coords: 起始点车体坐标
            target_vehicle_coords: 目标点车体坐标
            
        Returns:
            Dict: 路径分析结果
        """
        # 转换为像素坐标
        start_pixel = self.vehicle_to_pixel_coords(*start_vehicle_coords)
        target_pixel = self.vehicle_to_pixel_coords(*target_vehicle_coords)
        
        # 检查起始点和目标点的可行驶性
        start_value = self._get_pixel_value_safe(image, start_pixel)
        target_value = self._get_pixel_value_safe(image, target_pixel)
        
        result = {
            "start_coords": {
                "vehicle": start_vehicle_coords,
                "pixel": start_pixel,
                "drivable_status": DRIVABLE_CLASSES.get(start_value, {}).get("label", "unknown")
            },
            "target_coords": {
                "vehicle": target_vehicle_coords,
                "pixel": target_pixel,
                "drivable_status": DRIVABLE_CLASSES.get(target_value, {}).get("label", "unknown")
            },
            "path_feasible": start_value in [1, 2] and target_value in [1, 2]
        }
        
        # 简单的直线路径可行性检查
        if result["path_feasible"]:
            path_pixels = self._get_line_pixels(start_pixel, target_pixel)
            path_feasible = self._check_path_feasibility(image, path_pixels)
            result["direct_path_feasible"] = path_feasible
        else:
            result["direct_path_feasible"] = False
            
        return result
    
    def _get_pixel_value_safe(self, image: np.ndarray, pixel_coords: Tuple[int, int]) -> int:
        """安全获取像素值"""
        x, y = pixel_coords
        h, w = image.shape
        if 0 <= x < w and 0 <= y < h:
            return int(image[y, x])
        return 0  # 越界返回未知区域
    
    def _get_line_pixels(self, start: Tuple[int, int], end: Tuple[int, int]) -> List[Tuple[int, int]]:
        """获取两点间直线上的像素坐标（Bresenham算法）"""
        x0, y0 = start
        x1, y1 = end
        pixels = []
        
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        while True:
            pixels.append((x0, y0))
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
                
        return pixels
    
    def _check_path_feasibility(self, image: np.ndarray, path_pixels: List[Tuple[int, int]]) -> bool:
        """检查路径的可行性"""
        for pixel in path_pixels:
            value = self._get_pixel_value_safe(image, pixel)
            if value not in [1, 2]:  # 不可行驶或未知区域
                return False
        return True
    
    def create_visualization(self, image: np.ndarray, 
                           save_path: Optional[str] = None,
                           show_grid: bool = True) -> np.ndarray:
        """
        创建可行驶域可视化图像
        
        Args:
            image: 可行驶域图像
            save_path: 保存路径（可选）
            show_grid: 是否显示网格
            
        Returns:
            np.ndarray: RGB可视化图像
        """
        height, width = image.shape
        rgb_image = np.zeros((height, width, 3), dtype=np.uint8)
        
        # 为每个类别分配颜色
        for class_id, class_info in DRIVABLE_CLASSES.items():
            mask = (image == class_id)
            color = class_info["color"]
            rgb_image[mask] = color
        
        # 添加车体中心标记
        center_x, center_y = self.config.vehicle_center_pixel
        cv2.circle(rgb_image, (center_x, center_y), 5, [255, 255, 255], -1)  # 白色圆点
        cv2.circle(rgb_image, (center_x, center_y), 10, [0, 0, 0], 2)        # 黑色边框
        
        # 添加坐标轴（可选）
        if show_grid:
            # X轴 (向右)
            cv2.arrowedLine(rgb_image, (center_x, center_y), (center_x + 50, center_y), [255, 255, 255], 2)
            # Y轴 (向前，图像中向上)
            cv2.arrowedLine(rgb_image, (center_x, center_y), (center_x, center_y - 50), [255, 255, 255], 2)
        
        if save_path:
            cv2.imwrite(save_path, cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR))
        
        return rgb_image

def demonstrate_usage():
    """演示使用方法"""
    # 配置参数
    config = DrivableAreaConfig(
        voxel_size=0.1,  # 10cm/pixel
        vehicle_center_pixel=(512, 512),
        coverage_range={
            'forward': 50.0,
            'backward': 10.0, 
            'left': 25.0,
            'right': 25.0
        }
    )
    
    # 创建处理器
    processor = DrivableAreaProcessor(config)
    
    # 示例：创建模拟数据（实际使用时加载真实PNG文件）
    # image = processor.load_drivable_area("path/to/drivable_area.png")
    
    # 创建示例数据
    image = np.zeros((1024, 1024), dtype=np.uint8)
    # 设置一些可行驶区域
    image[400:600, 400:600] = 1  # 可行驶
    image[300:400, 400:600] = 2  # 受限
    image[200:300, 400:600] = 3  # 不可行驶
    
    try:
        # 1. 分析统计信息
        stats = processor.analyze_drivable_statistics(image)
        print("=== 可行驶域统计信息 ===")
        for class_id, stat in stats["class_statistics"].items():
            print(f"{stat['label']}: {stat['pixel_count']} 像素, "
                  f"{stat['coverage_percentage']}%, {stat['area_m2']} m²")
        
        # 2. 坐标转换示例
        print("\n=== 坐标转换示例 ===")
        # 车体前方10米，右侧5米的点
        vehicle_point = (5.0, 10.0)
        pixel_point = processor.vehicle_to_pixel_coords(*vehicle_point)
        back_to_vehicle = processor.pixel_to_vehicle_coords(*pixel_point)
        print(f"车体坐标 {vehicle_point} -> 像素坐标 {pixel_point} -> 车体坐标 {back_to_vehicle}")
        
        # 3. 路径可行性分析
        print("\n=== 路径可行性分析 ===")
        start_coords = (0.0, 0.0)  # 车体中心
        target_coords = (10.0, 20.0)  # 前方20米，右侧10米
        path_analysis = processor.find_drivable_path_candidates(image, start_coords, target_coords)
        print(f"起点状态: {path_analysis['start_coords']['drivable_status']}")
        print(f"终点状态: {path_analysis['target_coords']['drivable_status']}")
        print(f"路径可行: {path_analysis['path_feasible']}")
        print(f"直线路径可行: {path_analysis['direct_path_feasible']}")
        
        # 4. 创建可视化
        rgb_viz = processor.create_visualization(image, "drivable_area_viz.png")
        print("\n已生成可视化图像: drivable_area_viz.png")
        
        # 5. 区域提取
        regions = processor.extract_regions(image)
        print(f"\n=== 区域掩码 ===")
        for region_name, mask in regions.items():
            print(f"{region_name}: {np.sum(mask)} 像素")
            
    except Exception as e:
        print(f"处理失败: {e}")

if __name__ == "__main__":
    demonstrate_usage() 