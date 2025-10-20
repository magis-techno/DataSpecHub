# 训练数据集管理 Wiki

作者：

## 概述

本文档定义了训练数据集发布后的版本管理和操作追踪规范，用于管理数据策划过程中的清洗、新增、调平等操作。

## 背景

1. **DataSpecHub仓库**：定义数据规格和通道需求（设计阶段）
2. **生产发布**：基于规格生产并发布数据到训练仓库
3. **训练仓库**：包含训练数据集索引文件，支持常规训练和DAgger训练
4. **数据策划**：基于索引文件进行清洗、新增、调平等操作，支持混合版本数据挖掘

## 目录结构

```
training_repo/
├── training_dataset.json           # 常规训练数据集索引（由 Tag/Release 所在 commit 固化）
└── training_dataset.dagger.json    # DAgger训练专用数据集索引（特殊处理，避免误加载）
```

## 多任务训练支持

本仓库支持多任务训练场景（如GOD检测+可行驶域分割），通过在数据集配置中添加 **任务标签（task_tags）** 实现：

- 在数据集中标记适用的任务类型，训练时可按需过滤
- 同一数据集可服务多个任务，通过 `task_tags` 声明支持的任务
- 不同任务类型可维护独立的分支进行管理（可选）

**支持的任务类型**：
- `multi_task`: 多任务联合训练（GOD+可行驶域）
- `god_base`: GOD基础训练（20cm分辨率）
- `god_hd`: GOD高精训练（5cm分辨率）
- `drivable_2cls`: 可行驶域2分类
- `drivable_multi`: 可行驶域多分类（园区场景）

## 文件格式规范

### 1. training_dataset.json (常规训练数据)

```json
{
    "meta": {
        "release_name": "JointTrain_20250727",
        "consumer_version": "v1.2.0",
        "bundle_versions": ["v1.2.0-20250620-143500"],
        "created_at": "2025-07-27 15:00:00",
        "description": "端到端网络联合训练数据集",
        "version": "v1.2.0",
        "tasks": ["god_base", "drivable_2cls"]
    },
    "dataset_index": [
        {
            "name": "enter_waiting_red2green_494",
            "obs_path": "obs://yw-ads-training-gy1/data/ide/cleantask/cc8c7fed-a3ea-438d-8650-2436001b0ae3/waiting_area/golden0520_pkl7.8_enter_waiting_red2green_clip_494_frame_25252.jsonl.shrink",
            "bundle_versions": ["v1.2.0-20250620-143500"],
            "duplicate": 8,
            "task_tags": ["god_base", "drivable_2cls"]
        },
        {
            "name": "highway_merge_mixed_dataset",
            "obs_path": "obs://training-data/highway_merge_mixed.jsonl",
            "bundle_versions": ["v1.1.0-20250618", "v1.2.0-20250620"],
            "duplicate": 3,
            "task_tags": ["god_base"]
        }
    ]
}
```

### 2. training_dataset.dagger.json (DAgger训练专用)

```json
{
    "meta": {
        "release_name": "DAgger_OnlineTraining_20250727", 
        "consumer_version": "v1.2.0",
        "bundle_versions": ["v1.2.0-20250620-143500"],
        "created_at": "2025-07-27 15:00:00",
        "description": "DAgger在线训练专用数据集",
        "version": "v1.2.0",
        "training_type": "dagger"
    },
    "dataset_index": [
        {
            "name": "dagger_correction_scenarios_001",
            "obs_path": "obs://dagger-data/correction_scenarios.jsonl",
            "bundle_versions": ["v1.2.0-20250620-143500"],
            "duplicate": 1,
        }
    ]
}
```

#### 字段说明

**Meta字段：**
- **release_name**: 训练数据集的发布名称
- **consumer_version**: 对应的Consumer版本，格式：`v{major}.{minor}.{patch}`
- **bundle_versions**: 对应的Bundle版本列表，支持混合版本，格式：`["v{version}-{timestamp}"]`
- **version**: 当前训练数据集版本，语义化版本格式
- **training_type**: 训练类型，dagger文件专用，标识为"dagger"
- **tasks**: （可选）训练任务列表，用于说明该数据集包含的任务类型，如 `["god_base", "drivable_2cls"]`

**Dataset字段：**
- **name**: 数据集唯一名称（IDE生成或手工命名，确保唯一性）
- **obs_path**: 数据集存储路径（生产前为空，生产后回写）
- **bundle_versions**: 数据集来源的Bundle版本列表，支持混合版本场景
- **duplicate**: 数据复制倍数
- **task_tags**: （可选）该数据集适用的任务标签列表，用于多任务训练时的数据过滤，如 `["god_base"]` 或 `["god_base", "drivable_2cls"]`

#### 使用场景

**混合版本场景：** 数据挖掘时从多个Bundle版本中提取数据，形成新的数据集
**DAgger训练：** 在线学习需要特殊数据处理，使用独立的dagger文件避免误加载
**配置生产：** training_dataset.json既作为数据生产的配置输入，也作为生产结果的索引记录
**多任务训练：** 使用 `task_tags` 字段标记数据集适用的任务类型，训练时可按任务过滤数据集

