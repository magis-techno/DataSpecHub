#!/usr/bin/env python3
"""
基于数据库的简化Bundle生成器
结合semver约束解析 + 数据库可用性查询，生成轻量级Bundle
"""

import yaml
import os
import sys
import datetime
from pathlib import Path
import argparse
from typing import Dict, List, Any, Optional
import json

# 导入现有的核心模块
from bundle_manager import BundleManager
from database_query_helper import DatabaseQueryHelper

class DatabaseBundleGenerator:
    """基于数据库的简化Bundle生成器"""
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root)
        self.consumers_dir = self.workspace_root / "consumers"
        self.bundles_dir = self.workspace_root / "bundles"
        
        # 使用现有的版本管理核心
        self.bundle_manager = BundleManager(workspace_root)
        # 使用数据库查询助手
        self.db_helper = DatabaseQueryHelper(workspace_root)
        
    def generate_bundle(self, consumer_path: str, bundle_type: str = "weekly") -> str:
        """
        生成基于数据库的Bundle
        
        Args:
            consumer_path: Consumer配置文件路径 (如 "consumers/end_to_end/latest.yaml")
            bundle_type: Bundle类型 (weekly/release/snapshot)
            
        Returns:
            生成的bundle文件路径
        """
        print(f"🔨 开始生成Bundle: {consumer_path}")
        
        # 1. 加载Consumer配置
        consumer_config = self._load_consumer_config(consumer_path)
        consumer_name = self._extract_consumer_name(consumer_config)
        
        print(f"📋 Consumer: {consumer_name}")
        print(f"📦 Bundle类型: {bundle_type}")
        
        # 2. 使用bundle_manager进行版本约束解析 (保留完整的semver功能)
        print("🔍 解析版本约束...")
        resolved_versions = self._resolve_versions_with_bundle_manager(consumer_config)
        
        # 3. 查询数据库验证可用性
        print("🗄️  验证数据库可用性...")
        availability_report = self.db_helper.validate_bundle_data_availability(resolved_versions)
        
        # 4. 生成Bundle配置 (简化版本)
        bundle_config = self._create_simplified_bundle_config(
            consumer_config, resolved_versions, availability_report, bundle_type
        )
        
        # 5. 保存Bundle文件
        bundle_path = self._save_bundle(consumer_name, bundle_config, bundle_type)
        
        # 6. 输出报告
        self._print_generation_report(bundle_path, resolved_versions, availability_report)
        
        return bundle_path
    
    def _load_consumer_config(self, consumer_path: str) -> Dict[str, Any]:
        """加载Consumer配置"""
        full_path = self.workspace_root / consumer_path
        if not full_path.exists():
            raise FileNotFoundError(f"Consumer配置不存在: {consumer_path}")
            
        with open(full_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _extract_consumer_name(self, consumer_config: Dict[str, Any]) -> str:
        """提取Consumer名称"""
        # 支持多种配置格式
        if 'meta' in consumer_config:
            return consumer_config['meta'].get('consumer', 'unknown')
        elif 'consumer' in consumer_config:
            return consumer_config['consumer'].get('name', 'unknown')
        else:
            return 'unknown'
    
    def _resolve_versions_with_bundle_manager(self, consumer_config: Dict[str, Any]) -> Dict[str, str]:
        """使用bundle_manager解析版本约束 (保留完整semver功能)"""
        
        # 提取requirements
        requirements = []
        if 'requirement_groups' in consumer_config:
            # 支持分组requirements
            for group_name, group_config in consumer_config['requirement_groups'].items():
                if 'requirements' in group_config:
                    requirements.extend(group_config['requirements'])
        elif 'requirements' in consumer_config:
            requirements = consumer_config['requirements']
        else:
            raise ValueError("Consumer配置中没有找到requirements")
        
        resolved_versions = {}
        
        for req in requirements:
            channel = req['channel']
            version_constraint = req.get('version', '>=0.0.0')
            
            print(f"  解析 {channel}: {version_constraint}")
            
            # 使用bundle_manager的版本解析功能
            resolved_version = self.bundle_manager.resolve_version_constraint(
                channel, version_constraint
            )
            
            if resolved_version:
                resolved_versions[channel] = resolved_version
                print(f"    ✅ 解析为: {resolved_version}")
            else:
                print(f"    ❌ 无法解析版本约束: {version_constraint}")
                # 查询数据库获取最新版本作为fallback
                latest = self.db_helper.query_latest_version(channel)
                if latest:
                    resolved_versions[channel] = latest
                    print(f"    🔄 使用数据库最新版本: {latest}")
                else:
                    raise ValueError(f"无法为通道 {channel} 找到可用版本")
        
        return resolved_versions
    
    def _create_simplified_bundle_config(self, consumer_config: Dict, 
                                       resolved_versions: Dict[str, str],
                                       availability_report: Dict,
                                       bundle_type: str) -> Dict[str, Any]:
        """创建简化的Bundle配置"""
        
        now = datetime.datetime.now()
        consumer_name = self._extract_consumer_name(consumer_config)
        
        # 生成版本标识
        if bundle_type == "weekly":
            year = now.year
            week = now.isocalendar()[1]
            bundle_version = f"v{consumer_config['meta'].get('version', '1.0.0')}-{year}.{week:02d}"
        elif bundle_type == "release":
            bundle_version = f"v{consumer_config['meta'].get('version', '1.0.0')}-release"
        else:
            bundle_version = f"v{consumer_config['meta'].get('version', '1.0.0')}-{now.strftime('%Y%m%d-%H%M%S')}"
        
        # 创建简化的Bundle配置
        bundle_config = {
            'meta': {
                'bundle_name': consumer_name,
                'bundle_version': bundle_version,
                'bundle_type': bundle_type,
                'created_at': now.isoformat() + 'Z',
                'created_by': 'database_bundle_generator',
                'consumer_source': consumer_config['meta'],
                'data_validated': availability_report['all_available']
            },
            'resolved_channels': {},
            'data_summary': {
                'total_channels': len(resolved_versions),
                'available_channels': availability_report['summary']['available_channels'],
                'total_data_size_gb': availability_report['summary']['total_data_size_gb'],
                'validation_passed': availability_report['all_available']
            },
            'database_info': {
                'query_time': now.isoformat() + 'Z',
                'availability_report': availability_report
            }
        }
        
        # 添加每个通道的详细信息
        for channel, version in resolved_versions.items():
            channel_availability = availability_report['channels'].get(channel, {})
            
            bundle_config['resolved_channels'][channel] = {
                'version': version,
                'available': channel_availability.get('available', False),
                'data_path': channel_availability.get('data_path', ''),
                'size_gb': channel_availability.get('size_gb', 0),
                'sample_count': channel_availability.get('sample_count', 0),
                'quality_score': channel_availability.get('quality_score', 0.0)
            }
        
        return bundle_config
    
    def _save_bundle(self, consumer_name: str, bundle_config: Dict[str, Any], bundle_type: str) -> str:
        """保存Bundle文件"""
        
        # 创建目录结构
        if bundle_type == "weekly":
            bundle_dir = self.bundles_dir / "weekly"
        elif bundle_type == "release":
            bundle_dir = self.bundles_dir / "release"
        else:
            bundle_dir = self.bundles_dir / "snapshots"
            
        bundle_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        bundle_version = bundle_config['meta']['bundle_version']
        filename = f"{consumer_name}-{bundle_version}.yaml"
        bundle_path = bundle_dir / filename
        
        # 保存文件
        with open(bundle_path, 'w', encoding='utf-8') as f:
            yaml.dump(bundle_config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
        return str(bundle_path.relative_to(self.workspace_root))
    
    def _print_generation_report(self, bundle_path: str, 
                               resolved_versions: Dict[str, str],
                               availability_report: Dict):
        """打印生成报告"""
        print(f"\n📊 Bundle生成报告:")
        print(f"✅ Bundle保存至: {bundle_path}")
        print(f"📈 解析通道数: {len(resolved_versions)}")
        print(f"💾 总数据大小: {availability_report['summary']['total_data_size_gb']} GB")
        print(f"🟢 可用通道: {availability_report['summary']['available_channels']}")
        print(f"🔴 不可用通道: {availability_report['summary']['unavailable_channels']}")
        
        if not availability_report['all_available']:
            print(f"\n⚠️  警告: 存在不可用的通道数据")
            for channel, info in availability_report['channels'].items():
                if not info.get('available', True):
                    print(f"   ❌ {channel}: {info.get('reason', 'Unknown error')}")
        else:
            print(f"\n🎉 所有通道数据验证通过!")
    
    def quick_validate(self, consumer_path: str) -> Dict[str, Any]:
        """快速验证Consumer的数据可用性，不生成Bundle"""
        print(f"🔍 快速验证: {consumer_path}")
        
        consumer_config = self._load_consumer_config(consumer_path)
        resolved_versions = self._resolve_versions_with_bundle_manager(consumer_config)
        availability_report = self.db_helper.validate_bundle_data_availability(resolved_versions)
        
        print(f"\n📊 验证结果:")
        print(f"📈 通道数: {len(resolved_versions)}")
        print(f"🟢 可用: {availability_report['summary']['available_channels']}")
        print(f"🔴 不可用: {availability_report['summary']['unavailable_channels']}")
        print(f"💾 总大小: {availability_report['summary']['total_data_size_gb']} GB")
        
        return availability_report

def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(description="基于数据库的简化Bundle生成器")
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # generate命令
    gen_parser = subparsers.add_parser('generate', help='生成Bundle')
    gen_parser.add_argument('--consumer', required=True, help='Consumer配置文件路径')
    gen_parser.add_argument('--type', choices=['weekly', 'release', 'snapshot'], 
                           default='weekly', help='Bundle类型')
    gen_parser.add_argument('--workspace', default='.', help='工作空间根目录')
    
    # validate命令
    val_parser = subparsers.add_parser('validate', help='快速验证数据可用性')
    val_parser.add_argument('--consumer', required=True, help='Consumer配置文件路径')
    val_parser.add_argument('--workspace', default='.', help='工作空间根目录')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    try:
        generator = DatabaseBundleGenerator(args.workspace)
        
        if args.command == 'generate':
            bundle_path = generator.generate_bundle(args.consumer, args.type)
            print(f"\n🎉 Bundle生成成功: {bundle_path}")
            
        elif args.command == 'validate':
            report = generator.quick_validate(args.consumer)
            exit_code = 0 if report['all_available'] else 1
            sys.exit(exit_code)
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
