# Data Release仓库多任务训练支持方案

**评审日期**: 2025-10-20  
**提案人**: Data Platform Team  
**评审对象**: 端到端、静态、BEV、PV感知团队

---

## 📌 Slide 1: Data Release Repo 简介

### 什么是Data Release Repo？

**定位**: 训练数据集版本管理和发布仓库

**核心交付物**: `training_dataset.json` - 训练数据集索引文件

**主要职责**:
- 管理训练数据集的版本控制和发布
- 追踪数据策划操作（清洗、新增、调平）
- 通过Git分支、Tag、Release管理数据集演进
- 支持混合版本数据挖掘和DAgger训练

### 与训练任务的关系
```
训练任务 = 训练代码commit + data_release tag
           ↓                    ↓
      code repo          training_dataset.json
                              ↓
                        JSONL索引文件
```

**上游系统**: DataSpecHub（定义数据规格和通道需求）  
**下游使用**: 训练脚本读取training_dataset.json加载数据

---

## 📌 Slide 2: 原有设计的基础假设

### 核心约束（设计初衷）

#### 1. 一一对应关系
```
1个训练任务 = 1个训练代码commit + 1个data_release tag
```

#### 2. 唯一数据集文件
```
1个tag → 1个分支commit → 1个training_dataset.json
```

#### 3. 设计优势

| 优势 | 说明 |
|------|------|
| ✅ **对应关系明确** | 训练任务与数据集一一对应，可追溯 |
| ✅ **策划动作前置** | 数据清洗、调平等操作在发布前完成 |
| ✅ **版本精确固化** | 通过tag实现数据集版本的精确固化 |
| ✅ **避免运行时拼接** | 不需要从多个分支/tag拼接数据集 |

#### 4. 版本追溯链路
```
training_dataset.json → Bundle版本 → Consumer版本 → Channel规格
    (data_release)      (DataSpecHub)  (DataSpecHub)   (DataSpecHub)
```

---

## 📌 Slide 3: 遇到的实际问题

### 场景：GOD网络训练

#### 训练目标
**最终产出**: 1个pth文件（包含多个head）

#### 训练模式多样

| 训练模式 | 数据需求 | 训练频率 | 产出 |
|---------|---------|---------|------|
| **多任务联合训练** | GOD + 可行驶域数据 | 每2周 | 产出pth |
| **单任务finetune（GOD）** | 仅GOD数据 | 随时 | 更新pth |
| **单任务finetune（可行驶域）** | 仅可行驶域数据 | 随时 | 更新pth |
| **高清训练（GOD 5cm）** | GOD高分辨率数据 | 每月 | 产出pth_hd |

### 核心矛盾

#### 如果强行放在一个分支

```
master分支的commit历史：
├── commit1: 多任务数据集（GOD+可行驶域）
├── commit2: 单任务数据集（仅GOD）
├── commit3: 多任务数据集（GOD+可行驶域）
├── commit4: 高清数据集（GOD 5cm）
└── commit5: 单任务数据集（仅可行驶域）
```

#### 问题表现

| 问题 | 具体表现 |
|------|---------|
| **数据集需求不同** | 多任务需要GOD+可行驶域，单任务只需一种 |
| **发布节奏不同** | 多任务每2周发布，单任务随时finetune |
| **分支内容混乱** | 一会多任务、一会单任务，只能靠tag区分 |
| **演进关系模糊** | tag之间不是完全的线性演进关系 |
| **数据策划复杂** | 需要在同一分支维护不同类型的数据集 |

---

## 📌 Slide 4: 解决方案 - 任务特定分支

### 方案核心思想

**按任务类型维护独立的master分支**

```
data_release_repo/
├── master/multi_task          # 多任务联合训练分支
│   └── training_dataset.json  # GOD+可行驶域数据
│
├── master/god_base            # GOD基础训练分支（20cm）
│   └── training_dataset.json  # 仅GOD数据（20cm）
│
├── master/god_hd              # GOD高清训练分支（5cm）
│   └── training_dataset.json  # 仅GOD数据（5cm）
│
├── master/drivable_2cls       # 可行驶域2分类分支
│   └── training_dataset.json  # 仅可行驶域数据（2分类）
│
└── master/drivable_multi      # 可行驶域多分类分支
    └── training_dataset.json  # 仅可行驶域数据（多分类）
```

