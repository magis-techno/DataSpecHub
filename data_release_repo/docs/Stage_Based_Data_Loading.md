# 阶段化数据加载机制

作者：
版本：v1.0.0
更新时间：2025-09-23

## 概述

本文档定义了支持不同训练阶段加载不同数据集的机制，通过配置文件和环境变量实现无代码修改的数据切换。

## 背景需求

在机器学习训练过程中，不同阶段可能需要不同的数据：
- **预训练阶段**: 大规模基础数据集
- **微调阶段**: 特定场景的精选数据集  
- **评估阶段**: 标准测试数据集
- **在线学习阶段**: 实时收集的数据集
- **A/B测试阶段**: 对比实验数据集

## 🎯 设计方案

### 1. 阶段化配置文件结构

```
data_release_repo/
├── training_dataset.json              # 默认数据集配置
├── stages/                            # 阶段化配置目录
│   ├── pretraining.json              # 预训练阶段
│   ├── finetuning.json               # 微调阶段
│   ├── evaluation.json               # 评估阶段
│   ├── online_learning.json          # 在线学习阶段
│   └── ab_testing/                    # A/B测试目录
│       ├── variant_a.json
│       └── variant_b.json
├── stage_config.yaml                 # 阶段配置映射
└── active_stage.yaml                 # 当前激活阶段
```

### 2. 阶段配置映射文件

**stage_config.yaml**:
```yaml
# 阶段定义和配置
stages:
  pretraining:
    name: "预训练阶段"
    description: "大规模基础数据集训练"
    config_file: "stages/pretraining.json"
    priority: 1
    auto_switch_conditions:
      - epoch: 0
        condition: "start"
    
  finetuning:
    name: "微调阶段" 
    description: "特定场景精细化训练"
    config_file: "stages/finetuning.json"
    priority: 2
    auto_switch_conditions:
      - epoch: 50
        condition: "pretraining_complete"
    
  evaluation:
    name: "评估阶段"
    description: "模型性能评估"
    config_file: "stages/evaluation.json"
    priority: 3
    auto_switch_conditions:
      - epoch: 100
        condition: "training_complete"
    
  online_learning:
    name: "在线学习阶段"
    description: "增量学习和模型更新"
    config_file: "stages/online_learning.json"
    priority: 4
    trigger_mode: "manual"  # 手动触发
    
  ab_testing:
    name: "A/B测试阶段"
    description: "对比实验数据集"
    variants:
      variant_a:
        config_file: "stages/ab_testing/variant_a.json"
        weight: 0.5
      variant_b:
        config_file: "stages/ab_testing/variant_b.json"
        weight: 0.5

# 默认阶段
default_stage: "pretraining"

# 阶段切换策略
switch_strategy:
  mode: "auto"  # auto | manual | hybrid
  check_interval: 10  # 检查间隔(epoch)
  fallback_stage: "pretraining"
```

### 3. 激活阶段状态文件

**active_stage.yaml**:
```yaml
# 当前激活的阶段
current_stage: "pretraining"
current_variant: null  # A/B测试时使用
activated_at: "2025-09-23 10:30:00"
activated_by: "system"  # system | user | scheduler
switch_reason: "training_start"

# 历史记录
history:
  - stage: "pretraining"
    activated_at: "2025-09-23 10:30:00"
    deactivated_at: null
    duration: null
    reason: "training_start"

# 下一阶段预测
next_stage:
  predicted_stage: "finetuning"
  estimated_switch_time: "2025-09-25 14:00:00"
  conditions:
    - "epoch >= 50"
    - "loss < 0.1"
```

## 📁 阶段化数据集配置格式

### 预训练阶段配置示例

