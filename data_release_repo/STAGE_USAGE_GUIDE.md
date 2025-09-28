# 阶段化数据加载使用指南

## 🎯 快速开始

### 1. 环境变量方式（推荐）

这是最简单的使用方式，无需修改任何代码：

```bash
# 设置训练阶段
export TRAINING_STAGE="finetuning"

# 运行训练（你的现有代码）
python train.py
```

你的训练代码会自动加载对应阶段的数据配置。

### 2. 手动切换阶段

```bash
# 切换到微调阶段
python scripts/stage_manager.py switch-stage finetuning

# 切换到评估阶段
python scripts/stage_manager.py switch-stage evaluation

# A/B测试（切换到变体A）
python scripts/stage_manager.py switch-stage ab_testing --variant variant_a
```

### 3. 查看当前状态

```bash
# 查看当前阶段
python scripts/stage_manager.py status

# 列出所有可用阶段
python scripts/stage_manager.py list-stages
```

## 🔧 集成到现有代码

### 方法1: 环境变量检测（推荐）

在你的数据加载代码中添加以下逻辑：

```python
import os
import json
import yaml

def get_dataset_config():
    """获取数据集配置，支持阶段化加载"""
    
    # 1. 检查是否强制指定配置文件
    force_config = os.getenv('FORCE_DATASET_CONFIG')
    if force_config and os.path.exists(force_config):
        with open(force_config, 'r') as f:
            return json.load(f)
    
    # 2. 检查当前激活的阶段
    active_stage_file = 'active_stage.yaml'
    if os.path.exists(active_stage_file):
        with open(active_stage_file, 'r') as f:
            active_stage = yaml.safe_load(f)
        
        config_file = active_stage.get('config_file')
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
    
    # 3. 使用默认配置
    default_config = 'training_dataset.json'
    if os.path.exists(default_config):
        with open(default_config, 'r') as f:
            return json.load(f)
    
    raise FileNotFoundError("未找到数据集配置文件")

# 在你的训练脚本中使用
config = get_dataset_config()
dataset_index = config['dataset_index']

# 按阶段配置创建数据加载器
stage_config = config['meta'].get('stage_config', {})
batch_size = stage_config.get('loading_config', {}).get('batch_size', 32)
```

### 方法2: 直接使用阶段管理器

```python
from scripts.stage_manager import StageManager

def create_data_loader():
    """创建基于当前阶段的数据加载器"""
    manager = StageManager()
    
    # 获取当前阶段配置
    current_stage, variant = manager.get_current_stage()
    config = manager.preview_stage_config(current_stage, variant)
    
    # 根据配置创建数据加载器
    batch_size = config.get('stage_config', {}).get('loading_config', {}).get('batch_size', 32)
    
    # 你的数据加载逻辑
    return create_dataloader_with_config(config, batch_size)
```

## 📊 实际使用场景

### 场景1: 渐进式训练

```bash
# 启动自动阶段切换训练
export TRAINING_STAGE="auto"
python train.py

# 训练过程会自动经历：
# pretraining (0-50 epochs) → finetuning (50-100 epochs) → evaluation
```

### 场景2: 特定阶段调试

```bash
# 只测试微调阶段的数据
export TRAINING_STAGE="finetuning"
python train.py --epochs 5 --debug

# 或者使用特定配置文件
export FORCE_DATASET_CONFIG="stages/finetuning.json"
python train.py --debug
```

### 场景3: A/B测试

```bash
# 启动A组实验
export TRAINING_STAGE="ab_testing"
export AB_VARIANT="variant_a"
python train.py --experiment-name "exp_a"

# 启动B组实验（另一个终端）
export AB_VARIANT="variant_b"  
python train.py --experiment-name "exp_b"
```

### 场景4: 在线学习

```bash
# 切换到在线学习模式
python scripts/stage_manager.py switch-stage online_learning

# 启动在线训练
python online_training.py
```

## 🛠️ 高级配置

### 自定义阶段配置

你可以创建自己的阶段配置：

```bash
# 复制现有配置作为模板
cp stages/finetuning.json stages/my_custom_stage.json

# 编辑配置文件
vim stages/my_custom_stage.json

# 在stage_config.yaml中添加新阶段
vim stage_config.yaml
```

### 条件切换

在`stage_config.yaml`中配置自动切换条件：

```yaml
stages:
  my_custom_stage:
    name: "自定义阶段"
    config_file: "stages/my_custom_stage.json"
    auto_switch_conditions:
      - epoch: 75
        condition: "custom_trigger"
      - metric: "accuracy"
        threshold: 0.9
        operator: ">"
```

