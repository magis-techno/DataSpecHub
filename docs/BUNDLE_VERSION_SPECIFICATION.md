# Bundle版本规范说明文档

## 概述
本文档定义了DataSpecHub中Bundle文件和Consumer配置的版本管理规范，包括语义化版本控制(SemVer)原则、Bundle类型说明、Consumer版本约束语法以及版本字段的标准含义。

## 语义化版本控制(SemVer)基础

### 版本格式
采用 `MAJOR.MINOR.PATCH` 三位版本号格式，遵循SemVer标准。

### 版本约束表达式
- `1.2.0`: 精确版本匹配
- `>=1.2.0`: 大于等于1.2.0的任何版本
- `>1.2.0`: 大于1.2.0（不包含1.2.0本身）
- `^1.2.0`: 兼容1.2.0但小于2.0.0（允许MINOR和PATCH更新）
- `~1.2.0`: 兼容1.2.0但小于1.3.0（只允许PATCH更新）
- `*`: 任何版本（最新优先）

## Bundle类型说明

### Weekly Bundle (周度Bundle)
- **用途**: 定期训练和开发环境使用
- **生成频率**: 每周生成
- **命名格式**: `{consumer}-{version}-{年}.{周数}`
- **示例**: `end_to_end-v1.2.0-2025.25`
- **特点**: 基于稳定版本，适合常规开发工作

### Release Bundle (发布Bundle)  
- **用途**: 生产环境和重要里程碑发布
- **生成时机**: 重大版本发布时
- **命名格式**: `{consumer}-{version}-release`
- **示例**: `pv_trafficlight-v1.1.0-release`
- **特点**: 经过充分测试，版本固定，用于生产部署

### Snapshot Bundle (快照Bundle)
- **用途**: 特定时间点的数据快照
- **生成时机**: 重要实验或数据备份需要
- **命名格式**: `{consumer}-{version}-{YYYYMMDD}-{HHMMSS}`
- **示例**: `foundational_model-v1.0.0-20250620-143500`
- **特点**: 精确时间标记，用于实验复现和数据审计

## 核心概念

### Consumer Version vs Bundle Version

#### Consumer Version
- **定义**: 消费者组件的功能版本标识
- **格式**: SemVer格式，如 `v1.2.0`
- **含义**: 标识消费者的功能迭代和兼容性要求
- **示例**: `v1.2.0` 表示端到端网络的第1.2.0功能版本

#### Bundle Version  
- **定义**: Bundle数据快照的唯一标识符
- **格式**: 根据Bundle类型确定具体格式
- **含义**: 将Consumer的版本约束转换为具体可用数据版本的快照
- **示例**: `v1.2.0-2025.25` 表示基于Consumer v1.2.0需求在2025年第25周的数据快照

### Bundle唯一标识
每个Bundle由 `bundle_name` + `bundle_version` 唯一确定：
- **bundle_name**: 对应Consumer名称，如 `end_to_end`
- **bundle_version**: 根据Bundle类型生成的版本标识，如 `v1.2.0-2025.25`
- **文件路径**: `bundles/{type}/{bundle_name}-{bundle_version}.yaml`

### 版本转换关系
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

## Bundle文件字段规范

### Meta字段
```yaml
meta:
  bundle_name: end_to_end              # Bundle名称（对应Consumer名称）
  consumer_version: "v1.2.0"          # 源Consumer的版本
  bundle_version: "v1.2.0-2025.25"    # Bundle快照版本
  bundle_type: weekly                  # Bundle类型
  created_at: "2025-06-20T14:30:00Z"  # 创建时间
  source_consumer: "consumers/end_to_end/latest.yaml"  # 源Consumer文件路径
  description: "端到端网络数据快照 - 2025年第25周"
```

### 版本转换追踪
```yaml
conversion_source:
  consumer_config: "consumers/end_to_end/latest.yaml"  # 源配置文件
  consumer_version: "v1.2.0"                          # Consumer版本
  conversion_time: "2025-06-20T14:30:00Z"            # 转换时间
  converted_by: "bundle_generator"                     # 转换工具
```

### 通道版本规范

