# DataSpecHub 完整使用指南

## 概述
本文档提供DataSpecHub系统的完整使用指南，包括系统架构、版本管理规范、配置方法、运作机制和最佳实践。通过本文档，使用者可以全面了解如何配置和使用DataSpecHub进行数据规格管理和版本控制。

## 1. 系统概述与双要素模型

### 1.1 数据集发布的双要素模型

DataSpecHub采用双要素模型来管理数据集发布：

**数据集最终发布 = SPEC + 生产输入列表**

- **SPEC（规格定义）**：由DataSpecHub仓库管理，包括数据格式、字段定义、验证规则、版本约束等
- **生产输入列表**：由data_release仓库管理，包括实际数据范围、来源、采集条件、JSONL索引文件等

**当前DataSpecHub仓库聚焦**：SPEC管理，包括channel规格定义、consumer需求约定、bundle版本指导。

### 1.2 系统架构与数据流

```
DataSpecHub 仓库职责：
├── Channels/     - 数据通道规格定义（格式、字段、验证规则）
├── Consumers/    - 用户版本需求配置（约束、依赖、缺失处理）
└── Bundles/      - 版本清单指导（可用版本、推荐版本）

外部生产系统：
└── 根据DataSpecHub规范重新开发的生产工具

data_release 仓库：
└── 最终交付物管理（JSONL索引文件、训练数据集配置）
```

**数据流转过程**：
```
1. 数据规格定义    →  channels/  (格式标准)
2. 用户需求配置    →  consumers/ (版本约束)  
3. 版本清单生成    →  bundles/   (可用版本列表)
4. 外部系统生产    →  根据bundle指导生产数据
5. 交付物管理      →  data_release仓 (JSONL索引)
```

### 1.3 核心概念

#### 生产规格 vs 发布规格
- **生产规格（Production Spec）**: 数据生产过程中使用的内部规格，包含具体的生产批次、数据路径、质量指标等
- **发布规格（Release Spec）**: 面向消费者的标准化规格，提供稳定的API和数据格式定义

#### 版本清单记录器
Bundle系统专注于三个核心功能：
1. **版本清单生成** - 将Consumer的软约束转换为明确的版本列表
2. **链路追溯** - 记录从Consumer到Bundle的完整转换路径  
3. **灵活选择** - 提供版本列表而非固定版本，支持动态数据环境

### 1.4 角色分工与配置职责

| 角色 | 主要职责 | 负责的配置文件 |
|------|----------|---------------|
| **数据SE** | 复杂通道规格设计、技术方案制定 | `channels/<complex>/spec-*.yaml` |
| **MDE** | 简单通道规格维护、模块协调 | `channels/<simple>/spec-*.yaml` |
| **FO（Feature Owner）** | Consumer需求管理、变更协调 | `consumers/*/` |
| **外部RM** | 根据Bundle指导进行数据生产 | 使用bundles指导生产 |

### 1.5 与data_release仓的协作关系

DataSpecHub定义"做什么"和"怎么做"，data_release仓管理"做出来的是什么"：

**DataSpecHub → data_release 的版本追溯链路**：
```
Consumer版本 → Bundle版本 → Training Dataset版本
foundational_model/v1.0.0.yaml → foundational_model-v1.0.0-20250620-143500.yaml → JointTrain_20250727-v1.2.0
```

通过 `consumer_version` 和 `bundle_versions` 数组可以追溯到DataSpecHub中的具体配置文件，实现完整的数据血缘关系。

## 2. Bundle版本规范

### 2.1 语义化版本控制(SemVer)基础

#### 版本格式
采用 `MAJOR.MINOR.PATCH` 三位版本号格式，遵循SemVer标准。

#### 版本约束表达式
- `1.2.0`: 精确版本匹配
- `>=1.2.0`: 大于等于1.2.0的任何版本
- `>1.2.0`: 大于1.2.0（不包含1.2.0本身）
- `^1.2.0`: 兼容1.2.0但小于2.0.0（允许MINOR和PATCH更新）
- `~1.2.0`: 兼容1.2.0但小于1.3.0（只允许PATCH更新）
- `*`: 任何版本（最新优先）

### 2.2 Bundle类型说明

#### Weekly Bundle (周度Bundle)
- **用途**: 定期训练和开发环境使用
- **生成频率**: 每周生成
- **命名格式**: `{consumer}-{version}-{年}.{周数}`
- **示例**: `end_to_end-v1.2.0-2025.25`
- **特点**: 基于稳定版本，适合常规开发工作