#### 多任务训练示例

对于支持多任务（如GOD检测和可行驶域分割）的训练场景：

```json
{
    "meta": {
        "release_name": "GOD_MultiTask_20251017",
        "consumer_version": "v1.2.0",
        "bundle_versions": ["v1.2.0-20251017-100000"],
        "version": "v1.2.0",
        "tasks": ["god_base", "drivable_2cls"]
    },
    "dataset_index": [
        {
            "name": "highway_god_only",
            "obs_path": "obs://god-data/highway_god.jsonl",
            "bundle_versions": ["v1.2.0-20251017-100000"],
            "duplicate": 5,
            "task_tags": ["god_base"]
        },
        {
            "name": "highway_drivable_only",
            "obs_path": "obs://dri-data/highway_drivable.jsonl",
            "bundle_versions": ["v1.2.0-20251017-100000"],
            "duplicate": 5,
            "task_tags": ["drivable_2cls"]
        },
        {
            "name": "urban_joint_annotated",
            "obs_path": "obs://multi-task/urban_joint.jsonl",
            "bundle_versions": ["v1.2.0-20251017-100000"],
            "duplicate": 3,
            "task_tags": ["god_base", "drivable_2cls"]
        }
    ]
}
```

**训练时按任务过滤：**
- 多任务训练：使用所有数据集（task_tags包含 "god_base" 或 "drivable_2cls" 的数据）
- 单任务训练（仅GOD）：只加载 task_tags 包含 "god_base" 的数据集
- 单任务训练（仅可行驶域）：只加载 task_tags 包含 "drivable_2cls" 的数据集

**常用任务标签：**

| 任务标签 | 说明 |
|---------|------|
| `multi_task` | 多任务联合训练（GOD+可行驶域） |
| `god_base` | GOD基础训练（20cm分辨率） |
| `god_hd` | GOD高精训练（5cm分辨率） |
| `drivable_2cls` | 可行驶域2分类（通用场景） |
| `drivable_multi` | 可行驶域多分类（园区场景） |

### 3. 配置文件生产流程

training_dataset.json具有**双重用途**：既是生产配置输入，也是生产结果记录。

#### 配置阶段（生产输入）
```json
{
    "meta": {
        "release_name": "DataMining_Mixed_20250727",
        "consumer_version": "v1.2.0", 
        "bundle_versions": ["v1.1.0-20250618", "v1.2.0-20250620"],
        "version": "v1.2.0",
        "status": "pending"
    },
    "dataset_index": [
        {
            "name": "highway_merge_mixed_dataset",
            "obs_path": "",  // 空路径，等待生产
            "bundle_versions": ["v1.1.0-20250618"],
            "duplicate": 3
        }
    ]
}
```

#### 生产过程
1. **解析配置**：生产系统读取配置文件，识别`obs_path`为空的待生产数据集
2. **混合版本处理**：根据dataset级别的`bundle_versions`从多个Bundle中获取数据
3. **数据挖掘/合并**：调用外部工具进行数据处理（挖掘过程不纳管）
4. **生成数据**：产出最终的JSONL文件到OBS


### 2. 提交信息模板（以 Git Commit 追踪变更）

使用结构化 Commit Message 作为唯一变更记录载体：

```yaml
date: "2025-07-28"
type: "modify(clean)"   # add | modify(clean) | modify(balance)
description: "对大数据集进行整体清洗"
task_tag: ""     # 任务单/工单编号；手动操作留空
details:          # 可选，按需补充
  dataset: "mega_driving_dataset_v2"
  total_clips_before: 500000
  clips_removed: 50000
  clips_after: 450000
  # 可选更多明细字段
```

#### 类型枚举（用于 Commit 的 `type` 字段）

- **add**: 新增数据集或 clips
- **modify(clean)**: 清洗类修改（去重、质量过滤、整体清洗等）
- **modify(balance)**: 平衡类修改（调整场景/类别分布等）

#### 动作类型

- **add**: 新增数据集或 clips
- **modify(clean)**: 清洗类修改（去重、质量过滤、整体清洗等）
- **modify(balance)**: 平衡类修改（调整场景/类别分布等）

<!-- 预留“删除详情格式”章节，当前按需再启用 -->

### 4. 快照说明

以 Tag/Release 固化的 commit 即为快照，快照内容即该 commit 下的 `training_dataset.json`。

## 操作流程

### 基本操作步骤

1. **执行数据操作**（清洗、新增、调平等）
2. **更新结果文件**：更新 `training_dataset.json`
3. **提交变更**：使用结构化 Commit Message（见“提交信息模板”）
4. **固化版本**：专题交付打 Tag；大版本创建 Release



## 分支、Tag 与 Release 策略

### 交付物定义
- 唯一交付物：某个代码仓的特定分支上的特定 commit（通过 Tag 固化）。
- 大版本发布：在关键 Tag 基础上创建 Release（Release 是 Tag 的子集，面向对外/对内广泛消费的稳定版本）。

