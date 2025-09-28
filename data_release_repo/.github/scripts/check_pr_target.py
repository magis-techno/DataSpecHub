#!/usr/bin/env python3
"""
检查PR目标分支是否符合工作流规范
"""

import sys
from typing import Dict, List

def get_valid_pr_targets() -> Dict[str, List[str]]:
    """定义有效的PR目标分支映射"""
    return {
        # feature_dataset 分支只能合并到 develop
        'feature_dataset': ['develop'],
        
        # experiment 分支可以合并到 develop，也可以cherry-pick到其他分支
        'experiment': ['develop'],
        
        # release 分支可以合并到 main 和 develop
        'release': ['main', 'develop'],
        
        # hotfix 分支可以合并到 main 和 develop
        'hotfix': ['main', 'develop'],
        
        # develop 分支可以合并到 release 分支
        'develop': ['release'],
        
        # 其他分支的规则
        'main': [],  # main分支不应该向其他分支发起PR
    }

def get_branch_type(branch_name: str) -> str:
    """获取分支类型"""
    if branch_name == 'main':
        return 'main'
    elif branch_name == 'develop':
        return 'develop'
    elif branch_name.startswith('feature_dataset/'):
        return 'feature_dataset'
    elif branch_name.startswith('experiment/'):
        return 'experiment'
    elif branch_name.startswith('release/'):
        return 'release'
    elif branch_name.startswith('hotfix/'):
        return 'hotfix'
    else:
        return 'unknown'

def validate_pr_target(source_branch: str, target_branch: str) -> tuple[bool, str]:
    """验证PR目标分支"""
    source_type = get_branch_type(source_branch)
    target_type = get_branch_type(target_branch)
    
    valid_targets = get_valid_pr_targets()
    
    # 检查源分支类型是否有定义的目标规则
    if source_type not in valid_targets:
        return False, f"未知的源分支类型: {source_type}"
    
    allowed_targets = valid_targets[source_type]
    
    # 特殊处理：develop可以合并到任何release分支
    if source_type == 'develop' and target_type == 'release':
        return True, f"develop分支可以合并到release分支"
    
    # 检查目标分支是否在允许列表中
    if target_branch in allowed_targets or target_type in allowed_targets:
        return True, f"合法的PR目标: {source_type} -> {target_branch}"
    
    return False, f"不允许的PR目标: {source_type}分支不能合并到{target_branch}"

def get_recommended_targets(source_branch: str) -> List[str]:
    """获取推荐的目标分支"""
    source_type = get_branch_type(source_branch)
    valid_targets = get_valid_pr_targets()
    
    if source_type in valid_targets:
        targets = valid_targets[source_type]
        
        # 为develop分支添加具体的release分支建议
        if source_type == 'develop':
            targets = targets + ['release/v<version>']
        
        return targets
    
    return []

def get_workflow_explanation(source_type: str) -> str:
    """获取工作流说明"""
    explanations = {
        'feature_dataset': (
            "功能数据集分支用于特定场景的数据开发，完成后应合并到develop分支进行集成测试。"
        ),
        'experiment': (
            "实验分支用于数据挖掘和处理的实验性工作，验证后可合并到develop分支，"
            "或使用cherry-pick将有价值的commit合并到其他分支。"
        ),
        'release': (
            "发布分支用于准备新版本发布，完成后应同时合并到main和develop分支，"
            "确保主分支包含发布版本，开发分支包含最新变更。"
        ),
        'hotfix': (
            "热修复分支用于紧急问题修复，应同时合并到main和develop分支，"
            "确保修复在所有分支中生效。"
        ),
        'develop': (
            "开发分支的变更应合并到release分支进行发布准备。"
        ),
    }
    
    return explanations.get(source_type, "请参考分支规范文档了解正确的工作流程。")

def main():
    """主函数"""
    if len(sys.argv) != 3:
        print("用法: python check_pr_target.py <source_branch> <target_branch>")
        sys.exit(1)
    
    source_branch = sys.argv[1]
    target_branch = sys.argv[2]
    
    print(f"=== PR目标分支验证 ===")
    print(f"源分支: {source_branch}")
    print(f"目标分支: {target_branch}")
    
    is_valid, message = validate_pr_target(source_branch, target_branch)
    
    if is_valid:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")
        
        # 提供建议
        recommended = get_recommended_targets(source_branch)
        if recommended:
            print(f"\n💡 推荐的目标分支: {', '.join(recommended)}")
        
        # 提供工作流说明
        source_type = get_branch_type(source_branch)
        explanation = get_workflow_explanation(source_type)
        print(f"\n📖 工作流说明:")
        print(f"   {explanation}")
        
        print(f"\n📋 完整的分支合并规则:")
        valid_targets = get_valid_pr_targets()
        for branch_type, targets in valid_targets.items():
            if targets:
                print(f"   • {branch_type} → {', '.join(targets)}")
        
        print(f"\n🔄 特殊规则:")
        print(f"   • develop分支可以合并到任何release/v<version>分支")
        print(f"   • experiment分支的结果可以通过cherry-pick合并到其他分支")
        print(f"   • main分支不应该向其他分支发起PR")
        
        sys.exit(1)

if __name__ == "__main__":
    main()

