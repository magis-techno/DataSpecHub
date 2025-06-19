# 基于角色的实际操作示例

本文档通过具体的日常工作场景，展示各个角色如何使用DataSpecHub系统。

## 1. 研发工程师：李明 - 传感器团队

### 场景：新增毫米波雷达传感器

**背景**：公司采购了新的Continental ARS548毫米波雷达，需要接入数据处理管道。

#### 步骤1：创建GitHub Issue

李明在GitHub上创建Issue：

```markdown
---
title: '[DATA_SPEC] Add Continental ARS548 radar channel'
labels: ['DATA_SPEC', 'needs-review']
---

## 📋 变更基本信息

**通道名称**: radar_continental
**当前版本**: 无（新通道）
**目标版本**: 1.0.0
**变更类型**: [x] Major [ ] Minor [ ] Patch
**变更分类**: [x] 新增通道 [ ] 格式优化 [ ] 字段修改 [ ] 废弃通道

## 🎯 需求背景

**业务背景**:
我们的新车型将搭载Continental ARS548毫米波雷达，需要将其数据接入现有的感知处理管道。
这款雷达相比现有的Bosch雷达具有更高的角度分辨率和更远的探测距离。

**技术背景**:
- ARS548输出4D点云（x,y,z,velocity）
- 数据格式为自定义二进制格式，需要专门的解析库
- 更新频率为20Hz，比现有radar.v2的10Hz更高

## 📊 影响面分析

### 下游消费者影响
- [x] 自动驾驶系统 (autonomous_driving) - 需要适配新的4D点云
- [x] 感知训练平台 (perception_training) - 需要更新训练数据格式
- [ ] 仿真平台 (simulation_platform) - 暂不影响

### 影响程度评估
- **高影响** (需要代码修改): [x] 是 [ ] 否
- **中影响** (需要配置更新): [x] 是 [ ] 否  
- **低影响** (仅文档更新): [ ] 是 [x] 否

### 预计工作量
- **开发工作量**: 3 人天
- **测试工作量**: 2 人天
- **部署工作量**: 1 人天

## ⚠️ 兼容性分析

**是否破坏向后兼容性**: [ ] 是 [x] 否

**双写窗口需求**: [ ] 需要 [x] 不需要

## 🧪 测试用例

### 功能测试
- [x] 数据格式解析正确性
- [x] 字段完整性验证
- [x] 边界值测试
- [x] 错误处理测试

### 性能测试  
- [x] 数据加载性能
- [x] 内存占用测试
- [x] 并发处理能力

## 📁 样本数据

**样本数据路径**: /data/samples/radar_continental/
**样本数量**: 50个文件
**数据大小**: 每个文件约2MB
**覆盖场景**: 
- [x] 晴天
- [x] 雨天  
- [x] 夜间
- [x] 高速
- [x] 城区
```

#### 步骤2：准备规格文件

李明创建PR，添加新的通道规格：

```bash
# 创建通道目录
mkdir channels/radar_continental

# 创建规格文件
cat > channels/radar_continental/spec-1.0.0.yaml << 'EOF'
meta:
  channel: radar_continental
  version: 1.0.0
  category: sensor_raw
  description: "Continental ARS548 毫米波雷达4D点云数据"
  
schema:
  data_format:
    type: point_cloud_4d
    encoding: continental_binary
    coordinate_system: vehicle_frame
    
  point_structure:
    x:
      type: float32
      unit: meters
      range: [-200, 200]
      description: "横向距离"
    y:
      type: float32
      unit: meters
      range: [0, 250]
      description: "纵向距离"
    z:
      type: float32
      unit: meters
      range: [-10, 10]
      description: "高度"
    velocity:
      type: float32
      unit: m/s
      range: [-50, 50]
      description: "径向速度"
    rcs:
      type: float32
      unit: dBsm
      description: "雷达截面积"
    timestamp:
      type: uint64
      unit: nanoseconds
      description: "数据时间戳"
      
  sensor_info:
    model: "Continental ARS548"
    frequency: 77  # GHz
    update_rate: 20  # Hz
    fov_horizontal: 120  # degrees
    fov_vertical: 16   # degrees
    range_max: 250     # meters
    
validation:
  file_extensions: [".bin"]
  max_file_size: "5MB"
  required_fields: ["x", "y", "z", "velocity", "timestamp"]
  
lifecycle:
  status: draft
  created_at: "2025-01-15"
  maintainer: "sensor-team@company.com"
EOF
```

