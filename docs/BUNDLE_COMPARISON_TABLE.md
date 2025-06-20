# Bundle类型对比表

## 核心特征对比

| 维度 | Release Bundle | Weekly Bundle | Snapshots Bundle |
|------|----------------|---------------|------------------|
| **主要用途** | 生产部署、客户交付 | 团队协作、定期训练 | 快速验证、临时试验 |
| **版本格式** | v1.2.0 (语义化) | 2025.25 (年.周) | 20250620-143500 (时间戳) |
| **生命周期** | 6-12个月 | 4周 | 7-30天 |
| **质量要求** | 生产级 | 开发级 | 实验级 |
| **审批流程** | 严格审批 | 团队协调 | 无需审批 |
| **自动化** | 手动发布 | 自动生成 | 即时创建 |
| **向后兼容** | 必须保证 | 尽量保证 | 无需保证 |

## 使用频率和用户群体

| Bundle类型 | 创建频率 | 主要用户 | 使用场景数量 |
|------------|----------|----------|-------------|
| **Release** | 每月1-2次 | 运维、产品、客户 | 少而精 (5-10个/年) |
| **Weekly** | 每周1次 | 开发、测试、训练 | 定期稳定 (52个/年) |
| **Snapshots** | 随时创建 | 研究、调试、分析 | 大量临时 (200+个/年) |

## 技术实现差异

### Release Bundle
```yaml
特征:
  stability_check: "全面回归测试"
  quality_gates: ["代码审查", "性能测试", "安全扫描"]
  documentation: "完整发布说明"
  rollback_plan: "详细回滚方案"
  support_team: "专门运维团队"

示例配置:
  meta:
    bundle_type: release
    version: "v1.2.0"
    support_until: "2026-06-20"
    quality_gate_passed: true
```

### Weekly Bundle  
```yaml
特征:
  auto_generation: "每周一10:00"
  team_notification: "自动通知相关团队"
  regression_test: "基础兼容性测试"
  retention_policy: "保留最近4个版本"
  collaboration_tool: "团队协作基准"

示例配置:
  meta:
    bundle_type: weekly
    version: "2025.25"
    auto_cleanup: "4周后"
    team_sync: true
```

### Snapshots Bundle
```yaml
特征:
  instant_creation: "立即生成"
  purpose_tracking: "明确使用目的"
  auto_cleanup: "TTL自动清理"
  minimal_validation: "基础格式检查"
  audit_trail: "使用审计记录"

示例配置:
  meta:
    bundle_type: snapshot
    version: "20250620-143500"
    ttl_hours: 168
    purpose: "radar融合算法验证"
```

## 决策流程图

```
收到数据需求
├── 是否用于生产？
│   ├── 是 → 是否需要长期维护？
│   │   ├── 是 → Release Bundle
│   │   └── 否 → Weekly Bundle
│   └── 否 → 是否团队共用？
│       ├── 是 → Weekly Bundle
│       └── 否 → Snapshots Bundle
│
├── 紧急程度如何？
│   ├── 紧急 → Snapshots Bundle
│   ├── 常规 → Weekly Bundle
│   └── 计划 → Release Bundle
│
└── 质量要求如何？
    ├── 严格 → Release Bundle
    ├── 一般 → Weekly Bundle
    └── 宽松 → Snapshots Bundle
```

## 实际工作流示例

### 典型的一周工作流
```
周一:
- 09:00 自动生成Weekly Bundle (2025.25)
- 10:00 团队收到通知，开始使用新版本
- 11:00 开发者创建Snapshots验证新想法

周二-周四:
- 研究员创建多个Snapshots进行实验
- 开发团队基于Weekly Bundle进行开发
- 测试团队使用Weekly Bundle进行回归测试

周五:
- 评估本周实验结果
- 清理过期的Snapshots
- 规划下周的工作内容

月末:
- 评估Monthly Release的准备情况
- 将稳定的Weekly功能合并到Release分支
```

### 不同角色的使用模式

**算法研究员**
```bash
# 90%使用Snapshots，10%使用Weekly
python scripts/bundle_generator.py --consumer research/new_idea.yaml --type snapshot
python scripts/bundle_generator.py --consumer research/baseline.yaml --type weekly
```

**模型训练工程师**  
```bash
# 80%使用Weekly，20%使用Snapshots
dataspec load --bundle bundles/weekly/training-2025.25.yaml  # 主要训练
python scripts/bundle_generator.py --consumer debug/training_issue.yaml --type snapshot  # 调试
```

**生产运维工程师**
```bash
# 95%使用Release，5%使用Weekly
dataspec load --bundle bundles/release/production-v2.1.0.yaml  # 生产部署
dataspec load --bundle bundles/weekly/staging-2025.25.yaml    # 预发布验证
```

## 存储和清理策略

| Bundle类型 | 存储位置 | 保留策略 | 清理策略 |
|------------|----------|----------|----------|
| **Release** | `bundles/release/` | 永久保留 | 手动清理，需审批 |
| **Weekly** | `bundles/weekly/` | 保留4个版本 | 自动清理旧版本 |
| **Snapshots** | `bundles/snapshots/` | TTL过期 | 自动清理，无需审批 |

## 监控指标

```yaml
metrics:
  release_bundle:
    success_rate: ">99%"
    deployment_time: "<30min"
    rollback_frequency: "<1%"
    
  weekly_bundle:
    generation_punctuality: ">95%"
    team_adoption_rate: ">90%"
    version_skipping: "<10%"
    
  snapshots_bundle:
    creation_latency: "<5min"
    cleanup_efficiency: ">95%"
    storage_utilization: "<80%"
```

这样的分层设计确保了：
- **Release**: 生产环境的稳定可靠
- **Weekly**: 团队协作的规范有序  
- **Snapshots**: 研发过程的敏捷灵活 