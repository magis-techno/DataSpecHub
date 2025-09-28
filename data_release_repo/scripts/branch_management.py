#!/usr/bin/env python3
"""
分支管理自动化脚本
提供分支创建、清理、状态检查等功能
"""

import os
import subprocess
import sys
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

class BranchManager:
    def __init__(self):
        self.repo_root = self._get_repo_root()
        
    def _get_repo_root(self) -> str:
        """获取Git仓库根目录"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            print("❌ 当前目录不是Git仓库")
            sys.exit(1)
    
    def _run_git_command(self, cmd: List[str]) -> str:
        """执行Git命令"""
        try:
            result = subprocess.run(
                ['git'] + cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"❌ Git命令执行失败: {' '.join(cmd)}")
            print(f"错误信息: {e.stderr}")
            return ""
    
    def create_feature_branch(self, topic: str, method: str, base_branch: str = "develop") -> bool:
        """创建功能数据集分支"""
        branch_name = f"feature_dataset/{topic}/{method}"
        
        print(f"🌿 创建功能分支: {branch_name}")
        
        # 检查分支是否已存在
        existing_branches = self._run_git_command(['branch', '-a'])
        if branch_name in existing_branches:
            print(f"❌ 分支 {branch_name} 已存在")
            return False
        
        # 确保基础分支是最新的
        print(f"📥 更新基础分支: {base_branch}")
        self._run_git_command(['fetch', 'origin'])
        self._run_git_command(['checkout', base_branch])
        self._run_git_command(['pull', 'origin', base_branch])
        
        # 创建新分支
        self._run_git_command(['checkout', '-b', branch_name])
        
        print(f"✅ 成功创建分支: {branch_name}")
        print(f"💡 现在可以开始进行 {topic} 场景的 {method} 操作")
        
        return True
    
    def create_experiment_branch(self, topic: str, trial: str, base_branch: str = "main") -> bool:
        """创建实验分支"""
        branch_name = f"experiment/{topic}/{trial}"
        
        print(f"🧪 创建实验分支: {branch_name}")
        
        # 检查分支是否已存在
        existing_branches = self._run_git_command(['branch', '-a'])
        if branch_name in existing_branches:
            print(f"❌ 分支 {branch_name} 已存在")
            return False
        
        # 确保基础分支是最新的
        print(f"📥 更新基础分支: {base_branch}")
        self._run_git_command(['fetch', 'origin'])
        self._run_git_command(['checkout', base_branch])
        if base_branch != 'main':  # main分支通常是保护的，可能不需要pull
            self._run_git_command(['pull', 'origin', base_branch])
        
        # 创建新分支
        self._run_git_command(['checkout', '-b', branch_name])
        
        print(f"✅ 成功创建实验分支: {branch_name}")
        print(f"💡 现在可以开始进行 {topic} 的 {trial} 实验")
        
        return True
    
    def create_release_branch(self, version: str, base_branch: str = "develop") -> bool:
        """创建发布分支"""
        # 验证版本格式
        if not version.startswith('v'):
            version = f"v{version}"
        
        branch_name = f"release/{version}"
        
        print(f"🚀 创建发布分支: {branch_name}")
        
        # 检查分支是否已存在
        existing_branches = self._run_git_command(['branch', '-a'])
        if branch_name in existing_branches:
            print(f"❌ 分支 {branch_name} 已存在")
            return False
        
        # 确保基础分支是最新的
        print(f"📥 更新基础分支: {base_branch}")
        self._run_git_command(['fetch', 'origin'])
        self._run_git_command(['checkout', base_branch])
        self._run_git_command(['pull', 'origin', base_branch])
        
        # 创建新分支
        self._run_git_command(['checkout', '-b', branch_name])
        
        print(f"✅ 成功创建发布分支: {branch_name}")
        print(f"💡 请在此分支上准备 {version} 版本的发布")
        
        return True
    
    def list_stale_branches(self, days: int = 30) -> List[Dict[str, str]]:
        """列出长期未更新的分支"""
        print(f"🔍 查找 {days} 天内未更新的分支...")
        
        self._run_git_command(['fetch', 'origin'])
        
        # 获取所有分支及其最后提交时间
        branches_info = []
        
        # 获取本地分支
        local_branches = self._run_git_command(['branch', '--format=%(refname:short)']).split('\n')
        for branch in local_branches:
            if branch and branch not in ['main', 'develop']:
                last_commit = self._run_git_command(['log', '-1', '--format=%ci', branch])
                if last_commit:
                    branches_info.append({
                        'name': branch,
                        'type': 'local',
                        'last_commit': last_commit,
                        'location': 'local'
                    })
        
        # 获取远程分支
        remote_branches = self._run_git_command(['branch', '-r', '--format=%(refname:short)']).split('\n')
        for branch in remote_branches:
            if branch and 'origin/' in branch:
                branch_name = branch.replace('origin/', '')
                if branch_name not in ['main', 'develop', 'HEAD']:
                    last_commit = self._run_git_command(['log', '-1', '--format=%ci', branch])
                    if last_commit:
                        branches_info.append({
                            'name': branch_name,
                            'type': 'remote',
                            'last_commit': last_commit,
                            'location': 'origin'
                        })
        
        # 过滤出过期的分支
        cutoff_date = datetime.now() - timedelta(days=days)
        stale_branches = []
        
        for branch_info in branches_info:
            try:
                # 解析时间格式: 2025-09-23 10:30:00 +0800
                commit_date_str = branch_info['last_commit'].split(' +')[0]
                commit_date = datetime.strptime(commit_date_str, '%Y-%m-%d %H:%M:%S')
                
                if commit_date < cutoff_date:
                    stale_branches.append(branch_info)
            except ValueError:
                continue  # 跳过无法解析的日期
        
        return stale_branches
    
    def cleanup_merged_branches(self, dry_run: bool = True) -> List[str]:
        """清理已合并的分支"""
        print("🧹 查找已合并的分支...")
        
        self._run_git_command(['fetch', 'origin'])
        
        # 获取已合并到main的分支
        merged_to_main = self._run_git_command(['branch', '--merged', 'main']).split('\n')
        merged_to_main = [b.strip() for b in merged_to_main if b.strip() and not b.strip().startswith('*')]
        
        # 获取已合并到develop的分支
        merged_to_develop = self._run_git_command(['branch', '--merged', 'develop']).split('\n')
        merged_to_develop = [b.strip() for b in merged_to_develop if b.strip() and not b.strip().startswith('*')]
        
        # 合并列表并去重
        all_merged = list(set(merged_to_main + merged_to_develop))
        
        # 排除主要分支
        protected_branches = ['main', 'develop']
        cleanable_branches = [b for b in all_merged if b not in protected_branches]
        
        if not cleanable_branches:
            print("✅ 没有找到可清理的已合并分支")
            return []
        
        if dry_run:
            print(f"🔍 找到 {len(cleanable_branches)} 个已合并的分支 (仅预览):")
            for branch in cleanable_branches:
                print(f"   • {branch}")
            print("\n💡 使用 --no-dry-run 参数执行实际清理")
        else:
            print(f"🗑️  清理 {len(cleanable_branches)} 个已合并的分支:")
            for branch in cleanable_branches:
                print(f"   删除: {branch}")
                self._run_git_command(['branch', '-d', branch])
            print("✅ 分支清理完成")
        
        return cleanable_branches
    
    def get_branch_status(self) -> Dict[str, any]:
        """获取分支状态信息"""
        print("📊 收集分支状态信息...")
        
        self._run_git_command(['fetch', 'origin'])
        
        current_branch = self._run_git_command(['branch', '--show-current'])
        
        # 统计各类型分支数量
        all_branches = self._run_git_command(['branch', '-a']).split('\n')
        branch_types = {
            'feature_dataset': 0,
            'experiment': 0,
            'release': 0,
            'hotfix': 0,
            'other': 0
        }
        
        for branch in all_branches:
            branch = branch.strip().replace('*', '').strip()
            if 'origin/' in branch:
                branch = branch.replace('origin/', '')
            
            if branch.startswith('feature_dataset/'):
                branch_types['feature_dataset'] += 1
            elif branch.startswith('experiment/'):
                branch_types['experiment'] += 1
            elif branch.startswith('release/'):
                branch_types['release'] += 1
            elif branch.startswith('hotfix/'):
                branch_types['hotfix'] += 1
            elif branch and branch not in ['main', 'develop', 'HEAD']:
                branch_types['other'] += 1
        
        # 检查工作目录状态
        status = self._run_git_command(['status', '--porcelain'])
        has_changes = bool(status.strip())
        
        # 检查是否有未推送的提交
        try:
            unpushed = self._run_git_command(['log', f'origin/{current_branch}..HEAD', '--oneline'])
            has_unpushed = bool(unpushed.strip())
        except:
            has_unpushed = False
        
        return {
            'current_branch': current_branch,
            'branch_counts': branch_types,
            'has_uncommitted_changes': has_changes,
            'has_unpushed_commits': has_unpushed,
            'total_branches': sum(branch_types.values()) + 2  # +2 for main and develop
        }

def main():
    parser = argparse.ArgumentParser(description='分支管理工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 创建功能分支
    create_feature = subparsers.add_parser('create-feature', help='创建功能数据集分支')
    create_feature.add_argument('topic', help='主题名称 (如: toll_station)')
    create_feature.add_argument('method', help='方法名称 (如: strict)')
    create_feature.add_argument('--base', default='develop', help='基础分支 (默认: develop)')
    
    # 创建实验分支
    create_exp = subparsers.add_parser('create-experiment', help='创建实验分支')
    create_exp.add_argument('topic', help='主题名称 (如: toll_station)')
    create_exp.add_argument('trial', help='试验名称 (如: ablation-01)')
    create_exp.add_argument('--base', default='main', help='基础分支 (默认: main)')
    
    # 创建发布分支
    create_release = subparsers.add_parser('create-release', help='创建发布分支')
    create_release.add_argument('version', help='版本号 (如: 1.2.0 或 v1.2.0)')
    create_release.add_argument('--base', default='develop', help='基础分支 (默认: develop)')
    
    # 列出过期分支
    list_stale = subparsers.add_parser('list-stale', help='列出长期未更新的分支')
    list_stale.add_argument('--days', type=int, default=30, help='天数阈值 (默认: 30)')
    
    # 清理已合并分支
    cleanup = subparsers.add_parser('cleanup', help='清理已合并的分支')
    cleanup.add_argument('--dry-run', action='store_true', default=True, help='仅预览，不执行删除 (默认)')
    cleanup.add_argument('--no-dry-run', action='store_true', help='执行实际删除')
    
    # 状态信息
    status = subparsers.add_parser('status', help='显示分支状态信息')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = BranchManager()
    
    if args.command == 'create-feature':
        manager.create_feature_branch(args.topic, args.method, args.base)
    
    elif args.command == 'create-experiment':
        manager.create_experiment_branch(args.topic, args.trial, args.base)
    
    elif args.command == 'create-release':
        manager.create_release_branch(args.version, args.base)
    
    elif args.command == 'list-stale':
        stale_branches = manager.list_stale_branches(args.days)
        if stale_branches:
            print(f"📋 找到 {len(stale_branches)} 个超过 {args.days} 天未更新的分支:")
            for branch in stale_branches:
                print(f"   • {branch['name']} ({branch['location']}) - 最后提交: {branch['last_commit']}")
            print(f"\n💡 可以考虑清理这些分支，如果确认不再需要")
        else:
            print(f"✅ 没有找到超过 {args.days} 天未更新的分支")
    
    elif args.command == 'cleanup':
        dry_run = args.dry_run and not args.no_dry_run
        manager.cleanup_merged_branches(dry_run)
    
    elif args.command == 'status':
        status_info = manager.get_branch_status()
        print(f"📊 分支状态报告")
        print(f"当前分支: {status_info['current_branch']}")
        print(f"总分支数: {status_info['total_branches']}")
        print(f"分支类型统计:")
        for branch_type, count in status_info['branch_counts'].items():
            if count > 0:
                print(f"   • {branch_type}: {count}")
        
        if status_info['has_uncommitted_changes']:
            print("⚠️  有未提交的修改")
        
        if status_info['has_unpushed_commits']:
            print("⚠️  有未推送的提交")
        
        if not status_info['has_uncommitted_changes'] and not status_info['has_unpushed_commits']:
            print("✅ 工作目录干净，所有提交已推送")

if __name__ == "__main__":
    main()