#### 步骤3：提交PR

```bash
git checkout -b feature/add-continental-radar
git add channels/radar_continental/
git commit -m "[DATA_SPEC] Add Continental ARS548 radar channel

- Add spec-1.0.0.yaml with 4D point cloud definition
- Support velocity field for enhanced object tracking
- 20Hz update rate for better temporal resolution

Fixes: DATA_SPEC-2024-042"

git push origin feature/add-continental-radar
```

## 2. Data Steward：王芳 - 数据治理专家

### 场景：审核雷达规格变更并维护分类体系

王芳收到李明的PR后，开始审核工作。

#### 步骤1：PR审核

王芳使用审核清单检查：

```markdown
## PR Review - Continental Radar Channel

### ✅ 审核检查清单

- [x] 命名规范符合约定（radar_continental，snake_case）
- [x] 版本号遵循SemVer规范（1.0.0）
- [x] 分类归属正确（sensor_raw）
- [x] 描述信息完整准确
- [x] Schema定义清晰无歧义
- [x] 验证规则覆盖完整
- [x] 生命周期状态合理（draft -> stable）
- [x] 向后兼容性分析正确（新通道，无兼容性问题）
- [x] 示例数据格式合格
- [ ] 文档更新同步 - **需要补充**

### 📝 Review Comments

1. **Schema改进建议**：
   ```yaml
   # 建议添加置信度字段
   confidence:
     type: float32
     range: [0.0, 1.0]
     description: "检测置信度"
   ```

2. **验证规则增强**：
   ```yaml
   validation:
     # 建议添加点云数量范围检查
     point_count_range: [100, 10000]
     # 添加时间戳单调性检查
     timestamp_monotonic: true
   ```

3. **分类体系更新**：需要在taxonomy中添加对应分类

### 🔄 Action Items
- [ ] 作者补充confidence字段
- [ ] 作者添加点云验证规则
- [ ] Reviewer更新taxonomy分类
- [ ] 作者提供更多样本数据
```

#### 步骤2：更新分类体系

王芳更新taxonomy文件：

```yaml
# taxonomy/channel_taxonomy.yaml
categories:
  sensor_raw:
    desc: 基础传感器原始数据
    channels:
      - img_cam1
      - fisheye_original_cam9
      - image_raw
      - lidar
      - radar
      - radar.v2
      - radar_continental  # 新增
      - uss
      - dtof_lidar
    
    # 添加雷达子分类
    subcategories:
      radar_sensors:
        desc: 毫米波雷达传感器
        channels:
          - radar         # Bosch MRR
          - radar.v2      # Bosch MRR升级版
          - radar_continental  # Continental ARS548
        standards:
          coordinate_system: "vehicle_frame"
          update_rate_min: 10  # Hz
          range_min: 50        # meters
```

#### 步骤3：创建规格标准文档

```markdown
# docs/SCHEMA_STANDARDS.md

## 雷达传感器规格标准

### 必需字段
所有雷达传感器必须包含以下字段：
- `x`, `y`, `z`: 空间坐标（float32）
- `timestamp`: 时间戳（uint64，纳秒）
- `rcs`: 雷达截面积（float32，dBsm）

### 推荐字段
- `velocity`: 径向速度（float32，m/s）
- `confidence`: 检测置信度（float32，0-1）

### 命名规范
- 雷达通道命名：`radar_{manufacturer}_{model}`
- 版本升级：使用语义化版本号
- 坐标系：统一使用vehicle_frame
```

## 3. 消费方代表：张伟 - 自动驾驶算法工程师

### 场景：评估新雷达对自动驾驶系统的影响

张伟代表自动驾驶团队评估Continental雷达的影响。

#### 步骤1：影响分析

```markdown
## Continental雷达影响评估报告

**评估人**: 张伟 (ad-team@company.com)
**评估日期**: 2025-01-16
**相关PR**: #123

### 当前系统依赖
```yaml
# consumers/autonomous_driving.yaml 当前配置
requirement_groups:
  perception:
    requirements:
      - channel: radar.v2
        version: "^2.0.0"
        required: true
        priority: critical
