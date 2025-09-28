#!/usr/bin/env python3
"""
创建结构化提交信息的辅助工具
"""

import os
import sys
import argparse
import yaml
from datetime import datetime
from typing import Dict, Optional, Any
import subprocess

def get_current_date() -> str:
    """获取当前日期"""
    return datetime.now().strftime("%Y-%m-%d")

def get_dataset_stats(dataset_name: str) -> Optional[Dict[str, Any]]:
    """尝试从training_dataset.json获取数据集统计信息"""
    dataset_files = ['training_dataset.json', 'training_dataset.dagger.json']
    
    for filename in dataset_files:
        if os.path.exists(filename):
            try:
                import json
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                dataset_index = data.get('dataset_index', [])
                for dataset in dataset_index:
                    if dataset.get('name') == dataset_name:
                        return dataset
            except:
                continue
    
    return None

def create_commit_message(
    commit_type: str,
    description: str,
    task_tag: str = "",
    details: Optional[Dict[str, Any]] = None
) -> str:
    """创建结构化的提交信息"""
    
    # 构建YAML正文
    yaml_body = {
        'date': get_current_date(),
        'type': commit_type,
        'description': description
    }
    
    if task_tag:
        yaml_body['task_tag'] = task_tag
    else:
        yaml_body['task_tag'] = ""
    
    if details:
        yaml_body['details'] = details
    
    # 生成完整的提交信息
    commit_msg = f"{description}\n\n"
    commit_msg += yaml.dump(yaml_body, default_flow_style=False, allow_unicode=True)
    
    return commit_msg

def interactive_commit_builder() -> str:
    """交互式构建提交信息"""
    print("🔧 结构化提交信息构建器")
    print("=" * 40)
    
    # 获取提交类型
    print("\n📝 提交类型:")
    types = [
        ('add', '新增数据集或clips'),
        ('modify(clean)', '清洗类修改（去重、质量过滤等）'),
        ('modify(balance)', '平衡类修改（调整场景/类别分布等）'),
        ('fix', '修复数据错误或配置问题'),
        ('docs', '文档更新'),
        ('refactor', '重构但不改变功能的修改')
    ]
    
    for i, (type_key, desc) in enumerate(types, 1):
        print(f"   {i}. {type_key} - {desc}")
    
    while True:
        try:
            choice = int(input("\n选择提交类型 (1-6): ")) - 1
            if 0 <= choice < len(types):
                commit_type = types[choice][0]
                break
            else:
                print("❌ 无效选择，请重新输入")
        except ValueError:
            print("❌ 请输入数字")
    
    # 获取描述
    description = input("\n📄 提交描述: ").strip()
    while not description:
        description = input("❌ 描述不能为空，请重新输入: ").strip()
    
    # 获取任务标签
    task_tag = input("\n🏷️  任务标签 (可选，如 TASK-12345): ").strip()
    
    # 获取详细信息
    details = {}
    if commit_type in ['add', 'modify(clean)', 'modify(balance)']:
        print(f"\n📊 详细信息 ({commit_type} 操作建议填写):")
        
        dataset_name = input("   数据集名称: ").strip()
        if dataset_name:
            details['dataset'] = dataset_name
        
        if commit_type == 'add':
            try:
                clips_added = int(input("   新增clips数量: ") or "0")
                if clips_added > 0:
                    details['clips_added'] = clips_added
            except ValueError:
                pass
            
            try:
                clips_after = int(input("   新增后总clips数量: ") or "0")
                if clips_after > 0:
                    details['clips_after'] = clips_after
            except ValueError:
                pass
        
        elif commit_type in ['modify(clean)', 'modify(balance)']:
            try:
                clips_before = int(input("   处理前clips数量: ") or "0")
                if clips_before > 0:
                    details['total_clips_before'] = clips_before
            except ValueError:
                pass
            
            try:
                clips_removed = int(input("   移除clips数量: ") or "0")
                if clips_removed > 0:
                    details['clips_removed'] = clips_removed
            except ValueError:
                pass
            
            try:
                clips_after = int(input("   处理后clips数量: ") or "0")
                if clips_after > 0:
                    details['clips_after'] = clips_after
            except ValueError:
                pass
            
            if commit_type == 'modify(clean)':
                quality_threshold = input("   质量阈值 (可选): ").strip()
                if quality_threshold:
                    try:
                        details['quality_threshold'] = float(quality_threshold)
                    except ValueError:
                        details['quality_threshold'] = quality_threshold
        
        # 其他自定义字段
        print("   其他字段 (输入空行结束):")
        while True:
            field_input = input("   字段名=值: ").strip()
            if not field_input:
                break
            
            if '=' in field_input:
                key, value = field_input.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # 尝试转换为数字
                try:
                    if '.' in value:
                        value = float(value)
                    else:
                        value = int(value)
                except ValueError:
                    pass  # 保持字符串
                
                details[key] = value
    
    # 生成提交信息
    commit_msg = create_commit_message(commit_type, description, task_tag, details if details else None)
    
    # 预览
    print(f"\n📋 生成的提交信息:")
    print("=" * 40)
    print(commit_msg)
    print("=" * 40)
    
    return commit_msg

