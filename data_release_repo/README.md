# Data Release Repository

训练数据集管理仓库，用于管理训练数据集的版本控制、数据策划操作追踪和发布管理。

## 🎯 仓库目标

本仓库用于管理训练数据集的发布后版本管理和操作追踪，支持：

- ✅ 训练数据集索引文件管理
- ✅ 数据策划操作追踪（清洗、新增、调平等）
- ✅ 混合版本数据挖掘支持
- ✅ DAgger训练专用数据集管理
- ✅ 完整的Git工作流和分支管理
- ✅ 自动化工具支持

## 📁 目录结构

```
data_release_repo/
├── training_dataset.json           # 常规训练数据集索引
├── training_dataset.dagger.json    # DAgger训练专用数据集索引 (可选)
├── docs/                           # 文档目录
│   ├── Training_Dataset_Management_Wiki.md  # 核心管理规范
│   └── Git_Branch_Strategy.md               # 分支管理规范
├── scripts/                        # 自动化脚本
│   ├── branch_management.py        # 分支管理工具
│   ├── create_structured_commit.py # 结构化提交工具
│   └── tag_release_helper.py       # Tag和Release创建工具
└── .github/                        # CI/CD配置
    ├── workflows/
    │   └── data-validation.yml     # 数据验证工作流
    └── scripts/                    # CI脚本
        ├── validate_dataset_format.py
        ├── validate_commit_message.py
        ├── check_branch_naming.py
        └── check_pr_target.py
```

## 🚀 快速开始

### 1. 克隆仓库
```bash
git clone <repository-url>
cd data_release_repo
```

### 2. 安装依赖
```bash
pip install -r requirements.txt  # 如果有的话
# 或者手动安装
pip install pyyaml jsonschema
```

### 3. 创建功能分支
```bash
# 使用脚本创建功能分支
python scripts/branch_management.py create-feature toll_station strict

# 或手动创建
git checkout -b feature_dataset/toll_station/strict
```

### 4. 进行数据操作
编辑 `training_dataset.json` 文件，进行数据清洗、新增或调平操作。

### 5. 提交变更
```bash
# 使用结构化提交工具
python scripts/create_structured_commit.py --interactive

# 或手动创建结构化提交
git add training_dataset.json
git commit -m "对收费站场景数据进行质量清洗

date: \"2025-09-23\"
type: \"modify(clean)\"
description: \"对收费站场景数据进行质量清洗\"
task_tag: \"TASK-12345\"
details:
  dataset: \"toll_station_scenarios_v2\"
  total_clips_before: 150000
  clips_removed: 15000
  clips_after: 135000
  quality_threshold: 0.95"
```

## 📋 分支管理

### 分支类型

- **main**: 生产稳定版本，仅通过PR合并
- **develop**: 开发集成分支，功能分支合并目标
- **feature_dataset/<topic>/<method>**: 功能数据集分支
- **experiment/<topic>/<trial>**: 实验分支
- **release/<version>**: 发布分支
- **hotfix/<version>-<issue>**: 热修复分支

### 分支工作流

```bash
# 功能开发流程
develop → feature_dataset/topic/method → develop

# 实验流程
main → experiment/topic/trial → cherry-pick → develop

# 发布流程
develop → release/v1.2.0 → main & develop
```

详细的分支管理规范请参考：[Git_Branch_Strategy.md](docs/Git_Branch_Strategy.md)

## 🛠️ 自动化工具

### 分支管理工具
```bash
# 查看分支状态
python scripts/branch_management.py status

# 创建功能分支
python scripts/branch_management.py create-feature toll_station strict

# 创建实验分支
python scripts/branch_management.py create-experiment toll_station ablation-01

# 创建发布分支
python scripts/branch_management.py create-release v1.2.0

# 列出过期分支
python scripts/branch_management.py list-stale --days 30

# 清理已合并分支
python scripts/branch_management.py cleanup --dry-run
```