### 保持原有约束

✅ 每个分支的tag依然对应**唯一的training_dataset.json**  
✅ 训练任务依然是：**代码commit + data_release tag**  
✅ 数据策划动作依然**前置**在分支内完成  
✅ 分支内commit历史是**线性演进**关系

### 带来的改进

✅ 不同任务的数据集清晰归属  
✅ 各分支独立演进，互不干扰  
✅ Tag关系清晰，易于理解和维护

---

## 📌 Slide 5: 技术实现 - task_tags字段

### training_dataset.json 扩展

#### Meta字段新增
```json
{
    "meta": {
        "release_name": "GOD_MultiTask_20251017",
        "consumer_version": "v1.2.0",
        "bundle_versions": ["v1.2.0-20251017-100000"],
        "version": "v1.2.0",
        
        // 新增字段
        "tasks": ["god_base", "drivable_2cls"]  // 说明包含的任务类型
    }
}
```

#### Dataset字段新增
```json
{
    "dataset_index": [
        {
            "name": "highway_god",
            "obs_path": "obs://god-data/highway_god.jsonl",
            "bundle_versions": ["v1.2.0-20251017-100000"],
            "duplicate": 5,
            
            // 新增字段
            "task_tags": ["god_base"]  // 标记数据集适用的任务
        },
        {
            "name": "highway_drivable",
            "obs_path": "obs://dri-data/highway_drivable.jsonl",
            "bundle_versions": ["v1.2.0-20251017-100000"],
            "duplicate": 5,
            "task_tags": ["drivable_2cls"]
        },
        {
            "name": "urban_joint",
            "obs_path": "obs://multi-task/urban_joint.jsonl",
            "bundle_versions": ["v1.2.0-20251017-100000"],
            "duplicate": 3,
            "task_tags": ["god_base", "drivable_2cls"]  // 共享数据
        }
    ]
}
```

### 训练时按需过滤

```python
# 伪代码示例
def load_datasets_by_task(config_path, task_tags):
    config = load_json(config_path)
    
    filtered_datasets = []
    for dataset in config["dataset_index"]:
        dataset_tasks = dataset.get("task_tags", [])
        
        # 检查是否有交集
        if any(task in task_tags for task in dataset_tasks):
            filtered_datasets.append(dataset)
    
    return filtered_datasets

# 使用示例
# 多任务训练：加载包含god_base或drivable_2cls的数据
datasets = load_datasets_by_task("training_dataset.json", 
                                 ["god_base", "drivable_2cls"])

# 单任务训练：只加载god_base的数据
datasets = load_datasets_by_task("training_dataset.json", 
                                 ["god_base"])
```

---

## 📌 Slide 6: 方案优势对比

### 解决的问题

| 原问题 | 单分支方案 | 多分支方案 ✅ |
|--------|-----------|-------------|
| 数据需求混杂 | ❌ 多种数据集混在一个分支 | ✅ 独立分支，数据集清晰归属 |
| 发布节奏冲突 | ❌ 不同任务互相干扰 | ✅ 各分支独立演进，互不影响 |
| Tag关系模糊 | ❌ Tag之间关系复杂 | ✅ 分支内tag是线性演进 |
| 维护复杂度高 | ❌ 需要理解整个历史 | ✅ 每个分支职责单一 |

### 保持的优势

| 原有优势 | 是否保持 | 说明 |
|---------|---------|------|
| 数据策划动作前置 | ✅ 保持 | 在分支内完成数据策划 |
| 训练任务一一对应 | ✅ 保持 | 1训练任务=1tag=1数据集 |
| 版本精确固化 | ✅ 保持 | 通过tag精确固化版本 |
| 向后兼容 | ✅ 保持 | 传统分支策略继续有效 |

### 额外收益

✅ **数据复用灵活**：通过task_tags实现数据集在任务间共享  
✅ **职责更清晰**：每个分支只负责一种训练模式  
✅ **扩展性更好**：新增任务类型只需创建新分支

---

