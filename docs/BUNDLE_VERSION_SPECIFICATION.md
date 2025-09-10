# Bundle版本规范说明文档

## 概述
本文档定义了DataSpecHub中Bundle文件的版本管理规范，包括语义化版本控制(SemVer)原则、Bundle类型说明以及版本字段的标准含义。

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
    
  - channel: object_array_fusion_infer  
    version: ">=1.2.0"         # 范围约束
    
  - channel: utils_slam
    version: "~1.0.0"          # 补丁级兼容
    on_missing: "substitute"   # 支持替代策略
    substitute_with:
      channel: utils_slam
      version: ">=1.0.0"
      
  - channel: occupancy
    version: ">=1.0.0"         # 范围约束，允许1.0.0+
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
    available_versions: ["1.2.0"]                    # 满足>=1.2.0的版本
    source_constraint: ">=1.2.0"
    
  - channel: utils_slam
    available_versions: ["1.0.5", "1.0.2", "1.0.0"] # 满足~1.0.0，按推荐度排序
    source_constraint: "~1.0.0"
    
  - channel: occupancy
    available_versions: ["1.0.0"]                    # 满足>=1.0.0的版本
    source_constraint: ">=1.0.0"
```

## 版本约束解析规则

### 约束类型处理

假设系统中可用版本为：`[2.1.0, 1.5.1, 1.5.0, 1.4.0, 1.3.0, 1.2.8, 1.2.0, 1.1.9]`

| Consumer约束 | Bundle解析结果 | 使用场景 |
|-------------|---------------|----------|
| `"1.2.0"` | `["1.2.0"]` | 精确版本，严格要求 |
| `">=1.3.0"` | `["2.1.0", "1.5.1", "1.5.0", "1.4.0", "1.3.0"]` | 最低版本要求，无上限 |
| `"~1.2.0"` | `["1.2.8", "1.2.0"]` | 保守策略，只允许补丁更新 |
| `"^1.2.0"` | `["1.5.1", "1.5.0", "1.4.0", "1.3.0", "1.2.8", "1.2.0"]` | 兼容更新，但排除2.x版本 |
| `"*"` | `["2.1.0", "1.5.1", "1.5.0", "1.4.0", "1.3.0", "1.2.8", "1.2.0", "1.1.9"]` | 任何版本，追求最新 |

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

### Substitute策略处理
当Consumer配置了substitute策略时，Bundle中的`available_versions`包含：
1. **主要版本**: 满足原始约束的版本
2. **替代版本**: 满足substitute约束的版本（如果与主要版本不同）

