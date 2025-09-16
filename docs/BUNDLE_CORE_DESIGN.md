# Bundle系统核心设计

## 设计原则：版本清单记录器

Bundle系统专注于三个核心功能：
1. **版本清单生成** - 将Consumer的软约束转换为明确的版本列表
2. **链路追溯** - 记录从Consumer到Bundle的完整转换路径  
3. **灵活选择** - 提供版本列表而非固定版本，支持动态数据环境

## 核心流程

```
Consumer配置 (软约束)  →  Bundle生成器  →  Bundle快照 (版本清单)
     ↓                      ↓                    ↓
版本范围约束           版本解析算法        可用版本列表
 ">=1.0.0"         →  扫描可用版本  →    ["1.2.0", "1.1.0", "1.0.0"]
```

## Bundle类型设计

### 1. Weekly Bundle - 固定周期
```yaml
# bundles/weekly/end_to_end-v1.2.0-2025.25.yaml
meta:
  bundle_name: end_to_end
  consumer_version: "v1.2.0"        # Consumer版本
  bundle_version: "v1.2.0-2025.25"  # Bundle版本（Consumer版本-年.周数）
  bundle_type: weekly
  
channels:
  - channel: image_original
    available_versions: ["1.2.0"]           # 版本列表
    source_constraint: "1.2.0"              # 原始约束
    required: true                           # 是否必需
    on_missing: "fail"                       # 缺失处理策略
```

**用途**：生产环境、定期发布、团队协作的标准版本

### 2. Snapshot Bundle - 灵活使用  
```yaml
# bundles/snapshots/foundational_model-v1.0.0-20250620-143500.yaml
meta:
  bundle_name: foundational_model
  consumer_version: "v1.0.0"                   # Consumer版本
  bundle_version: "v1.0.0-20250620-143500"    # Bundle版本（Consumer版本-时间戳）
  bundle_type: snapshot
  
snapshot_config:
  ttl_hours: 168                            # 自动过期
  purpose: "多模态大模型训练数据验证"
```

**用途**：临时需求、快速验证、实验性工作

### 3. Release Bundle - 正式发布
```yaml
# bundles/release/pv_trafficlight-v1.1.0-release.yaml
meta:
  bundle_name: pv_trafficlight
  consumer_version: "v1.1.0"        # Consumer版本
  bundle_version: "v1.1.0-release"  # Bundle版本（Consumer版本-类型）
  bundle_type: release
  
release_config:
  support_until: "2026-06-15"              # 长期支持
  quality_gate_passed: true                # 质量门控
```

**用途**：生产部署、长期支持、严格质量控制

## 命名规范

### **文件命名：`{consumer_name}-{consumer_version}-{bundle_identifier}.yaml`**

```
bundles/
├── weekly/                    # 固定周期
│   ├── end_to_end-v1.2.0-2025.25.yaml
│   └── foundational_model-v1.0.0-2025.25.yaml
├── snapshots/                 # 灵活使用
│   ├── foundational_model-v1.0.0-20250620-143500.yaml
│   └── debug_config-v1.0.0-20250621-090000.yaml
└── release/                   # 正式发布
    ├── pv_trafficlight-v1.1.0-release.yaml
    └── autonomous_driving-v2.0.0-release.yaml
```

## 核心配置格式

每个Bundle包含以下核心字段：

```yaml
# === 元数据 ===
meta:
  bundle_name: consumer_name
  consumer_version: "v1.2.0"       # Consumer版本
  bundle_version: "{consumer_version}-{identifier}"  # 包含Consumer版本的Bundle版本
  bundle_type: weekly|snapshot|release
  created_at: timestamp
  source_consumer: consumer_path

# === 追溯信息 ===  
conversion_source:
  consumer_config: path/to/consumer.yaml
  consumer_version: "v1.2.0"
  conversion_time: timestamp
  converted_by: converter_id

# === 版本清单 === (核心)
channels:
  - channel: channel_name
    available_versions: ["1.2.0", "1.1.0", "1.0.0"]  # 版本列表
    source_constraint: ">=1.0.0"                      # 原始约束
    required: true                                     # 是否必需
    on_missing: "fail"                                 # 缺失处理策略


# === 完整性验证 ===
integrity:
  constraint_hash: hash_value
  all_constraints_resolved: true
  total_channels: 4
```

## 使用流程

### 生成Bundle
```bash
# 周级Bundle - 生产环境
python scripts/bundle_generator.py --consumer consumers/end_to_end/latest.yaml --type weekly
# 生成: bundles/weekly/end_to_end-v1.2.0-2025.25.yaml

# 快照Bundle - 临时需求  
python scripts/bundle_generator.py --consumer consumers/foundational_model/latest.yaml --type snapshot
# 生成: bundles/snapshots/foundational_model-v1.0.0-20250620-143500.yaml

# 发布Bundle - 正式版本
python scripts/bundle_generator.py --consumer consumers/pv_trafficlight/latest.yaml --type release
# 生成: bundles/release/pv_trafficlight-v1.1.0-release.yaml
```

### 使用Bundle
```bash
# 加载指定Bundle
dataspec load --bundle bundles/weekly/end_to_end-v1.2.0-2025.25.yaml

# 验证Bundle完整性
dataspec verify --bundle bundles/release/pv_trafficlight-v1.1.0-release.yaml
```

## 版本管理一致性

Bundle 系统的关键设计原则是**文件名与内部版本字段完全一致**：

| Bundle类型 | 文件名格式 | bundle_version格式 | 示例 |
|-----------|-----------|-------------------|------|
| **Weekly** | `{consumer}-v{consumer_ver}-{year}.{week}.yaml` | `v{consumer_ver}-{year}.{week}` | `end_to_end-v1.2.0-2025.25.yaml` ↔ `"v1.2.0-2025.25"` |
| **Snapshot** | `{consumer}-v{consumer_ver}-{timestamp}.yaml` | `v{consumer_ver}-{timestamp}` | `foundational_model-v1.0.0-20250620-143500.yaml` ↔ `"v1.0.0-20250620-143500"` |
| **Release** | `{consumer}-v{consumer_ver}-release.yaml` | `v{consumer_ver}-release` | `pv_trafficlight-v1.1.0-release.yaml` ↔ `"v1.1.0-release"` |

### 一致性优势：
- **直观映射** - 文件名和内部版本字段直接对应
- **自动化友好** - 工具可以轻松解析和处理版本信息
- **追溯简单** - 从任何地方都能快速定位 Consumer 版本
- **管理统一** - 无需维护额外的版本映射关系

## 核心优势

1. **版本清单明确**：提供明确的可用版本列表，而非固定版本
2. **Consumer版本可见**：文件名和内部字段都直接体现Consumer版本
3. **完全可追溯**：精确记录从Consumer约束到版本列表的转换过程
4. **灵活适配**：支持动态数据环境，适应数据生产的渐进性
5. **易于维护**：清晰的目录结构和命名规范
6. **版本一致性**：文件名与内部版本字段完全一致，提升可维护性

## 与其他组件关系

```
Channels (数据规格) → Consumers (需求定义) → Bundles (版本清单) → 数据获取系统
     ↓                    ↓                   ↓                ↓
   固定格式            软约束范围          版本列表         智能版本选择
```

Bundle是整个数据链路的**版本快照节点**，提供从需求到数据获取的版本桥梁。 