## 📌 Slide 7: Tag和Release命名规范

### Tag命名规范

#### 通用Tag（原有）
```
feature_dataset/<topic>/release-YYYYMMDD
示例: feature_dataset/toll_station/release-20250709
```

#### 任务特定Tag（新增，可选）
```
<task_type>/release-YYYYMMDD
<task_type>/v<MAJOR>.<MINOR>.<PATCH>

示例:
  multi_task/release-20251017
  god_base/v1.1.0
  drivable_2cls/release-20251017
```

### Release命名规范

#### 通用Release（原有）
```
TrainingDataset v<MAJOR>.<MINOR>.<PATCH>
示例: TrainingDataset v1.2.0
```

#### 任务特定Release（新增，可选）
```
<TaskType> v<MAJOR>.<MINOR>.<PATCH>

示例:
  MultiTask v1.2.0
  GOD-Base v1.1.0
  Drivable2Class v1.2.0
```

### Tag注释规范

```yaml
# 任务特定Tag注释示例
task_type: "multi_task"
release_name: "multi_task/release-20251017"
consumer_version: "v1.2.0"
bundle_version: "v1.2.0-20251017-100000"
training_dataset_version: "v1.2.0"
tasks: ["god_base", "drivable_2cls"]
```

---

## 📌 Slide 8: 支持的任务类型（GOD示例）

### GOD网络任务类型定义

| 任务标签 | 任务名称 | 建议分支 | 分辨率/类型 | 使用场景 |
|---------|---------|---------|-----------|---------|
| `multi_task` | 多任务联合训练 | `master/multi_task` | - | GOD+可行驶域联合训练 |
| `god_base` | GOD基础训练 | `master/god_base` | 20cm | GOD单任务标准训练 |
| `god_hd` | GOD高清训练 | `master/god_hd` | 5cm | GOD高分辨率场景 |
| `drivable_2cls` | 可行驶域2分类 | `master/drivable_2cls` | 2类 | 通用场景二分类 |
| `drivable_multi` | 可行驶域多分类 | `master/drivable_multi` | 5类 | 园区多分类场景 |

### 分支演进关系

```
master/multi_task:
  v1.0.0 → v1.1.0 → v1.2.0 (线性演进)

master/god_base:
  v1.0.0 → v1.1.0 → v1.2.0 (线性演进)

master/god_hd:
  v1.0.0 → v1.0.1 → v1.1.0 (线性演进)
```

### 任务间关系

```
多任务训练（第一阶段）
    ↓ 产出pth_v1.0
单任务finetune（第二阶段）
    ↓ 更新pth_v1.1
持续迭代...
```

---

## 📌 Slide 9: 典型使用流程

### 场景1：多任务训练（第一阶段）

```bash
# 1. 在multi_task分支准备数据
git checkout master/multi_task
# 编辑training_dataset.json，包含GOD和可行驶域数据

# 2. 打tag
git tag -a multi_task/v1.0.0 -m "Multi-task training v1.0.0"

# 3. 训练
训练任务 = 代码commit(abc123) + multi_task/v1.0.0
         ↓
    产出 pth_v1.0 (包含GOD和可行驶域head)
```

### 场景2：单任务Finetune（第二阶段）

```bash
# 1. 在god_base分支准备数据
git checkout master/god_base
# 编辑training_dataset.json，只包含GOD数据

# 2. 打tag
git tag -a god_base/v1.1.0 -m "GOD base training v1.1.0"

# 3. 训练
训练任务 = 代码commit(def456) + god_base/v1.1.0
         ↓
    加载 pth_v1.0，finetune GOD head
         ↓
    产出 pth_v1.1 (GOD head更新)
```

### 场景3：高清训练

```bash
# 1. 在god_hd分支准备数据
git checkout master/god_hd
# 编辑training_dataset.json，包含5cm高清数据

# 2. 打tag
git tag -a god_hd/v1.0.0 -m "GOD HD training v1.0.0"

# 3. 训练
训练任务 = 代码commit(ghi789) + god_hd/v1.0.0
         ↓
    产出 pth_hd_v1.0 (高清模型)
```

---

## 📌 Slide 10: 分支工作流

### Feature开发流程