#### Release Bundle (发布Bundle)  
- **用途**: 生产环境和重要里程碑发布
- **生成时机**: 重大版本发布时
- **命名格式**: `{consumer}-{version}-release`
- **示例**: `pv_trafficlight-v1.1.0-release`
- **特点**: 经过充分测试，版本固定，用于生产部署

#### Snapshot Bundle (快照Bundle)
- **用途**: 特定时间点的数据快照
- **生成时机**: 重要实验或数据备份需要
- **命名格式**: `{consumer}-{version}-{YYYYMMDD}-{HHMMSS}`
- **示例**: `foundational_model-v1.0.0-20250620-143500`
- **特点**: 精确时间标记，用于实验复现和数据审计

### 2.3 核心概念

#### Consumer Version vs Bundle Version

**Consumer Version**
- **定义**: 消费者组件的功能版本标识
- **格式**: SemVer格式，如 `v1.2.0`
- **含义**: 标识消费者的功能迭代和兼容性要求
- **示例**: `v1.2.0` 表示端到端网络的第1.2.0功能版本

**Bundle Version**  
- **定义**: Bundle数据快照的唯一标识符
- **格式**: 根据Bundle类型确定具体格式
- **含义**: 将Consumer的版本约束转换为具体可用数据版本的快照
- **示例**: `v1.2.0-2025.25` 表示基于Consumer v1.2.0需求在2025年第25周的数据快照

#### Bundle唯一标识
每个Bundle由 `bundle_name` + `bundle_version` 唯一确定：
- **bundle_name**: 对应Consumer名称，如 `end_to_end`
- **bundle_version**: 根据Bundle类型生成的版本标识，如 `v1.2.0-2025.25`
- **文件路径**: `bundles/{type}/{bundle_name}-{bundle_version}.yaml`

#### 版本转换关系
```
Consumer需求 (软约束) → Bundle Generator → Bundle快照 (硬版本清单)
     v1.2.0                                    v1.2.0-2025.25
    
约束示例:
- image_original: "1.2.0" (精确要求)
- object_array_fusion_infer: ">=1.2.0" (范围约束，允许1.2.0+)  
- utils_slam: "~1.0.0" (补丁兼容，允许1.0.x)
- occupancy: ">=1.0.0" (范围约束，允许1.0.0+)

快照结果:
- image_original: ["1.2.0"]
- object_array_fusion_infer: ["1.2.0"]  
- utils_slam: ["1.0.5", "1.0.2", "1.0.0"] (满足~1.0.0的版本)
- occupancy: ["1.0.0"]
```

### 2.4 Bundle文件字段规范

#### Bundle文件字段组成

**Meta字段**：Bundle基础信息
- `bundle_name`: Bundle名称（对应Consumer名称）
- `consumer_version`: 源Consumer的版本
- `bundle_version`: Bundle快照版本
- `bundle_type`: Bundle类型（weekly/release/snapshot）
- `created_at`: 创建时间
- `source_consumer`: 源Consumer文件路径

**版本转换追踪字段**：完整的追溯信息
- `consumer_config`: 源配置文件路径
- `consumer_version`: Consumer版本
- `conversion_time`: 转换时间
- `converted_by`: 转换工具标识

**通道版本字段**：核心的版本清单信息
- `channel`: 通道名称
- `available_versions`: 按推荐度排序的版本列表
- `source_constraint`: 来自Consumer的原始约束
- `required`: 是否必需（从Consumer配置继承）
- `on_missing`: 缺失处理策略（从Consumer配置继承）

*完整的Bundle文件结构示例请参见第6.2节。*

**字段含义详解**

| 字段 | 含义 | 示例 | 使用规则 |
|------|------|------|----------|
| `channel` | 通道名称 | `object_array_fusion_infer` | 对应channels目录下的通道 |
| `available_versions` | 可用版本列表 | `["1.2.0", "1.1.0"]` | 按推荐度排序，第一个为最佳选择 |
| `source_constraint` | 原始约束 | `">=1.2.0"` | 来自Consumer配置，用于审计 |
| `required` | 是否必需 | `true` | 从Consumer配置继承 |
| `on_missing` | 缺失处理策略 | `"fail"` | 从Consumer配置继承 |

#### 版本选择策略
Bundle生成器在解析版本约束时遵循以下原则：

1. **约束范围**: 首先确定满足约束的所有可用版本
   - `>=1.2.0` 且可用版本为 `[1.2.0, 1.3.0, 1.5.0]` → 都满足约束
   
2. **稳定性优先**: 不一定选择最新版本，优先考虑稳定性
   - 可能选择 `1.3.0` 而不是 `1.5.0`（如果1.5.0太新未充分验证）
   