### 环境特定配置

```yaml
environments:
  development:
    switch_strategy:
      mode: "manual"  # 开发环境手动切换
  
  production:
    switch_strategy:
      mode: "auto"    # 生产环境自动切换
      check_interval: 10
```

## 📈 监控和日志

### 查看阶段切换历史

```bash
# 生成详细报告
python scripts/stage_manager.py report --output stage_report.md

# 查看切换历史
python scripts/stage_manager.py status
```

### 实时监控

```python
# 在训练循环中添加监控
def training_loop():
    manager = StageManager()
    
    for epoch in range(num_epochs):
        # 训练逻辑
        train_epoch()
        
        # 更新指标（可选）
        current_metrics = {
            'epoch': epoch,
            'loss': current_loss,
            'accuracy': current_accuracy
        }
        # 这里可以添加指标更新逻辑
        
        # 检查是否需要切换阶段
        if should_check_stage_switch(epoch):
            status = manager.get_stage_status()
            print(f"当前阶段: {status['current_stage']}")
```

## 🚨 故障排除

### 常见问题

#### Q: 找不到配置文件
```bash
# 检查文件是否存在
ls -la stages/
python scripts/stage_manager.py list-stages
```

#### Q: 阶段切换不生效
```bash
# 验证配置
python scripts/stage_manager.py validate-config finetuning

# 检查当前状态
python scripts/stage_manager.py status
```

#### Q: 环境变量不生效
```bash
# 检查环境变量
echo $TRAINING_STAGE
echo $FORCE_DATASET_CONFIG

# 重新设置
export TRAINING_STAGE="finetuning"
```

### 调试模式

```bash
# 启用调试日志
export STAGE_DEBUG=1
python scripts/stage_manager.py status

# 预览配置而不切换
python scripts/stage_manager.py preview finetuning
```

## 📝 最佳实践

### 1. 版本控制

```bash
# 为阶段配置创建版本Tag
git add stages/
git commit -m "更新微调阶段配置

date: \"2025-09-23\"
type: \"modify(balance)\"
description: \"优化微调阶段数据比例\"
details:
  stage: \"finetuning\"
  toll_station_ratio: 0.6
  intersection_ratio: 0.3"

git tag -a "stage/finetuning/v1.2.1" -m "微调阶段配置 v1.2.1"
```

### 2. 环境隔离

```bash
# 开发环境
export STAGE_CONFIG_PATH="./dev_stage_config.yaml"
export TRAINING_STAGE="finetuning"

# 生产环境
export STAGE_CONFIG_PATH="/app/config/prod_stage_config.yaml"
export TRAINING_STAGE="auto"
```

### 3. 容器化部署

```dockerfile
# Dockerfile
FROM python:3.9

# 复制阶段配置
COPY data_release_repo/ /app/data_release_repo/
COPY scripts/ /app/scripts/

# 设置环境变量
ENV STAGE_CONFIG_PATH=/app/data_release_repo/stage_config.yaml
ENV TRAINING_STAGE=pretraining

# 启动脚本
CMD ["python", "train.py"]
```

### 4. CI/CD集成

```yaml
# .github/workflows/training.yml
name: Training Pipeline

on:
  push:
    branches: [main]

jobs:
  pretraining:
    runs-on: ubuntu-latest
    env:
      TRAINING_STAGE: pretraining
    steps:
      - uses: actions/checkout@v3
      - name: Run pretraining
        run: python train.py --epochs 50

  finetuning:
    needs: pretraining
    runs-on: ubuntu-latest
    env:
      TRAINING_STAGE: finetuning
    steps:
      - uses: actions/checkout@v3
      - name: Run finetuning
        run: python train.py --epochs 30
```

## 🔗 相关文档

- [阶段化数据加载机制详解](docs/Stage_Based_Data_Loading.md)
- [训练数据集管理Wiki](docs/Training_Dataset_Management_Wiki.md)
- [Git分支策略](docs/Git_Branch_Strategy.md)

## 📞 技术支持

遇到问题时的排查步骤：

1. **检查配置**: `python scripts/stage_manager.py validate-config <stage>`
2. **查看状态**: `python scripts/stage_manager.py status`
3. **生成报告**: `python scripts/stage_manager.py report`
4. **检查日志**: 查看训练日志中的数据加载信息
5. **联系支持**: 提供报告和错误信息

---

**维护团队**: Data Platform Team  
**最后更新**: 2025-09-23