```

### 新雷达集成方案

#### 方案1：替换现有雷达
```yaml
requirement_groups:
  perception:
    requirements:
      - channel: radar_continental
        version: ">=1.0.0"
        required: true
        priority: critical
        rationale: "更高精度的4D感知"
```

#### 方案2：双雷达融合（推荐）
```yaml
requirement_groups:
  perception:
    requirements:
      - channel: radar.v2
        version: "^2.0.0"
        required: true
        priority: high
        rationale: "保持现有稳定性"
        
      - channel: radar_continental
        version: ">=1.0.0"
        required: false
        priority: high
        on_missing: ignore
        rationale: "增强感知能力"
```

### 技术影响评估

**正面影响**：
- 4D点云提供速度信息，提升动态目标跟踪
- 更高角度分辨率，改善侧向车辆检测
- 20Hz更新率，减少运动模糊

**技术挑战**：
- 需要适配新的数据格式解析
- 融合算法需要处理不同更新频率（10Hz vs 20Hz）
- 标定流程需要更新

**开发工作量评估**：
- 数据解析适配：2人天
- 融合算法更新：5人天
- 测试验证：3人天
- **总计**：10人天

### 建议
1. **接受新通道**，采用双雷达融合方案
2. **分阶段部署**：先在仿真环境验证，再到实车测试
3. **保留fallback**：新雷达出现问题时可回退到单雷达模式
```

#### 步骤2：更新消费者配置

```yaml
# consumers/autonomous_driving.yaml 更新
meta:
  consumer: autonomous_driving
  owner: "ad-team@company.com"
  version: "2.2.0"  # 版本升级
  
requirement_groups:
  perception:
    description: "感知算法所需的传感器数据"
    requirements:
      - channel: img_cam1
        version: ">=1.0.0 <2.0.0"
        required: true
        priority: critical
        
      - channel: lidar
        version: ">=1.0.0"
        required: true
        priority: critical
        
      # 现有雷达保持
      - channel: radar.v2
        version: "^2.0.0"
        required: true
        priority: high
        rationale: "基础雷达感知"
        
      # 新增Continental雷达
      - channel: radar_continental
        version: ">=1.0.0"
        required: false
        priority: high
        on_missing: ignore
        rationale: "增强4D感知能力"
        
# 环境特定配置
environments:
  development:
    radar_continental.required: false
  testing:
    radar_continental.required: true
  production:
    radar_continental.required: false  # 逐步推广

integration:
  jira_epic: "AD-2025-Q1"
  approval_status: "approved"
  approver: "zhang.wei@company.com"
  approval_date: "2025-01-16"
```

## 4. Release Manager：陈静 - 发布经理

### 场景：管理周度发布和Bundle创建

陈静负责2025年第3周的发布管理。

#### 步骤1：发布计划制定

```markdown
# 发布计划：2025年第3周 (2025.03)

**发布日期**: 2025-01-22 (周三)
**发布标签**: release/2025.03

## 📦 包含变更

### 新增通道
- `radar_continental v1.0.0` - Continental ARS548雷达支持

### 版本升级
- `img_cam1: 1.2.3 -> 1.2.4` (patch) - 修复曝光控制bug
- `lidar: 2.1.0 -> 2.1.1` (patch) - 优化点云去噪算法

### 消费者配置更新
- `autonomous_driving: 2.1.0 -> 2.2.0` - 新增Continental雷达支持

## ✅ 发布检查清单
- [x] 所有PR已合并到main分支
- [x] CI/CD流水线全部通过
- [x] 回归测试完成，无阻塞问题
- [x] 文档更新同步
- [x] 消费方影响评估完成
- [x] 发布说明准备就绪
- [x] 回滚方案确认

## 🕐 发布时间线
- 09:00 - 创建release分支
- 10:00 - 执行自动化测试
- 11:00 - 生成Bundle快照
- 14:00 - 发布到staging环境
- 16:00 - 生产环境发布
- 17:00 - 发布后验证
```

#### 步骤2：创建发布规格