3. **团队策略**: 考虑团队的使用习惯和兼容性需求

#### 版本排序原则
`available_versions`数组按以下优先级排序：
1. **稳定性优先**: 经过验证的稳定版本排在前面
2. **兼容性考虑**: 确保向后兼容性
3. **数据质量**: 在满足约束的前提下选择数据质量最佳的版本

#### 使用约定
- **第一个版本**: 系统推荐的主选版本（不一定是最新版本）
- **后续版本**: 按优先级排序的备选版本（fallback选项）

## 3. Consumer版本管理

### 3.1 Consumer版本结构

#### 目录组织
```
consumers/
├── end_to_end/
│   ├── v1.0.0.yaml           # 基础版本
│   ├── v1.2.0.yaml           # 当前稳定版本  
│   ├── v1.2.1-experiment.yaml    # 实验分支
│   └── latest.yaml           # 指向当前推荐版本
├── foundational_model/
│   ├── v1.0.0.yaml           # 基础版本
│   ├── v1.0.1-pretraining.yaml   # 预训练特化版本
│   ├── v1.0.2-finetuning.yaml    # 微调特化版本
│   └── latest.yaml
└── pv_trafficlight/
    ├── v1.1.0.yaml           # 当前版本
    ├── v1.1.1-weather.yaml      # 天气适应性分支
    └── latest.yaml
```

#### 文件命名规范
- **主版本**: `v{major}.{minor}.{patch}.yaml`
- **分支版本**: `v{major}.{minor}.{patch}-{variant}.yaml`

#### 变体后缀含义
| 后缀 | 含义 | 使用场景 |
|------|------|----------|
| `-experiment` | 实验性功能测试 | 功能验证、A/B测试 |
| `-pretraining` | 预训练阶段特化 | 大模型预训练阶段 |
| `-finetuning` | 微调阶段特化 | 大模型微调阶段 |
| `-debug` | 调试版本 | 问题诊断、开发调试 |

### 3.2 Consumer配置文件规范

#### Meta字段
```yaml
meta:
  consumer: end_to_end              # Consumer名称
  version: "1.2.0"                  # 版本号（遵循SemVer）
  parent_version: "1.1.0"           # 基于哪个版本创建（可选）
  branch_type: "stable"             # stable/experiment/optimization/pretraining/finetuning
  created_at: "2025-04-10"          # 创建时间
  expires_at: "2025-05-10"          # 实验分支过期时间（可选）
  owner: "e2e-team@company.com"     # 负责团队
  description: "端到端网络的数据通道版本需求"
```

#### Requirements字段
```yaml
requirements:
  - channel: image_original
    version: "1.2.0"              # 单版本约束
    required: true                 # 是否必需
    on_missing: "fail"            # 缺失处理策略
    
  - channel: object_array_fusion_infer
    version:                      # 多版本候选列表（按优先级排序）
      - "1.2.0_optimized"         # 首选版本（支持非标准命名）
      - "1.2.0"                   # 备选版本
      - ">=1.1.0"                 # SemVer备选约束
    required: true
    on_missing: "fail"
      
  - channel: utils_slam
    version: "~1.0.0"
    required: false
    on_missing: "ignore"          # 忽略缺失
```

### 3.3 版本约束语法

#### 支持的格式
- **单版本**: `version: "1.2.0"` 或 `version: ">=1.2.0"`
- **版本列表**: `version: ["1.2.0_opt", "1.2.0", ">=1.1.0"]`
- **混合约束**: 列表中可以包含精确版本和SemVer约束

#### 处理逻辑
1. **单版本**: 按标准SemVer约束解析
2. **版本列表**: 按优先级顺序查找可用版本
   - 精确版本: 直接匹配
   - SemVer约束: 解析后合并到结果中

### 3.4 运行时配置字段

#### `required`: 是否必需（true/false）
- `true`: 核心数据，业务流程必需
- `false`: 可选数据，缺失时可继续

#### `on_missing`: 缺失处理策略
- `"fail"`: 任务失败中断
- `"ignore"`: 忽略缺失继续处理

#### 推荐配置

**核心数据**：
```yaml
- channel: image_original
  required: true
  on_missing: "fail"
```

**可选数据**：
```yaml
- channel: occupancy
  required: false
  on_missing: "ignore"
```

### 3.5 版本约束解析规则

#### 约束类型处理

假设系统中可用版本为：`[2.1.0, 1.5.1, 1.5.0, 1.4.0_opt, 1.3.0, 1.2.8, 1.2.0, 1.1.9]`