#### 字段定义
```yaml
channels:
  - channel: object_array_fusion_infer
    available_versions: ["1.2.0", "1.1.0"]  # 按推荐度排序的版本列表
    source_constraint: ">=1.2.0"            # 来自Consumer的原始约束
```

#### 字段含义详解

| 字段 | 含义 | 示例 | 使用规则 |
|------|------|------|----------|
| `channel` | 通道名称 | `object_array_fusion_infer` | 对应channels目录下的通道 |
| `available_versions` | 可用版本列表 | `["1.2.0", "1.1.0"]` | 按推荐度排序，第一个为最佳选择 |
| `source_constraint` | 原始约束 | `">=1.2.0"` | 来自Consumer配置，用于审计 |

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

## 下游使用指南

### 自动化系统使用
```python
# 推荐用法：使用第一个版本
def load_data(bundle, channel_name):
    channel = find_channel(bundle, channel_name)
    primary_version = channel['available_versions'][0]
    return load_channel_data(channel_name, primary_version)
```

### 容错处理
```python
# 带fallback的用法
def load_data_with_fallback(bundle, channel_name):
    channel = find_channel(bundle, channel_name)
    for version in channel['available_versions']:
        try:
            return load_channel_data(channel_name, version)
        except DataNotFoundError:
            continue
    raise DataNotFoundError(f"No available version for {channel_name}")
```

### 版本选择逻辑
```python
# 手动版本选择
def select_version(bundle, channel_name, strategy="recommended"):
    channel = find_channel(bundle, channel_name)
    versions = channel['available_versions']
    
    if strategy == "recommended":
        return versions[0]  # 第一个版本
    elif strategy == "latest":
        return max(versions, key=parse_version)  # 语义上最新的版本
    elif strategy == "stable":
        return versions[0]  # 当前约定第一个是最稳定的
```

## 实际示例

### Consumer配置示例
```yaml
# consumers/end_to_end/v1.2.0.yaml
requirements:
  - channel: image_original
    version: "1.2.0"           # 精确版本要求
    required: true
    on_missing: "fail"
    
  - channel: object_array_fusion_infer  
    version:                   # 多版本候选
      - "1.2.0_optimized"      # 首选优化版本
      - ">=1.2.0"              # 备选范围约束
    required: true
    on_missing: "fail"
    
  - channel: utils_slam
    version: "~1.0.0"          # 补丁级兼容
    required: true
    on_missing: "fail"
      
  - channel: occupancy
    version: ">=1.0.0"         # 范围约束，允许1.0.0+
    required: false            # 可选数据
    on_missing: "ignore"
```

### 对应Bundle快照
```yaml
# bundles/weekly/end_to_end-v1.2.0-2025.25.yaml
# Bundle唯一标识: bundle_name="end_to_end" + bundle_version="v1.2.0-2025.25"

meta:
  bundle_name: end_to_end
  bundle_version: "v1.2.0-2025.25"
  
channels:
  - channel: image_original
    available_versions: ["1.2.0"]                    # 精确匹配
    source_constraint: "1.2.0"
    
  - channel: object_array_fusion_infer  
    available_versions: ["1.2.0_optimized", "1.2.0"] # 首选优化版本 + 备选版本
    source_constraint: "['1.2.0_optimized', '>=1.2.0']"
    
  - channel: utils_slam
    available_versions: ["1.0.5", "1.0.2", "1.0.0"] # 满足~1.0.0，按推荐度排序
    source_constraint: "~1.0.0"
    
  - channel: occupancy
    available_versions: ["1.0.0"]                    # 满足>=1.0.0的版本
    source_constraint: ">=1.0.0"
```

## 版本约束解析规则

### 约束类型处理

假设系统中可用版本为：`[2.1.0, 1.5.1, 1.5.0, 1.4.0_opt, 1.3.0, 1.2.8, 1.2.0, 1.1.9]`

