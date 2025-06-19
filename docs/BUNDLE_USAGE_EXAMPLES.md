# Bundle系统使用示例

本文档通过具体示例展示Bundle系统如何解决版本共存、聚合版本和可复现性问题。

## 核心概念回顾

### Consumers vs Bundles 定位差异

| 维度 | `consumers/` | `bundles/` |
|------|-------------|------------|
| **定位** | "愿景/意图"清单 | "可复现快照" |
| **约束类型** | 软约束、版本范围 | 硬锁定、精确版本 |
| **变化频率** | 高频变化，随需求演进 | 低频变化，里程碑式发布 |
| **使用场景** | 需求规划、兼容性评估 | 数据交付、实验复现 |

## 实际应用场景

### 场景1：业务团队的聚合版本需求

**问题**：自动驾驶团队需要选择7个通道的特定版本组合，形成一个统一的版本标识。

#### 步骤1：定义Consumer意图
```yaml
# consumers/autonomous_driving.yaml
meta:
  consumer: autonomous_driving
  owner: "ad-team@company.com"
  
requirement_groups:
  core_sensors:
    requirements:
      - channel: img_cam1
        version: ">=1.0.0 <2.0.0"  # 范围约束
        required: true
        priority: critical
        
      - channel: lidar
        version: ">=2.0.0"
        required: true
        priority: critical
        
      - channel: radar.v2
        version: "^2.0.0"
        required: false
        on_missing: substitute
        substitute_with:
          channel: radar.v1
          version: "1.0.0"
          
  positioning:
    requirements:
      - channel: utils
        version: ">=1.0.0"
        required: true
        
      - channel: ego_pose
        version: ">=1.0.0"
        required: true
        
      - channel: calib
        version: ">=1.0.0"
        required: true
        
  perception:
    requirements:
      - channel: object_array_fusion
        version: ">=1.0.0"
        required: true
```

#### 步骤2：生成Bundle快照
```bash
# 使用CLI从Consumer创建Bundle
python scripts/bundle_manager.py create \
  --from-consumer autonomous_driving \
  --name ad_training \
  --version 2025.24

# 输出结果
🔨 Creating bundle 'ad_training:2025.24' from consumer 'autonomous_driving'...
✅ No conflicts detected
📦 Bundle saved to: bundles/ad_training/bundle-2025.24.yaml

📋 Resolved 7 channels:
  - img_cam1: 1.2.3
  - lidar: 2.1.0
  - radar.v2: 2.0.5
  - utils: 1.3.2
  - ego_pose: 1.1.0
  - calib: 1.0.1
  - object_array_fusion: 1.4.0
```

#### 步骤3：生成的Bundle配置
```yaml
# bundles/ad_training/bundle-2025.24.yaml
meta:
  bundle: ad_training
  version: '2025.24'  # 统一的聚合版本号
  created_from: consumers/autonomous_driving.yaml
  
resolved_versions:
  img_cam1: '1.2.3'
  lidar: '2.1.0'
  radar.v2: '2.0.5'
  utils: '1.3.2'
  ego_pose: '1.1.0'
  calib: '1.0.1'
  object_array_fusion: '1.4.0'
  
channels:
  - channel: img_cam1
    version: '1.2.3'  # 精确版本，不再是范围
    locked_at: '2025-06-15T10:30:00Z'
    priority: critical
    
  # ... 其他通道的精确版本锁定
```

**结果**：团队现在有了一个统一的版本标识 `ad_training:2025.24`，包含7个通道的确切版本组合。

### 场景2：版本共存管理

**问题**：radar.v1和radar.v2需要并存，有些场景用v2，有些场景需要v1兜底。

#### Consumer配置支持版本共存
```yaml
# consumers/radar_transition.yaml
meta:
  consumer: radar_transition
  description: "雷达版本过渡期的共存需求"
  
requirement_groups:
  radar_coexistence:
    requirements:
      - channel: radar.v2
        version: "^2.0.0"
        required: false
        priority: high
        
      - channel: radar.v1
        version: "1.0.0"
        required: false
        priority: medium
        usage: fallback  # 标记为备用
        
  base_sensors:
    requirements:
      - channel: img_cam1
        version: ">=1.0.0"
        required: true
```

#### 生成的Bundle支持共存
```yaml
# bundles/radar_transition/bundle-2025.24.yaml
coexistence:
  - name: "radar_transition"
    channels: [radar.v1, radar.v2]
    strategy: parallel
    primary: radar.v2
    fallback: radar.v1
    migration_deadline: '2025-12-01'
    
channels:
  - channel: radar.v2
    version: '2.0.5'
    usage: primary
    
  - channel: radar.v1
    version: '1.0.0'
    usage: fallback
```

#### 使用CLI分析版本兼容性
```bash
python scripts/bundle_manager.py analyze \
  bundles/radar_transition/bundle-2025.24.yaml \
  --conflicts

# 输出
📊 Analyzing bundle: bundles/radar_transition/bundle-2025.24.yaml

📈 Bundle Statistics:
  - Total channels: 3
  - Bundle version: 2025.24

📊 Version Distribution:
  - v1.x: 1 channels
  - v2.x: 2 channels

✅ No conflicts detected
```

### 场景3：历史实验的精确复现

**问题**：6个月前的训练实验需要精确复现，但不记得当时用的具体版本。

#### 历史Bundle快照
```yaml
# bundles/perception_training/bundle-2024.48.yaml (6个月前)
meta:
  bundle: perception_training
  version: '2024.48'
  snapshot_date: '2024-12-01T10:00:00Z'
  
resolved_versions:
  img_cam1: '1.1.5'    # 当时的版本
  lidar: '2.0.3'       # 当时的版本
  radar.v2: '2.0.2'    # 当时的版本
  
channels:
  - channel: img_cam1
    version: '1.1.5'
    locked_at: '2024-12-01T10:00:00Z'
    source_commit: 'abc123'
    data_path: '/data/training-2024-48/img_cam1'
    sample_count: 20000
```

