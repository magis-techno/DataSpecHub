# Bundle类型使用需求分析

## 使用需求映射

基于实际业务场景，三种Bundle类型分别满足不同的使用需求：

```
业务需求层次     →    Bundle类型     →    特征
生产部署         →    Release       →    长期稳定
定期协作         →    Weekly        →    固定节拍  
临时验证         →    Snapshots     →    快速灵活
```

## 1. Release Bundle - 正式发布版本

### 使用场景
- **生产环境部署** - 严格质量控制的生产数据版本
- **客户交付** - 向外部客户交付的数据包
- **里程碑发布** - 重大功能更新的正式版本
- **长期支持** - 需要维护和支持的稳定版本

### 目标用户
- 生产运维团队
- 产品发布经理
- 客户交付团队
- 质量保证团队

### 生命周期特征
```yaml
# 发布版本特征
lifecycle:
  planning_period: "2-4周"          # 规划周期长
  quality_gates: "严格"             # 多重质量门控
  support_duration: "6-12个月"       # 长期支持
  backward_compatibility: "必须"     # 必须向后兼容
  approval_required: true           # 需要正式审批
```

### 实际需求示例

**场景1：自动驾驶系统v2.0发布**
```bash
# 使用需求：新算法正式上线，需要严格验证的数据版本
python scripts/bundle_generator.py \
  --consumer consumers/autonomous_driving/v2.0.0.yaml \
  --type release

# 生成：bundles/release/autonomous_driving-v2.0.0.yaml
# 特点：经过完整QA流程，支持1年，有回滚计划
```

**场景2：客户交付数据包**
```bash
# 使用需求：向车厂客户交付训练数据包
python scripts/bundle_generator.py \
  --consumer consumers/customer_delivery/oem_a.yaml \
  --type release

# 生成：bundles/release/oem_a-v1.3.0.yaml  
# 特点：数据完整性验证，法律合规检查，长期维护
```

## 2. Weekly Bundle - 固定周期版本

### 使用场景
- **团队协作同步** - 保证团队使用相同的数据版本
- **定期训练任务** - 每周定期的模型训练
- **集成测试环境** - 持续集成的标准数据环境
- **进度同步节点** - 项目进度的数据版本里程碑

### 目标用户
- 算法开发团队
- 模型训练工程师
- 集成测试团队
- 项目管理人员

### 生命周期特征
```yaml
# 周级版本特征
lifecycle:
  generation_schedule: "每周一10:00"   # 固定生成时间
  retention_period: "4周"            # 保留4个版本
  stability_level: "测试稳定"         # 适合开发测试
  auto_generation: true              # 自动生成
  team_notification: true            # 自动通知团队
```

### 实际需求示例

**场景1：端到端团队周例会**
```bash
# 使用需求：每周一团队例会前，生成统一的数据版本
# 自动任务：每周一上午10:00自动执行
python scripts/bundle_generator.py \
  --consumer consumers/end_to_end/latest.yaml \
  --type weekly

# 生成：bundles/weekly/end_to_end-2025.25.yaml
# 团队收到通知：📅 Weekly Bundle 2025.25 已生成，请更新本地环境
```

**场景2：模型训练Pipeline**
```bash
# 使用需求：每周定期训练模型，使用固定的数据版本基线
# CI/CD Pipeline中使用
dataspec load --bundle bundles/weekly/perception_training-2025.25.yaml
python train_model.py --config weekly_training.yaml

# 结果：每周训练结果可对比，数据版本一致性保证
```

**场景3：多团队协作**
```yaml
# 团队协作场景
teams:
  perception_team:
    usage: "使用weekly bundle进行算法开发"
    sync_schedule: "每周一检查新版本"
    
  training_team:
    usage: "基于weekly bundle进行模型训练"
    dependency: "perception_team的算法更新"
    
  testing_team:
    usage: "使用weekly bundle进行回归测试"
    trigger: "新weekly bundle生成后24小时内"
```