| Consumer约束 | Bundle解析结果 | 使用场景 |
|-------------|---------------|----------|
| `"1.2.0"` | `["1.2.0"]` | 精确版本，严格要求 |
| `">=1.3.0"` | `["2.1.0", "1.5.1", "1.5.0", "1.4.0_opt", "1.3.0"]` | 最低版本要求，无上限 |
| `"~1.2.0"` | `["1.2.8", "1.2.0"]` | 保守策略，只允许补丁更新 |
| `"^1.2.0"` | `["1.5.1", "1.5.0", "1.4.0_opt", "1.3.0", "1.2.8", "1.2.0"]` | 兼容更新，但排除2.x版本 |
| `["1.4.0_opt", ">=1.3.0"]` | `["1.4.0_opt", "2.1.0", "1.5.1", "1.5.0", "1.3.0"]` | 首选特定版本+备选范围 |
| `"*"` | `["2.1.0", "1.5.1", "1.5.0", "1.4.0_opt", "1.3.0", "1.2.8", "1.2.0", "1.1.9"]` | 任何版本，追求最新 |

#### 关键约束区别

**`^1.2.0` vs `>=1.2.0` 的重要区别**：
- `^1.2.0`: 允许 `1.2.0` 到 `1.x.x`，但**排除 `2.0.0`** (兼容性边界)
- `>=1.2.0`: 允许 `1.2.0` 及以上**任何版本**，包括 `2.0.0`, `3.0.0` 等

在上面例子中：
- `^1.2.0` 结果**不包含** `2.1.0`
- `>=1.3.0` 结果**包含** `2.1.0`

#### 常见使用建议

| 场景 | 推荐约束 | 说明 |
|------|---------|------|
| 生产环境 | `"~1.2.0"` | 稳定性优先，只接受补丁更新 |
| 开发环境 | `"^1.2.0"` | 功能更新，但避免破坏性变更 |
| 实验环境 | `">=1.2.0"` | 允许任何新版本，包括破坏性更新 |
| 特定功能依赖 | `">=1.3.0"` | 需要特定版本的新功能 |

## 4. 配置指南与运作机制

### 4.1 创建新通道的配置流程

#### 步骤1：定义通道规范
在 `channels/<channel_name>/` 目录下创建规范文件：

```yaml
# channels/new_sensor/spec-1.0.0.yaml
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
```

#### 步骤2：创建发布规范
```yaml
# channels/new_sensor/release-1.0.0.yaml
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
```

#### 步骤3：更新分类体系
编辑 `taxonomy/channel_taxonomy.yaml`，将新通道添加到相应分类中。

### 4.2 配置Consumer需求

#### 创建Consumer配置文件
```yaml
# consumers/my_application/v1.0.0.yaml
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
    on_missing: "fail"
    
  - channel: occupancy
    version: "1.0.0"
    required: false
    on_missing: "ignore"  # 忽略缺失继续处理

# 需求变更历史
change_history:
  - date: "2025-04-10"
    version: "1.0.0"
    changes: "初始版本：支持基础图像和目标检测需求"
```

#### 创建latest指针文件
```yaml
# consumers/my_application/latest.yaml
# 指向当前推荐版本: v1.0.0

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
    on_missing: "fail"
    
  - channel: occupancy
    version: "1.0.0"
    required: false
    on_missing: "ignore"
```

### 4.3 Bundle生成与使用机制

#### Bundle生成过程
```
1. Consumer配置 → 外部Bundle生成器读取约束
2. 版本解析 → 扫描可用版本，应用约束逻辑
3. 版本清单 → 生成按推荐度排序的版本列表
4. Bundle文件 → 输出完整的Bundle配置文件
```

#### Bundle文件结构解读
Bundle文件包含以下核心字段：
- **meta**: Bundle元数据，包括名称、版本、类型、创建时间等
- **conversion_source**: 版本转换追溯信息，记录从Consumer到Bundle的转换过程
- **channels**: 版本清单，包含每个通道的可用版本列表和运行时配置

**完整的Bundle文件示例请参见第6.2节**，其中包含了所有字段的详细说明和实际配置。

### 4.4 版本约束转换逻辑

#### 约束解析流程
```
1. 读取Consumer配置中的版本约束
2. 扫描channels目录获取所有可用版本
3. 应用SemVer匹配规则过滤版本
4. 按稳定性和推荐度排序
5. 生成available_versions列表
```

