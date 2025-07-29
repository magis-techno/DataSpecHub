# 训练数据集发布管理

本仓库定义了训练数据集发布后的版本管理和操作追踪规范。

## 目录结构

```
data_release_repo/
├── README.md                        # 本文档
├── docs/                           # 规范文档
│   └── Training_Dataset_Management_Wiki.md  # 完整规范wiki
└── examples/                       # 示例文件
    ├── training_dataset.json      # 标准格式示例
    └── dataset_history/            # 变更历史示例
        ├── changes.yaml
        ├── removed_clips/
        │   └── op_001_enter_waiting_removed.txt
        └── snapshots/
            └── baseline_v1.0.0.json
```

## 核心概念

### 数据流转

```
DataSpecHub (规格定义) 
    ↓ 
生产发布 
    ↓ 
training_dataset.json (训练仓库)
    ↓ 
数据策划 (清洗、新增、调平)
    ↓ 
最终训练数据集
```

### 版本对应关系

```
DataSpecHub Consumer版本 → Bundle版本 → Training Dataset版本
foundational_model/v1.0.0.yaml → foundational_model-v1.0.0-20250620-143500.yaml → JointTrain_20250727-v1.2.0
```

## 快速开始

1. **查看完整规范**: 阅读 `docs/Training_Dataset_Management_Wiki.md`
2. **参考示例**: 查看 `examples/` 目录下的标准格式
3. **建立训练仓库**: 按照规范在训练仓库中建立目录结构
4. **记录操作**: 每次数据策划后更新 `changes.yaml`

## 关键文件

- **training_dataset.json**: 当前最终的训练数据集索引
- **changes.yaml**: 所有操作的详细记录
- **removed_clips/*.txt**: 删除条目的具体跟踪
- **snapshots/*.json**: 关键版本的完整备份

## 主要特性

- ✅ **结果与历史分离**: 保持最终结果文件的简洁
- ✅ **完整操作追踪**: 记录每次新增、删除、修改
- ✅ **版本可回滚**: 支持任意历史版本的恢复
- ✅ **上游可追溯**: 与DataSpecHub版本保持对应关系
- ✅ **人工维护友好**: 简单的YAML格式，易于手工编辑

## 使用场景

### 数据清洗
去除重复、低质量clips，记录具体删除的条目

### 数据挖掘  
合入外部数据集，扩充训练数据

### 数据平衡
调整场景分布，优化训练效果

### 版本管理
支持实验分支、A/B测试等需求

## 工具支持

- `yq`: YAML文件查询和编辑
- `diff`: 版本对比
- `git`: 可选的版本控制（对整个训练仓库）

## 相关文档

- [DataSpecHub主仓](../): 数据规格和通道定义
- [训练数据集管理Wiki](docs/Training_Dataset_Management_Wiki.md): 完整的操作规范
- [示例文件](examples/): 标准格式参考 