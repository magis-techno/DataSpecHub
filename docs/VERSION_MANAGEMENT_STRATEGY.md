# Consumer版本管理策略

## 概述

为了管理大网络在不同阶段的数据需求组合，以及基于某个版本衍生的多个分支，我们采用**目录内多版本文件 + 语义化版本控制**的混合策略。

## 目录结构设计

```
consumers/
├── end_to_end/
│   ├── v1.0.0.yaml           # 基础版本
│   ├── v1.1.0.yaml           # 功能增强版本
│   ├── v1.2.0.yaml           # 当前稳定版本
│   ├── v1.2.1-experiment.yaml    # 实验分支
│   └── latest.yaml           # 指向当前推荐版本的软链接
├── foundational_model/
│   ├── v1.0.0.yaml           # 基础版本
│   ├── v1.0.1-pretraining.yaml   # 预训练特化版本
│   ├── v1.0.2-finetuning.yaml    # 微调特化版本
│   └── latest.yaml           # 指向当前推荐版本
└── pv_trafficlight/
    ├── v1.0.0.yaml           # 基础版本
    ├── v1.1.0.yaml           # 当前版本
    ├── v1.1.1-weather.yaml      # 天气适应性增强分支
    └── latest.yaml           # 指向当前推荐版本
```

## 配置文件结构

每个consumer配置文件采用简化结构，专注于核心的版本依赖和数据缺失处理：

```yaml
meta:
  consumer: end_to_end
  version: "1.2.0"
  parent_version: "1.1.0"  # 基于哪个版本创建（可选，用于分支）
  branch_type: "stable"  # stable/experiment/optimization/pretraining/finetuning
  created_at: "2025-04-10"
  expires_at: "2025-05-10"   # 实验分支的过期时间（可选）
  owner: "e2e-team@company.com"
  description: "端到端网络的数据通道版本需求"

# 数据需求 - 专注于版本依赖和缺失处理
requirements:
  - channel: image_original
    version: "1.2.0"         # 精确版本或版本范围 (>=1.0.0)
    required: true           # 是否必需
    on_missing: "fail"       # 缺失时的处理策略
    
  - channel: occupancy
    version: "1.0.0"
    required: false
    on_missing: "ignore"

# 需求变更历史
change_history:
  - date: "2025-04-10"
    version: "1.2.0"
    changes: "升级 image_original 到 1.2.0"
```

## 数据缺失处理策略

`on_missing` 字段定义了当数据通道缺失时的处理方式：

- **`fail`**: 任务失败中断 - 用于关键数据，如核心传感器数据
- **`ignore`**: 忽略缺失继续处理 - 用于可选的辅助数据
- **`substitute`**: 使用替代数据源 - 配合`substitute_with`字段指定替代通道
- **`use_default`**: 使用默认值或占位符 - 用于可降级的数据

## 版本命名规范

### 主版本号规则
- `v{major}.{minor}.{patch}.yaml` - 标准语义化版本
- `v{major}.{minor}.{patch}-{variant}.yaml` - 特殊变体/分支

### 变体后缀含义
- `-experiment`: 实验性功能测试
- `-pretraining`: 预训练阶段特化
- `-finetuning`: 微调阶段特化
- `-debug`: 调试版本

## 分支管理原则

### 1. 控制分支膨胀
- 每个主版本最多保留 **3个活跃变体**
- 实验性分支应在 **1个月内** 决定合并或删除
- 过时的分支要及时清理

### 2. 保持灵活性
- 支持基于任何稳定版本创建新变体
- 允许快速迭代和A/B测试
- 支持团队独立的配置需求

### 3. 版本生命周期
```
创建 → 测试 → 稳定化 → 合并主线 → 归档/删除
  ↓       ↓        ↓         ↓         ↓
experimental → beta → stable → main → deprecated
```

## 使用示例

### 创建新的实验分支
```bash
# 基于v1.2.0创建实验分支
python scripts/consumer_version_manager.py create-branch \
  --consumer end_to_end \
  --base-version v1.2.0 \
  --new-version v1.2.1-experiment \
  --description "测试新的数据融合策略"
```

### 更新latest指向
```bash
# 更新latest指向新的稳定版本
python scripts/consumer_version_manager.py update-latest \
  --consumer end_to_end \
  --version v1.2.0
```

## 工具支持

### 脚本工具
1. `scripts/consumer_version_manager.py` - 版本管理工具
2. `scripts/consumer_branch_cleaner.py` - 分支清理工具（可选）
3. `scripts/consumer_validator.py` - 配置验证工具（可选）

### 使用命令
```bash
# 列出所有版本
python scripts/consumer_version_manager.py list

# 创建新分支
python scripts/consumer_version_manager.py create-branch \
  --consumer end_to_end \
  --base-version v1.2.0 \
  --new-version v1.2.1-experiment \
  --description "测试新功能"

# 清理过期分支
python scripts/consumer_version_manager.py clean --execute

# 验证配置
python scripts/consumer_version_manager.py validate \
  --consumer end_to_end --version v1.2.0
```
