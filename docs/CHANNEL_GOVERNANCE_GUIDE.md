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
    encoding: protobuf
    
  # 详细的数据结构定义...
  
validation:
  file_extensions: [".pb"]
  max_file_size: "50MB"
  
lifecycle:
  status: draft
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
  
spec_ref: ./spec-1.0.0.yaml

# 生产规格到发布规格的映射关系
production_mapping:
  production_runs:
    - run_id: "prod-2024-001"
      date: "2024-01-01"
      data_path: "/data/prod-2024-001/new_sensor"
      
changes:
  - type: "feature"
    description: "初始版本发布"
    
lifecycle:
  status: stable
EOF
```

#### 步骤3：添加样本数据
```bash
mkdir channels/new_sensor/samples
# 添加示例数据文件到samples目录（用于格式验证，不涉及数据量要求）
```

#### 步骤4：更新分类体系
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
  
changes:
  - type: "feature"
    description: "新增字段X"
  - type: "improvement"
    description: "优化数据压缩"
    
compatibility:
  backward_compatible: true
  breaking_changes: []
EOF
```

### 3. 配置消费者需求

#### 创建消费者配置文件
```bash
cat > consumers/my_application.yaml << EOF
meta:
  consumer: my_application
  owner: "app-team@company.com"
  description: "我的应用数据需求"
  
requirement_groups:
  core_sensors:
    requirements:
      - channel: img_cam1
        version: ">=1.0.0 <2.0.0"
        required: true
        on_missing: fail
        priority: critical
        
      - channel: lidar
        version: ">=1.0.0"
        required: true
        on_missing: fail
        priority: critical
        
  optional_sensors:
    requirements:
      - channel: radar.v2
        version: "^2.0.0"
        required: false
        on_missing: substitute
        substitute_with:
          channel: radar.v1
          version: "1.0.0"
        priority: medium

global_config:
  default_on_missing: ignore
  # 注意：这里只定义SPEC层面的要求，不涉及具体数据量

integration:
  jira_epic: "APP-2024-001"
  approval_status: "pending"
EOF
```

### 4. 创建生产Bundle

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
  - channel: img_cam1
    production_spec: "proj-img-cam1-2024-q1"
    release_spec: "1.0.0"
    data_path: "/data/proj-2024-q1/img_cam1"
    
channels:
  - channel: img_cam1
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

### GitHub集成

1. **提交PR时自动验证**
   - 通道规范语法检查
   - 版本兼容性检查
   - 样本数据格式验证（非数量验证）
   - 与需求管理系统集成

2. **PR标题格式**
   ```
   [DATA_SPEC-123] Add new sensor channel specification
   ```
   系统会自动提取Issue ID并关联。

3. **自动生成文档**
   - 合并到main分支后自动生成通道文档
   - 更新API文档和Schema文档

## 最佳实践

### 1. 版本管理
- 使用语义化版本号
- 重大变更时递增主版本号
- 向后兼容的新功能递增次版本号
- Bug修复递增修订版本号

### 2. 生产映射
- 记录SPEC版本与生产批次的对应关系
- 建立清晰的生产规格到发布规格映射
- 记录数据收集的环境和条件

### 3. 消费者需求
- 按功能模块组织需求
- 明确优先级（critical/high/medium/low）
- 定义清晰的缺失处理策略
- 与需求管理系统保持同步

### 4. 质量保证
- 每个通道必须包含样本数据（用于格式验证）
- 定期审查和更新废弃通道
- 监控SPEC变更的影响
- 建立变更审批流程

## 管理边界

### 当前仓库管理范围
- ✅ SPEC定义和版本管理
- ✅ Taxonomy分类体系
- ✅ Consumer需求约定
- ✅ Bundle规格配置
- ✅ 兼容性和影响分析

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

### 联系支持

- 技术问题：data-platform@company.com
- 流程问题：data-governance@company.com
- 紧急问题：data-oncall@company.com 