## 3. Snapshots Bundle - 临时快照版本

### 使用场景
- **快速验证实验** - 临时数据需求的快速响应
- **POC概念验证** - 新想法的快速试验
- **Bug调试** - 特定问题的数据重现
- **临时需求** - 紧急或短期的数据需求

### 目标用户
- 算法研究员
- 实验工程师
- 问题调试人员
- 业务分析师

### 生命周期特征
```yaml
# 快照版本特征
lifecycle:
  creation_time: "即时"              # 随时创建
  ttl: "7-30天"                    # 短期有效
  auto_cleanup: true               # 自动清理
  approval_required: false         # 无需审批
  purpose_tracking: true           # 用途追踪
```

### 实际需求示例

**场景1：算法研究员的新想法验证**
```bash
# 使用需求：想测试新的融合算法，需要特定的数据组合
python scripts/bundle_generator.py \
  --consumer consumers/experiments/radar_fusion_test.yaml \
  --type snapshot

# 生成：bundles/snapshots/radar_fusion_test-20250620-143500.yaml
# 特点：7天后自动清理，用途明确标记
```

**场景2：紧急Bug调试**
```bash
# 使用需求：生产环境出现问题，需要复现特定版本组合
# 临时创建consumer配置
cat > consumers/debug/emergency_debug.yaml << EOF
meta:
  consumer: emergency_debug
  purpose: "复现生产环境Issue #1234"
requirements:
  - channel: image_original
    version: "1.1.8"  # 出问题时的版本
  - channel: object_array_fusion_infer  
    version: "1.1.9"  # 出问题时的版本
EOF

python scripts/bundle_generator.py \
  --consumer consumers/debug/emergency_debug.yaml \
  --type snapshot

# 生成：bundles/snapshots/emergency_debug-20250620-153000.yaml
# 用于：本地复现问题，找到根因后清理
```

**场景3：业务团队临时数据需求**
```bash
# 使用需求：市场团队需要特定场景的数据进行分析
python scripts/bundle_generator.py \
  --consumer consumers/business/market_analysis_temp.yaml \
  --type snapshot

# 特点：
# - 无需走正式流程
# - 2周后自动过期
# - 数据使用有审计记录
```

## 使用决策树

```
数据需求分析
├── 用途期限？
│   ├── 长期使用(>3个月) → Release Bundle
│   ├── 定期使用(周期性) → Weekly Bundle  
│   └── 短期使用(<1个月) → Snapshots Bundle
│
├── 质量要求？
│   ├── 生产级别 → Release Bundle
│   ├── 开发级别 → Weekly Bundle
│   └── 实验级别 → Snapshots Bundle
│
└── 审批流程？
    ├── 需要正式审批 → Release Bundle
    ├── 团队内协调 → Weekly Bundle
    └── 个人/小组使用 → Snapshots Bundle
```

## 管理策略

### 自动化管理
```bash
# Weekly Bundle - 自动生成
# crontab: 0 10 * * 1  # 每周一10:00
/scripts/auto_weekly_bundle.sh

# Snapshots - 自动清理  
# crontab: 0 2 * * *   # 每天凌晨2:00
/scripts/cleanup_expired_snapshots.sh

# Release - 手动管理，严格控制
# 需要通过正式的发布流程
```

### 监控告警
```yaml
monitoring:
  weekly_bundle:
    alert_if: "生成失败或延迟超过30分钟"
    notification: "team-channel"
    
  snapshots:
    alert_if: "数量超过50个"
    action: "提醒清理旧快照"
    
  release:
    alert_if: "质量检查失败"  
    action: "阻止发布，通知相关人员"
```

## 总结

三种Bundle类型形成了完整的数据版本管理体系：

- **Release**: 生产环境的稳定基石
- **Weekly**: 团队协作的同步节拍  
- **Snapshots**: 敏捷开发的灵活工具

通过这种分层设计，既保证了生产环境的稳定性，又满足了开发过程中的灵活性需求。 