#### 生成Lock文件确保完整性
```bash
python scripts/bundle_manager.py lock \
  bundles/perception_training/bundle-2024.48.yaml

# 生成 bundle-2024.48.lock.json
{
  "bundle_ref": "bundles/perception_training/bundle-2024.48.yaml",
  "lock_version": "1.0",
  "generated_at": "2024-12-01T10:00:00Z",
  "channels": {
    "img_cam1": {
      "version": "1.1.5",
      "spec_hash": "sha256:abc123def456...",
      "locked_at": "2024-12-01T10:00:00Z",
      "source_commit": "abc123"
    }
  },
  "integrity_hash": "sha256:def456789..."
}
```

#### 复现实验
```bash
# 基于历史Bundle复现环境
dataspec load --bundle bundles/perception_training/bundle-2024.48.yaml
# 或者使用Lock文件
dataspec load --lock bundles/perception_training/bundle-2024.48.lock.json
```

### 场景4：Bundle版本升级和影响分析

**问题**：需要从2025.24升级到2025.30，但要了解变更影响。

#### 升级分析
```bash
python scripts/bundle_manager.py upgrade \
  --from bundles/e2e/bundle-2025.24.yaml \
  --to bundles/e2e/bundle-2025.30.yaml \
  --dry-run

# 输出升级分析
🔄 Bundle Upgrade Analysis: 2025.24 → 2025.30

📈 Channel Changes:
  ✅ img_cam1: 1.2.3 → 1.2.4 (patch update, backward compatible)
  ⚠️  lidar: 2.1.0 → 2.2.0 (minor update, new features added)
  ❌ radar.v2: 2.0.5 → 3.0.0 (major update, breaking changes)
  
🔍 Impact Analysis:
  - 3 consumers affected by radar.v2 major update
  - Migration guide available: docs/radar-v3-migration.md
  - Estimated migration effort: 2-3 days
  
⚠️  Recommendations:
  - Test radar.v2 v3.0.0 in staging environment
  - Update consumer configurations before deployment
  - Consider gradual rollout strategy
```

## 最佳实践

### 1. Consumer配置最佳实践

```yaml
# ✅ 好的Consumer配置
meta:
  consumer: my_application
  owner: "team@company.com"
  version: "1.0.0"  # Consumer配置本身也有版本
  
requirement_groups:
  # 按功能模块组织
  core_perception:
    description: "核心感知算法需求"
    requirements:
      - channel: img_cam1
        version: ">=1.0.0 <2.0.0"  # 明确的版本范围
        required: true
        priority: critical
        rationale: "主要的视觉输入源"  # 说明使用原因
        
  optional_enhancement:
    description: "可选的增强功能"
    requirements:
      - channel: radar.v2
        version: "^2.0.0"
        required: false
        on_missing: ignore
        priority: low
        
# 环境特定配置
environments:
  development:
    relaxed_requirements: true
  production:
    strict_validation: true
    
# 与需求管理系统集成
integration:
  jira_epic: "PROJ-2024-001"
  approval_status: "approved"
```

### 2. Bundle命名和版本管理

```bash
# 命名规范
bundles/
├── e2e/                    # 端到端测试
│   ├── bundle-2025.24.yaml # 年份.周数
│   └── bundle-2025.30.yaml
├── perception_training/    # 感知训练
│   ├── bundle-v1.0.0.yaml  # 语义化版本
│   └── bundle-v1.1.0.yaml
└── production/            # 生产数据
    ├── bundle-prod-2025-q1.yaml  # 季度版本
    └── bundle-prod-2025-q2.yaml
```

### 3. 版本共存策略

```yaml
# 在Bundle中明确共存策略
coexistence:
  - name: "sensor_migration"
    channels: [old_sensor, new_sensor]
    strategy: parallel      # parallel | sequential | exclusive
    primary: new_sensor
    fallback: old_sensor
    migration_deadline: '2025-12-01'
    migration_plan: |
      Phase 1: Parallel deployment (Q3 2025)
      Phase 2: Primary switch (Q4 2025)
      Phase 3: Legacy removal (Q1 2026)
```

### 4. 质量门控

```yaml
# Bundle质量要求
quality_gates:
  - gate: "minimum_samples"
    threshold: 1000
    description: "每个通道至少1000个样本"
    
  - gate: "compatibility_check"
    description: "所有通道版本兼容性检查"
    
  - gate: "data_integrity"
    threshold: 0.95
    description: "数据完整性评分 > 95%"
```

## 故障排除

### 常见问题

1. **版本解析失败**
```bash
# 检查可用版本
python scripts/bundle_manager.py list-versions --channel img_cam1

# 验证版本约束
python scripts/bundle_manager.py resolve-version \
  --channel img_cam1 --constraint ">=1.0.0 <2.0.0"
```

2. **版本冲突**
```bash
# 分析冲突详情
python scripts/bundle_manager.py analyze \
  bundles/my_bundle/bundle-2025.24.yaml --conflicts
  
# 获取解决建议
python scripts/bundle_manager.py suggest-resolution \
  --conflicts bundles/my_bundle/bundle-2025.24.yaml
```

3. **Bundle验证失败**
```bash
# 详细验证
python scripts/bundle_manager.py validate \
  bundles/my_bundle/bundle-2025.24.yaml --verbose
  
# 检查数据完整性
python scripts/bundle_manager.py check-integrity \
  bundles/my_bundle/bundle-2025.24.lock.json
```

通过这些示例，您可以看到Bundle系统如何有效解决版本共存、聚合版本管理和实验复现等核心问题。 