**stages/pretraining.json**:
```json
{
    "meta": {
        "stage": "pretraining",
        "release_name": "Pretraining_Foundation_20250923",
        "consumer_version": "v1.2.0",
        "bundle_versions": ["v1.2.0-20250620-143500"],
        "created_at": "2025-09-23 10:30:00",
        "description": "预训练阶段基础数据集",
        "version": "v1.2.0",
        "stage_config": {
            "data_ratio": {
                "highway": 0.4,
                "urban": 0.3,
                "parking": 0.2,
                "others": 0.1
            },
            "sampling_strategy": "balanced",
            "max_clips_per_dataset": 100000,
            "shuffle": true,
            "augmentation": {
                "enabled": true,
                "methods": ["rotation", "brightness", "noise"]
            }
        }
    },
    "dataset_index": [
        {
            "name": "highway_foundation_large",
            "obs_path": "obs://pretraining-data/highway_foundation_large.jsonl",
            "bundle_versions": ["v1.2.0-20250620-143500"],
            "duplicate": 10,
            "stage_weight": 0.4,
            "sampling_priority": "high",
            "enabled": true
        },
        {
            "name": "urban_scenarios_base",
            "obs_path": "obs://pretraining-data/urban_scenarios_base.jsonl", 
            "bundle_versions": ["v1.2.0-20250620-143500"],
            "duplicate": 8,
            "stage_weight": 0.3,
            "sampling_priority": "medium",
            "enabled": true
        }
    ]
}
```

### 微调阶段配置示例

**stages/finetuning.json**:
```json
{
    "meta": {
        "stage": "finetuning",
        "release_name": "Finetuning_Specialized_20250923",
        "consumer_version": "v1.2.0", 
        "bundle_versions": ["v1.2.0-20250620-143500"],
        "created_at": "2025-09-23 10:30:00",
        "description": "微调阶段特化数据集",
        "version": "v1.2.0",
        "stage_config": {
            "data_ratio": {
                "toll_station": 0.6,
                "intersection": 0.3,
                "merge_lane": 0.1
            },
            "sampling_strategy": "targeted",
            "max_clips_per_dataset": 50000,
            "shuffle": false,
            "augmentation": {
                "enabled": false
            },
            "difficulty_progression": true
        }
    },
    "dataset_index": [
        {
            "name": "toll_station_scenarios_refined",
            "obs_path": "obs://finetuning-data/toll_station_scenarios_refined.jsonl",
            "bundle_versions": ["v1.2.0-20250620-143500"],
            "duplicate": 5,
            "stage_weight": 0.6,
            "sampling_priority": "critical",
            "enabled": true,
            "difficulty_level": "progressive"
        },
        {
            "name": "intersection_complex_cases",
            "obs_path": "obs://finetuning-data/intersection_complex_cases.jsonl",
            "bundle_versions": ["v1.2.0-20250620-143500"], 
            "duplicate": 3,
            "stage_weight": 0.3,
            "sampling_priority": "high",
            "enabled": true,
            "difficulty_level": "advanced"
        }
    ]
}
```

## 🔧 实现机制

### 1. 环境变量控制

```bash
# 设置训练阶段
export TRAINING_STAGE="finetuning"

# 设置A/B测试变体
export AB_VARIANT="variant_a"

# 设置配置文件路径
export STAGE_CONFIG_PATH="/path/to/data_release_repo/stage_config.yaml"

# 强制使用特定配置文件
export FORCE_DATASET_CONFIG="/path/to/custom_config.json"
```

### 2. 数据加载逻辑

训练代码中的数据加载器会按以下优先级查找配置：

1. **环境变量指定的配置文件** (`FORCE_DATASET_CONFIG`)
2. **当前激活阶段的配置文件** (从`active_stage.yaml`读取)
3. **默认配置文件** (`training_dataset.json`)

### 3. 阶段切换机制

#### 自动切换
```python
# 伪代码示例
def check_stage_switch_conditions():
    current_epoch = get_current_epoch()
    current_loss = get_current_loss()
    
    for stage, config in stage_configs.items():
        for condition in config.get('auto_switch_conditions', []):
            if evaluate_condition(condition, current_epoch, current_loss):
                switch_to_stage(stage)
                break
```

#### 手动切换
```bash
# 使用工具脚本切换阶段
python scripts/stage_manager.py switch-stage finetuning

# 或直接修改激活文件
python scripts/stage_manager.py activate finetuning --reason "manual_switch"
```

## 🛠️ 阶段管理工具

### 1. 阶段管理命令

```bash
# 查看当前阶段
python scripts/stage_manager.py status

# 列出所有可用阶段
python scripts/stage_manager.py list-stages

# 切换到指定阶段
python scripts/stage_manager.py switch-stage finetuning

# 预览阶段配置
python scripts/stage_manager.py preview finetuning

# 验证阶段配置
python scripts/stage_manager.py validate-config stages/finetuning.json

# 生成阶段报告
python scripts/stage_manager.py report --output stage_report.md
```

