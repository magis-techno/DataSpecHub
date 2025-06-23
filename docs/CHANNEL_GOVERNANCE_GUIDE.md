# 数据通道治理操作指南

## 概述

DataSpecHub 提供了完整的数据通道规范治理方案，解决了以下核心问题：
- 生产规格与发布规格的混淆
- 通道格式定义不明确
- 版本映射缺失
- 需求方差异化处理

## 核心概念

### 1. 数据集发布的双要素模型

**数据集最终发布 = SPEC + 生产输入列表**

- **SPEC（规格定义）**：本仓库管理的核心，包括数据格式、字段定义、验证规则等
- **生产输入列表**：实际数据的范围、来源、采集条件等（暂时hold，作为未来扩展）

**当前仓库聚焦**：SPEC管理，包括taxonomy定义、consumers约定、bundles配置

### 2. 生产规格 vs 发布规格

- **生产规格（Production Spec）**: 数据生产过程中使用的内部规格，包含具体的生产批次、数据路径、质量指标等
- **发布规格（Release Spec）**: 面向消费者的标准化规格，提供稳定的API和数据格式定义

### 3. 通道版本管理

每个通道遵循语义化版本管理：
- `1.0.0` - 主版本.次版本.修订版本
- 生命周期状态：`draft` → `stable` → `deprecated` → `legacy`

### 4. 消费者需求管理

支持不同消费者的差异化需求：
- 必选性配置（required/optional）
- 版本约束（>=1.0.0, ^2.0.0等）
- 缺失处理策略（fail/ignore/substitute/use_default）

## 操作流程

### 1. 创建新通道

#### 步骤1：定义通道规范
```bash
# 创建通道目录
mkdir channels/new_sensor

# 创建规范文件
cat > channels/new_sensor/spec-1.0.0.yaml << EOF
meta:
  channel: new_sensor
  version: 1.0.0
  category: sensor_raw
  description: "新传感器数据"
  
schema:
  data_format:
    type: binary
    encoding: [protobuf]
    compression:
      bitrate: 4000000  # 4Mbps
      quality: standard
    average_file_size: "2.0MB"
    
  timestamp:
    type: int64
    unit: nanoseconds
    description: "数据采集时间戳"
      
  metadata:
    data_source:
      type: string
      description: "数据来源话题"
    sensor_position: 
      type: string
      description: "传感器位置标识"

# 上游依赖信息 - 数据来源和处理模块
upstream_dependencies:
  module_name: "processing_module"
  module_version: "v1.0.0"
  description: "传感器数据由指定处理模块生成"
  source_topic: "sensor_data.bag"

validation:
  file_extensions: [".pb"]
  max_file_size: "50MB"
  
lifecycle:
  status: draft
  created_at: "2024-01-01"
  updated_at: "2024-01-01"
  maintainer: "sensor-team@company.com"
EOF
```

#### 步骤2：创建发布规范
```bash
cat > channels/new_sensor/release-1.0.0.yaml << EOF
meta:
  channel: new_sensor
  version: 1.0.0
  release_date: "2024-01-01"
  release_type: major
  
spec_ref: ./spec-1.0.0.yaml

changes:
  - type: "feature"
    description: "初始版本发布"
    
compatibility:
  backward_compatible: true
  breaking_changes: []
  deprecated_fields: []

quality_metrics:
  validation_passed: true
  sample_coverage: 100%
  format_compliance: 100%
  
performance:
  file_size_avg: "2.0MB"
  processing_time: "120ms"
  
lifecycle:
  status: stable
  next_version: "1.1.0"
  support_until: "2025-06-01"
EOF
```

#### 步骤3：创建变更日志
```bash
cat > channels/new_sensor/CHANGELOG.md << EOF
# new_sensor 通道变更日志

## [1.0.0] - 2024-01-01

### 新增
- 初始版本发布
- 支持protobuf格式的传感器数据
- 标准时间戳和元数据字段
- 语义化存储映射信息

### 架构设计
- 采用分离式设计：通道专注数据格式，索引系统管理关联关系
- 传感器命名按位置而非具体硬件，提高通用性
EOF
```