```bash
# 为Continental雷达创建发布规格
cat > channels/radar_continental/release-1.0.0.yaml << 'EOF'
meta:
  channel: radar_continental
  version: 1.0.0
  release_date: "2025-01-22"
  release_type: major
  
spec_ref: ./spec-1.0.0.yaml

# 生产规格到发布规格的映射关系
production_mapping:
  production_runs:
    - run_id: "test-2025-003"
      date: "2025-01-20"
      data_path: "/data/test-2025-003/radar_continental"
      environment: "testing"
      
changes:
  - type: "feature"
    description: "新增Continental ARS548雷达支持"
    jira_ticket: "DATA_SPEC-2024-042"
  - type: "feature"
    description: "支持4D点云（包含速度信息）"
  - type: "improvement"
    description: "20Hz高频率数据更新"
    
compatibility:
  backward_compatible: true  # 新通道，不影响现有系统
  breaking_changes: []
  
lifecycle:
  status: stable
  support_until: "2026-01-22"
  maintainer: "sensor-team@company.com"
EOF
```

#### 步骤3：生成Bundle快照

```bash
# 创建周度训练Bundle
python scripts/bundle_manager.py create \
  --from-consumer autonomous_driving \
  --name weekly_training \
  --version 2025.03

# 输出结果
🔨 Creating bundle 'weekly_training:2025.03' from consumer 'autonomous_driving'...
✅ No conflicts detected
📦 Bundle saved to: bundles/weekly_training/bundle-2025.03.yaml

📋 Resolved 7 channels:
  - img_cam1: 1.2.4
  - lidar: 2.1.1
  - radar.v2: 2.0.5
  - radar_continental: 1.0.0  # 新增
  - utils: 1.3.2
  - ego_pose: 1.1.0
  - calib: 1.0.1
```

#### 步骤4：发布执行

```bash
# 创建发布标签
git tag release/2025.03
git push origin release/2025.03

# 生成发布说明
cat > RELEASE_NOTES_2025.03.md << 'EOF'
# Release 2025.03 - Continental雷达支持

## 🚀 新功能
- **新增Continental ARS548雷达支持** (`radar_continental v1.0.0`)
  - 4D点云数据（包含速度信息）
  - 20Hz高频率更新
  - 增强的角度分辨率

## 🔧 改进
- `img_cam1 v1.2.4`: 修复曝光控制算法bug
- `lidar v2.1.1`: 优化点云去噪算法，提升5%精度

## 📦 Bundle更新
- `weekly_training:2025.03`: 包含所有最新稳定版本
- 新增Continental雷达数据支持

## 🔄 消费者影响
- `autonomous_driving`: 可选集成Continental雷达
- `perception_training`: 支持4D点云训练数据

## 📋 升级指南
详见: [Continental雷达集成指南](docs/continental-radar-integration.md)
EOF
```

## 5. QA工程师：刘强 - 质量保证

### 场景：验证Continental雷达样本数据格式

刘强负责确保新雷达的样本数据符合规格要求。

#### 步骤1：样本数据验证

