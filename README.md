# DataSpecHub

See high‑level **prd.md** and module‑level PRDs in `prd/`.

## Bundle系统

Bundle系统专注于核心功能：**版本清单生成 + 链路追溯 + 灵活选择**

### 核心原理
```
Consumer配置 (软约束) → Bundle生成器 → Bundle快照 (版本清单)
  ">=1.0.0"          →   版本解析    →    ["1.2.0", "1.1.0", "1.0.0"]
```

### 三种Bundle类型

1. **Weekly Bundle** - 固定周期，团队协作的版本快照
2. **Snapshot Bundle** - 灵活使用，临时验证和实验
3. **Release Bundle** - 正式发布，经过验证的版本清单

### 使用方法

```bash
# 生成Bundle (新的命名规范)
python scripts/bundle_generator.py --consumer consumers/end_to_end/latest.yaml --type weekly
# 生成: bundles/weekly/end_to_end-v1.2.0-2025.25.yaml

python scripts/bundle_generator.py --consumer consumers/foundational_model/latest.yaml --type snapshot  
# 生成: bundles/snapshots/foundational_model-v1.0.0-20250620-143500.yaml

python scripts/bundle_generator.py --consumer consumers/pv_trafficlight/latest.yaml --type release
# 生成: bundles/release/pv_trafficlight-v1.1.0-release.yaml

# 验证Bundle
python scripts/bundle_validator.py bundles/weekly/end_to_end-v1.2.0-2025.25.yaml

# 使用Bundle
dataspec load --bundle bundles/weekly/end_to_end-v1.2.0-2025.25.yaml
```

更多详情见 [Bundle核心设计文档](docs/BUNDLE_CORE_DESIGN.md)
