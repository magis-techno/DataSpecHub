# Bundle使用场景分析 - 版本清单模式

## 使用需求映射

基于实际业务场景，三种Bundle类型分别满足不同的使用需求：

```
业务需求层次     →    Bundle类型     →    特征
生产部署         →    Release       →    经过验证的版本清单
定期协作         →    Weekly        →    固定节拍的版本快照  
临时验证         →    Snapshots     →    快速灵活的实验清单
```

## 1. Release Bundle - 正式发布版本

### 使用场景
- **生产环境部署** - 经过严格质量验证的版本清单
- **客户交付** - 向外部客户交付的数据版本组合
- **里程碑发布** - 重大功能更新的正式版本
- **长期支持** - 需要维护和支持的稳定版本清单

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

**场景1：红绿灯检测系统v1.1.0发布**
```bash
# 使用需求：红绿灯检测新算法正式上线
python scripts/bundle_generator.py \
  --consumer consumers/pv_trafficlight/latest.yaml \
  --type release

# 生成：bundles/release/pv_trafficlight-v1.1.0-release.yaml
# 特点：
# - Consumer版本 v1.1.0 体现在文件名中
# - 版本清单: image_original ["1.2.0"], occupancy ["1.0.0"]
# - 经过完整QA流程，支持1年，有回滚计划
```

**场景2：客户交付数据包**
```bash
# 使用需求：向车厂客户交付训练数据包
python scripts/bundle_generator.py \
  --consumer consumers/customer_delivery/oem_a-v2.0.0.yaml \
  --type release

# 生成：bundles/release/oem_a-v2.0.0-release.yaml  
# 特点：包含明确的版本清单，法律合规检查，长期维护
```

## 2. Weekly Bundle - 固定周期版本

### 使用场景
- **团队协作同步** - 保证团队使用相同的版本清单
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
# 使用需求：每周一团队例会前，生成统一的版本清单
# 自动任务：每周一上午10:00自动执行
python scripts/bundle_generator.py \
  --consumer consumers/end_to_end/latest.yaml \
  --type weekly

# 生成：bundles/weekly/end_to_end-v1.2.0-2025.25.yaml
# 版本清单内容：
#   image_original: ["1.2.0"]
#   object_array_fusion_infer: ["1.2.0", "1.1.0", "1.0.0"]
#   occupancy: ["1.0.0"] 
#   utils_slam: ["1.1.0", "1.0.0"]
# 团队收到通知：📅 Weekly Bundle 2025.25 已生成，包含4个channel的版本清单
```

**场景2：模型训练Pipeline**
```bash
# 使用需求：每周定期训练模型，使用固定的版本清单基线
# CI/CD Pipeline中使用
dataspec load --bundle bundles/weekly/end_to_end-v1.2.0-2025.25.yaml
python train_model.py --config weekly_training.yaml

# 结果：每周训练结果可对比，版本清单一致性保证
```

**场景3：多团队协作**
```yaml
# 团队协作场景
teams:
  perception_team:
    usage: "使用weekly bundle的版本清单进行算法开发"
    sync_schedule: "每周一检查新版本清单"
    
  training_team:
    usage: "基于weekly bundle版本清单进行模型训练"
    dependency: "perception_team的算法更新"
    
  testing_team:
    usage: "使用weekly bundle版本清单进行回归测试"
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
# 使用需求：测试新的多模态融合算法，需要特定的数据组合
python scripts/bundle_generator.py \
  --consumer consumers/experiments/multimodal_fusion_test.yaml \
  --type snapshot

# 生成：bundles/snapshots/multimodal_fusion_test-v1.0.0-20250620-143500.yaml
# 版本清单特点：
#   - 支持多版本并行: image_original ["1.2.0", "1.1.0", "1.0.0"]
#   - 实验用途标记: experiment_role字段
#   - 7天后自动清理
```

**场景2：紧急Bug调试**
```bash
# 使用需求：生产环境出现问题，需要复现特定版本组合
# 临时创建consumer配置
cat > consumers/debug/emergency_debug-v1.0.0.yaml << EOF
meta:
  consumer: emergency_debug
  version: "v1.0.0"
  purpose: "复现生产环境Issue #1234"
requirements:
  - channel: image_original
    version: "1.1.8"  # 出问题时的版本
  - channel: object_array_fusion_infer  
    version: "1.1.9"  # 出问题时的版本
EOF

python scripts/bundle_generator.py \
  --consumer consumers/debug/emergency_debug-v1.0.0.yaml \
  --type snapshot

# 生成：bundles/snapshots/emergency_debug-v1.0.0-20250620-153000.yaml
# 用于：本地复现问题，找到根因后清理
```

**场景3：基础模型实验**
```bash
# 使用需求：智能驾驶大模型团队需要多模态训练数据验证
python scripts/bundle_generator.py \
  --consumer consumers/foundational_model/latest.yaml \
  --type snapshot

# 生成：bundles/snapshots/foundational_model-v1.0.0-20250620-143500.yaml
# 特点：
# - 支持多版本对比实验
# - 明确的experiment_role标记
# - 自动过期机制
```

## 新的Bundle优势

### 1. **版本清单明确**
- 提供明确的可用版本列表：`["1.2.0", "1.1.0", "1.0.0"]`
- 推荐版本指导：`recommended_version: "1.2.0"`
- 适应数据生产的渐进性和异步性

### 2. **Consumer版本可见**
- 文件名体现Consumer版本：`end_to_end-v1.2.0-2025.25.yaml`
- 直接的版本对应关系
- 易于浏览和管理

### 3. **灵活的数据获取**
```yaml
# Bundle提供版本清单
channels:
  - channel: object_array_fusion_infer
    available_versions: ["1.2.0", "1.1.0", "1.0.0"]
    recommended_version: "1.2.0"

# 数据获取系统根据实际情况选择：
# - 优先使用 1.2.0 (如果数据可用)
# - 必要时降级到 1.1.0 或 1.0.0
# - 支持多版本混合使用
```

### 4. **完整的追溯性**
```yaml
# 每个Bundle都记录转换历史
conversion_source:
  consumer_config: "consumers/end_to_end/latest.yaml"
  consumer_version: "v1.2.0"
  conversion_time: "2025-06-20T14:30:00Z"
  
channels:
  - channel: object_array_fusion_infer
    source_constraint: ">=1.2.0"           # 原始约束
    available_versions: ["1.2.0", "1.1.0"] # 解析结果

```

这样的Bundle设计更贴近数据生产的现实情况，提供了**版本清单**而非**固定版本**，既保持了可追溯性，又提供了灵活性。 