```python
# scripts/validate_continental_radar.py
#!/usr/bin/env python3

import struct
from pathlib import Path
import numpy as np

def validate_continental_sample(sample_file: Path) -> bool:
    """验证Continental雷达样本数据格式"""
    
    print(f"🔍 Validating {sample_file.name}...")
    
    # 1. 文件格式检查
    if not sample_file.suffix == '.bin':
        print(f"❌ Invalid file extension: {sample_file.suffix}")
        return False
        
    # 2. 文件大小检查
    file_size = sample_file.stat().st_size
    if file_size > 5 * 1024 * 1024:  # 5MB
        print(f"❌ File too large: {file_size / 1024 / 1024:.1f}MB")
        return False
        
    # 3. 二进制格式解析
    try:
        with open(sample_file, 'rb') as f:
            # 读取文件头
            header = struct.unpack('<I', f.read(4))[0]  # 点云数量
            
            if header < 100 or header > 10000:
                print(f"❌ Invalid point count: {header}")
                return False
                
            # 验证点云数据结构
            point_size = 6 * 4 + 8  # 6个float32 + 1个uint64
            expected_size = 4 + header * point_size
            
            if file_size != expected_size:
                print(f"❌ Size mismatch: expected {expected_size}, got {file_size}")
                return False
                
            # 读取几个点验证数据范围
            for i in range(min(10, header)):
                point_data = struct.unpack('<ffffffQ', f.read(point_size))
                x, y, z, velocity, rcs, confidence, timestamp = point_data
                
                # 验证坐标范围
                if not (-200 <= x <= 200):
                    print(f"❌ X coordinate out of range: {x}")
                    return False
                if not (0 <= y <= 250):
                    print(f"❌ Y coordinate out of range: {y}")
                    return False
                if not (-10 <= z <= 10):
                    print(f"❌ Z coordinate out of range: {z}")
                    return False
                    
                # 验证速度范围
                if not (-50 <= velocity <= 50):
                    print(f"❌ Velocity out of range: {velocity}")
                    return False
                    
                # 验证置信度
                if not (0.0 <= confidence <= 1.0):
                    print(f"❌ Confidence out of range: {confidence}")
                    return False
                    
    except Exception as e:
        print(f"❌ Parse error: {e}")
        return False
        
    print(f"✅ {sample_file.name} validation passed")
    return True

def main():
    samples_dir = Path("channels/radar_continental/samples")
    
    if not samples_dir.exists():
        print(f"❌ Samples directory not found: {samples_dir}")
        return False
        
    sample_files = list(samples_dir.glob("*.bin"))
    if len(sample_files) < 10:
        print(f"⚠️ Insufficient samples: {len(sample_files)} (minimum 10)")
        
    success_count = 0
    for sample_file in sample_files:
        if validate_continental_sample(sample_file):
            success_count += 1
            
    success_rate = success_count / len(sample_files) if sample_files else 0
    print(f"\n📊 Validation Summary:")
    print(f"  Total files: {len(sample_files)}")
    print(f"  Passed: {success_count}")
    print(f"  Success rate: {success_rate:.1%}")
    
    if success_rate >= 0.95:
        print("✅ Sample validation PASSED")
        return True
    else:
        print("❌ Sample validation FAILED")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
```

#### 步骤2：集成测试

```python
# tests/integration/test_radar_continental.py
import pytest
from pathlib import Path
import yaml

class TestContinentalRadar:
    
    def test_spec_format(self):
        """测试规格文件格式正确性"""
        spec_file = Path("channels/radar_continental/spec-1.0.0.yaml")
        assert spec_file.exists(), "Spec file not found"
        
        with open(spec_file) as f:
            spec = yaml.safe_load(f)
            
        # 验证基本结构
        assert 'meta' in spec
        assert 'schema' in spec
        assert 'validation' in spec
        assert 'lifecycle' in spec
        
        # 验证meta信息
        meta = spec['meta']
        assert meta['channel'] == 'radar_continental'
        assert meta['version'] == '1.0.0'
        assert meta['category'] == 'sensor_raw'
        
    def test_schema_completeness(self):
        """测试Schema定义完整性"""
        spec_file = Path("channels/radar_continental/spec-1.0.0.yaml")
        with open(spec_file) as f:
            spec = yaml.safe_load(f)
            
        schema = spec['schema']
        point_structure = schema['point_structure']
        
        # 验证必需字段
        required_fields = ['x', 'y', 'z', 'velocity', 'rcs', 'timestamp']
        for field in required_fields:
            assert field in point_structure, f"Missing required field: {field}"
            
        # 验证字段类型
        assert point_structure['x']['type'] == 'float32'
        assert point_structure['timestamp']['type'] == 'uint64'
        
    def test_sample_data_availability(self):
        """测试样本数据可用性"""
        samples_dir = Path("channels/radar_continental/samples")
        assert samples_dir.exists(), "Samples directory not found"
        
        sample_files = list(samples_dir.glob("*.bin"))
        assert len(sample_files) >= 10, f"Insufficient samples: {len(sample_files)}"
        
    def test_consumer_integration(self):
        """测试消费者配置集成"""
        consumer_file = Path("consumers/autonomous_driving.yaml")
        with open(consumer_file) as f:
            consumer = yaml.safe_load(f)
            
        # 查找Continental雷达配置
        found_continental = False
        for group in consumer['requirement_groups'].values():
            for req in group['requirements']:
                if req['channel'] == 'radar_continental':
                    found_continental = True
                    assert req['version'] == '>=1.0.0'
                    break
                    
        assert found_continental, "Continental radar not found in consumer config"
```

