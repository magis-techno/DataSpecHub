# DataSpecHub

See high‑level **prd.md** and module‑level PRDs in `prd/`.

## Bundle系统

Bundle系统专注于核心功能：**硬约束快照 + 链路追溯 + 灵活周期**

### 核心原理
```
Consumer配置 (软约束) → Bundle生成器 → Bundle快照 (硬约束)
  ">=1.0.0"          →   版本解析    →    "1.2.0"
```

### 三种Bundle类型

1. **Weekly Bundle** - 固定周期，生产环境标准版本
2. **Snapshot Bundle** - 灵活使用，临时验证和实验
3. **Release Bundle** - 正式发布，长期支持版本

### 使用方法

```bash
# 生成Bundle
python scripts/bundle_generator.py --consumer consumers/end_to_end/latest.yaml --type weekly
python scripts/bundle_generator.py --consumer consumers/test_config.yaml --type snapshot  
python scripts/bundle_generator.py --consumer consumers/prod/v1.1.0.yaml --type release

# 验证Bundle
python scripts/bundle_validator.py bundles/weekly/end_to_end-2025.25.yaml

# 使用Bundle
dataspec load --bundle bundles/weekly/end_to_end-2025.25.yaml
```

更多详情见 [Bundle核心设计文档](docs/BUNDLE_CORE_DESIGN.md)
