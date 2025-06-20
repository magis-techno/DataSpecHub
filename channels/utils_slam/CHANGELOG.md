# utils_slam 通道变更日志

## [1.1.0] - 2024-08-01

### 重大修复
- **坐标系命名修复**: 将`enu_pose`重命名为`utm_pose`，与实际使用的UTM坐标系相符
- **UTM区域信息恢复**: 新增`utm_zone_info`字段，包含zone_id、hemisphere、datum
- **全局坐标联系**: 恢复与全局坐标系的转换能力

### 新增功能
- **数据质量指标**: 新增`quality_metrics`字段
  - 位置精度估计 (position_accuracy)
  - 方向精度估计 (orientation_accuracy)  
  - 地图置信度 (map_confidence)
  - 跟踪状态 (tracking_status)

### 兼容性变更 ⚠️
**注意**: 此版本包含破坏性变更
- `enu_pose` → `utm_pose` (字段重命名)
- 新增必需字段 `utm_zone_info`

### 迁移指南
```yaml
# v1.0.0 (旧格式)
slam_data:
  pose_info:
    enu_pose:  # 命名不准确
      position: [x, y, z]
      orientation: {...}
    # 缺失UTM区域信息

# v1.1.0 (新格式)  
slam_data:
  pose_info:
    utm_pose:  # 修正命名
      position: [x, y, z]
      orientation: {...}
    utm_zone_info:  # 新增必需字段
      zone_id: 50
      hemisphere: "N"
      datum: "WGS84"
  metadata:
    quality_metrics:  # 新增质量指标
      position_accuracy: 0.3
      tracking_status: "tracking"
```

### 问题修复
| 问题 | 严重程度 | 修复方案 | 状态 |
|------|----------|----------|------|
| enu_pose字段命名不准确 | Medium | 重命名为utm_pose | ✅ 已修复 |
| 缺失UTM zone_id字段 | High | 新增utm_zone_info | ✅ 已修复 |
| 缺少数据质量指标 | Medium | 新增quality_metrics | ✅ 已修复 |

### 性能改进
- 处理时间从25ms优化至22ms
- 位置精度从±0.5m提升至±0.3m
- 支持实时跟踪状态监控

## [1.0.0] - 2024-02-01

### 新增
- 初始版本发布
- 提供SLAM位姿和地图数据
- 包含位置、方向、协方差和地标信息

### 已知问题
- ⚠️ enu_pose字段命名不准确（实际为UTM坐标）
- ⚠️ 缺失UTM投影区域信息
- ⚠️ 缺少数据质量评估指标

> 建议升级至v1.1.0以获得完整功能和修复 