### 分支命名规范
- **功能分支**：`feature_dataset/<topic>/<method>`
  - 示例：`feature_dataset/toll_station/strict`
  - 用于数据集功能开发和数据策划操作
  
- **实验分支**：`experiment/<topic>/<trial>`
  - 示例：`experiment/toll_station/ablation-01`
  - 用于快速实验验证
  
- **主分支**：`master` 或 `main`
  - 稳定生产版本，仅通过PR合并
  
- 任意分支（含 `master` 与 `feature_dataset/*`）均可直接在 IDE 中进行编辑与验证。

### Tag 规范
- **专题数据交付**：仅打 Tag，不必创建 Release
  - 命名：`feature_dataset/<topic>/release-YYYYMMDD`
  - 示例：`feature_dataset/toll_station/release-20250709`
  - 可选别名：`<topic>-<YYMMDD>`（便于人读）
  
- **Tag注释**：建议包含追溯元信息
  ```yaml
  release_name: "feature_dataset/toll_station/release-20250709"
  consumer_version: "v1.2.0"
  bundle_version: "v1.2.0-20250620-143500"
  training_dataset_version: "v1.2.0"
  ```

#### 多任务场景的Tag命名（可选）
针对多任务场景，Tag可包含任务类型前缀：
- `<task_type>/release-YYYYMMDD` - 示例：`multi_task/release-20251017`
- `<task_type>/v<MAJOR>.<MINOR>.<PATCH>` - 示例：`god_base/v1.1.0`
- Tag注释可增加 `task_type` 和 `tasks` 字段说明任务类型

### Release 规范（大版本）
- **创建时机**：面向广泛消费、需要稳定性的里程碑版本（例如 `v1.2.0`）
- **与Tag关系**：Release 指向某个已存在的 Tag
- **命名建议**：
  - Release名称：`TrainingDataset v<MAJOR>.<MINOR>.<PATCH>`
  - 示例：`TrainingDataset v1.2.0`
  - 对应Tag：`training/v<MAJOR>.<MINOR>.<PATCH>` 或具体业务自定义命名

- **Release说明应包含**：
  - 基线来源：`consumer_version`、`bundle_version`
  - 数据规模与要点：clips统计、关键操作摘要
  - 追溯信息：Tag/Release注释 + commit hash

#### 多任务场景的Release（可选）
针对多任务场景，Release可包含任务类型：
- **命名格式**：`<TaskType> v<MAJOR>.<MINOR>.<PATCH>`
  - 示例：`MultiTask v1.2.0`、`GOD-Base v1.1.0`
  - 对应Tag：`<task_type>/v<MAJOR>.<MINOR>.<PATCH>`

- **Release说明增加**：
  - 任务类型：`task_type` 和包含的 `tasks` 列表
  - 各任务数据分布统计

### 提交信息规范（强制）
- 所有对数据的有效变更必须体现在 `training_dataset.json`；提交时使用结构化 Commit Message。
- Commit message 建议使用结构化正文：
  ```yaml
  date: "2025-07-28"
  type: "modify(clean)"   # add | modify(clean) | modify(balance)
  description: "对大数据集进行整体清洗"
  task_tag: ""     # 任务单/工单编号；手动操作留空
  ```

### 场景与操作
- **场景1（常规演进）**：在 `master` 或 `feature_dataset/*` 分支编辑，按需打 Tag；里程碑版本创建 Release
- **场景2（golden 上做单点实验）**：从 golden 拉 `experiment/<topic>/<trial>`，对专题分支变更做 cherry-pick；实验 Tag 仅内部可见，不创建 Release

#### 多任务场景补充（可选）
针对多任务训练，可采用任务特定分支：
- 在 `master/<task_type>` 分支维护不同任务的数据集
- 使用 `task_tags` 标记数据集的任务归属
- 按需创建任务特定的Tag和Release（如 `multi_task/v1.2.0`）

### 长期规划
- 通过 IDE/自动化纳管上述操作，校验提交模板、自动生成快照与统计，并辅助创建 Tag/Release。



## 与DataSpecHub集成

### 版本对应关系

```
DataSpecHub Consumer版本 → Bundle版本 → Training Dataset版本
foundational_model/v1.0.0.yaml → foundational_model-v1.0.0-20250620-143500.yaml → JointTrain_20250727-v1.2.0
```

**说明**：
- Consumer版本：在DataSpecHub中定义，如 `version: "1.0.0"`
- Bundle版本：引用Consumer时加v前缀，如 `consumer_version: "v1.0.0"`，Bundle自身版本为 `bundle_versions: ["v1.0.0-20250620-143500"]`
- Training Dataset版本：基于Bundle进一步数据策划后的版本，支持混合多个Bundle版本

### 追溯链路

通过 `consumer_version` 和 `bundle_versions` 数组可以追溯到DataSpecHub中的具体配置文件，实现完整的数据血缘关系。混合版本场景下，可追溯到多个Bundle版本的来源。