#### 实际转换示例
```yaml
# Consumer输入约束
requirements:
  - channel: object_array_fusion_infer
    version: ">=1.2.0"

# 系统扫描可用版本
Available versions in channels/object_array_fusion_infer/:
- spec-1.3.0.yaml (最新，但可能不稳定)
- spec-1.2.5.yaml (稳定)
- spec-1.2.0.yaml (稳定)
- spec-1.1.0.yaml (不满足约束)

# Bundle输出结果
channels:
  - channel: object_array_fusion_infer
    available_versions: ["1.2.5", "1.2.0", "1.3.0"]  # 1.2.5优先推荐
    source_constraint: ">=1.2.0"
```

### 4.5 协作机制

#### 角色协作流程
```
1. 数据SE/MDE → 维护channels规格
   ↓
2. FO (Feature Owner) → 配置Consumer需求
   ↓ 
3. 外部生产系统 → 根据Bundle指导生产数据
   ↓
4. data_release仓 → 管理最终JSONL索引
```

#### 变更协调机制
1. **Channel变更**：SE/MDE更新规格后通知FO
2. **Consumer更新**：FO评估影响，更新consumer配置
3. **Bundle重生成**：外部系统基于新配置重新生成Bundle
4. **下游通知**：FO协调下游团队适配新版本

#### 版本锁定策略
```yaml
# compatibility/consumer_matrix.yaml 中的生产锁定
production_locks:
  end_to_end_network:
    current_production:
      image_original: "1.2.0"
      object_array_fusion_infer: "1.0.0"
      occupancy: "1.0.0"
      utils_slam: "1.0.0"
      locked_until: "2025-07-01"      # 生产环境锁定期
      environment_rollout:
        development: "1.2.0"
        testing: "1.2.0" 
        staging: "1.1.1"              # 保守策略
        production: "1.1.1"           # 生产保守策略
```

## 5. 使用场景与最佳实践

### 5.1 三种Bundle的使用场景

#### Release Bundle - 正式发布版本

**使用场景**：
- **生产环境部署** - 经过严格质量验证的版本清单
- **客户交付** - 向外部客户交付的数据版本组合
- **里程碑发布** - 重大功能更新的正式版本
- **长期支持** - 需要维护和支持的稳定版本清单

**特点**：
- 经过完整QA流程验证的版本清单
- 支持1年以上长期维护，有完整回滚计划
- 用于生产部署和客户交付

*详细的Release Bundle配置示例请参见第6.2节。*

#### Weekly Bundle - 固定周期版本

**使用场景**：
- **团队协作同步** - 保证团队使用相同的版本清单
- **定期训练任务** - 每周定期的模型训练
- **集成测试环境** - 持续集成的标准数据环境
- **进度同步节点** - 项目进度的数据版本里程碑

**特点**：
- 支持多版本备选，提供灵活的版本选择
- 按推荐度排序的版本清单，便于自动化系统选择
- 保留4周历史版本，便于问题追溯

**使用方式**：
- 每周一团队例会前自动生成
- 团队收到通知：📅 Weekly Bundle 2025.25 已生成，包含4个channel的版本清单
- 每周训练结果可对比，版本清单一致性保证

#### Snapshot Bundle - 临时快照版本

**使用场景**：
- **快速验证实验** - 临时数据需求的快速响应
- **POC概念验证** - 新想法的快速试验
- **Bug调试** - 特定问题的数据重现
- **临时需求** - 紧急或短期的数据需求

**特点**：
- **多版本并行实验**：支持A/B测试和版本对比
- **精确版本复现**：用于Bug调试和问题追溯
- **实验用途标记**：可添加experiment_role等自定义字段
- **自动过期清理**：7-30天后自动清理，避免积累

**常见使用场景**：
- 算法研究员测试新想法：支持多版本并行验证
- 紧急Bug调试：复现特定版本组合的问题
- POC概念验证：快速验证新技术方案的可行性

*具体的Snapshot Bundle配置示例请参见第6.2节。*

### 5.2 版本管理最佳实践

#### 版本约束选择策略

| 环境类型 | 推荐约束策略 | 原因 | 示例约束 |
|----------|-------------|------|----------|
| **生产环境** | 保守策略 | 稳定性优先，避免意外变更 | `"~1.2.0"` 只允许补丁更新 |
| **测试环境** | 兼容策略 | 验证功能更新，但避免破坏性变更 | `"^1.2.0"` 允许小版本更新 |
| **实验环境** | 开放策略 | 允许尝试新功能，包括破坏性更新 | `">=1.2.0"` 允许任何新版本 |
| **特定功能** | 精确策略 | 依赖特定版本的新功能 | `">=1.3.0"` 明确最低版本需求 |

#### Consumer版本规划