def execute_commit(commit_msg: str, auto_confirm: bool = False) -> bool:
    """执行Git提交"""
    if not auto_confirm:
        confirm = input("\n✅ 确认提交? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ 取消提交")
            return False
    
    try:
        # 检查是否有已暂存的文件
        result = subprocess.run(['git', 'diff', '--cached', '--name-only'], 
                              capture_output=True, text=True, check=True)
        staged_files = result.stdout.strip()
        
        if not staged_files:
            print("❌ 没有已暂存的文件，请先使用 'git add' 添加文件")
            return False
        
        print(f"📁 将提交的文件:")
        for file in staged_files.split('\n'):
            if file:
                print(f"   • {file}")
        
        # 执行提交
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
        print("✅ 提交成功!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 提交失败: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='结构化提交信息生成器')
    parser.add_argument('--type', choices=['add', 'modify(clean)', 'modify(balance)', 'fix', 'docs', 'refactor'],
                       help='提交类型')
    parser.add_argument('--description', help='提交描述')
    parser.add_argument('--task-tag', help='任务标签')
    parser.add_argument('--dataset', help='数据集名称')
    parser.add_argument('--clips-before', type=int, help='处理前clips数量')
    parser.add_argument('--clips-removed', type=int, help='移除clips数量')
    parser.add_argument('--clips-after', type=int, help='处理后clips数量')
    parser.add_argument('--clips-added', type=int, help='新增clips数量')
    parser.add_argument('--quality-threshold', type=float, help='质量阈值')
    parser.add_argument('--interactive', '-i', action='store_true', help='交互式模式')
    parser.add_argument('--commit', action='store_true', help='自动执行提交')
    parser.add_argument('--dry-run', action='store_true', help='仅生成提交信息，不执行提交')
    
    args = parser.parse_args()
    
    if args.interactive or not args.type or not args.description:
        # 交互式模式
        commit_msg = interactive_commit_builder()
    else:
        # 命令行模式
        details = {}
        
        if args.dataset:
            details['dataset'] = args.dataset
        
        if args.clips_before is not None:
            details['total_clips_before'] = args.clips_before
        
        if args.clips_removed is not None:
            details['clips_removed'] = args.clips_removed
        
        if args.clips_after is not None:
            details['clips_after'] = args.clips_after
        
        if args.clips_added is not None:
            details['clips_added'] = args.clips_added
        
        if args.quality_threshold is not None:
            details['quality_threshold'] = args.quality_threshold
        
        commit_msg = create_commit_message(
            args.type, 
            args.description, 
            args.task_tag or "", 
            details if details else None
        )
        
        print("📋 生成的提交信息:")
        print("=" * 40)
        print(commit_msg)
        print("=" * 40)
    
    if args.dry_run:
        print("🔍 仅预览模式，未执行提交")
        return
    
    if args.commit:
        execute_commit(commit_msg, auto_confirm=True)
    else:
        execute_commit(commit_msg, auto_confirm=False)

if __name__ == "__main__":
    main()