```bash
# 从任务特定分支创建feature分支
master/god_base 
    ↓
feature_dataset/god_base/highway/clean
    ↓ PR合并
master/god_base
```

### Experiment流程

```bash
# 从任务特定分支创建experiment分支
master/multi_task 
    ↓
experiment/multi_task/ablation-01
    ↓ cherry-pick有价值的commit
master/multi_task
```

### 完整示例

```bash
# 1. 创建功能分支
git checkout -b feature_dataset/god_base/highway/clean master/god_base

# 2. 进行数据清洗
# 编辑training_dataset.json

# 3. 提交变更
git commit -m "清洗highway场景GOD数据"

# 4. 合并到master
git checkout master/god_base
git merge feature_dataset/god_base/highway/clean

# 5. 打tag发布
git tag -a god_base/v1.2.0 -m "GOD base v1.2.0"
```

---

## 📌 Slide 11: 评审结论

### ✅ 同意事项

#### 1. 方案符合原有设计约束
- 保持"1训练任务=1tag=1数据集"的核心约束
- 数据策划动作前置不变
- 版本追溯机制完整

#### 2. 解决了实际问题
- 不同任务类型数据集清晰归属
- 各分支独立演进，互不干扰
- Tag演进关系清晰

#### 3. 保持向后兼容
- 传统分支策略继续有效
- 任务特定分支作为可选方案
- 现有训练任务不受影响

### 📝 方案采纳决定

**同意**：多任务训练数据发布规范

适用范围：
- ✅ GOD网络：按照本方案实施
- ✅ 其他网络：可选采用，由各团队评估决定

---

## 📌 Slide 12: 后续行动项

### 📋 各团队需完成的工作

| 网络 | 负责团队 | 任务 | 截止日期 |
|------|---------|------|---------|
| **端到端（E2E）** | E2E团队 | 审视多任务需求，制定分支规范 | TBD |
| **静态感知** | 静态团队 | 审视多任务需求，制定分支规范 | TBD |
| **BEV感知** | BEV团队 | 审视多任务需求，制定分支规范 | TBD |
| **PV感知** | PV团队 | 审视多任务需求，制定分支规范 | TBD |

### 📝 需要制定的内容

参照GOD方案，各团队需明确：

#### 1. 任务类型定义
```yaml
示例（各团队根据实际情况定义）：
- task_id: multi_task
  description: 多任务联合训练
  branch: master/multi_task
  
- task_id: xxx_base
  description: 基础训练
  branch: master/xxx_base
```

#### 2. 分支命名规范
- Master分支命名：`master/<task_type>`
- Feature分支命名：`feature_dataset/<task_type>/<topic>/<method>`
- Experiment分支命名：`experiment/<task_type>/<trial>`

#### 3. Tag/Release命名
- Tag格式：`<task_type>/v<MAJOR>.<MINOR>.<PATCH>`
- Release格式：`<TaskType> v<MAJOR>.<MINOR>.<PATCH>`

#### 4. 典型训练流程
- 多任务训练流程
- 单任务训练流程
- Finetune流程
- 数据集更新流程

---

## 📌 Slide 13: 评估指导原则

### 什么情况需要采用多分支方案？

#### ✅ 建议采用的场景

| 场景 | 理由 |
|------|------|
| 存在多种训练模式 | 多任务、单任务混合训练 |
| 不同模式数据需求差异大 | 数据集内容、规模、类型差异明显 |
| 发布节奏不一致 | 定期训练 vs 随时finetune |
| 需要独立演进 | 不同任务版本独立管理 |

#### ❌ 不建议采用的场景

| 场景 | 理由 |
|------|------|
| 只有单一训练模式 | 使用传统分支即可 |
| 数据集差异小 | 通过配置文件区分即可 |
| 训练流程简单 | 不需要复杂的分支管理 |
| 团队规模小 | 维护成本可能超过收益 |

### 评估问题清单

各团队可通过以下问题自评：

1. 你的网络是否有多种训练模式？（多任务、单任务、finetune等）
2. 不同训练模式的数据需求差异有多大？
3. 不同训练模式的发布节奏是否一致？
4. 是否经常需要在不同训练模式间切换？
5. 当前是否遇到分支管理混乱的问题？

