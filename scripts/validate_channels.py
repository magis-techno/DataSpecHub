#!/usr/bin/env python3
"""
Channel Specification Validation Script

验证通道规范的完整性、一致性和质量
"""

import os
import sys
import yaml
import json
import glob
from pathlib import Path
from typing import Dict, List, Any, Optional
import jsonschema
from datetime import datetime

class ChannelValidator:
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.channels_path = self.root_path / "channels"
        self.taxonomy_path = self.root_path / "taxonomy"
        self.errors = []
        self.warnings = []
        
    def load_taxonomy(self) -> Dict[str, Any]:
        """加载通道分类体系"""
        taxonomy_file = self.taxonomy_path / "channel_taxonomy.yaml"
        if not taxonomy_file.exists():
            self.errors.append(f"Taxonomy file not found: {taxonomy_file}")
            return {}
            
        with open(taxonomy_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def validate_spec_schema(self, spec_path: Path) -> bool:
        """验证规范文件的Schema"""
        try:
            with open(spec_path, 'r', encoding='utf-8') as f:
                spec = yaml.safe_load(f)
                
            # 基本结构验证
            required_fields = ['meta', 'schema', 'validation', 'lifecycle']
            for field in required_fields:
                if field not in spec:
                    self.errors.append(f"{spec_path}: Missing required field '{field}'")
                    return False
                    
            # Meta信息验证
            meta = spec['meta']
            required_meta = ['channel', 'version', 'category', 'description']
            for field in required_meta:
                if field not in meta:
                    self.errors.append(f"{spec_path}: Missing meta field '{field}'")
                    
            # 版本格式验证
            version = meta.get('version', '')
            if not self._is_valid_semver(version):
                self.errors.append(f"{spec_path}: Invalid version format '{version}'")
                
            # 生命周期状态验证
            lifecycle = spec['lifecycle']
            valid_statuses = ['draft', 'stable', 'deprecated', 'legacy']
            status = lifecycle.get('status', '')
            if status not in valid_statuses:
                self.errors.append(f"{spec_path}: Invalid lifecycle status '{status}'")
                
            return len(self.errors) == 0
            
        except Exception as e:
            self.errors.append(f"{spec_path}: Failed to parse YAML: {e}")
            return False
    
    def validate_release_mapping(self, release_path: Path) -> bool:
        """验证发布规范中的生产映射"""
        try:
            with open(release_path, 'r', encoding='utf-8') as f:
                release = yaml.safe_load(f)
                
            # 检查生产映射信息
            if 'production_mapping' in release:
                mapping = release['production_mapping']
                
                # 验证生产批次信息
                if 'production_runs' in mapping:
                    for run in mapping['production_runs']:
                        required_run_fields = ['run_id', 'date', 'data_path', 'samples_count']
                        for field in required_run_fields:
                            if field not in run:
                                self.warnings.append(f"{release_path}: Missing production run field '{field}'")
                                
                        # 验证数据路径是否存在（如果是本地路径）
                        data_path = run.get('data_path', '')
                        if data_path.startswith('/') and not Path(data_path).exists():
                            self.warnings.append(f"{release_path}: Data path does not exist: {data_path}")
                            
            # 验证变更记录
            if 'changes' not in release:
                self.warnings.append(f"{release_path}: No change log found")
            else:
                for change in release['changes']:
                    if 'type' not in change or 'description' not in change:
                        self.warnings.append(f"{release_path}: Incomplete change record")
                        
            return True
            
        except Exception as e:
            self.errors.append(f"{release_path}: Failed to parse release file: {e}")
            return False
    
    def validate_channel_consistency(self, channel_dir: Path) -> bool:
        """验证通道内部一致性"""
        channel_name = channel_dir.name
        
        # 查找所有规范和发布文件
        spec_files = list(channel_dir.glob("spec-*.yaml"))
        release_files = list(channel_dir.glob("release-*.yaml"))
        
        if not spec_files:
            self.errors.append(f"Channel '{channel_name}': No specification files found")
            return False
            
        if not release_files:
            self.errors.append(f"Channel '{channel_name}': No release files found")
            return False
            
        # 验证每个发布文件都有对应的规范文件
        for release_file in release_files:
            try:
                with open(release_file, 'r', encoding='utf-8') as f:
                    release = yaml.safe_load(f)
                    
                spec_ref = release.get('spec_ref', '')
                if spec_ref:
                    spec_path = channel_dir / spec_ref.replace('./', '')
                    if not spec_path.exists():
                        self.errors.append(f"Release '{release_file}': Referenced spec file not found: {spec_ref}")
                        
            except Exception as e:
                self.errors.append(f"Release '{release_file}': Failed to parse: {e}")
                
        # 验证样本数据
        samples_dir = channel_dir / "samples"
        if not samples_dir.exists():
            self.warnings.append(f"Channel '{channel_name}': No samples directory found")
        elif not list(samples_dir.iterdir()):
            self.warnings.append(f"Channel '{channel_name}': Samples directory is empty")
            
        return len(self.errors) == 0
    
    def validate_taxonomy_consistency(self, taxonomy: Dict[str, Any]) -> bool:
        """验证分类体系一致性"""
        if 'categories' not in taxonomy:
            self.errors.append("Taxonomy: Missing 'categories' section")
            return False
            
        # 收集所有通道
        all_channels = set()
        for category, info in taxonomy['categories'].items():
            if 'channels' in info:
                all_channels.update(info['channels'])
                
        # 验证别名
        if 'aliases' in taxonomy:
            for alias, target in taxonomy['aliases'].items():
                if target not in all_channels:
                    self.warnings.append(f"Taxonomy: Alias '{alias}' points to unknown channel '{target}'")
                    
        # 验证废弃通道
        if 'deprecated' in taxonomy:
            for dep in taxonomy['deprecated']:
                channel = dep.get('channel', '')
                replacement = dep.get('replacement', '')
                if replacement and replacement not in all_channels:
                    self.warnings.append(f"Taxonomy: Deprecated channel '{channel}' replacement '{replacement}' not found")
                    
        return True
    
    def _is_valid_semver(self, version: str) -> bool:
        """验证语义化版本格式"""
        import re
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$'
        return bool(re.match(pattern, version))
    
    def generate_report(self) -> Dict[str, Any]:
        """生成验证报告"""
        return {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_errors': len(self.errors),
                'total_warnings': len(self.warnings),
                'validation_passed': len(self.errors) == 0
            },
            'errors': self.errors,
            'warnings': self.warnings
        }
    
    def run_validation(self) -> bool:
        """运行完整验证"""
        print("🔍 Starting channel specification validation...")
        
        # 加载分类体系
        taxonomy = self.load_taxonomy()
        if taxonomy:
            self.validate_taxonomy_consistency(taxonomy)
            
        # 验证所有通道
        if self.channels_path.exists():
            for channel_dir in self.channels_path.iterdir():
                if channel_dir.is_dir():
                    print(f"  Validating channel: {channel_dir.name}")
                    
                    # 验证通道一致性
                    self.validate_channel_consistency(channel_dir)
                    
                    # 验证规范文件
                    for spec_file in channel_dir.glob("spec-*.yaml"):
                        self.validate_spec_schema(spec_file)
                        
                    # 验证发布文件
                    for release_file in channel_dir.glob("release-*.yaml"):
                        self.validate_release_mapping(release_file)
        else:
            self.errors.append(f"Channels directory not found: {self.channels_path}")
            
        # 生成报告
        report = self.generate_report()
        
        # 输出结果
        print(f"\n📊 Validation Results:")
        print(f"  ✅ Errors: {report['summary']['total_errors']}")
        print(f"  ⚠️  Warnings: {report['summary']['total_warnings']}")
        
        if self.errors:
            print(f"\n❌ Errors:")
            for error in self.errors:
                print(f"  - {error}")
                
        if self.warnings:
            print(f"\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")
                
        # 保存详细报告
        report_path = self.root_path / "validation-report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        print(f"\n📄 Detailed report saved to: {report_path}")
        
        return report['summary']['validation_passed']

def main():
    validator = ChannelValidator()
    success = validator.run_validation()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 