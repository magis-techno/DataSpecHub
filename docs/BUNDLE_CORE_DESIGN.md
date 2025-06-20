# Bundle系统核心设计

## 设计原则：直击本质

Bundle系统专注于三个核心功能：
1. **硬约束快照** - 将Consumer的软约束转换为精确版本
2. **链路追溯** - 记录从Consumer到Bundle的完整转换路径  
3. **灵活周期** - 支持不同场景的版本管理需求

## 核心流程

```
Consumer配置 (软约束)  →  Bundle生成器  →  Bundle快照 (硬约束)
     ↓                      ↓                    ↓
版本范围约束           版本解析算法        精确版本锁定
 ">=1.0.0"         →  解析出最新版本  →    "1.2.0"
```

## Bundle类型设计

### 1. Weekly Bundle - 固定周期
```yaml
# bundles/weekly/end_to_end-2025.25.yaml
meta:
  bundle_version: 2025.25        # 年.周数格式
  bundle_type: weekly
  
channels:
  - channel: image_original
    version: "1.2.0"             # 硬锁定版本
    source_constraint: ">=1.0.0" # 追溯原始约束
```

**用途**：生产环境、定期发布、团队协作的标准版本

### 2. Snapshot Bundle - 灵活使用  
```yaml
# bundles/snapshots/model-20250620-143500.yaml
meta:
  bundle_version: "20250620-143500"  # 时间戳
  bundle_type: snapshot
  
snapshot_config:
  ttl_hours: 168                     # 自动过期
  purpose: "快速验证实验"
```

**用途**：临时需求、快速验证、实验性工作

### 3. Release Bundle - 正式发布
```yaml
# bundles/release/pv_trafficlight-v1.1.0.yaml
meta:
  bundle_version: "v1.1.0"          # 语义化版本
  bundle_type: release
  
release_config:
  support_until: "2026-06-20"       # 长期支持
  quality_gate_passed: true         # 质量门控
```

**用途**：生产部署、长期支持、严格质量控制

## 目录结构

```
bundles/
├── weekly/                    # 固定周期
│   ├── end_to_end-2025.25.yaml
│   └── foundational_model-2025.25.yaml
├── snapshots/                 # 灵活使用
│   ├── model-20250620-143500.yaml
│   └── test-20250621-090000.yaml
└── release/                   # 正式发布
    ├── pv_trafficlight-v1.1.0.yaml
    └── autonomous_driving-v2.0.0.yaml
```

## 核心配置格式

每个Bundle包含以下核心字段：

```yaml
# === 元数据 ===
meta:
  bundle_name: consumer_name
  bundle_version: version_identifier
  bundle_type: weekly|snapshot|release
  created_at: timestamp
  source_consumer: consumer_path

# === 追溯信息 ===  
source_consumer: path/to/consumer.yaml
snapshot_time: timestamp

# === 硬约束内容 === (核心)
channels:
  - channel: channel_name
    version: "exact.version"     # 精确版本
    locked_at: timestamp         # 锁定时间
    source_constraint: original  # 原始约束
    spec_file: path/to/spec.yaml

# === 完整性验证 ===
integrity_hash: hash_value
```

## 使用流程

### 生成Bundle
```bash
# 周级Bundle - 生产环境
python scripts/bundle_generator.py --consumer consumers/end_to_end/latest.yaml --type weekly

# 快照Bundle - 临时需求  
python scripts/bundle_generator.py --consumer consumers/test_config.yaml --type snapshot

# 发布Bundle - 正式版本
python scripts/bundle_generator.py --consumer consumers/prod/v1.1.0.yaml --type release
```

### 使用Bundle
```bash
# 加载指定Bundle
dataspec load --bundle bundles/weekly/end_to_end-2025.25.yaml

# 验证Bundle完整性
dataspec verify --bundle bundles/release/pv_trafficlight-v1.1.0.yaml
```

## 核心优势

1. **简洁明确**：专注于版本锁定和追溯，去除冗余功能
2. **可重现性**：精确版本保证下游活动100%可重现
3. **多场景支持**：三种类型覆盖不同的使用场景
4. **易于维护**：清晰的目录结构和配置格式

## 与其他组件关系

```
Channels (数据规格) → Consumers (需求定义) → Bundles (版本快照) → 下游应用
     ↓                    ↓                   ↓             ↓
   固定格式            软约束范围           硬约束版本    可重现加载
```

Bundle是整个数据链路的**版本快照节点**，确保从需求到使用的完整可追溯性。 