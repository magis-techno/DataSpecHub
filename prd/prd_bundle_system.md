# PRD — Bundle & Lock System

## 1. Purpose
解决业务团队聚合版本需求和数据版本共存管理问题，提供可复现的数据集快照。

### 核心问题
- **版本共存困境**：一个数据通道存在多个版本，有些共存、有些老化无用，缺乏清晰的生命周期管理
- **聚合版本需求**：业务团队选择多个通道及版本后，需要统一的版本号标识（如选择7个通道形成一个聚合版本）
- **可复现性缺失**：历史实验/训练无法精确复现，因为缺乏当时使用的确切版本快照

### Consumers vs Bundles 定位差异

| 维度 | `consumers/` | `bundles/` |
|------|-------------|------------|
| **定位** | "愿景/意图"清单 | "可复现快照" |
| **内容** | 业务团队列出想要哪些通道、允许的版本范围、缺失时的默认处理 | 当业务需要锁死一组通道与具体版本时的硬锁定配置 |
| **生命周期** | 长期，随业务功能演进而迭代，变化频率较高 | 阶段性/里程碑，一旦发布就不轻易改动，只追加新版本号 |
| **典型问题** | "我要新增一条数据通道，老版本能否兜底？"<br/>"替换雷达v2会不会影响红绿灯模块？" | "6月底交付的训练集到底用的哪一版传感器格式？"<br/>"我要复现实验X，直接拉e2e:2025.24 Bundle就能跑" |

**理解要点**：
- `consumers/*.yaml` = 需求池（软约束、范围）
- `bundles/**/bundle-*.yaml` = 出货快照（硬锁定）

## 2. Functional Requirements

### 2.1 版本共存管理
1. **生命周期状态追踪**：`active` | `deprecated` | `legacy` | `archived`
2. **版本依赖图**：自动分析通道间的依赖关系和兼容性
3. **老化策略**：定义版本的支持期限和迁移路径

### 2.2 聚合版本生成
1. **Bundle创建**：从Consumer意图生成具体的版本锁定文件
2. **版本解析**：根据版本约束（`>=1.0.0 <2.0.0`, `^2.1.0`）解析出具体版本
3. **冲突检测**：检测版本约束冲突并提供解决建议
4. **Lock文件生成**：生成确定性的`.lock.json`文件

### 2.3 快照管理
1. **不可变快照**：Bundle一旦创建，内容不可修改（只能创建新版本）
2. **快照验证**：验证Bundle中所有通道版本的可用性和兼容性
3. **快照复现**：基于Bundle快照精确复现历史环境

### 2.4 CLI工具集
```bash
# 从Consumer配置创建Bundle
dataspec bundle create --from-consumer autonomous_driving --name e2e --version 2025.24

# 验证Bundle完整性
dataspec bundle validate bundles/e2e/bundle-2025.24.yaml

# 基于Bundle生成Lock文件
dataspec bundle lock bundles/e2e/bundle-2025.24.yaml

# 版本冲突分析
dataspec bundle analyze --conflicts bundles/e2e/bundle-2025.24.yaml

# 版本升级建议
dataspec bundle upgrade --from 2025.24 --to 2025.25 --dry-run
```

## 3. Non‑Functional Requirements

### 3.1 性能要求
- Bundle创建 < 5 min for 100 channels
- Lock文件生成具有确定性（same input → same hash）
- 版本解析 < 10s for complex dependency graphs

### 3.2 可靠性要求
- Bundle快照不可变性保证
- 版本冲突检测准确率 > 99%
- 历史Bundle的长期可访问性

### 3.3 可用性要求
- CLI工具简单易用，支持交互式向导
- Bundle配置支持YAML schema验证
- 清晰的错误信息和修复建议

## 4. Technical Design

### 4.1 Bundle配置结构
```yaml
meta:
  bundle: e2e
  version: '2025.24'
  created_from: consumers/autonomous_driving.yaml  # 来源Consumer
  snapshot_date: '2025-01-15T10:30:00Z'
  
# 版本解析结果（从Consumer的范围约束解析出的具体版本）
resolved_versions:
  img_cam1: '1.2.3'
  lidar: '2.1.0' 
  radar.v2: '2.0.5'
  
# 硬锁定的通道配置
channels:
  - channel: img_cam1
    version: '1.2.3'  # 精确版本，不再是范围
    locked_at: '2025-01-15T10:30:00Z'
    source_commit: 'abc123def'  # 规格定义的Git commit
    
# 版本共存处理
coexistence:
  - channels: [radar.v1, radar.v2]
    strategy: parallel  # 并行共存
    migration_deadline: '2025-06-01'
    
# 兼容性验证结果
compatibility_matrix:
  validated_at: '2025-01-15T10:30:00Z'
  all_compatible: true
  warnings: []
```

### 4.2 Lock文件格式
```json
{
  "bundle_ref": "bundles/e2e/bundle-2025.24.yaml",
  "lock_version": "1.0",
  "generated_at": "2025-01-15T10:30:00Z",
  "channels": {
    "img_cam1": {
      "version": "1.2.3",
      "spec_hash": "sha256:abc123...",
      "data_locations": ["/data/prod-2025-001/img_cam1"],
      "sample_count": 15000
    }
  },
  "integrity_hash": "sha256:def456..."
}
```

## 5. Acceptance Criteria

### 5.1 基本功能验证
- [ ] 从Consumer配置成功创建Bundle
- [ ] Bundle验证通过且生成Lock文件
- [ ] 基于Bundle快照可完整复现数据环境
- [ ] 版本冲突能被准确检测并提供解决方案

### 5.2 业务场景验证
- [ ] **聚合版本场景**：选择7个通道后生成统一的Bundle版本号
- [ ] **版本共存场景**：radar.v1和radar.v2可以在同一Bundle中并存
- [ ] **可复现场景**：6个月后仍能基于历史Bundle精确复现实验环境
- [ ] **升级场景**：Bundle版本升级时提供清晰的变更说明和影响分析

### 5.3 集成验证
- [ ] GitHub Actions自动验证Bundle配置
- [ ] 与需求管理系统的工单关联
- [ ] CLI工具的用户体验符合预期