#### 步骤3：质量指标监控

```python
# scripts/quality_metrics.py 更新
def generate_quality_report():
    """生成SPEC质量报告"""
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'metrics': {}
    }
    
    # SPEC覆盖率
    total_channels = count_total_channels()
    documented_channels = count_documented_channels()
    spec_coverage = documented_channels / total_channels
    
    report['metrics']['spec_coverage'] = {
        'value': spec_coverage,
        'target': 1.0,
        'status': 'good' if spec_coverage >= 0.95 else 'warning'
    }
    
    # 格式合规性
    compliant_specs = validate_all_specs()
    total_specs = count_all_specs()
    format_compliance = compliant_specs / total_specs
    
    report['metrics']['format_compliance'] = {
        'value': format_compliance,
        'target': 1.0,
        'status': 'good' if format_compliance >= 0.98 else 'warning'
    }
    
    # 样本数据覆盖率
    channels_with_samples = count_channels_with_samples()
    sample_coverage = channels_with_samples / total_channels
    
    report['metrics']['sample_coverage'] = {
        'value': sample_coverage,
        'target': 1.0,
        'status': 'good' if sample_coverage >= 0.90 else 'warning'
    }
    
    # Continental雷达特定指标
    continental_metrics = validate_continental_radar_quality()
    report['metrics']['continental_radar'] = continental_metrics
    
    return report

def validate_continental_radar_quality():
    """Continental雷达特定质量指标"""
    return {
        'spec_completeness': 1.0,  # 所有必需字段都已定义
        'sample_format_compliance': 0.98,  # 98%的样本格式正确
        'integration_test_pass_rate': 1.0,  # 所有集成测试通过
        'consumer_compatibility': 1.0,  # 与所有消费者兼容
        'status': 'excellent'
    }
```

## 6. Platform Engineer：赵磊 - 平台工程师

### 场景：维护CI/CD流水线和自动化工具

赵磊负责确保整个系统的自动化运行。

#### 步骤1：更新CI流水线

```yaml
# .github/workflows/continental-radar-validation.yml
name: Continental Radar Validation

on:
  pull_request:
    paths:
      - 'channels/radar_continental/**'
  push:
    branches: [main]
    paths:
      - 'channels/radar_continental/**'

jobs:
  validate-continental-radar:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install struct numpy
          
      - name: Validate Continental radar spec
        run: |
          python scripts/validate_continental_radar.py
          
      - name: Run integration tests
        run: |
          pytest tests/integration/test_radar_continental.py -v
          
      - name: Check sample data quality
        run: |
          python scripts/quality_metrics.py --channel radar_continental
          
      - name: Generate radar-specific report
        run: |
          python scripts/generate_radar_report.py \
            --channel radar_continental \
            --output continental-radar-report.html
            
      - name: Upload radar report
        uses: actions/upload-artifact@v3
        with:
          name: continental-radar-report
          path: continental-radar-report.html
```

#### 步骤2：创建监控脚本