**主版本演进策略**：
```
v1.0.0 → v1.1.0 → v1.2.0 → v2.0.0
  ↓        ↓        ↓        ↓
基础功能   增强功能   优化改进   架构升级
```

**分支管理策略**：
```
v1.2.0 (稳定主线)
├── v1.2.1-experiment (实验分支, 30天后决定合并或删除)
├── v1.2.1-debug (调试分支, 问题解决后删除)  
└── v1.3.0-pretraining (预训练特化, 长期维护)
```

#### 生产环境部署策略

**环境推进策略**：
```
开发环境 → 测试环境 → 预发布环境 → 生产环境
  ↓         ↓         ↓          ↓
 最新版本   稳定版本   保守版本    锁定版本
 (>=1.2.0) (^1.2.0)  (~1.2.0)   (1.2.0)
```

**版本锁定管理**：
- **开发环境**: 使用最新的Weekly Bundle
- **测试环境**: 使用上一周的Weekly Bundle 
- **预发布环境**: 使用Release Bundle的候选版本
- **生产环境**: 使用经过验证的Release Bundle，锁定期1-3个月

### 5.3 配置变更协调流程

#### 标准变更流程
```
1. 需求评估 → FO收集下游需求，评估变更必要性
   ↓
2. 影响分析 → 分析对现有Consumer和Bundle的影响  
   ↓
3. 配置更新 → 更新Consumer配置，创建新版本
   ↓
4. Bundle重生成 → 外部系统基于新配置生成Bundle
   ↓
5. 下游通知 → FO协调下游团队适配新版本
   ↓
6. 分阶段部署 → 开发→测试→预发布→生产的渐进部署
```

#### 紧急变更流程
```
1. 问题识别 → 发现影响生产的紧急问题
   ↓
2. 快速评估 → 15分钟内评估影响范围和解决方案
   ↓  
3. 临时配置 → 创建Snapshot Bundle解决紧急问题
   ↓
4. 验证测试 → 在测试环境快速验证
   ↓
5. 紧急部署 → 直接部署到生产环境
   ↓
6. 后续完善 → 问题解决后，完善正式版本和流程
```

### 5.4 数据质量保证

#### Bundle质量检查
- **版本一致性检查**: 确保所有约束都能找到满足的版本
- **依赖关系验证**: 验证通道间的依赖关系正确
- **追溯完整性**: 确保能追溯到源Consumer配置
- **格式规范检查**: 验证Bundle文件格式符合规范

#### Consumer配置验证
- **约束合理性**: 检查版本约束是否过于严格或宽松
- **依赖完整性**: 确保所有必需的通道都有配置
- **兼容性影响**: 评估对现有生产环境的影响
- **配置一致性**: 检查latest.yaml与版本文件的一致性

### 5.5 监控与追溯

#### 版本使用监控
- **Bundle使用统计**: 监控各Bundle的使用频率和覆盖率
- **版本分布分析**: 分析生产环境中各通道版本的分布
- **异常检测**: 监控版本约束解析失败或数据缺失情况
- **性能影响**: 跟踪版本变更对系统性能的影响

#### 完整追溯链路
```
training_dataset.json → Bundle版本 → Consumer版本 → Channel规格
       ↓                    ↓           ↓           ↓
   JSONL索引文件         版本清单     需求配置     格式定义
   (data_release仓)    (DataSpecHub) (DataSpecHub) (DataSpecHub)
```

这样的设计确保了从最终数据产品到原始规格定义的完整可追溯性。

## 6. 故障排除与参考

### 6.1 常见问题解决

#### 配置相关问题

**问题1：Bundle生成时版本约束无法满足**
```
错误信息：No available versions found for channel 'object_array_fusion_infer' with constraint '>=1.5.0'
```

**解决方案**：
1. 检查channels目录下是否存在满足约束的版本文件
2. 确认版本约束是否过于严格
3. 考虑放宽版本约束或添加备选版本

```yaml
# 修改前
version: ">=1.5.0"

# 修改后  
version:
  - ">=1.5.0"      # 首选约束
  - ">=1.4.0"      # 备选约束
```

**问题2：Consumer配置文件YAML格式错误**
```
错误信息：YAML parsing error at line 15: mapping values are not allowed here
```

**解决方案**：
1. 检查YAML缩进是否正确（使用空格，不要使用制表符）
2. 确认字符串值是否正确引用
3. 验证列表格式是否正确

```yaml
# 错误格式
requirements:
- channel: image_original
  version: 1.2.0          # 缺少引号
  required true            # 缺少冒号

# 正确格式  
requirements:
  - channel: image_original
    version: "1.2.0"       # 正确引用
    required: true         # 正确格式
```

