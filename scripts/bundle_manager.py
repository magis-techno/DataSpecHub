#!/usr/bin/env python3
"""
Bundle Manager CLI Tool

支持Bundle的创建、验证、版本解析和冲突检测等功能
"""

import os
import sys
import yaml
import json
import click
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import semver

class BundleManager:
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.channels_path = self.root_path / "channels"
        self.consumers_path = self.root_path / "consumers"
        self.bundles_path = self.root_path / "bundles"
        
    def load_consumer_config(self, consumer_name: str) -> Dict[str, Any]:
        """加载Consumer配置"""
        consumer_file = self.consumers_path / f"{consumer_name}.yaml"
        if not consumer_file.exists():
            raise FileNotFoundError(f"Consumer config not found: {consumer_file}")
            
        with open(consumer_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get_available_versions(self, channel: str) -> List[str]:
        """获取通道的所有可用版本"""
        channel_dir = self.channels_path / channel
        if not channel_dir.exists():
            return []
            
        versions = []
        for spec_file in channel_dir.glob("spec-*.yaml"):
            version = spec_file.stem.replace("spec-", "")
            versions.append(version)
            
        # 按语义化版本排序
        try:
            versions.sort(key=lambda v: semver.VersionInfo.parse(v))
        except ValueError:
            # 如果不是标准语义化版本，按字符串排序
            versions.sort()
            
        return versions
    
    def resolve_version_constraint(self, channel: str, constraint: str) -> Optional[str]:
        """解析版本约束，返回具体版本"""
        available_versions = self.get_available_versions(channel)
        if not available_versions:
            return None
            
        # 简化的版本解析逻辑
        if constraint.startswith(">="):
            min_version = constraint[2:].strip()
            for version in reversed(available_versions):
                if semver.compare(version, min_version) >= 0:
                    return version
                    
        elif constraint.startswith("^"):
            base_version = constraint[1:].strip()
            base_major = semver.VersionInfo.parse(base_version).major
            for version in reversed(available_versions):
                version_info = semver.VersionInfo.parse(version)
                if (version_info.major == base_major and 
                    semver.compare(version, base_version) >= 0):
                    return version
                    
        elif constraint.startswith("~"):
            base_version = constraint[1:].strip()
            base_info = semver.VersionInfo.parse(base_version)
            for version in reversed(available_versions):
                version_info = semver.VersionInfo.parse(version)
                if (version_info.major == base_info.major and
                    version_info.minor == base_info.minor and
                    semver.compare(version, base_version) >= 0):
                    return version
                    
        else:
            # 精确版本或范围
            if constraint in available_versions:
                return constraint
                
        return available_versions[-1] if available_versions else None
    
    def detect_conflicts(self, resolved_versions: Dict[str, str]) -> List[Dict[str, Any]]:
        """检测版本冲突"""
        conflicts = []
        
        # 检查是否有多个版本的同一通道
        channel_families = {}
        for channel, version in resolved_versions.items():
            # 提取通道族（如radar.v1和radar.v2都属于radar族）
            family = channel.split('.')[0]
            if family not in channel_families:
                channel_families[family] = []
            channel_families[family].append((channel, version))
            
        # 检查每个通道族的冲突
        for family, channels in channel_families.items():
            if len(channels) > 1:
                # 检查是否支持共存
                coexistence_supported = self._check_coexistence_support(channels)
                if not coexistence_supported:
                    conflicts.append({
                        'type': 'version_conflict',
                        'family': family,
                        'channels': channels,
                        'message': f"Multiple versions of {family} are not compatible",
                        'severity': 'high'
                    })
                    
        return conflicts
    
    def _check_coexistence_support(self, channels: List[Tuple[str, str]]) -> bool:
        """检查通道是否支持版本共存"""
        # 简化逻辑：检查是否有明确的共存配置
        # 实际实现中应该检查通道的兼容性矩阵
        for channel, version in channels:
            channel_dir = self.channels_path / channel
            release_file = channel_dir / f"release-{version}.yaml"
            
            if release_file.exists():
                with open(release_file, 'r', encoding='utf-8') as f:
                    release_config = yaml.safe_load(f)
                    
                # 检查是否有共存配置
                if 'coexistence' in release_config:
                    return True
                    
        return False
    
    def create_bundle_from_consumer(self, consumer_name: str, bundle_name: str, 
                                  bundle_version: str) -> Dict[str, Any]:
        """从Consumer配置创建Bundle"""
        consumer_config = self.load_consumer_config(consumer_name)
        
        # 收集所有需求
        all_requirements = []
        if 'requirement_groups' in consumer_config:
            for group_name, group_config in consumer_config['requirement_groups'].items():
                if 'requirements' in group_config:
                    all_requirements.extend(group_config['requirements'])
        elif 'requirements' in consumer_config:
            all_requirements = consumer_config['requirements']
            
        # 解析版本约束
        resolved_versions = {}
        for req in all_requirements:
            channel = req['channel']
            version_constraint = req.get('version', '>=0.0.0')
            
            resolved_version = self.resolve_version_constraint(channel, version_constraint)
            if resolved_version:
                resolved_versions[channel] = resolved_version
            else:
                print(f"Warning: Could not resolve version for {channel} with constraint {version_constraint}")
                
        # 检测冲突
        conflicts = self.detect_conflicts(resolved_versions)
        
        # 生成Bundle配置
        bundle_config = {
            'meta': {
                'bundle': bundle_name,
                'version': bundle_version,
                'owner': consumer_config.get('meta', {}).get('owner', 'unknown'),
                'description': f"Bundle created from consumer {consumer_name}",
                'created_from': f"consumers/{consumer_name}.yaml",
                'snapshot_date': datetime.now().isoformat() + 'Z'
            },
            'resolved_versions': resolved_versions,
            'channels': [],
            'compatibility_matrix': {
                'validated_at': datetime.now().isoformat() + 'Z',
                'validation_passed': len(conflicts) == 0,
                'all_compatible': len(conflicts) == 0,
                'conflicts': conflicts
            }
        }
        
        # 生成通道配置
        for channel, version in resolved_versions.items():
            channel_config = {
                'channel': channel,
                'version': version,
                'locked_at': datetime.now().isoformat() + 'Z',
                'source_commit': self._get_channel_commit(channel, version)
            }
            
            # 从原始需求中获取额外配置
            for req in all_requirements:
                if req['channel'] == channel:
                    if 'required' in req:
                        channel_config['required'] = req['required']
                    if 'on_missing' in req:
                        channel_config['on_missing'] = req['on_missing']
                    break
                    
            bundle_config['channels'].append(channel_config)
            
        return bundle_config
    
    def _get_channel_commit(self, channel: str, version: str) -> str:
        """获取通道特定版本的Git commit（简化实现）"""
        # 实际实现中应该查询Git历史
        return hashlib.md5(f"{channel}-{version}".encode()).hexdigest()[:8]
    
    def save_bundle(self, bundle_config: Dict[str, Any], output_path: Path):
        """保存Bundle配置到文件"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(bundle_config, f, default_flow_style=False, 
                     allow_unicode=True, sort_keys=False)
    
    def generate_lock_file(self, bundle_path: Path) -> Dict[str, Any]:
        """生成Bundle的Lock文件"""
        with open(bundle_path, 'r', encoding='utf-8') as f:
            bundle_config = yaml.safe_load(f)
            
        lock_data = {
            'bundle_ref': str(bundle_path.relative_to(self.root_path)),
            'lock_version': '1.0',
            'generated_at': datetime.now().isoformat() + 'Z',
            'channels': {}
        }
        
        # 为每个通道生成详细信息
        for channel_config in bundle_config.get('channels', []):
            channel = channel_config['channel']
            version = channel_config['version']
            
            # 计算规格文件的hash
            spec_path = self.channels_path / channel / f"spec-{version}.yaml"
            spec_hash = self._calculate_file_hash(spec_path) if spec_path.exists() else "unknown"
            
            lock_data['channels'][channel] = {
                'version': version,
                'spec_hash': f"sha256:{spec_hash}",
                'locked_at': channel_config.get('locked_at'),
                'source_commit': channel_config.get('source_commit')
            }
            
        # 计算整体完整性hash
        content_str = json.dumps(lock_data['channels'], sort_keys=True)
        integrity_hash = hashlib.sha256(content_str.encode()).hexdigest()
        lock_data['integrity_hash'] = f"sha256:{integrity_hash}"
        
        return lock_data
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件的SHA256 hash"""
        if not file_path.exists():
            return "file_not_found"
            
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

# CLI命令定义
@click.group()
def cli():
    """DataSpec Bundle Manager - 管理数据Bundle的创建、验证和版本控制"""
    pass

@cli.command()
@click.option('--from-consumer', required=True, help='Consumer配置名称')
@click.option('--name', required=True, help='Bundle名称')
@click.option('--version', required=True, help='Bundle版本')
@click.option('--output', help='输出路径（可选）')
def create(from_consumer, name, version, output):
    """从Consumer配置创建Bundle"""
    manager = BundleManager()
    
    try:
        click.echo(f"🔨 Creating bundle '{name}:{version}' from consumer '{from_consumer}'...")
        
        bundle_config = manager.create_bundle_from_consumer(from_consumer, name, version)
        
        # 确定输出路径
        if not output:
            output = manager.bundles_path / name / f"bundle-{version}.yaml"
        else:
            output = Path(output)
            
        manager.save_bundle(bundle_config, output)
        
        # 检查冲突
        conflicts = bundle_config['compatibility_matrix']['conflicts']
        if conflicts:
            click.echo(f"⚠️  Found {len(conflicts)} conflicts:")
            for conflict in conflicts:
                click.echo(f"  - {conflict['message']} (severity: {conflict['severity']})")
        else:
            click.echo("✅ No conflicts detected")
            
        click.echo(f"📦 Bundle saved to: {output}")
        
        # 显示解析结果
        resolved = bundle_config['resolved_versions']
        click.echo(f"\n📋 Resolved {len(resolved)} channels:")
        for channel, version in resolved.items():
            click.echo(f"  - {channel}: {version}")
            
    except Exception as e:
        click.echo(f"❌ Error creating bundle: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('bundle_path')
def validate(bundle_path):
    """验证Bundle配置的完整性"""
    manager = BundleManager()
    bundle_path = Path(bundle_path)
    
    try:
        click.echo(f"🔍 Validating bundle: {bundle_path}")
        
        with open(bundle_path, 'r', encoding='utf-8') as f:
            bundle_config = yaml.safe_load(f)
            
        errors = []
        warnings = []
        
        # 基本结构验证
        required_fields = ['meta', 'channels']
        for field in required_fields:
            if field not in bundle_config:
                errors.append(f"Missing required field: {field}")
                
        # 验证通道版本是否存在
        for channel_config in bundle_config.get('channels', []):
            channel = channel_config.get('channel')
            version = channel_config.get('version')
            
            if not channel or not version:
                errors.append(f"Channel config missing channel or version: {channel_config}")
                continue
                
            # 检查规格文件是否存在
            spec_path = manager.channels_path / channel / f"spec-{version}.yaml"
            if not spec_path.exists():
                errors.append(f"Spec file not found: {spec_path}")
                
        # 输出结果
        if errors:
            click.echo(f"❌ Validation failed with {len(errors)} errors:")
            for error in errors:
                click.echo(f"  - {error}")
            sys.exit(1)
        else:
            click.echo("✅ Bundle validation passed")
            
        if warnings:
            click.echo(f"⚠️  {len(warnings)} warnings:")
            for warning in warnings:
                click.echo(f"  - {warning}")
                
    except Exception as e:
        click.echo(f"❌ Error validating bundle: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('bundle_path')
@click.option('--output', help='Lock文件输出路径')
def lock(bundle_path, output):
    """生成Bundle的Lock文件"""
    manager = BundleManager()
    bundle_path = Path(bundle_path)
    
    try:
        click.echo(f"🔒 Generating lock file for: {bundle_path}")
        
        lock_data = manager.generate_lock_file(bundle_path)
        
        # 确定输出路径
        if not output:
            output = bundle_path.with_suffix('.lock.json')
        else:
            output = Path(output)
            
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(lock_data, f, indent=2, ensure_ascii=False)
            
        click.echo(f"🔒 Lock file saved to: {output}")
        click.echo(f"🔐 Integrity hash: {lock_data['integrity_hash']}")
        
    except Exception as e:
        click.echo(f"❌ Error generating lock file: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('bundle_path')
@click.option('--conflicts', is_flag=True, help='显示版本冲突分析')
def analyze(bundle_path, conflicts):
    """分析Bundle的版本兼容性和冲突"""
    manager = BundleManager()
    bundle_path = Path(bundle_path)
    
    try:
        click.echo(f"📊 Analyzing bundle: {bundle_path}")
        
        with open(bundle_path, 'r', encoding='utf-8') as f:
            bundle_config = yaml.safe_load(f)
            
        # 基本统计
        channels = bundle_config.get('channels', [])
        click.echo(f"\n📈 Bundle Statistics:")
        click.echo(f"  - Total channels: {len(channels)}")
        click.echo(f"  - Bundle version: {bundle_config.get('meta', {}).get('version', 'unknown')}")
        
        # 版本分布
        version_dist = {}
        for channel_config in channels:
            version = channel_config.get('version', 'unknown')
            major_version = version.split('.')[0] if '.' in version else version
            version_dist[major_version] = version_dist.get(major_version, 0) + 1
            
        click.echo(f"\n📊 Version Distribution:")
        for major_ver, count in sorted(version_dist.items()):
            click.echo(f"  - v{major_ver}.x: {count} channels")
            
        # 冲突分析
        if conflicts:
            compatibility_matrix = bundle_config.get('compatibility_matrix', {})
            bundle_conflicts = compatibility_matrix.get('conflicts', [])
            
            if bundle_conflicts:
                click.echo(f"\n⚠️  Found {len(bundle_conflicts)} conflicts:")
                for conflict in bundle_conflicts:
                    click.echo(f"  - {conflict.get('message', 'Unknown conflict')}")
                    click.echo(f"    Severity: {conflict.get('severity', 'unknown')}")
                    if 'channels' in conflict:
                        click.echo(f"    Affected: {conflict['channels']}")
            else:
                click.echo(f"\n✅ No conflicts detected")
                
    except Exception as e:
        click.echo(f"❌ Error analyzing bundle: {e}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    cli() 