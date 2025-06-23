#!/usr/bin/env python3
"""
DataSpec CLI - 简化用户体验的数据获取工具
让用户用熟悉的consumer版本直接获取数据，隐藏bundle转换的复杂性
"""

import argparse
import sys
from pathlib import Path
from typing import Optional
import yaml

# 导入我们的管理器
from consumer_alias_manager import ConsumerAliasManager
from production_cycle_manager import ProductionCycleManager

class DataSpecCLI:
    """DataSpec 简化命令行工具"""
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root)
        self.alias_manager = ConsumerAliasManager(workspace_root)
        self.cycle_manager = ProductionCycleManager(workspace_root)
        
    def load_data(self, consumer_name: str, consumer_version: str = "latest") -> str:
        """
        用户友好的数据加载接口
        
        Args:
            consumer_name: 消费者名称 (用户熟悉的)
            consumer_version: 消费者版本 (用户熟悉的，默认latest)
            
        Returns:
            实际的数据加载命令
        """
        print(f"🎯 准备加载数据: {consumer_name}@{consumer_version}")
        
        # 1. 如果用户指定了latest，先检查生产周期状态
        if consumer_version == "latest":
            active_version = self.cycle_manager.get_active_version(consumer_name)
            if active_version:
                consumer_version = active_version
                print(f"📋 根据生产周期，推荐使用: {consumer_version}")
        
        # 2. 获取对应的bundle
        bundle_path = self.alias_manager.get_bundle_for_consumer(
            consumer_name, consumer_version
        )
        
        if not bundle_path:
            print(f"❌ 找不到 {consumer_name}@{consumer_version} 对应的数据包")
            self._suggest_available_versions(consumer_name)
            return ""
            
        # 3. 生成实际的数据加载命令
        actual_command = f"dataspec load --bundle {bundle_path}"
        
        print(f"✅ 数据包已找到: {bundle_path}")
        print(f"💻 执行命令: {actual_command}")
        print()
        print("🏃 正在加载数据...")
        
        return actual_command
        
    def get_status(self, consumer_name: Optional[str] = None) -> None:
        """获取状态信息"""
        if consumer_name:
            # 单个consumer状态
            status = self.cycle_manager.get_user_friendly_status(consumer_name)
            print(status)
            
            # 显示可用版本
            self._show_available_versions(consumer_name)
        else:
            # 所有consumer状态
            self._show_all_status()
            
    def list_consumers(self) -> None:
        """列出所有可用的consumer"""
        consumers_dir = self.workspace_root / "consumers"
        if not consumers_dir.exists():
            print("❌ 找不到consumers目录")
            return
            
        print("📋 可用的Consumer:")
        for consumer_dir in consumers_dir.iterdir():
            if consumer_dir.is_dir():
                latest_file = consumer_dir / "latest.yaml"
                if latest_file.exists():
                    # 读取版本信息
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                        version = config.get('meta', {}).get('version', 'unknown')
                        description = config.get('meta', {}).get('description', '')
                    
                    status = self.cycle_manager.get_user_friendly_status(consumer_dir.name)
                    print(f"  • {consumer_dir.name}@{version}")
                    print(f"    {description}")
                    print(f"    状态: {status.split(': ', 1)[1] if ': ' in status else status}")
                    print()
                    
    def quick_setup(self, consumer_name: str) -> None:
        """快速设置：为consumer生成当前可用的bundle"""
        print(f"🚀 正在为 {consumer_name} 设置数据环境...")
        
        # 1. 检查consumer配置是否存在
        consumer_file = self.workspace_root / f"consumers/{consumer_name}/latest.yaml"
        if not consumer_file.exists():
            print(f"❌ 找不到consumer配置: {consumer_file}")
            return
            
        # 2. 生成bundle (使用现有的bundle_generator)
        from bundle_generator import BundleGenerator
        generator = BundleGenerator(self.workspace_root)
        
        try:
            bundle_path = generator.generate_bundle(
                f"consumers/{consumer_name}/latest.yaml", 
                bundle_type="weekly"
            )
            
            # 3. 读取consumer版本
            with open(consumer_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                consumer_version = config.get('meta', {}).get('version', 'latest')
            
            # 4. 注册到别名管理器
            self.alias_manager.register_consumer_version(
                consumer_name, consumer_version, bundle_path, "weekly"
            )
            
            print(f"✅ 快速设置完成!")
            print(f"   现在可以使用: dataspec load {consumer_name}")
            
        except Exception as e:
            print(f"❌ 设置失败: {e}")
            
    def _suggest_available_versions(self, consumer_name: str) -> None:
        """建议可用版本"""
        print(f"\n💡 {consumer_name} 的可用版本:")
        self._show_available_versions(consumer_name)
        
    def _show_available_versions(self, consumer_name: str) -> None:
        """显示可用版本"""
        consumer_dir = self.workspace_root / f"consumers/{consumer_name}"
        if not consumer_dir.exists():
            print(f"   ❌ Consumer目录不存在: {consumer_name}")
            return
            
        versions = []
        for yaml_file in consumer_dir.glob("*.yaml"):
            if yaml_file.name != "latest.yaml":
                version = yaml_file.stem
                bundle_path = self.alias_manager.get_bundle_for_consumer(consumer_name, version)
                status = "✅ 有数据包" if bundle_path else "❌ 无数据包"
                versions.append((version, status))
                
        if versions:
            for version, status in versions:
                print(f"   • {version} - {status}")
        else:
            print(f"   • latest - 默认版本")
            
    def _show_all_status(self) -> None:
        """显示所有consumer状态"""
        consumers_dir = self.workspace_root / "consumers"
        if not consumers_dir.exists():
            return
            
        print("📊 所有Consumer状态:")
        for consumer_dir in consumers_dir.iterdir():
            if consumer_dir.is_dir():
                status = self.cycle_manager.get_user_friendly_status(consumer_dir.name)
                print(f"  {status}")

def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="DataSpec CLI - 简化的数据获取工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 加载数据 (用熟悉的consumer版本)
  dataspec load end_to_end
  dataspec load end_to_end@v1.2.0
  
  # 查看状态
  dataspec status
  dataspec status end_to_end
  
  # 列出所有consumer
  dataspec list
  
  # 快速设置新环境
  dataspec setup end_to_end
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # load命令
    load_parser = subparsers.add_parser('load', help='加载数据')
    load_parser.add_argument('consumer_spec', help='Consumer规格 (name 或 name@version)')
    
    # status命令
    status_parser = subparsers.add_parser('status', help='查看状态')
    status_parser.add_argument('consumer', nargs='?', help='Consumer名称 (可选)')
    
    # list命令
    list_parser = subparsers.add_parser('list', help='列出所有consumer')
    
    # setup命令
    setup_parser = subparsers.add_parser('setup', help='快速设置consumer环境')
    setup_parser.add_argument('consumer', help='Consumer名称')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    cli = DataSpecCLI()
    
    if args.command == 'load':
        # 解析consumer规格
        if '@' in args.consumer_spec:
            consumer_name, consumer_version = args.consumer_spec.split('@', 1)
        else:
            consumer_name = args.consumer_spec
            consumer_version = "latest"
            
        cli.load_data(consumer_name, consumer_version)
        
    elif args.command == 'status':
        cli.get_status(args.consumer)
        
    elif args.command == 'list':
        cli.list_consumers()
        
    elif args.command == 'setup':
        cli.quick_setup(args.consumer)

if __name__ == "__main__":
    main() 