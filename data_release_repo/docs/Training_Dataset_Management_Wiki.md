# 训练数据集管理 Wiki

## 概述

本文档定义了训练数据集发布后的版本管理和操作追踪规范，用于管理数据策划过程中的清洗、新增、调平等操作。

## 背景

1. **DataSpecHub仓库**：定义数据规格和通道需求（设计阶段）
2. **生产发布**：基于规格生产并发布数据到训练仓库
3. **训练仓库**：包含 `training_dataset.json`（发布产物的索引）
4. **数据策划**：在 `training_dataset.json` 基础上进行清洗、新增、调平等操作

## 目录结构

```
training_repo/
├── training_dataset.json           # 当前最终结果
└── dataset_history/                 # 变更历史目录
    ├── changes.yaml                # 主变更记录
    ├── removed_clips/              # 删除条目跟踪
    │   ├── op_001_enter_waiting_removed.txt
    │   └── op_002_simple_navigation_removed.txt
    └── snapshots/                  # 关键版本备份
        ├── baseline_v1.0.0.json
        └── final_v1.2.0.json
```

## 文件格式规范

### 1. training_dataset.json (主文件)

```json
{
    "meta": {
        "release_name": "JointTrain_20250727",
        "consumer_version": "v1.2.0",
        "bundle_version": "v1.2.0-20250620-143500",
        "created_at": "2025-07-27 15:00:00",
        "description": "端到端网络联合训练数据集",
        "version": "v1.2.0"
    },
    "dataset_index": [
        {
            "name": "enter_waiting_red2green_494",
            "obs_path": "obs://yw-ads-training-gy1/data/ide/cleantask/cc8c7fed-a3ea-438d-8650-2436001b0ae3/waiting_area/golden0520_pkl7.8_enter_waiting_red2green_clip_494_frame_25252.jsonl.shrink",
            "duplicate": 8
        },
        {
            "name": "simple_合理博弈导航换道_18873",
            "obs_path": "obs://yw-ads-training-gy1/data/ide/cleantask/cc8c7fed-a3ea-438d-8650-2436001b0ae3/clip/simple_合理博弈导航换道_18873.jsonl.shrink",
            "duplicate": 3
        },
        {
            "name": "highway_behavior_dataset",
            "obs_path": "obs://external-data/highway_behavior.jsonl",
            "duplicate": 2
        }
    ]
}
```

#### 字段说明

- **release_name**: 训练数据集的发布名称
- **consumer_version**: 对应的Consumer版本，格式：`v{major}.{minor}.{patch}`
- **bundle_version**: 对应的Bundle版本，格式：`v{version}-{timestamp}`
- **version**: 当前训练数据集版本，语义化版本格式

### 2. changes.yaml (变更记录)

```yaml
# 变更记录 - 每个操作有独立key
meta:
  current_version: "v1.2.0"
  last_updated: "2025-07-27"
  base_consumer: "v1.2.0"
  base_bundle: "v1.2.0-20250620-143500"

operations:
  op_001:
    date: "2025-07-25"
    type: "cleaning"
    operator: "张三"
    version_change: "v1.0.0 → v1.1.0"
    description: "去重和质量过滤"
    datasets:
      - name: "enter_waiting_red2green_494"
        action: "remove"
        clips_removed: 2072
        clips_before: 25252
        clips_after: 23180
        removed_clips_file: "removed_clips/op_001_enter_waiting_removed.txt"
      - name: "simple_合理博弈导航换道_18873"
        action: "remove"
        clips_removed: 2
        clips_before: 18873
        clips_after: 18871
        removed_clips_file: "removed_clips/op_001_simple_navigation_removed.txt"

  op_002:
    date: "2025-07-26"
    type: "mining"
    operator: "李四"
    version_change: "v1.1.0 → v1.2.0"
    description: "合入外部高速公路数据"
    datasets:
      - name: "highway_behavior_dataset"
        action: "add"
        source_path: "obs://external-data/highway_behavior.jsonl"
        clips_added: 8500
        duplicate: 2
        total_training_clips: 17000

  op_003:
    date: "2025-07-27"
    type: "balancing"
    operator: "王五"
    version_change: "v1.2.0 (内部调整)"
    description: "调整场景分布平衡"
    datasets:
      - name: "simple_合理博弈导航换道_18873"
        action: "remove"
        clips_removed: 426
        clips_before: 18871
        clips_after: 18445
        removed_clips_file: "removed_clips/op_003_simple_navigation_removed.txt"
        reason: "场景过多，调整平衡"

  op_004:
    date: "2025-07-28"
    type: "cleaning"
    operator: "赵六"
    version_change: "v1.2.0 → v1.2.1"
    description: "对大数据集进行整体清洗"
    git_commit: "a1b2c3d"  # 引用Git commit（如涉及数据集级变更）
    datasets:
      - name: "mega_driving_dataset_v2"
        action: "clean_dataset"
        total_clips_before: 500000
        clips_removed: 50000
        clips_after: 450000
        removed_clips_file: "removed_clips/op_004_mega_dataset_removed.txt"
        reason: "大规模质量过滤和去重"

  op_005:
    date: "2025-07-29"
    type: "dataset_add"
    operator: "孙七"
    version_change: "v1.2.1 → v1.3.0"
    description: "新增外部合作伙伴数据集"
    git_commit: "b2c3d4e"  # Git commit记录数据集级变更
    datasets:
      - name: "partner_weather_dataset"
        action: "add_dataset"
        source_path: "obs://partner-data/weather_scenarios.jsonl"
        clips_added: 25000
        duplicate: 1
```