#### 步骤4：添加样本数据
```bash
mkdir channels/new_sensor/samples
# 添加示例数据文件到samples目录（用于格式验证，不涉及数据量要求）
```

#### 步骤5：更新分类体系
编辑 `taxonomy/channel_taxonomy.yaml`，将新通道添加到相应分类中。

### 2. 版本升级

#### 创建新版本规范
```bash
# 复制现有规范作为基础
cp channels/existing_channel/spec-1.0.0.yaml channels/existing_channel/spec-1.1.0.yaml

# 编辑新版本规范
# 更新版本号和变更内容

# 创建对应的发布规范
cat > channels/existing_channel/release-1.1.0.yaml << EOF
meta:
  channel: existing_channel
  version: 1.1.0
  release_type: minor
  
spec_ref: ./spec-1.1.0.yaml

changes:
  - type: "feature"
    description: "新增字段X"
  - type: "improvement"
    description: "优化数据压缩"
    
compatibility:
  backward_compatible: true
  breaking_changes: []

quality_metrics:
  validation_passed: true
  sample_coverage: 100%
  format_compliance: 100%
  
performance:
  file_size_avg: "1.8MB"
  processing_time: "100ms"
  
lifecycle:
  status: stable
  next_version: "1.2.0"
  support_until: "2025-12-01"
EOF
```

#### 更新变更日志
在 `CHANGELOG.md` 中添加新版本的变更记录。

### 3. 配置消费者需求

#### 创建消费者配置文件
```bash
cat > consumers/my_application/v1.0.0.yaml << EOF
meta:
  consumer: my_application
  owner: "app-team@company.com"
  description: "我的应用数据需求"
  team: "应用开发团队"
  version: "1.0.0"
  created_at: "2025-04-10"
  updated_at: "2025-04-10"

# 应用的数据需求
requirements:
  - channel: image_original
    version: ">=1.0.0"
    required: true
    on_missing: "fail"  # 任务失败中断
    
  - channel: object_array_fusion_infer
    version: ">=1.0.0"
    required: true
    on_missing: "substitute"  # 使用替代数据源
    substitute_with:
      channel: object_array_fusion_infer
      version: ">=1.0.0"
    
  - channel: occupancy
    version: "1.0.0"
    required: false
    on_missing: "ignore"  # 忽略缺失继续处理

# 需求变更历史
change_history:
  - date: "2025-04-10"
    version: "1.0.0"
    changes: "初始版本：支持基础图像和目标检测需求"

# 集成信息
integration:
  jira_epic: "APP-2024-001"
  approval_status: "pending"
EOF
```

#### 创建latest指针文件
```bash
# 创建指向当前推荐版本的符号链接
cat > consumers/my_application/latest.yaml << EOF
# This file points to the current recommended version: v1.0.0
# In production, this would be a symbolic link: ln -s v1.0.0.yaml latest.yaml

meta:
  consumer: my_application
  owner: "app-team@company.com"
  description: "我的应用数据需求"
  team: "应用开发团队"
  version: "1.0.0"
  created_at: "2025-04-10"
  updated_at: "2025-04-10"

# 当前数据需求 - 专注于版本依赖
requirements:
  - channel: image_original
    version: ">=1.0.0"
    required: true
    on_missing: "fail"
    
  - channel: object_array_fusion_infer
    version: ">=1.0.0"
    required: true
    on_missing: "substitute"
    substitute_with:
      channel: object_array_fusion_infer
      version: ">=1.0.0"
    
  - channel: occupancy
    version: "1.0.0"
    required: false
    on_missing: "ignore"

# 需求变更历史
change_history:
  - date: "2025-04-10"
    version: "1.0.0"
    changes: "初始版本：支持基础图像和目标检测需求"
EOF
```

### 4. 缺失处理策略详解

缺失处理策略（`on_missing`）定义了当所需通道数据缺失时的处理方式：

- **fail**: 任务失败中断，要求数据必须存在
- **ignore**: 忽略缺失，继续处理其他可用数据  
- **substitute**: 使用替代数据源，通过 `substitute_with` 指定
- **use_default**: 使用预设的默认值（需在规范中定义默认值）

