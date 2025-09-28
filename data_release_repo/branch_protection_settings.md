# GitHub分支保护设置指南

本文档提供GitHub仓库分支保护的推荐配置，确保分支规范的有效执行。

## 🛡️ 分支保护配置

### main分支保护设置

**路径**: Settings → Branches → Add protection rule

**分支名称模式**: `main`

**保护规则**:
- ✅ **Require a pull request before merging**
  - ✅ Require approvals: `2`
  - ✅ Dismiss stale PR approvals when new commits are pushed
  - ✅ Require review from code owners
  - ✅ Restrict pushes that create files that change the code owner

- ✅ **Require status checks to pass before merging**
  - ✅ Require branches to be up to date before merging
  - **Required status checks**:
    - `validate-data-format`
    - `validate-commit-message`
    - `validate-version-consistency`
    - `branch-policy-check`

- ✅ **Require conversation resolution before merging**
- ✅ **Require linear history**
- ✅ **Include administrators** (推荐)
- ✅ **Restrict pushes**
  - **Restrict to specific roles**: Maintain role and above

### develop分支保护设置

**分支名称模式**: `develop`

**保护规则**:
- ✅ **Require a pull request before merging**
  - ✅ Require approvals: `1`
  - ✅ Dismiss stale PR approvals when new commits are pushed

- ✅ **Require status checks to pass before merging**
  - ✅ Require branches to be up to date before merging
  - **Required status checks**:
    - `validate-data-format`
    - `validate-commit-message`
    - `branch-policy-check`

- ✅ **Require conversation resolution before merging**
- ❌ **Require linear history** (允许merge commits保留功能分支历史)
- ✅ **Include administrators**

### release分支保护设置

**分支名称模式**: `release/*`

**保护规则**:
- ✅ **Require a pull request before merging**
  - ✅ Require approvals: `1`
  - ✅ Require review from code owners

- ✅ **Require status checks to pass before merging**
  - **Required status checks**:
    - `validate-data-format`
    - `validate-version-consistency`

- ✅ **Require conversation resolution before merging**
- ✅ **Include administrators**

## 🏷️ Tag保护设置

**路径**: Settings → General → Tag protection rules

### 版本Tag保护
**Tag name pattern**: `training/v*`
- 仅允许Maintain角色及以上创建和删除

### 专题Tag保护
**Tag name pattern**: `feature_dataset/*/release-*`
- 仅允许Write角色及以上创建和删除

## 👥 团队权限设置

**路径**: Settings → Manage access

### 推荐权限配置

| 角色 | 权限 | 说明 |
|------|------|------|
| **Admin** | Admin | 项目负责人，完整权限 |
| **Maintainer** | Maintain | 高级开发者，可管理分支和Tag |
| **Developer** | Write | 普通开发者，可创建分支和PR |
| **Reviewer** | Triage | 仅用于代码审查的外部人员 |

### 团队分配示例
- **DataPlatform-Admins**: Admin权限
- **DataPlatform-Maintainers**: Maintain权限  
- **DataPlatform-Developers**: Write权限
- **External-Reviewers**: Triage权限

## 🤖 自动化设置

### Branch Auto-deletion
**路径**: Settings → General → Pull Requests

- ✅ **Automatically delete head branches**
  - 自动删除已合并的PR源分支

### Security Settings
**路径**: Settings → Code security and analysis

- ✅ **Dependency graph**
- ✅ **Dependabot alerts**
- ✅ **Dependabot security updates**

## 🔧 Webhooks配置

如果需要集成外部系统，可以配置Webhooks：

**路径**: Settings → Webhooks

### 数据处理系统集成
```json
{
  "url": "https://your-data-system.com/webhook",
  "content_type": "application/json",
  "events": [
    "push",
    "pull_request",
    "release"
  ]
}
```

## 📋 GitHub Actions配置

### Repository Secrets
**路径**: Settings → Security → Secrets and variables → Actions

需要配置的Secrets:
- `GH_TOKEN`: GitHub Personal Access Token (用于自动化操作)
- `DATA_SYSTEM_API_KEY`: 数据系统API密钥 (如果需要)

### Environment配置
**路径**: Settings → Environments

#### Production环境
- **Environment name**: `production`
- **Deployment branches**: `main`分支
- **Required reviewers**: 2人
- **Wait timer**: 30分钟

#### Staging环境  
- **Environment name**: `staging`
- **Deployment branches**: `develop`和`release/*`分支
- **Required reviewers**: 1人

## 🎯 规则验证清单

在配置完成后，验证以下规则是否生效：

### main分支
- [ ] 不能直接push代码
- [ ] PR需要2人审批
- [ ] 必须通过所有CI检查
- [ ] 只能从release和hotfix分支合并

### develop分支
- [ ] 不能直接push代码
- [ ] PR需要1人审批
- [ ] 必须通过CI检查
- [ ] 可以从feature_dataset和experiment分支合并

### 功能分支
- [ ] 可以直接push (开发阶段)
- [ ] 向develop创建PR时需要审批
- [ ] 合并后7天自动删除

### Tag创建
- [ ] 版本Tag只能由Maintainer创建
- [ ] 专题Tag可以由Developer创建
- [ ] Tag创建后不能删除 (除非Admin权限)

## 📚 相关文档

- [GitHub分支保护官方文档](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/about-protected-branches)
- [GitHub Actions权限管理](https://docs.github.com/en/actions/security-guides/automatic-token-authentication)
- [Git_Branch_Strategy.md](Git_Branch_Strategy.md) - 本仓库分支策略

## 📞 支持

如果在配置过程中遇到问题：
1. 检查权限是否正确分配
2. 验证CI脚本是否正常工作
3. 联系仓库管理员获取帮助

---
**注意**: 这些设置需要仓库Admin权限才能配置。建议在测试仓库先验证配置的有效性。