#### 操作类型

- **cleaning**: 数据清洗（去重、质量过滤、大数据集清洗）
- **mining**: 数据挖掘（新增外部数据集）
- **balancing**: 数据平衡（调整场景分布）
- **filtering**: 数据过滤（移除特定条件数据）
- **dataset_add**: 新增整个数据集（可结合Git管理）
- **dataset_remove**: 删除整个数据集（可结合Git管理）

#### 动作类型

- **add**: 新增数据集或clips
- **remove**: 删除clips或数据集
- **modify**: 修改existing数据
- **add_dataset**: 新增整个数据集
- **remove_dataset**: 删除整个数据集
- **clean_dataset**: 对整个大数据集进行清洗

### 3. removed_clips 文件格式

```
# 操作: op_001 - 数据清洗
# 数据集: enter_waiting_red2green_494
# 删除时间: 2025-07-25
# 删除原因: 去重和质量过滤
# 删除数量: 2072

# 删除的clips列表 (clip token/uuid)
550e8400-e29b-41d4-a716-446655440001    # 重复: 与另一clip相似度0.98
550e8400-e29b-41d4-a716-446655440123    # 质量低: 评分0.3，时长2.1s  
550e8400-e29b-41d4-a716-446655440234    # 重复: 与另一clip相似度0.95
550e8400-e29b-41d4-a716-446655440345    # 质量低: 缺少目标物体
...
# (共2072个token)
```

### 4. snapshots 文件格式

Snapshot文件与 `training_dataset.json` 格式完全相同，只是代表不同时间点的状态。

## 操作流程

### 基本操作步骤

1. **执行数据操作**（清洗、新增、调平等）
2. **记录操作信息**：更新 `changes.yaml` 添加新操作记录
3. **记录删除详情**：如有删除操作，记录clip tokens到 `removed_clips/` 文件
4. **更新结果文件**：更新 `training_dataset.json`
5. **Git管理**：对于数据集级操作，建议结合Git commit记录
6. **创建快照**：重要版本节点创建snapshot备份



## 与DataSpecHub集成

### 版本对应关系

```
DataSpecHub Consumer版本 → Bundle版本 → Training Dataset版本
foundational_model/v1.0.0.yaml → foundational_model-v1.0.0-20250620-143500.yaml → JointTrain_20250727-v1.2.0
```

**说明**：
- Consumer版本：在DataSpecHub中定义，如 `version: "1.0.0"`
- Bundle版本：引用Consumer时加v前缀，如 `consumer_version: "v1.0.0"`，Bundle自身版本为 `bundle_version: "v1.0.0-20250620-143500"`
- Training Dataset版本：基于Bundle进一步数据策划后的版本

### 追溯链路

通过 `consumer_version` 和 `bundle_version` 可以追溯到DataSpecHub中的具体配置文件，实现完整的数据血缘关系。

## 最佳实践

### 1. 操作记录

- 每次操作必须记录在 `changes.yaml` 中
- 删除操作必须保存具体的删除列表
- 操作描述要清晰明确

### 2. 版本追溯

- 保持与上游Bundle版本的对应关系
- 重要操作节点创建snapshot备份

### 3. 数据质量

- 新增数据要进行格式和质量验证
- 清洗操作要有明确的评判标准
- 保持操作的可重现性

### 4. 协作管理

- 操作前要明确责任人
- 重要操作要进行review
- 数据集级操作建议结合Git管理



## 工具支持

### 推荐工具

- **YAML编辑**: `yq` 命令行工具
- **文件对比**: `diff` 或 `vimdiff`
- **版本管理**: `git` (可选，对整个training_repo进行版本控制)

### 自动化脚本

可以开发简单的脚本来：
- 自动生成operation ID
- 验证changes.yaml格式
- 自动创建snapshot
- 生成统计报告

## 常见问题

### Q: 删除的clips文件会很大吗？
A: 是的，但这是必要的。可以考虑压缩存储或定期归档。

### Q: 如何处理并发操作？
A: 建议串行操作，避免同时修改同一个数据集。

### Q: 大数据集清洗和普通数据集清洗有什么区别？
A: 大数据集清洗通常涉及更多clips，建议结合Git管理数据集级变更，并在changes.yaml中引用对应的commit。

### Q: 何时使用Git管理，何时使用changes.yaml？
A: 建议混合管理 - changes.yaml记录所有操作详情，Git commit记录数据集级变更，在changes.yaml中引用commit hash。 