#### 替代数据源配置
```yaml
on_missing: "substitute"
substitute_with:
  channel: backup_channel_name
  version: ">=1.0.0"
```

### 5. 创建生产Bundle

#### 定义Bundle配置
```bash
cat > bundles/my_project/bundle-2024-q1.yaml << EOF
meta:
  bundle: my_project
  version: '2024-q1'
  owner: 'project-team@company.com'
  
production_info:
  batch_id: "proj-2024-q1"
  data_collection_period:
    start: "2024-01-01T00:00:00Z"
    end: "2024-03-31T23:59:59Z"
    
# SPEC到生产的映射关系
channel_mappings:
  - channel: image_original
    production_spec: "proj-img-cam1-2024-q1"
    release_spec: "1.0.0"
    data_path: "/data/proj-2024-q1/image_original"
    
channels:
  - channel: image_original
    version: '1.0.0'
    required: true
    
# 注意：这里记录SPEC使用情况，具体数据输入范围由生产系统管理
EOF
```

## 验证和CI/CD

### 本地验证
```bash
# 验证通道规范
python scripts/validate_channels.py

# 验证消费者需求
python scripts/validate_consumers.py

# 验证Bundle配置
python scripts/validate_bundles.py

# 验证分类体系一致性
python scripts/validate_taxonomy.py
```

### CodeHub集成

1. **提交RR时自动验证**
   - 通道规范语法检查
   - 版本兼容性检查
   - 样本数据格式验证（非数量验证）
   - 与需求管理系统集成

2. **RR标题格式**
   ```
   [RR/AR/DTS:******] 新增传感器通道规范
   ```
   系统会自动提取Issue ID并关联。

## 最佳实践

### 1. 版本管理
- 使用语义化版本号
- 重大变更时递增主版本号
- 向后兼容的新功能递增次版本号
- Bug修复递增修订版本号

### 2. 上游依赖管理
- 使用 `upstream_dependencies` 字段记录数据来源和处理模块信息
- 记录上游模块名称、版本号和数据来源话题
- 建立清晰的数据处理链路和依赖关系

### 3. 消费者需求管理
- 使用 `latest.yaml` 指向当前推荐版本
- 维护详细的 `change_history` 记录需求演进
- 明确定义缺失处理策略和替代方案
- 与需求管理系统保持同步

### 4. 质量保证
- 每个通道必须包含样本数据（用于格式验证）
- 维护详细的CHANGELOG.md记录所有变更
- 定期审查和更新废弃通道
- 监控SPEC变更的影响
- 建立变更审批流程

### 5. 性能监控
- 记录详细的性能指标（推理时间、文件大小、准确率等）
- 为AI模型通道维护benchmark数据
- 监控版本升级对性能的影响

## 管理边界

### 当前仓库管理范围
- ✅ SPEC定义和版本管理
- ✅ Taxonomy分类体系
- ✅ Consumer需求约定
- ✅ Bundle规格配置
- ✅ 兼容性和影响分析
- ✅ 上游依赖关系管理
- ✅ 变更历史追踪

### 未来扩展范围（暂时hold）
- 🔄 生产输入列表管理
- 🔄 实际数据量统计
- 🔄 数据质量监控
- 🔄 完整的数据复现能力

## 故障排除

### 常见问题

1. **验证失败：规范文件格式错误**
   ```bash
   # 检查YAML语法
   python -c "import yaml; yaml.safe_load(open('channels/xxx/spec-1.0.0.yaml'))"
   ```

2. **通道不在分类体系中**
   - 编辑 `taxonomy/channel_taxonomy.yaml`
   - 将通道添加到相应分类

3. **生产数据路径不存在**
   - 检查Bundle中的数据路径配置
   - 确认数据已正确上传到指定位置

4. **版本兼容性冲突**
   - 检查消费者的版本约束
   - 更新通道的兼容性信息

5. **缺失处理策略配置错误**
   - 确认 `on_missing` 使用正确的策略值
   - 检查 `substitute_with` 配置是否完整

### 联系支持

- 技术问题：data-platform@company.com
- 流程问题：data-governance@company.com
- 紧急问题：data-oncall@company.com 