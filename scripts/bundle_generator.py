#!/usr/bin/env python3
"""
Bundle Generator - 硬约束快照生成器
核心功能：从Consumer配置生成硬约束的数据快照，确保可追溯性
"""

import yaml
import os
import sys
import datetime
from pathlib import Path
import argparse
from typing import Dict, List, Any
import hashlib
import json

class BundleGenerator:
    """Bundle生成器 - 专注于核心功能"""
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root)
        self.consumers_dir = self.workspace_root / "consumers"
        self.channels_dir = self.workspace_root / "channels"
        self.bundles_dir = self.workspace_root / "bundles"
        
    def generate_bundle(self, consumer_path: str, bundle_type: str = "snapshot") -> str:
        """
        生成Bundle快照
        
        Args:
            consumer_path: Consumer配置文件路径
            bundle_type: Bundle类型 (snapshot/weekly/release)
            
        Returns:
            生成的bundle文件路径
        """
        
        # 1. 加载Consumer配置
        consumer_config = self._load_consumer_config(consumer_path)
        consumer_name = consumer_config['meta']['consumer']
        
        # 2. 解析版本约束，生成精确版本
        resolved_channels = self._resolve_channel_versions(consumer_config['requirements'])
        
        # 3. 生成Bundle元数据
        bundle_meta = self._generate_bundle_meta(consumer_config, bundle_type)
        
        # 4. 创建Bundle配置
        bundle_config = {
            'meta': bundle_meta,
            'source_consumer': consumer_path,
            'snapshot_time': datetime.datetime.now().isoformat() + 'Z',
            'channels': resolved_channels,
            'integrity_hash': self._calculate_bundle_hash(resolved_channels)
        }
        
        # 5. 保存Bundle文件
        bundle_path = self._save_bundle(consumer_name, bundle_config, bundle_type)
        
        print(f"✅ Bundle generated: {bundle_path}")
        print(f"📊 Channels resolved: {len(resolved_channels)}")
        
        return bundle_path
    
    def _load_consumer_config(self, consumer_path: str) -> Dict[str, Any]:
        """加载Consumer配置"""
        full_path = self.workspace_root / consumer_path
        if not full_path.exists():
            raise FileNotFoundError(f"Consumer config not found: {consumer_path}")
            
        with open(full_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _resolve_channel_versions(self, requirements: List[Dict]) -> List[Dict]:
        """解析版本约束，生成精确版本快照"""
        resolved = []
        
        for req in requirements:
            channel = req['channel']
            version_constraint = req['version']
            
            # 获取channel的实际可用版本
            available_versions = self._get_available_versions(channel)
            
            # 解析版本约束，选择具体版本
            resolved_version = self._resolve_version_constraint(version_constraint, available_versions)
            
            # 生成硬约束配置
            channel_config = {
                'channel': channel,
                'version': resolved_version,  # 精确版本，不再是范围
                'locked_at': datetime.datetime.now().isoformat() + 'Z',
                'required': req.get('required', True),
                'source_constraint': version_constraint,  # 记录原始约束，便于追溯
                'spec_file': f"channels/{channel}/spec-{resolved_version}.yaml"
            }
            
            resolved.append(channel_config)
            
        return resolved
    
    def _get_available_versions(self, channel: str) -> List[str]:
        """获取channel的可用版本列表"""
        channel_dir = self.channels_dir / channel
        if not channel_dir.exists():
            raise FileNotFoundError(f"Channel not found: {channel}")
            
        # 扫描spec文件，提取版本号
        versions = []
        for spec_file in channel_dir.glob("spec-*.yaml"):
            # 从文件名提取版本号: spec-1.2.0.yaml -> 1.2.0
            version = spec_file.stem.replace("spec-", "")
            versions.append(version)
            
        return sorted(versions, key=lambda v: [int(x) for x in v.split('.')])
    
    def _resolve_version_constraint(self, constraint: str, available: List[str]) -> str:
        """解析版本约束，选择具体版本"""
        
        # 精确版本
        if constraint in available:
            return constraint
            
        # 范围约束 >= 、>= <、^等
        if constraint.startswith(">="):
            min_version = constraint[2:].strip()
            for version in reversed(available):  # 选择最新的满足条件版本
                if self._version_compare(version, min_version) >= 0:
                    return version
                    
        # 简化处理，实际可以用packaging.version
        # 这里假设返回最新版本
        return available[-1] if available else "1.0.0"
    
    def _version_compare(self, v1: str, v2: str) -> int:
        """简单版本比较，实际应该用标准库"""
        def version_tuple(v):
            return tuple(map(int, v.split('.')))
        
        v1_tuple = version_tuple(v1)
        v2_tuple = version_tuple(v2)
        
        if v1_tuple > v2_tuple:
            return 1
        elif v1_tuple < v2_tuple:
            return -1
        else:
            return 0
    
    def _generate_bundle_meta(self, consumer_config: Dict, bundle_type: str) -> Dict:
        """生成Bundle元数据"""
        now = datetime.datetime.now()
        
        # 根据类型生成不同的版本标识
        if bundle_type == "weekly":
            # 周版本: 2025.24 (年.周数)
            year = now.year
            week = now.isocalendar()[1]
            version = f"{year}.{week:02d}"
        elif bundle_type == "release":
            # 发布版本: v1.0.0
            version = consumer_config['meta'].get('version', '1.0.0')
        else:
            # 快照版本: 20250620-143022
            version = now.strftime("%Y%m%d-%H%M%S")
            
        return {
            'bundle_name': consumer_config['meta']['consumer'],
            'bundle_version': version,
            'bundle_type': bundle_type,
            'created_at': now.isoformat() + 'Z',
            'created_by': 'bundle_generator',
            'source_consumer': consumer_config['meta']['consumer'],
            'consumer_version': consumer_config['meta'].get('version'),
            'description': f"Bundle generated from {consumer_config['meta']['consumer']} consumer"
        }
    
    def _calculate_bundle_hash(self, channels: List[Dict]) -> str:
        """计算Bundle的完整性哈希"""
        # 提取关键信息计算哈希
        hash_data = {
            'channels': [(ch['channel'], ch['version']) for ch in channels]
        }
        content = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _save_bundle(self, consumer_name: str, bundle_config: Dict, bundle_type: str) -> str:
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
        version = bundle_config['meta']['bundle_version']
        filename = f"{consumer_name}-{version}.yaml"
        bundle_path = bundle_dir / filename
        
        # 保存文件
        with open(bundle_path, 'w', encoding='utf-8') as f:
            yaml.dump(bundle_config, f, default_flow_style=False, allow_unicode=True)
            
        return str(bundle_path.relative_to(self.workspace_root))

def main():
    parser = argparse.ArgumentParser(description="Bundle Generator - 硬约束快照生成器")
    parser.add_argument("--consumer", required=True, help="Consumer配置文件路径")
    parser.add_argument("--type", choices=["snapshot", "weekly", "release"], 
                       default="snapshot", help="Bundle类型")
    parser.add_argument("--workspace", default=".", help="工作空间根目录")
    
    args = parser.parse_args()
    
    try:
        generator = BundleGenerator(args.workspace)
        bundle_path = generator.generate_bundle(args.consumer, args.type)
        print(f"🎉 Bundle successfully generated at: {bundle_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 