```python
# scripts/monitor_system_health.py
#!/usr/bin/env python3
"""
系统健康监控脚本
定期检查DataSpecHub系统的各项指标
"""

import requests
import json
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

class SystemHealthMonitor:
    def __init__(self):
        self.alerts = []
        
    def check_repo_health(self):
        """检查仓库健康状态"""
        
        # 检查最近的PR活动
        recent_prs = self.get_recent_prs()
        if len(recent_prs) == 0:
            self.alerts.append("⚠️ 过去7天没有PR活动")
            
        # 检查CI失败率
        failed_ci_rate = self.get_ci_failure_rate()
        if failed_ci_rate > 0.1:  # 10%
            self.alerts.append(f"🚨 CI失败率过高: {failed_ci_rate:.1%}")
            
        # 检查规格文件一致性
        inconsistent_specs = self.check_spec_consistency()
        if inconsistent_specs:
            self.alerts.append(f"📋 发现{len(inconsistent_specs)}个不一致的规格文件")
            
    def check_consumer_health(self):
        """检查消费者配置健康状态"""
        
        # 检查消费者配置更新频率
        stale_consumers = self.find_stale_consumers()
        if stale_consumers:
            self.alerts.append(f"📅 {len(stale_consumers)}个消费者配置超过30天未更新")
            
        # 检查版本约束冲突
        version_conflicts = self.check_version_conflicts()
        if version_conflicts:
            self.alerts.append(f"🔄 发现{len(version_conflicts)}个版本约束冲突")
            
    def check_bundle_health(self):
        """检查Bundle健康状态"""
        
        # 检查Bundle创建频率
        recent_bundles = self.get_recent_bundles()
        if not recent_bundles:
            self.alerts.append("📦 过去7天没有创建新Bundle")
            
        # 检查Bundle验证状态
        failed_bundles = self.get_failed_bundle_validations()
        if failed_bundles:
            self.alerts.append(f"❌ {len(failed_bundles)}个Bundle验证失败")
            
    def send_alerts(self):
        """发送告警通知"""
        if not self.alerts:
            print("✅ 系统健康状态良好")
            return
            
        alert_message = "DataSpecHub系统健康检查告警:\n\n"
        alert_message += "\n".join(self.alerts)
        
        # 发送到Slack
        self.send_slack_notification(alert_message)
        
        # 发送邮件给相关团队
        self.send_email_notification(alert_message)
        
    def generate_health_dashboard(self):
        """生成健康状态仪表板"""
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'system_health': {
                'overall_status': 'healthy' if not self.alerts else 'warning',
                'total_alerts': len(self.alerts),
                'alerts': self.alerts
            },
            'metrics': {
                'total_channels': self.count_total_channels(),
                'active_consumers': self.count_active_consumers(),
                'recent_bundles': len(self.get_recent_bundles()),
                'ci_success_rate': 1 - self.get_ci_failure_rate()
            }
        }
        
        # 保存到文件供Web界面展示
        with open('system-health-dashboard.json', 'w') as f:
            json.dump(dashboard_data, f, indent=2)
            
        return dashboard_data

# 每日定时执行
if __name__ == "__main__":
    monitor = SystemHealthMonitor()
    monitor.check_repo_health()
    monitor.check_consumer_health()
    monitor.check_bundle_health()
    monitor.send_alerts()
    monitor.generate_health_dashboard()
```

#### 步骤3：自动化工具增强

```bash
# scripts/auto_release.sh
#!/bin/bash
# 自动化发布脚本

set -e

WEEK_VERSION=$(date +"%Y.%U")
echo "🚀 Starting automated release for week $WEEK_VERSION"

# 1. 验证所有规格
echo "📋 Validating all specifications..."
python scripts/validate_channels.py
python scripts/validate_consumers.py
python scripts/validate_bundles.py

# 2. 生成Bundle
echo "📦 Creating weekly bundles..."
python scripts/bundle_manager.py create \
  --from-consumer autonomous_driving \
  --name weekly_release \
  --version $WEEK_VERSION

python scripts/bundle_manager.py create \
  --from-consumer perception_training \
  --name training_release \
  --version $WEEK_VERSION

# 3. 运行集成测试
echo "🧪 Running integration tests..."
pytest tests/integration/ -v

# 4. 生成发布说明
echo "📝 Generating release notes..."
python scripts/generate_release_notes.py \
  --version $WEEK_VERSION \
  --output RELEASE_NOTES_$WEEK_VERSION.md

# 5. 创建Git标签
echo "🏷️ Creating release tag..."
git tag "release/$WEEK_VERSION"
git push origin "release/$WEEK_VERSION"

# 6. 发布通知
echo "📢 Sending release notifications..."
python scripts/notify_release.py \
  --version $WEEK_VERSION \
  --channels slack,email

echo "✅ Release $WEEK_VERSION completed successfully!"
```

这些实际例子展示了每个角色在DataSpecHub系统中的日常工作流程，从规格变更的提出、审核、评估，到发布管理和质量保证的完整闭环。每个角色都有明确的职责分工和具体的操作步骤，确保整个数据规范治理流程的高效运行。 