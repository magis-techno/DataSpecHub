#!/usr/bin/env python3
"""
Consumer版本管理工具

用于管理consumer配置的版本和分支，支持创建、删除、合并和清理操作。
"""

import os
import yaml
import argparse
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import sys

class ConsumerVersionManager:
    def __init__(self, base_dir="consumers"):
        self.base_dir = Path(base_dir)
        
    def list_consumers(self):
        """列出所有consumer及其版本"""
        consumers = {}
        for consumer_dir in self.base_dir.iterdir():
            if consumer_dir.is_dir():
                versions = []
                for version_file in consumer_dir.glob("*.yaml"):
                    if version_file.name != "latest.yaml":
                        versions.append(version_file.name.replace(".yaml", ""))
                consumers[consumer_dir.name] = versions
        return consumers
    
    def create_branch(self, consumer, base_version, new_version, description="", branch_type="experiment", expires_days=30):
        """创建新的配置分支"""
        consumer_dir = self.base_dir / consumer
        if not consumer_dir.exists():
            raise ValueError(f"Consumer '{consumer}' 不存在")
            
        base_file = consumer_dir / f"{base_version}.yaml"
        if not base_file.exists():
            raise ValueError(f"基础版本 '{base_version}' 不存在")
            
        new_file = consumer_dir / f"{new_version}.yaml"
        if new_file.exists():
            raise ValueError(f"版本 '{new_version}' 已存在")
            
        # 复制基础版本
        shutil.copy2(base_file, new_file)
        
        # 更新metadata
        with open(new_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        config['meta']['version'] = new_version
        config['meta']['parent_version'] = base_version
        config['meta']['branch_type'] = branch_type
        config['meta']['created_at'] = datetime.now().strftime("%Y-%m-%d")
        
        if expires_days:
            expire_date = datetime.now() + timedelta(days=expires_days)
            config['meta']['expires_at'] = expire_date.strftime("%Y-%m-%d")
            
        if description:
            config['meta']['description'] = description
            
        # 添加变更历史
        if 'change_history' not in config:
            config['change_history'] = []
            
        config['change_history'].append({
            'date': datetime.now().strftime("%Y-%m-%d"),
            'version': new_version,
            'changes': f"基于{base_version}创建{branch_type}分支: {description}"
        })
        
        with open(new_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
            
        print(f"✅ 成功创建分支: {consumer}/{new_version}")
        return new_file
    
    def delete_branch(self, consumer, version, force=False):
        """删除配置分支"""
        consumer_dir = self.base_dir / consumer
        version_file = consumer_dir / f"{version}.yaml"
        
        if not version_file.exists():
            raise ValueError(f"版本 '{version}' 不存在")
            
        # 检查是否为latest
        latest_file = consumer_dir / "latest.yaml"
        if latest_file.exists():
            with open(latest_file, 'r', encoding='utf-8') as f:
                latest_config = yaml.safe_load(f)
                if latest_config.get('meta', {}).get('version') == version:
                    if not force:
                        raise ValueError(f"版本 '{version}' 是当前latest版本，使用 --force 强制删除")
                    
        version_file.unlink()
        print(f"✅ 已删除分支: {consumer}/{version}")
    
    def update_latest(self, consumer, version):
        """更新latest指向"""
        consumer_dir = self.base_dir / consumer
        version_file = consumer_dir / f"{version}.yaml"
        latest_file = consumer_dir / "latest.yaml"
        
        if not version_file.exists():
            raise ValueError(f"版本 '{version}' 不存在")
            
        # 复制配置内容到latest.yaml
        shutil.copy2(version_file, latest_file)
        
        # 在latest.yaml顶部添加注释
        with open(latest_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        header = f"# This file points to the current recommended version: {version}\n"
        header += f"# In production, this would be a symbolic link: ln -s {version}.yaml latest.yaml\n\n"
        
        with open(latest_file, 'w', encoding='utf-8') as f:
            f.write(header + content)
            
        print(f"✅ 已更新latest指向: {consumer}/{version}")
    
    def clean_expired(self, dry_run=True):
        """清理过期的分支"""
        today = datetime.now().date()
        expired_branches = []
        
        for consumer_dir in self.base_dir.iterdir():
            if not consumer_dir.is_dir():
                continue
                
            for version_file in consumer_dir.glob("*.yaml"):
                if version_file.name == "latest.yaml":
                    continue
                    
                try:
                    with open(version_file, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                        
                    expire_date_str = config.get('meta', {}).get('expires_at')
                    if expire_date_str:
                        expire_date = datetime.strptime(expire_date_str, "%Y-%m-%d").date()
                        if expire_date < today:
                            expired_branches.append((consumer_dir.name, version_file.stem))
                            
                except Exception as e:
                    print(f"⚠️  读取 {version_file} 失败: {e}")
                    
        if not expired_branches:
            print("✅ 没有发现过期的分支")
            return
            
        print(f"发现 {len(expired_branches)} 个过期分支:")
        for consumer, version in expired_branches:
            print(f"  - {consumer}/{version}")
            
        if not dry_run:
            for consumer, version in expired_branches:
                try:
                    self.delete_branch(consumer, version, force=True)
                    print(f"✅ 已删除过期分支: {consumer}/{version}")
                except Exception as e:
                    print(f"❌ 删除 {consumer}/{version} 失败: {e}")
        else:
            print("\n🔍 这是预览模式，使用 --execute 执行实际删除")
    
    def validate_config(self, consumer, version):
        """验证配置文件"""
        consumer_dir = self.base_dir / consumer
        version_file = consumer_dir / f"{version}.yaml"
        
        if not version_file.exists():
            raise ValueError(f"版本文件不存在: {version_file}")
            
        try:
            with open(version_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            # 验证必需字段
            required_fields = ['meta', 'requirements']
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"缺少必需字段: {field}")
                    
            # 验证meta字段
            meta = config['meta']
            required_meta = ['consumer', 'version', 'owner', 'description']
            for field in required_meta:
                if field not in meta:
                    raise ValueError(f"meta缺少必需字段: {field}")
                    
            # 验证requirements
            requirements = config['requirements']
            if not isinstance(requirements, list):
                raise ValueError("requirements必须是列表")
                
            for req in requirements:
                required_req = ['channel', 'version', 'required', 'on_missing']
                for field in required_req:
                    if field not in req:
                        raise ValueError(f"requirement缺少必需字段: {field}")
                        
                # 验证on_missing值
                valid_on_missing = ['interrupt', 'skip_frame', 'continue', 'fetch_latest']
                if req['on_missing'] not in valid_on_missing:
                    raise ValueError(f"无效的on_missing值: {req['on_missing']}，必须是 {valid_on_missing} 之一")
                        
            print(f"✅ 配置验证通过: {consumer}/{version}")
            return True
            
        except yaml.YAMLError as e:
            raise ValueError(f"YAML格式错误: {e}")

def main():
    parser = argparse.ArgumentParser(description="Consumer版本管理工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # list命令
    list_parser = subparsers.add_parser('list', help='列出所有consumer和版本')
    
    # create-branch命令
    create_parser = subparsers.add_parser('create-branch', help='创建新分支')
    create_parser.add_argument('--consumer', required=True, help='Consumer名称')
    create_parser.add_argument('--base-version', required=True, help='基础版本')
    create_parser.add_argument('--new-version', required=True, help='新版本名称')
    create_parser.add_argument('--description', default='', help='分支描述')
    create_parser.add_argument('--type', default='experiment', 
                              choices=['experiment', 'optimization', 'pretraining', 'finetuning', 'debug'],
                              help='分支类型')
    create_parser.add_argument('--expires-days', type=int, default=30, help='过期天数')
    
    # delete-branch命令
    delete_parser = subparsers.add_parser('delete-branch', help='删除分支')
    delete_parser.add_argument('--consumer', required=True, help='Consumer名称')
    delete_parser.add_argument('--version', required=True, help='版本名称')
    delete_parser.add_argument('--force', action='store_true', help='强制删除')
    
    # update-latest命令
    latest_parser = subparsers.add_parser('update-latest', help='更新latest指向')
    latest_parser.add_argument('--consumer', required=True, help='Consumer名称')
    latest_parser.add_argument('--version', required=True, help='版本名称')
    
    # clean命令
    clean_parser = subparsers.add_parser('clean', help='清理过期分支')
    clean_parser.add_argument('--execute', action='store_true', help='执行实际删除（默认为预览模式）')
    
    # validate命令
    validate_parser = subparsers.add_parser('validate', help='验证配置文件')
    validate_parser.add_argument('--consumer', required=True, help='Consumer名称')
    validate_parser.add_argument('--version', required=True, help='版本名称')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    manager = ConsumerVersionManager()
    
    try:
        if args.command == 'list':
            consumers = manager.list_consumers()
            print("📋 Consumer列表:")
            for consumer, versions in consumers.items():
                print(f"\n{consumer}:")
                for version in sorted(versions):
                    print(f"  - {version}")
                    
        elif args.command == 'create-branch':
            manager.create_branch(
                args.consumer, args.base_version, args.new_version,
                args.description, args.type, args.expires_days
            )
            
        elif args.command == 'delete-branch':
            manager.delete_branch(args.consumer, args.version, args.force)
            
        elif args.command == 'update-latest':
            manager.update_latest(args.consumer, args.version)
            
        elif args.command == 'clean':
            manager.clean_expired(dry_run=not args.execute)
            
        elif args.command == 'validate':
            manager.validate_config(args.consumer, args.version)
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 