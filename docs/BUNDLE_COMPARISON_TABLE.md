# Bundle对比表格 - 新版本清单模式

## 命名规范对比

| 旧命名格式 | 新命名格式 | 改进点 |
|-----------|-----------|--------|
| `end_to_end-2025.25.yaml` | `end_to_end-v1.2.0-2025.25.yaml` | Consumer版本直接可见 |
| `pv_trafficlight-v1.1.0.yaml` | `pv_trafficlight-v1.1.0-release.yaml` | Bundle类型明确标识 |
| `foundational_model-20250620-143500.yaml` | `foundational_model-v1.0.0-20250620-143500.yaml` | Consumer版本可追溯 |

## Bundle内容对比

### 旧设计 vs 新设计

| 方面 | 旧设计（固定版本） | 新设计（版本清单） |
|------|------------------|------------------|
| **核心思路** | 硬约束精确版本 | 提供版本选择清单 |
| **版本字段** | `version: "1.2.0"` | `available_versions: ["1.2.0", "1.1.0", "1.0.0"]` |
| **推荐机制** | 无 | `recommended_version: "1.2.0"` |
| **灵活性** | 低 - 固定版本 | 高 - 多版本可选 |
| **数据覆盖** | 可能缺失数据 | 最大化数据覆盖 |

### 具体示例对比

#### **Weekly Bundle**

**旧设计：**
```yaml
# bundles/weekly/end_to_end-2025.25.yaml
channels:
  - channel: object_array_fusion_infer
    version: "1.2.0"                    # 固定版本
    source_constraint: ">=1.2.0"
```

**新设计：**
```yaml
# bundles/weekly/end_to_end-v1.2.0-2025.25.yaml
channels:
  - channel: object_array_fusion_infer
    available_versions: ["1.2.0", "1.1.0", "1.0.0"]  # 版本清单
    recommended_version: "1.2.0"                      # 推荐版本
    source_constraint: ">=1.2.0"

```

## Bundle类型特征对比

| Bundle类型 | 文件命名模式 | 版本策略 | 生命周期 | 主要用途 |
|-----------|-------------|----------|----------|----------|
| **Weekly** | `{consumer}-v{consumer_ver}-{year}.{week}.yaml` | 稳定的版本清单 | 4周保留 | 团队协作同步 |
| **Release** | `{consumer}-v{consumer_ver}-release.yaml` | 经过验证的清单 | 长期支持 | 生产环境部署 |
| **Snapshot** | `{consumer}-v{consumer_ver}-{timestamp}.yaml` | 实验性版本清单 | 7-30天 | 快速验证实验 |

## 实际应用场景对比

### 场景1：数据部分可用的情况

**问题：** `object_array_fusion_infer` 数据集中，有些数据片段只有v1.1.0，有些有v1.2.0

**旧设计的问题：**
```yaml
# 固定版本 v1.2.0
channels:
  - channel: object_array_fusion_infer
    version: "1.2.0"  # 部分数据缺失
```
- 结果：数据覆盖不完整，训练数据量减少

**新设计的解决：**
```yaml
# 版本清单模式
channels:
  - channel: object_array_fusion_infer
    available_versions: ["1.2.0", "1.1.0", "1.0.0"]
    recommended_version: "1.2.0"
```
- 结果：数据获取系统可以智能选择，最大化数据覆盖

### 场景2：版本溯源

**旧设计：**
- 文件名：`end_to_end-2025.25.yaml`
- 问题：看不出基于哪个Consumer版本生成

**新设计：**
- 文件名：`end_to_end-v1.2.0-2025.25.yaml`
- 优势：直接知道Consumer版本，便于追溯

### 场景3：实验对比

**新设计的优势：**
```yaml
# Snapshot Bundle支持多版本实验
channels:
  - channel: image_original
    available_versions: ["1.2.0", "1.1.0", "1.0.0"]
    recommended_version: "1.2.0"
    experiment_role: "视觉模态主要输入"
```
- 支持A/B测试和版本对比实验
- 单个Bundle支持多种数据版本组合

## 文件组织结构

### 新的Bundle目录结构

```
bundles/
├── weekly/
│   ├── end_to_end-v1.2.0-2025.25.yaml           # 端到端v1.2.0的周级快照
│   ├── foundational_model-v1.0.0-2025.25.yaml   # 基础模型v1.0.0的周级快照
│   └── ...
├── release/
│   ├── pv_trafficlight-v1.1.0-release.yaml      # 红绿灯v1.1.0正式发布
│   └── ...
└── snapshots/
    ├── foundational_model-v1.0.0-20250620-143500.yaml  # 实验快照
    └── ...
```

### 文件浏览体验

**旧设计：**
```bash
ls bundles/weekly/
end_to_end-2025.25.yaml        # 看不出Consumer版本
pv_trafficlight-2025.25.yaml   # 版本信息不明确
```

**新设计：**
```bash
ls bundles/weekly/
end_to_end-v1.2.0-2025.25.yaml           # 一目了然的版本对应
foundational_model-v1.0.0-2025.25.yaml   # Consumer版本清晰可见
```

## 迁移指南

### 1. 文件重命名
```bash
# 旧文件重命名为新格式
mv bundles/weekly/end_to_end-2025.25.yaml \
   bundles/weekly/end_to_end-v1.2.0-2025.25.yaml
```

### 2. 内容结构升级
```yaml
# 从固定版本升级为版本清单
channels:
  - channel: object_array_fusion_infer
    # 旧格式
    version: "1.2.0"
    
    # 新格式
    available_versions: ["1.2.0", "1.1.0", "1.0.0"]
    recommended_version: "1.2.0"
    source_constraint: ">=1.2.0"

```

### 3. 工具链适配
- Bundle生成器自动使用新的命名规范
- 数据获取系统支持版本清单解析
- 验证工具兼容新的Bundle格式

## 核心优势总结

1. **更直观的命名** - Consumer版本直接体现在文件名中
2. **更灵活的版本选择** - 提供版本清单而非固定版本
3. **更好的数据覆盖** - 适应数据生产的渐进性
4. **更强的可追溯性** - 完整的转换历史记录
5. **更现实的设计** - 符合实际数据生产场景

新的Bundle设计解决了固定版本带来的数据覆盖问题，同时保持了版本管理的严谨性和可追溯性。 