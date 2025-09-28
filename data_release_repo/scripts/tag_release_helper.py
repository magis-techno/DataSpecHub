#!/usr/bin/env python3
"""
Tag和Release创建辅助工具
"""

import os
import sys
import argparse
import subprocess
import json
import yaml
from datetime import datetime
from typing import Dict, Optional, List, Any

class TagReleaseHelper:
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
    
    def get_dataset_info(self) -> Optional[Dict[str, Any]]:
        """从training_dataset.json获取数据集信息"""
        dataset_files = ['training_dataset.json', 'training_dataset.dagger.json']
        
        for filename in dataset_files:
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    return data
                except json.JSONDecodeError:
                    continue
        
        return None
    
    def create_feature_tag(self, topic: str, date: str = None) -> bool:
        """创建专题数据交付Tag"""
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        
        tag_name = f"feature_dataset/{topic}/release-{date}"
        
        print(f"🏷️  创建专题数据交付Tag: {tag_name}")
        
        # 检查Tag是否已存在
        existing_tags = self._run_git_command(['tag', '-l'])
        if tag_name in existing_tags.split('\n'):
            print(f"❌ Tag {tag_name} 已存在")
            return False
        
        # 获取数据集信息
        dataset_info = self.get_dataset_info()
        if not dataset_info:
            print("⚠️  未找到training_dataset.json，将创建简单的Tag注释")
            tag_annotation = f"专题数据交付: {topic}"
        else:
            meta = dataset_info.get('meta', {})
            dataset_index = dataset_info.get('dataset_index', [])
            
            # 创建Tag注释
            tag_annotation_dict = {
                'release_name': tag_name,
                'consumer_version': meta.get('consumer_version', ''),
                'bundle_version': meta.get('bundle_versions', [''])[0],
                'training_dataset_version': meta.get('version', ''),
                'description': f"{topic}场景数据集专题交付",
                'datasets_count': len(dataset_index),
                'total_clips': sum(ds.get('duplicate', 1) for ds in dataset_index),
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            tag_annotation = yaml.dump(tag_annotation_dict, default_flow_style=False, allow_unicode=True)
        
        # 创建带注释的Tag
        try:
            subprocess.run(['git', 'tag', '-a', tag_name, '-m', tag_annotation], check=True)
            print(f"✅ 成功创建Tag: {tag_name}")
            
            # 询问是否推送
            push = input("🚀 是否推送Tag到远程仓库? (y/N): ").strip().lower()
            if push == 'y':
                subprocess.run(['git', 'push', 'origin', tag_name], check=True)
                print("✅ Tag已推送到远程仓库")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 创建Tag失败: {e}")
            return False
    
    def create_version_tag(self, version: str) -> bool:
        """创建大版本Tag"""
        if not version.startswith('v'):
            version = f"v{version}"
        
        tag_name = f"training/{version}"
        
        print(f"🏷️  创建版本Tag: {tag_name}")
        
        # 检查Tag是否已存在
        existing_tags = self._run_git_command(['tag', '-l'])
        if tag_name in existing_tags.split('\n'):
            print(f"❌ Tag {tag_name} 已存在")
            return False
        
        # 获取数据集信息
        dataset_info = self.get_dataset_info()
        if not dataset_info:
            print("❌ 创建版本Tag需要training_dataset.json文件")
            return False
        
        meta = dataset_info.get('meta', {})
        dataset_index = dataset_info.get('dataset_index', [])
        
        # 验证版本一致性
        dataset_version = meta.get('version', '')
        if dataset_version != version:
            print(f"⚠️  training_dataset.json中的版本({dataset_version})与Tag版本({version})不一致")
            confirm = input("是否继续创建Tag? (y/N): ").strip().lower()
            if confirm != 'y':
                return False
        
        # 创建Tag注释
        tag_annotation_dict = {
            'release_name': f"TrainingDataset {version}",
            'consumer_version': meta.get('consumer_version', ''),
            'bundle_versions': meta.get('bundle_versions', []),
            'training_dataset_version': version,
            'description': f"训练数据集 {version} 版本发布",
            'datasets_count': len(dataset_index),
            'total_clips': sum(ds.get('duplicate', 1) for ds in dataset_index),
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'release_type': 'major'
        }
        
        tag_annotation = yaml.dump(tag_annotation_dict, default_flow_style=False, allow_unicode=True)
        
        # 创建带注释的Tag
        try:
            subprocess.run(['git', 'tag', '-a', tag_name, '-m', tag_annotation], check=True)
            print(f"✅ 成功创建版本Tag: {tag_name}")
            
            # 询问是否推送
            push = input("🚀 是否推送Tag到远程仓库? (y/N): ").strip().lower()
            if push == 'y':
                subprocess.run(['git', 'push', 'origin', tag_name], check=True)
                print("✅ Tag已推送到远程仓库")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 创建Tag失败: {e}")
            return False
    
    def generate_release_notes(self, version: str, previous_version: str = None) -> str:
        """生成Release说明"""
        dataset_info = self.get_dataset_info()
        
        if not dataset_info:
            return f"# TrainingDataset {version}\n\n发布说明待完善..."
        
        meta = dataset_info.get('meta', {})
        dataset_index = dataset_info.get('dataset_index', [])
        
        # 基本信息
        release_notes = f"# TrainingDataset {version}\n\n"
        release_notes += "## 版本信息\n"
        release_notes += f"- **Consumer Version**: {meta.get('consumer_version', 'N/A')}\n"
        release_notes += f"- **Bundle Versions**: {', '.join(meta.get('bundle_versions', []))}\n"
        release_notes += f"- **发布日期**: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        
        # 数据统计
        release_notes += "## 数据统计\n"
        release_notes += f"- **总数据集数量**: {len(dataset_index)}个\n"
        release_notes += f"- **总Clips数量**: {sum(ds.get('duplicate', 1) for ds in dataset_index):,}\n"
        
        # 训练类型统计
        training_type = meta.get('training_type', 'regular')
        if training_type == 'dagger':
            release_notes += "- **支持训练类型**: DAgger训练\n"
        else:
            release_notes += "- **支持训练类型**: 常规训练\n"
        
        release_notes += "\n## 数据集列表\n"
        for i, dataset in enumerate(dataset_index, 1):
            dataset_name = dataset.get('name', f'dataset_{i}')
            clips_count = dataset.get('duplicate', 1)
            bundle_versions = dataset.get('bundle_versions', [])
            release_notes += f"{i}. **{dataset_name}** - {clips_count:,} clips\n"
            release_notes += f"   - Bundle版本: {', '.join(bundle_versions)}\n"
        
        # 变更日志 (需要手动补充)
        release_notes += "\n## 主要变更\n"
        release_notes += "### 新增功能\n"
        release_notes += "- TODO: 请补充新增功能\n\n"
        release_notes += "### 数据优化\n"
        release_notes += "- TODO: 请补充数据优化内容\n\n"
        release_notes += "### Bug修复\n"
        release_notes += "- TODO: 请补充Bug修复内容\n\n"
        
        # 兼容性信息
        release_notes += "## 兼容性\n"
        consumer_version = meta.get('consumer_version', '')
        if consumer_version:
            major_minor = '.'.join(consumer_version.split('.')[:2])
            release_notes += f"- 向下兼容 {major_minor}.x\n"
            release_notes += f"- 需要DataSpecHub {consumer_version}+支持\n\n"
        
        # 获取变更历史 (如果有上一个版本)
        if previous_version:
            try:
                previous_tag = f"training/{previous_version}"
                current_commit = self._run_git_command(['rev-parse', 'HEAD'])
                commits = self._run_git_command(['log', '--oneline', f'{previous_tag}..{current_commit}'])
                
                if commits:
                    release_notes += "## 提交历史\n"
                    for commit in commits.split('\n'):
                        if commit.strip():
                            release_notes += f"- {commit}\n"
                    release_notes += "\n"
            except:
                pass
        
        release_notes += "## 迁移指南\n"
        release_notes += "详见: [Migration_Guide.md](docs/migrations/Migration_Guide.md)\n"
        
        return release_notes
    
    def create_release_draft(self, version: str, previous_version: str = None) -> bool:
        """创建Release草稿"""
        if not version.startswith('v'):
            version = f"v{version}"
        
        tag_name = f"training/{version}"
        
        # 检查Tag是否存在
        existing_tags = self._run_git_command(['tag', '-l'])
        if tag_name not in existing_tags.split('\n'):
            print(f"❌ Tag {tag_name} 不存在，请先创建Tag")
            return False
        
        # 生成Release说明
        release_notes = self.generate_release_notes(version, previous_version)
        
        # 保存到文件
        release_file = f"release_notes_{version.replace('v', '')}.md"
        with open(release_file, 'w', encoding='utf-8') as f:
            f.write(release_notes)
        
        print(f"📝 Release说明已生成: {release_file}")
        print("💡 请编辑此文件完善发布说明，然后在GitHub上创建Release")
        print(f"   Tag: {tag_name}")
        print(f"   Title: TrainingDataset {version}")
        
        return True

def main():
    parser = argparse.ArgumentParser(description='Tag和Release创建工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 创建专题Tag
    create_feature_tag = subparsers.add_parser('create-feature-tag', help='创建专题数据交付Tag')
    create_feature_tag.add_argument('topic', help='主题名称 (如: toll_station)')
    create_feature_tag.add_argument('--date', help='日期 (YYYYMMDD格式，默认今天)')
    
    # 创建版本Tag
    create_version_tag = subparsers.add_parser('create-version-tag', help='创建大版本Tag')
    create_version_tag.add_argument('version', help='版本号 (如: 1.2.0 或 v1.2.0)')
    
    # 生成Release说明
    generate_release = subparsers.add_parser('generate-release', help='生成Release说明')
    generate_release.add_argument('version', help='版本号 (如: 1.2.0 或 v1.2.0)')
    generate_release.add_argument('--previous', help='上一个版本号 (用于生成变更日志)')
    
    # 列出现有Tag
    list_tags = subparsers.add_parser('list-tags', help='列出现有Tag')
    list_tags.add_argument('--pattern', help='Tag名称模式过滤')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    helper = TagReleaseHelper()
    
    if args.command == 'create-feature-tag':
        helper.create_feature_tag(args.topic, args.date)
    
    elif args.command == 'create-version-tag':
        helper.create_version_tag(args.version)
    
    elif args.command == 'generate-release':
        helper.create_release_draft(args.version, args.previous)
    
    elif args.command == 'list-tags':
        if args.pattern:
            tags = helper._run_git_command(['tag', '-l', args.pattern])
        else:
            tags = helper._run_git_command(['tag', '-l'])
        
        if tags:
            print("📋 现有Tag列表:")
            for tag in sorted(tags.split('\n')):
                if tag:
                    print(f"   • {tag}")
        else:
            print("ℹ️  没有找到Tag")

if __name__ == "__main__":
    main()

