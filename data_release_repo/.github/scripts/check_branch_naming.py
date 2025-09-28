#!/usr/bin/env python3
"""
检查分支命名是否符合规范
"""

import sys
import re
from typing import List, Tuple

def get_branch_naming_rules() -> List[Tuple[str, str]]:
    """获取分支命名规则"""
    return [
        (r'^main$', 'main - 主分支'),
        (r'^develop$', 'develop - 开发分支'),
        (r'^feature_dataset/[a-z_]+/[a-z_]+$', 'feature_dataset/<topic>/<method> - 功能数据集分支'),
        (r'^experiment/[a-z_]+/[a-z0-9_-]+$', 'experiment/<topic>/<trial> - 实验分支'),
        (r'^release/v\d+\.\d+\.\d+$', 'release/v<major>.<minor>.<patch> - 发布分支'),
        (r'^hotfix/v\d+\.\d+\.\d+-[a-z0-9_-]+$', 'hotfix/v<version>-<issue> - 热修复分支'),
    ]

def validate_branch_name(branch_name: str) -> Tuple[bool, str]:
    """验证分支名称"""
    if not branch_name:
        return False, "分支名称不能为空"
    
    rules = get_branch_naming_rules()
    
    for pattern, description in rules:
        if re.match(pattern, branch_name):
            return True, f"匹配规则: {description}"
    
    return False, "分支名称不符合任何命名规范"

def get_suggestions(branch_name: str) -> List[str]:
    """根据分支名称提供命名建议"""
    suggestions = []
    
    # 常见的命名问题和建议
    if '/' not in branch_name and branch_name not in ['main', 'develop']:
        suggestions.append("考虑使用分层命名，如: feature_dataset/topic/method")
    
    if branch_name.startswith('feature/'):
        suggestions.append("数据集功能分支应使用 feature_dataset/ 前缀")
    
    if branch_name.startswith('exp/') or branch_name.startswith('test/'):
        suggestions.append("实验分支应使用 experiment/ 前缀")
    
    if 'release' in branch_name and not branch_name.startswith('release/'):
        suggestions.append("发布分支应使用 release/v<major>.<minor>.<patch> 格式")
    
    if 'fix' in branch_name and not branch_name.startswith('hotfix/'):
        suggestions.append("热修复分支应使用 hotfix/v<version>-<issue> 格式")
    
    # 字符检查
    if re.search(r'[A-Z]', branch_name):
        suggestions.append("分支名称应使用小写字母")
    
    if re.search(r'[^a-z0-9/_.-]', branch_name):
        suggestions.append("分支名称只能包含小写字母、数字、下划线、横线、斜杠和点")
    
    # 提供具体示例
    if branch_name.startswith('feature_dataset/'):
        parts = branch_name.split('/')
        if len(parts) != 3:
            suggestions.append("feature_dataset分支格式: feature_dataset/<topic>/<method>")
            suggestions.append("示例: feature_dataset/toll_station/strict")
    
    if branch_name.startswith('experiment/'):
        parts = branch_name.split('/')
        if len(parts) != 3:
            suggestions.append("experiment分支格式: experiment/<topic>/<trial>")
            suggestions.append("示例: experiment/toll_station/ablation-01")
    
    return suggestions

def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python check_branch_naming.py <branch_name>")
        sys.exit(1)
    
    branch_name = sys.argv[1]
    
    print(f"=== 分支命名验证 ===")
    print(f"分支名称: {branch_name}")
    
    is_valid, message = validate_branch_name(branch_name)
    
    if is_valid:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")
        
        suggestions = get_suggestions(branch_name)
        if suggestions:
            print("\n💡 命名建议:")
            for suggestion in suggestions:
                print(f"   • {suggestion}")
        
        print("\n📋 有效的分支命名规范:")
        rules = get_branch_naming_rules()
        for pattern, description in rules:
            print(f"   • {description}")
        
        print("\n🌰 命名示例:")
        examples = [
            "feature_dataset/toll_station/strict",
            "feature_dataset/highway_merge/balance", 
            "experiment/toll_station/ablation-01",
            "experiment/dagger/online-training-v2",
            "release/v1.2.0",
            "hotfix/v1.2.0-data-corruption"
        ]
        for example in examples:
            print(f"   • {example}")
        
        sys.exit(1)

if __name__ == "__main__":
    main()

