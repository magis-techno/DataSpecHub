#!/usr/bin/env python3
"""
Consumer别名管理器 - 简化用户体验
让用户直接用熟悉的consumer版本获取数据，无需关心bundle版本转换
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Optional
import datetime

class ConsumerAliasManager:
    """Consumer版本别名管理器"""
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root)
        self.alias_file = self.workspace_root / "consumer_version_aliases.yaml"
        
    def register_consumer_version(self, consumer_name: str, consumer_version: str, 
                                bundle_path: str, bundle_type: str = "weekly"):
        """
        注册consumer版本到bundle的映射
        
        Args:
            consumer_name: 消费者名称 (如 end_to_end)
            consumer_version: 消费者版本 (如 v1.2.0)
            bundle_path: 对应的bundle路径
            bundle_type: bundle类型
        """
        aliases = self._load_aliases()
        
        if consumer_name not in aliases:
            aliases[consumer_name] = {}
            
        aliases[consumer_name][consumer_version] = {
            'bundle_path': bundle_path,
            'bundle_type': bundle_type,
            'registered_at': datetime.datetime.now().isoformat(),
            'status': 'active'
        }
        
        # 更新latest别名
        aliases[consumer_name]['latest'] = aliases[consumer_name][consumer_version]
        
        self._save_aliases(aliases)
        print(f"✅ 注册成功: {consumer_name}@{consumer_version} -> {bundle_path}")
        
    def get_bundle_for_consumer(self, consumer_name: str, 
                              consumer_version: str = "latest") -> Optional[str]:
        """
        根据consumer版本获取对应的bundle路径
        
        Args:
            consumer_name: 消费者名称
            consumer_version: 消费者版本，默认"latest"
            
        Returns:
            bundle文件路径，如果没找到返回None
        """
        aliases = self._load_aliases()
        
        if consumer_name not in aliases:
            return None
            
        consumer_aliases = aliases[consumer_name]
        if consumer_version not in consumer_aliases:
            return None
            
        return consumer_aliases[consumer_version]['bundle_path']
        
    def load_data_by_consumer_version(self, consumer_name: str, 
                                    consumer_version: str = "latest") -> str:
        """
        用户友好的数据加载接口
        
        Args:
            consumer_name: 消费者名称 (用户熟悉的)
            consumer_version: 消费者版本 (用户熟悉的)
            
        Returns:
            数据加载命令
        """
        bundle_path = self.get_bundle_for_consumer(consumer_name, consumer_version)
        
        if not bundle_path:
            raise ValueError(f"找不到 {consumer_name}@{consumer_version} 对应的bundle")
            
        # 生成用户命令
        load_command = f"dataspec load --consumer {consumer_name}@{consumer_version}"
        
        print(f"🎯 使用consumer版本: {consumer_name}@{consumer_version}")
        print(f"📦 对应bundle: {bundle_path}")
        print(f"💻 简化命令: {load_command}")
        
        return load_command
        
    def _load_aliases(self) -> Dict:
        """加载别名配置"""
        if not self.alias_file.exists():
            return {}
            
        with open(self.alias_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
            
    def _save_aliases(self, aliases: Dict):
        """保存别名配置"""
        with open(self.alias_file, 'w', encoding='utf-8') as f:
            yaml.dump(aliases, f, default_flow_style=False, allow_unicode=True)

def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Consumer版本别名管理")
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # 注册命令
    register_parser = subparsers.add_parser('register', help='注册consumer版本')
    register_parser.add_argument('--consumer', required=True, help='消费者名称')
    register_parser.add_argument('--version', required=True, help='消费者版本')
    register_parser.add_argument('--bundle', required=True, help='bundle路径')
    register_parser.add_argument('--type', default='weekly', help='bundle类型')
    
    # 加载命令
    load_parser = subparsers.add_parser('load', help='根据consumer版本加载数据')
    load_parser.add_argument('--consumer', required=True, help='消费者名称')
    load_parser.add_argument('--version', default='latest', help='消费者版本')
    
    args = parser.parse_args()
    manager = ConsumerAliasManager()
    
    if args.command == 'register':
        manager.register_consumer_version(
            args.consumer, args.version, args.bundle, args.type
        )
    elif args.command == 'load':
        manager.load_data_by_consumer_version(args.consumer, args.version)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 