### 2. 配置生成工具

```bash
# 基于现有配置生成阶段配置
python scripts/generate_stage_config.py \
  --base-config training_dataset.json \
  --stage pretraining \
  --ratio highway:0.4,urban:0.3,parking:0.3

# 从模板创建新阶段
python scripts/generate_stage_config.py \
  --template finetuning \
  --stage custom_experiment \
  --output stages/custom_experiment.json
```

## 📊 监控和日志

### 1. 阶段切换日志

```json
{
    "timestamp": "2025-09-23 14:30:00",
    "event": "stage_switch",
    "from_stage": "pretraining", 
    "to_stage": "finetuning",
    "trigger": "auto",
    "condition": "epoch >= 50",
    "metadata": {
        "epoch": 50,
        "loss": 0.08,
        "accuracy": 0.92
    }
}
```

### 2. 数据加载统计

```json
{
    "timestamp": "2025-09-23 14:30:00",
    "stage": "finetuning",
    "datasets_loaded": [
        {
            "name": "toll_station_scenarios_refined",
            "clips_loaded": 25000,
            "weight": 0.6,
            "load_time": "2.3s"
        }
    ],
    "total_clips": 41667,
    "total_load_time": "3.8s"
}
```

## 🔄 与现有系统集成

### 1. 向后兼容

- 如果没有阶段配置，自动使用默认的`training_dataset.json`
- 现有的训练脚本无需修改，通过环境变量透明切换
- 保持与DataSpecHub的版本追溯关系

### 2. 版本管理

```bash
# 为特定阶段创建Tag
git tag -a "stage/pretraining/v1.2.0" -m "预训练阶段配置 v1.2.0"

# 为阶段配置创建分支
git checkout -b "feature_dataset/pretraining/optimization"
```

## 🎯 使用场景示例

### 场景1: 渐进式训练
```bash
# 自动阶段切换训练
export TRAINING_STAGE="auto"
python train.py  # 会自动从pretraining -> finetuning -> evaluation
```

### 场景2: A/B测试
```bash
# 启动A/B测试
export TRAINING_STAGE="ab_testing"
export AB_VARIANT="variant_a"  # 或variant_b
python train.py
```

### 场景3: 特定阶段调试
```bash
# 只运行微调阶段
export TRAINING_STAGE="finetuning"
export FORCE_DATASET_CONFIG="stages/finetuning.json"
python train.py --debug
```

### 场景4: 在线学习
```bash
# 切换到在线学习模式
python scripts/stage_manager.py switch-stage online_learning
python online_training.py
```

## 📋 配置文件模板

详见：
- [pretraining_template.json](templates/pretraining_template.json)
- [finetuning_template.json](templates/finetuning_template.json) 
- [evaluation_template.json](templates/evaluation_template.json)
- [ab_testing_template.json](templates/ab_testing_template.json)

## 🚀 部署建议

### 1. 开发环境
```bash
# 使用本地配置
export STAGE_CONFIG_PATH="./stage_config.yaml"
export TRAINING_STAGE="finetuning"
```

### 2. 生产环境
```bash
# 使用远程配置
export STAGE_CONFIG_PATH="obs://config-bucket/stage_config.yaml"
export TRAINING_STAGE="auto"
```

### 3. 容器化部署
```dockerfile
# 在Dockerfile中设置
ENV STAGE_CONFIG_PATH=/app/config/stage_config.yaml
ENV TRAINING_STAGE=pretraining
```

## ⚠️ 注意事项

1. **数据一致性**: 切换阶段时确保数据集的版本一致性
2. **缓存清理**: 阶段切换后可能需要清理数据加载缓存
3. **资源管理**: 不同阶段可能需要不同的计算资源配置
4. **监控报警**: 设置阶段切换的监控和报警机制
5. **回滚机制**: 提供快速回滚到上一阶段的能力

## 📞 支持

如有问题，请参考：
- [阶段管理工具使用指南](stage_manager_guide.md)
- [配置文件格式规范](stage_config_format.md)
- [故障排除指南](troubleshooting.md)

---

**维护团队**: Data Platform Team  
**最后更新**: 2025-09-23