**问题3：版本约束解析结果不符合预期**
```
输入: version: "^1.2.0" 
期望: 包含1.3.0、1.4.0等
实际: 只返回1.2.x版本
```

**解决方案**：
1. 确认可用版本列表：检查channels目录下的实际版本文件
2. 理解SemVer约束规则：`^1.2.0`包含1.2.0到<2.0.0
3. 检查版本排序逻辑：确认是否按稳定性而非时间排序

#### 文件结构问题

**问题4：新通道无法被识别**
```
错误信息：Channel 'new_sensor' not found in taxonomy
```

**解决方案**：
1. 确认已在`taxonomy/channel_taxonomy.yaml`中添加新通道
2. 检查通道目录结构是否正确
3. 验证规格文件命名是否符合规范

```yaml
# 在taxonomy/channel_taxonomy.yaml中添加
categories:
  sensor_raw:
    channels:
      - new_sensor        # 添加新通道
```

**问题5：Bundle文件找不到**
```
错误信息：Bundle file 'bundles/weekly/end_to_end-v1.2.0-2025.25.yaml' not found
```

**解决方案**：
1. 检查Bundle文件命名是否符合规范
2. 确认Bundle类型目录是否正确
3. 验证Consumer版本在文件名中是否正确

### 6.2 实际配置示例详解

#### 完整的Consumer配置示例
```yaml
# consumers/end_to_end/v1.2.0.yaml
meta:
  consumer: end_to_end
  owner: "e2e-team@company.com"
  description: "端到端网络的数据通道版本需求"
  team: "端到端团队"
  version: "1.2.0"
  created_at: "2025-01-15"
  updated_at: "2025-04-10"

# 当前数据需求 - 专注于版本依赖
requirements:
  - channel: image_original
    version: "1.2.0"              # 精确版本：业务关键，需要特定功能
    required: true
    on_missing: "fail"
    
  - channel: object_array_fusion_infer
    version: ">=1.2.0"            # 范围约束：允许功能增强
    required: true
    on_missing: "fail"
    
  - channel: occupancy
    version:                      # 多版本候选：首选特定版本，备选标准版本
      - "1.0.0"
    required: true
    on_missing: "fail"
    
  - channel: utils_slam
    version: ">=1.0.0"            # 范围约束：相对稳定的工具链
    required: true
    on_missing: "fail"
    
  - channel: lidar_points
    version:                      # 复杂多版本：支持不规范命名
      - "2.1.0_5cm_optimized"     # 首选：5cm精度优化版本
      - "2.1.0_5cm"               # 备选：5cm精度标准版本
      - "2.1.0_10cm"              # 备选：10cm精度版本
      - ">=2.1.0"                 # 最后备选：任何2.1+版本
    required: false               # 可选数据：缺失不影响核心功能
    on_missing: "ignore"

# 需求变更历史 - 便于追溯演进过程
change_history:
  - date: "2025-01-15"
    version: "1.0.0"
    changes: "初始版本：image_original(1.0.0) + object_array_fusion_infer(>=1.0.0)"
    
  - date: "2025-02-20"  
    version: "1.1.0"
    changes: "添加 occupancy(1.0.0)"
    
  - date: "2025-02-27"
    version: "1.1.1"
    changes: "添加 utils_slam(>=1.0.0)"
    
  - date: "2025-04-10"
    version: "1.2.0"
    changes: "升级 image_original 到 1.2.0，添加 lidar_points 支持"
```

#### 对应的Bundle解析结果
```yaml
# bundles/weekly/end_to_end-v1.2.0-2025.25.yaml
meta:
  bundle_name: end_to_end
  consumer_version: "v1.2.0"
  bundle_version: "v1.2.0-2025.25"
  bundle_type: weekly
  created_at: "2025-06-20T14:30:00Z"
  source_consumer: "consumers/end_to_end/latest.yaml"
  description: "端到端网络数据快照 - 2025年第25周"

conversion_source:
  consumer_config: "consumers/end_to_end/latest.yaml"
  consumer_version: "v1.2.0"
  conversion_time: "2025-06-20T14:30:00Z"
  converted_by: "bundle_generator"

channels:
  - channel: image_original
    available_versions: ["1.2.0"]                    # 精确匹配
    source_constraint: "1.2.0"
    required: true
    on_missing: "fail"
    
  - channel: object_array_fusion_infer  
    available_versions: ["1.2.0"]                    # 满足>=1.2.0的最佳版本
    source_constraint: ">=1.2.0"
    required: true
    on_missing: "fail"
    
  - channel: occupancy
    available_versions: ["1.0.0"]                    # 候选列表中的版本
    source_constraint: "['1.0.0']"
    required: true
    on_missing: "fail"
    
  - channel: utils_slam
    available_versions: ["1.1.0", "1.0.0"]           # 满足>=1.0.0，按推荐度排序
    source_constraint: ">=1.0.0"
    required: true
    on_missing: "fail"
    
  - channel: lidar_points
    available_versions: ["2.1.0_5cm_optimized", "2.1.0_5cm", "2.1.0"]  # 复杂版本解析
    source_constraint: "['2.1.0_5cm_optimized', '2.1.0_5cm', '2.1.0_10cm', '>=2.1.0']"
    required: false
    on_missing: "ignore"
```