| Consumer约束 | Bundle解析结果 | 使用场景 |
|-------------|---------------|----------|
| `"1.2.0"` | `["1.2.0"]` | 精确版本，严格要求 |
| `">=1.3.0"` | `["2.1.0", "1.5.1", "1.5.0", "1.4.0_opt", "1.3.0"]` | 最低版本要求，无上限 |
| `"~1.2.0"` | `["1.2.8", "1.2.0"]` | 保守策略，只允许补丁更新 |
| `"^1.2.0"` | `["1.5.1", "1.5.0", "1.4.0_opt", "1.3.0", "1.2.8", "1.2.0"]` | 兼容更新，但排除2.x版本 |
| `["1.4.0_opt", ">=1.3.0"]` | `["1.4.0_opt", "2.1.0", "1.5.1", "1.5.0", "1.3.0"]` | 首选特定版本+备选范围 |
| `"*"` | `["2.1.0", "1.5.1", "1.5.0", "1.4.0_opt", "1.3.0", "1.2.8", "1.2.0", "1.1.9"]` | 任何版本，追求最新 |

### 关键约束区别

**`^1.2.0` vs `>=1.2.0` 的重要区别**：
- `^1.2.0`: 允许 `1.2.0` 到 `1.x.x`，但**排除 `2.0.0`** (兼容性边界)
- `>=1.2.0`: 允许 `1.2.0` 及以上**任何版本**，包括 `2.0.0`, `3.0.0` 等

在上面例子中：
- `^1.2.0` 结果**不包含** `2.1.0`
- `>=1.3.0` 结果**包含** `2.1.0`

### 常见使用建议

| 场景 | 推荐约束 | 说明 |
|------|---------|------|
| 生产环境 | `"~1.2.0"` | 稳定性优先，只接受补丁更新 |
| 开发环境 | `"^1.2.0"` | 功能更新，但避免破坏性变更 |
| 实验环境 | `">=1.2.0"` | 允许任何新版本，包括破坏性更新 |
| 特定功能依赖 | `">=1.3.0"` | 需要特定版本的新功能 |

## Consumer版本管理规范

### Consumer版本结构

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

### Consumer配置文件规范

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

### 版本约束语法

#### 支持的格式
- **单版本**: `version: "1.2.0"` 或 `version: ">=1.2.0"`
- **版本列表**: `version: ["1.2.0_opt", "1.2.0", ">=1.1.0"]`
- **混合约束**: 列表中可以包含精确版本和SemVer约束

#### 处理逻辑
1. **单版本**: 按标准SemVer约束解析
2. **版本列表**: 按优先级顺序查找可用版本
   - 精确版本: 直接匹配
   - SemVer约束: 解析后合并到结果中

### 运行时配置字段

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

**特殊用法**：
```yaml
- channel: debug_info
  required: false
  on_missing: "fail"    # 非核心但需要完整性验证
```

### Bundle中的运行时配置

Bundle文件包含完整的运行时配置信息，使数据获取系统能够正确处理数据缺失情况：

```yaml
channels:
  - channel: image_original
    available_versions: ["1.2.0", "1.1.0", "1.0.0"]
    source_constraint: ">=1.0.0"
    required: true          # 从Consumer配置继承
    on_missing: "fail"      # 从Consumer配置继承
    
  - channel: occupancy
    available_versions: ["1.0.0"]
    source_constraint: "1.0.0"
    required: false         # 从Consumer配置继承
    on_missing: "ignore"    # 从Consumer配置继承
```

这样设计的优势：
- **自包含**：Bundle包含运行时所需的所有信息
- **一致性**：确保版本选择与运行时行为保持一致
- **简化部署**：无需回溯到Consumer配置文件

### Consumer版本约束在Bundle中的体现

Consumer中的版本约束经过Bundle生成器解析后，转换为具体的版本列表：

```yaml
# Consumer约束
requirements:
  - channel: lidar_data
    version:
      - "2.1.0_5cm"              # 首选非标准版本
      - "2.1.0"                  # 标准备选版本
      - ">=2.0.0"                # SemVer备选范围

# Bundle解析结果
channels:
  - channel: lidar_data
    available_versions: ["2.1.0_5cm", "2.1.0", "2.0.5"]  # 实际可用版本
    source_constraint: "['2.1.0_5cm', '2.1.0', '>=2.0.0']"  # 原始约束记录
    required: true                                        # 是否必需
    on_missing: "fail"                                    # 缺失处理策略
```

