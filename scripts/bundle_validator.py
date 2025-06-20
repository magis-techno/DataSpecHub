#!/usr/bin/env python3
"""
Bundle验证器 - 确保Bundle的完整性和可追溯性
核心功能：验证Bundle快照的有效性，确保下游可重现
"""

import yaml
import hashlib
import json
from pathlib import Path
import argparse
import sys
from typing import Dict, List, Any

class BundleValidator:
    """Bundle验证器 - 专注于核心验证"""
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root)
        self.bundles_dir = self.workspace_root / "bundles"
        self.channels_dir = self.workspace_root / "channels"
        self.consumers_dir = self.workspace_root / "consumers"
        
    def validate_bundle(self, bundle_path: str) -> Dict[str, Any]:
        """
        验证Bundle的完整性和可追溯性
        
        Returns:
            验证结果报告
        """
        
        # 1. 加载Bundle配置
        bundle_config = self._load_bundle_config(bundle_path)
        
        # 2. 核心验证项目
        results = {
            'bundle_path': bundle_path,
            'bundle_name': bundle_config['meta']['bundle_name'],
            'bundle_version': bundle_config['meta']['bundle_version'],
            'valid': True,
            'errors': [],
            'warnings': [],
            'checks': {}
        }
        
        # 3. 执行验证检查
        self._check_required_fields(bundle_config, results)
        self._check_source_traceability(bundle_config, results)
        self._check_channel_versions(bundle_config, results)
        self._check_integrity_hash(bundle_config, results)
        
        # 4. 汇总结果
        results['valid'] = len(results['errors']) == 0
        
        return results
    
    def _load_bundle_config(self, bundle_path: str) -> Dict[str, Any]:
        """加载Bundle配置"""
        full_path = self.workspace_root / bundle_path
        if not full_path.exists():
            raise FileNotFoundError(f"Bundle not found: {bundle_path}")
            
        with open(full_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _check_required_fields(self, config: Dict, results: Dict):
        """检查必需字段"""
        required_fields = [
            'meta.bundle_name',
            'meta.bundle_version', 
            'meta.bundle_type',
            'source_consumer',
            'channels',
            'integrity_hash'
        ]
        
        missing = []
        for field in required_fields:
            if '.' in field:
                keys = field.split('.')
                obj = config
                try:
                    for key in keys:
                        obj = obj[key]
                except (KeyError, TypeError):
                    missing.append(field)
            else:
                if field not in config:
                    missing.append(field)
        
        if missing:
            results['errors'].append(f"Missing required fields: {missing}")
        
        results['checks']['required_fields'] = len(missing) == 0
    
    def _check_source_traceability(self, config: Dict, results: Dict):
        """检查来源可追溯性"""
        source_consumer = config.get('source_consumer')
        if not source_consumer:
            results['errors'].append("Missing source_consumer field")
            results['checks']['source_traceability'] = False
            return
            
        # 检查源Consumer文件是否存在
        consumer_path = self.workspace_root / source_consumer
        if not consumer_path.exists():
            results['warnings'].append(f"Source consumer file not found: {source_consumer}")
        
        results['checks']['source_traceability'] = True
    
    def _check_channel_versions(self, config: Dict, results: Dict):
        """检查通道版本有效性"""
        channels = config.get('channels', [])
        invalid_channels = []
        
        for channel in channels:
            channel_name = channel.get('channel')
            version = channel.get('version')
            spec_file = channel.get('spec_file')
            
            if not all([channel_name, version, spec_file]):
                invalid_channels.append(f"{channel_name}: missing required fields")
                continue
                
            # 检查spec文件是否存在
            spec_path = self.workspace_root / spec_file
            if not spec_path.exists():
                invalid_channels.append(f"{channel_name}: spec file not found ({spec_file})")
        
        if invalid_channels:
            results['errors'].extend(invalid_channels)
            
        results['checks']['channel_versions'] = len(invalid_channels) == 0
    
    def _check_integrity_hash(self, config: Dict, results: Dict):
        """检查完整性哈希"""
        stored_hash = config.get('integrity_hash')
        if not stored_hash:
            results['errors'].append("Missing integrity_hash")
            results['checks']['integrity_hash'] = False
            return
            
        # 重新计算哈希
        channels = config.get('channels', [])
        calculated_hash = self._calculate_hash(channels)
        
        if stored_hash != calculated_hash:
            results['errors'].append(f"Integrity hash mismatch: stored={stored_hash}, calculated={calculated_hash}")
            results['checks']['integrity_hash'] = False
        else:
            results['checks']['integrity_hash'] = True
    
    def _calculate_hash(self, channels: List[Dict]) -> str:
        """计算Bundle完整性哈希"""
        hash_data = {
            'channels': [(ch.get('channel'), ch.get('version')) for ch in channels]
        }
        content = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def print_validation_report(self, results: Dict):
        """打印验证报告"""
        print(f"\n📋 Bundle Validation Report")
        print(f"Bundle: {results['bundle_name']} v{results['bundle_version']}")
        print(f"Path: {results['bundle_path']}")
        print(f"Status: {'✅ VALID' if results['valid'] else '❌ INVALID'}")
        
        print(f"\n🔍 Validation Checks:")
        for check, passed in results['checks'].items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {check}: {status}")
        
        if results['errors']:
            print(f"\n❌ Errors ({len(results['errors'])}):")
            for error in results['errors']:
                print(f"  - {error}")
                
        if results['warnings']:
            print(f"\n⚠️  Warnings ({len(results['warnings'])}):")
            for warning in results['warnings']:
                print(f"  - {warning}")

def main():
    parser = argparse.ArgumentParser(description="Bundle Validator - Bundle完整性验证")
    parser.add_argument("bundle", help="Bundle文件路径")
    parser.add_argument("--workspace", default=".", help="工作空间根目录")
    parser.add_argument("--quiet", action="store_true", help="只显示错误")
    
    args = parser.parse_args()
    
    try:
        validator = BundleValidator(args.workspace)
        results = validator.validate_bundle(args.bundle)
        
        if not args.quiet:
            validator.print_validation_report(results)
        
        # 返回适当的退出码
        sys.exit(0 if results['valid'] else 1)
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 