### 6.3 下游使用指南

#### 自动化系统使用模式
```python
# 推荐用法：使用第一个版本（最佳选择）
def load_data(bundle, channel_name):
    channel = find_channel(bundle, channel_name)
    primary_version = channel['available_versions'][0]
    return load_channel_data(channel_name, primary_version)
```

#### 容错处理模式
```python
# 带fallback的用法：依次尝试可用版本
def load_data_with_fallback(bundle, channel_name):
    channel = find_channel(bundle, channel_name)
    for version in channel['available_versions']:
        try:
            return load_channel_data(channel_name, version)
        except DataNotFoundError:
            continue
    raise DataNotFoundError(f"No available version for {channel_name}")
```

#### 版本选择策略
```python
# 手动版本选择：根据策略选择合适版本
def select_version(bundle, channel_name, strategy="recommended"):
    channel = find_channel(bundle, channel_name)
    versions = channel['available_versions']
    
    if strategy == "recommended":
        return versions[0]  # 第一个版本（系统推荐）
    elif strategy == "latest":
        return max(versions, key=parse_version)  # 语义上最新的版本
    elif strategy == "stable":
        return versions[0]  # 当前约定第一个是最稳定的
```

### 6.4 版本约束快速参考

#### SemVer约束语法速查表

| 约束表达式 | 匹配版本 | 使用场景 | 风险等级 |
|-----------|----------|----------|----------|
| `"1.2.0"` | 仅1.2.0 | 生产环境，严格要求 | 低 |
| `"~1.2.0"` | 1.2.x | 生产环境，允许补丁 | 低 |
| `"^1.2.0"` | 1.x.x (但<2.0.0) | 开发环境，功能兼容 | 中 |
| `">=1.2.0"` | 1.2.0及以上所有版本 | 实验环境，追求新功能 | 高 |
| `">1.2.0"` | 大于1.2.0的所有版本 | 特殊需求，排除特定版本 | 高 |
| `"*"` | 任何版本 | 开发测试，版本无关 | 高 |

*详细的版本约束语法说明和处理逻辑请参见第3.3节和第3.5节。*

#### 环境推荐约束策略

| 环境 | 推荐约束 | 说明 |
|------|---------|------|
| 生产环境 | `"~1.2.0"` | 只允许补丁更新 |
| 开发环境 | `"^1.2.0"` | 允许小版本更新 |
| 实验环境 | `">=1.2.0"` | 允许任何新版本 |

### 6.5 联系与支持

#### 技术支持
- **配置问题**: 数据平台团队 data-platform@company.com
- **版本兼容性**: 数据治理团队 data-governance@company.com  
- **紧急问题**: 通过企业IM联系相关FO或数据SE

#### 相关资源
- **DataSpecHub仓库**: 本仓库，包含所有规格和配置
- **data_release仓库**: 最终数据交付物管理
- **兼容性矩阵**: `compatibility/consumer_matrix.yaml`
- **通道分类**: `taxonomy/channel_taxonomy.yaml`

#### 最佳实践检查清单

**配置新Consumer时**：
- [ ] 版本约束是否合理（不过严不过松）
- [ ] 必需性设置是否正确（required字段）
- [ ] 缺失处理策略是否适当（on_missing字段）
- [ ] 变更历史是否记录完整（change_history字段）
- [ ] latest.yaml是否正确指向

**Bundle使用时**：
- [ ] Bundle类型是否适合使用场景
- [ ] 版本清单是否满足需求
- [ ] 追溯信息是否完整
- [ ] 运行时配置是否正确传递

**版本升级时**：
- [ ] 影响分析是否充分
- [ ] 兼容性测试是否完成
- [ ] 分阶段部署是否规划
- [ ] 回滚方案是否准备

这份完整指南涵盖了DataSpecHub的所有核心概念、配置方法、使用场景和故障排除，为使用者提供了从入门到精通的完整参考。