### 结构化提交工具
```bash
# 交互式创建提交
python scripts/create_structured_commit.py --interactive

# 命令行模式
python scripts/create_structured_commit.py \
  --type "modify(clean)" \
  --description "对收费站场景数据进行质量清洗" \
  --dataset "toll_station_scenarios_v2" \
  --clips-before 150000 \
  --clips-removed 15000 \
  --clips-after 135000
```

### Tag和Release工具
```bash
# 创建专题Tag
python scripts/tag_release_helper.py create-feature-tag toll_station

# 创建版本Tag
python scripts/tag_release_helper.py create-version-tag v1.2.0

# 生成Release说明
python scripts/tag_release_helper.py generate-release v1.2.0 --previous v1.1.0

# 列出现有Tag
python scripts/tag_release_helper.py list-tags --pattern "feature_dataset/*"
```

## 📝 提交规范

所有涉及数据集修改的提交必须使用结构化格式：

```yaml
date: "2025-09-23"
type: "modify(clean)"   # add | modify(clean) | modify(balance) | fix | docs | refactor
description: "对大数据集进行整体清洗"
task_tag: "TASK-12345"  # 任务单/工单编号；手动操作留空
details:                # 数据操作建议包含此字段
  dataset: "mega_driving_dataset_v2"
  total_clips_before: 500000
  clips_removed: 50000
  clips_after: 450000
  quality_threshold: 0.95
```

## 🏷️ Tag和Release策略

### 专题数据交付
- **Tag命名**: `feature_dataset/<topic>/release-YYYYMMDD`
- **用途**: 专题数据集交付，仅打Tag，不创建Release

### 大版本发布
- **Tag命名**: `training/v<MAJOR>.<MINOR>.<PATCH>`
- **Release命名**: `TrainingDataset v<MAJOR>.<MINOR>.<PATCH>`
- **用途**: 面向广泛消费的稳定版本

## 🔄 CI/CD

仓库配置了自动化检查，在提交和PR时会自动验证：

- ✅ 数据集JSON格式验证
- ✅ 提交信息结构验证
- ✅ 分支命名规范检查
- ✅ PR目标分支验证
- ✅ 版本一致性检查
- ✅ 自动分支清理

## 📖 详细文档

- [训练数据集管理Wiki](docs/Training_Dataset_Management_Wiki.md) - 核心管理规范和操作流程
- [Git分支策略](docs/Git_Branch_Strategy.md) - 完整的分支管理规范
- [DataSpecHub完整指南](../docs/DataSpecHub_Complete_Guide.md) - 上游系统集成指南

## 🤝 贡献指南

1. **Fork本仓库**
2. **创建功能分支**: `git checkout -b feature_dataset/your_topic/your_method`
3. **进行数据操作**: 编辑数据集文件
4. **使用结构化提交**: 遵循提交信息规范
5. **推送分支**: `git push origin feature_dataset/your_topic/your_method`
6. **创建PR**: 目标分支为`develop`

## ❓ 常见问题

### Q: 如何处理大数据集清洗？
A: 使用结构化提交记录详细的操作信息，包括处理前后的数据量、清洗规则等。

### Q: 实验分支的结果如何合并？
A: 使用`cherry-pick`将有价值的提交合并到目标分支，避免直接合并整个实验分支。

### Q: 如何追溯数据血缘？
A: 通过`consumer_version`和`bundle_versions`字段可以追溯到DataSpecHub中的配置。

### Q: DAgger训练数据如何管理？
A: 使用单独的`training_dataset.dagger.json`文件，设置`training_type: "dagger"`。

## 📞 支持

如有问题，请：
1. 查看[详细文档](docs/)
2. 检查[常见问题](#-常见问题)
3. 创建Issue描述问题
4. 联系维护团队

---

**维护团队**: Data Platform Team
**最后更新**: 2025-09-23

