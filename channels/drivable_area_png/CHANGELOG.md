# Drivable Area PNG Channel Changelog

所有关于drivable_area_png通道的重要变更都会记录在此文件中。

格式基于[Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且遵循[语义化版本控制](https://semver.org/lang/zh-CN/)。

## [1.0.0] - 2025-01-15

### 新增
- 初始版本发布
- 支持基于车体坐标系的可行驶域PNG数据格式
- 支持3级可行驶域分类系统
- 支持精确的坐标系转换（像素坐标 ↔ 车体坐标）
- 支持可配置的体素大小和覆盖范围
- 完整的数据验证和质量检查

### 可行驶域分类
- **像素值 1**: 可行驶区域 - 车辆可以安全通行
- **像素值 2**: 受限制行驶区域 - 有条件可行驶，需谨慎
- **像素值 3**: 不可行驶区域 - 禁止通行，包括障碍物
- **像素值 0**: 未知区域 - 数据未覆盖或无效区域

### 坐标系统
- **参考坐标系**: 车体坐标系 (ego_vehicle)
- **坐标轴定义**: RDF (Right-Down-Forward)
- **原点位置**: 车体中心
- **空间分辨率**: 可配置体素大小（默认0.1m/pixel）
- **覆盖范围**: 车体周围矩形区域

### 技术特性
- 文件格式：PNG灰度图（8-bit）
- 坐标转换：像素坐标与车体坐标的双向转换
- 数据验证：像素值范围、空间一致性检查
- 实时性能：加载时间 < 50ms，支持10Hz更新
- 空间精度：最小0.05m/pixel，最大0.5m/pixel

### 应用场景
- **路径规划**: 为自动驾驶提供可行驶域约束
- **运动规划**: 车辆运动规划的空间约束输入
- **安全监控**: 实时监控车辆周围环境状态
- **决策支持**: 为行为决策提供环境理解

### 数据生成流程
1. **多传感器融合**: 相机、激光雷达、毫米波雷达数据融合
2. **语义分割**: 场景语义理解和目标检测
3. **空间占据**: 生成3D空间占据栅格
4. **可行驶域分类**: 基于规则和学习的分类算法
5. **栅格投影**: 投影到车体坐标系的2D栅格
6. **PNG编码**: 生成最终的PNG格式数据

### 质量指标
- 分类准确率: > 95%
- 生成延迟: < 100ms
- 覆盖范围: 车体周围50m
- 更新频率: 10Hz实时更新

### 下游消费者
- `path_planner`: 路径规划模块
- `motion_planner`: 运动规划模块
- `safety_monitor`: 安全监控模块
- `decision_maker`: 决策模块

### 依赖项
- OpenCV (图像处理)
- NumPy (数值计算)
- 多传感器数据接口
- 坐标转换库

### 数据格式示例
```python
# 加载可行驶域数据
import cv2
drivable_map = cv2.imread('drivable_area.png', cv2.IMREAD_GRAYSCALE)

# 提取不同区域
drivable_area = (drivable_map == 1)      # 可行驶
restricted_area = (drivable_map == 2)    # 受限
blocked_area = (drivable_map == 3)       # 禁行

# 坐标转换（像素 -> 车体坐标）
x_vehicle = (pixel_x - center_x) * voxel_size
y_vehicle = (center_y - pixel_y) * voxel_size
```

### 配置参数
- `voxel_size`: 体素大小（米/像素）
- `vehicle_center_pixel`: 车体中心像素坐标
- `coverage_range`: 前后左右覆盖距离
- `confidence_threshold`: 分类置信度阈值 