**如果3个以上问题答案为"是"，建议采用多分支方案**

---

## 📌 Slide 14: 实施建议

### 渐进式实施策略

#### 阶段1：评估和规划（1-2周）
- 各团队评估自身需求
- 制定任务类型定义
- 设计分支命名规范

#### 阶段2：文档和规范（1周）
- 更新team wiki
- 编写操作手册
- 培训团队成员

#### 阶段3：试点实施（2-4周）
- 创建第一个任务特定分支
- 完成一次完整的训练流程
- 收集反馈和改进

#### 阶段4：全面推广（持续）
- 创建其他任务分支
- 迁移现有训练任务
- 持续优化流程

### 风险和缓解措施

| 风险 | 缓解措施 |
|------|---------|
| 分支数量增加 | 明确分支命名规范，定期清理 |
| 学习成本 | 提供详细文档和培训 |
| 数据重复 | 通过task_tags共享数据 |
| 工具适配 | 逐步更新CI/CD工具 |

---

## 📌 Slide 15: 参考资源

### 相关文档

- **Training Dataset Management Wiki**  
  `data_release_repo/docs/Training_Dataset_Management_Wiki.md`
  - 完整的字段定义
  - 多任务训练示例
  - Tag/Release规范

- **DataSpecHub Complete Guide**  
  `docs/DataSpecHub_Complete_Guide.md`
  - 上游系统集成指南
  - Bundle版本管理
  - 版本追溯链路

- **Git Branch Strategy**  
  `data_release_repo/docs/Git_Branch_Strategy.md`
  - 分支管理规范
  - 工作流说明

### 联系方式

- **Data Platform Team**: data-platform@company.com
- **方案设计**: [设计人员]
- **技术支持**: [支持团队]

### Q&A

欢迎提问和讨论

---

## 📌 附录：常见问题

### Q1: 是否所有网络都必须使用任务特定分支？

**A**: 不是。这是**可选方案**。如果网络训练模式简单，可继续使用传统分支策略。只有在遇到多训练模式、数据需求差异大等问题时，才建议采用。

### Q2: 如何保证不同分支的数据一致性？

**A**: 通过`task_tags`字段标记数据集归属。同一个数据集可以标记多个task_tags，实现在不同任务间共享。数据本身存储在OBS上，只是索引文件不同。

### Q3: 旧的训练任务如何处理？

**A**: 完全**向后兼容**。旧的tag和分支继续有效，不需要迁移。新的训练任务可以选择使用任务特定分支，旧的训练任务可以继续使用原有方式。

### Q4: 数据复用如何实现？

**A**: 通过`task_tags`字段，一个数据集可以服务多个任务。例如：
```json
{
    "name": "urban_joint",
    "task_tags": ["god_base", "drivable_2cls"]
}
```
这个数据集可以在god_base和drivable_2cls两个分支中使用。

### Q5: 是否增加管理成本？

**A**: 短期看分支数量增加，但长期看：
- ✅ 每个分支职责清晰，更易理解
- ✅ 避免了单分支内的混乱
- ✅ Tag演进关系清晰
- ✅ 整体管理成本降低

### Q6: 如何在不同分支间同步数据更新？

**A**: 
1. 共享数据通过task_tags标记，自然同步
2. 特定任务数据在各自分支独立管理
3. 可通过cherry-pick在分支间选择性同步commit

### Q7: CI/CD工具需要修改吗？

**A**: 需要小幅适配：
- 识别任务特定的tag格式
- 支持按task_tags过滤数据集
- 更新分支保护规则

这些改动较小，可以渐进式实施。

### Q8: 如何回退到旧版本？

**A**: 与传统方式相同：
```bash
# 回退到特定tag
git checkout god_base/v1.0.0

# 或回退分支
git reset --hard <commit-id>
```

### Q9: 多个team如何协作？

**A**: 
- 每个team负责自己的任务分支
- 通过PR机制协作
- 共享数据在各自分支标记task_tags
- 定期同步和review

---

**文档版本**: v1.0  
**最后更新**: 2025-10-20  
**维护团队**: Data Platform Team

