# Product Requirements Overview

## 总体目标与原则

DataSpecHub 致力于解决数据团队规范化管理的核心痛点，建立统一、可追溯、机器可验证的数据规格治理体系。

### 核心目标

| 目标 | 说明 |
|------|------|
| **统一规格仓库** | 所有通道的规格、示例文件、校验脚本都集中在一个 GitHub monorepo，避免分散、难以发现 |
| **版本即契约** | 对"生产规格"（生产线实际落地的格式）和"发布规格"（对外交付/下游消费的格式）分别按 SemVer 管理，任何字段级调整都需 bump 版本 |
| **变更即工单** | 每一次规格 PR 必须关联需求系统中的 Issue ID，自动写入 CHANGELOG 并触发评审流程 |
| **机器可验证** | 规格用 YAML/JSON schema 或 Protobuf IDL 描述，GitHub Actions 在 CI 阶段自动 lint + 示例数据验证 |
| **向后兼容优先** | 生产线变更默认不破坏旧版发布；若必须破坏，提前发布弃用公告并保留双写窗口 |

### 核心问题解决

- **生产规格与发布规格混淆** → 明确分离，建立映射关系
- **版本共存与老化管理** → Bundle系统提供快照锁定和生命周期管理  
- **业务团队聚合版本需求** → Consumer配置表达意图，Bundle提供可复现快照
- **变更追踪与影响分析** → 自动化工单关联和兼容性检查

## 四大核心模块

DataSpecHub is split into four core capability modules, each documented in its own PRD:

| Module | PRD |
|--------|-----|
| Channel Specification Governance | [`prd/prd_channel_spec.md`](prd/prd_channel_spec.md) |
| Bundle & Lock System | [`prd/prd_bundle_system.md`](prd/prd_bundle_system.md) |
| Loader SDK | [`prd/prd_loader_sdk.md`](prd/prd_loader_sdk.md) |
| Taxonomy & Docs Portal | [`prd/prd_docs_portal.md`](prd/prd_docs_portal.md) |
