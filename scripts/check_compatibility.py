#!/usr/bin/env python3
"""
Compatibility Check Script

检查通道规格变更是否破坏现有生产/发布版本的兼容性
"""

import os
import sys
import yaml
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import subprocess

class CompatibilityChecker:
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.channels_path = self.root_path / "channels"
        
    def load_consumer_matrix(self, matrix_path: Path) -> Dict[str, Any]:
        """加载消费者兼容性矩阵"""
        with open(matrix_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get_changed_files(self, base_ref: str, head_ref: str) -> List[str]:
        """获取变更的文件列表"""
        try:
            result = subprocess.run(
                ['git', 'diff', '--name-only', f"{base_ref}...{head_ref}"],
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
        except subprocess.CalledProcessError as e:
            print(f"Error getting changed files: {e}")
            return []
    
    def extract_channel_changes(self, changed_files: List[str]) -> Dict[str, List[str]]:
        """提取通道变更信息"""
        channel_changes = {}
        
        for file_path in changed_files:
            if file_path.startswith('channels/'):
                parts = file_path.split('/')
                if len(parts) >= 3:
                    channel = parts[1]
                    if channel not in channel_changes:
                        channel_changes[channel] = []
                    channel_changes[channel].append(file_path)
                    
        return channel_changes
    
    def analyze_spec_changes(self, channel: str, base_ref: str, head_ref: str) -> Dict[str, Any]:
        """分析规格文件的具体变更"""
        spec_files = list((self.channels_path / channel).glob("spec-*.yaml"))
        if not spec_files:
            return {"type": "new_channel", "severity": "low"}
            
        changes = {
            "type": "modification",
            "severity": "low",
            "breaking_changes": [],
            "additions": [],
            "modifications": []
        }
        
        for spec_file in spec_files:
            rel_path = spec_file.relative_to(self.root_path)
            
            # 获取文件的base和head版本
            base_content = self._get_file_content_at_ref(rel_path, base_ref)
            head_content = self._get_file_content_at_ref(rel_path, head_ref)
            
            if base_content is None and head_content is not None:
                # 新文件
                changes["additions"].append(str(rel_path))
            elif base_content is not None and head_content is not None:
                # 修改的文件
                breaking_changes = self._detect_breaking_changes(base_content, head_content)
                if breaking_changes:
                    changes["breaking_changes"].extend(breaking_changes)
                    changes["severity"] = "high"
                changes["modifications"].append(str(rel_path))
                
        return changes
    
    def _get_file_content_at_ref(self, file_path: Path, ref: str) -> Optional[str]:
        """获取指定Git引用下的文件内容"""
        try:
            result = subprocess.run(
                ['git', 'show', f"{ref}:{file_path}"],
                capture_output=True, text=True, check=True
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return None
    
    def _detect_breaking_changes(self, base_content: str, head_content: str) -> List[Dict[str, Any]]:
        """检测破坏性变更"""
        breaking_changes = []
        
        try:
            base_spec = yaml.safe_load(base_content)
            head_spec = yaml.safe_load(head_content)
        except yaml.YAMLError:
            return breaking_changes
            
        # 检查版本变更
        base_version = base_spec.get('meta', {}).get('version', '0.0.0')
        head_version = head_spec.get('meta', {}).get('version', '0.0.0')
        
        if self._is_major_version_bump(base_version, head_version):
            breaking_changes.append({
                "type": "major_version_change",
                "description": f"Version changed from {base_version} to {head_version}",
                "severity": "high"
            })
            
        # 检查Schema变更
        base_schema = base_spec.get('schema', {})
        head_schema = head_spec.get('schema', {})
        
        schema_breaking_changes = self._check_schema_breaking_changes(base_schema, head_schema)
        breaking_changes.extend(schema_breaking_changes)
        
        return breaking_changes
    
    def _is_major_version_bump(self, base_version: str, head_version: str) -> bool:
        """检查是否是主版本升级"""
        try:
            base_major = int(base_version.split('.')[0])
            head_major = int(head_version.split('.')[0])
            return head_major > base_major
        except (ValueError, IndexError):
            return False
    
    def _check_schema_breaking_changes(self, base_schema: Dict, head_schema: Dict) -> List[Dict[str, Any]]:
        """检查Schema的破坏性变更"""
        breaking_changes = []
        
        # 检查字段删除
        base_fields = self._extract_fields(base_schema)
        head_fields = self._extract_fields(head_schema)
        
        removed_fields = base_fields - head_fields
        for field in removed_fields:
            breaking_changes.append({
                "type": "field_removal",
                "description": f"Field '{field}' was removed",
                "severity": "critical"
            })
            
        # 检查数据格式变更
        base_format = base_schema.get('data_format', {})
        head_format = head_schema.get('data_format', {})
        
        if base_format.get('type') != head_format.get('type'):
            breaking_changes.append({
                "type": "format_change",
                "description": f"Data format type changed from {base_format.get('type')} to {head_format.get('type')}",
                "severity": "high"
            })
            
        return breaking_changes
    
    def _extract_fields(self, schema: Dict) -> set:
        """提取Schema中的所有字段"""
        fields = set()
        
        def extract_recursive(obj, prefix=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    field_path = f"{prefix}.{key}" if prefix else key
                    fields.add(field_path)
                    if isinstance(value, dict):
                        extract_recursive(value, field_path)
                        
        extract_recursive(schema)
        return fields
    
    def check_production_locks(self, matrix: Dict[str, Any], 
                             channel_changes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检查生产锁定冲突"""
        conflicts = []
        production_locks = matrix.get('production_locks', {})
        
        for consumer, locks in production_locks.items():
            lock_until = locks.get('locked_until', '')
            if self._is_lock_active(lock_until):
                for channel in channel_changes:
                    if channel in locks:
                        conflicts.append({
                            "consumer": consumer,
                            "channel": channel,
                            "locked_version": locks[channel],
                            "locked_until": lock_until,
                            "severity": "critical",
                            "message": f"Channel {channel} is locked for {consumer} until {lock_until}"
                        })
                        
        return conflicts
    
    def _is_lock_active(self, lock_until: str) -> bool:
        """检查锁定是否仍然有效"""
        try:
            lock_date = datetime.fromisoformat(lock_until)
            return datetime.now() < lock_date
        except ValueError:
            return False
    
    def generate_compatibility_report(self, base_ref: str, head_ref: str, 
                                    matrix_path: Path) -> Dict[str, Any]:
        """生成兼容性检查报告"""
        matrix = self.load_consumer_matrix(matrix_path)
        changed_files = self.get_changed_files(base_ref, head_ref)
        channel_changes = self.extract_channel_changes(changed_files)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "base_ref": base_ref,
            "head_ref": head_ref,
            "changed_files": changed_files,
            "channel_changes": {},
            "breaking_changes": [],
            "production_conflicts": [],
            "affected_consumers": [],
            "summary": {
                "total_channels_changed": len(channel_changes),
                "breaking_changes_count": 0,
                "production_conflicts_count": 0,
                "severity": "low"
            }
        }
        
        # 分析每个变更的通道
        for channel, files in channel_changes.items():
            change_analysis = self.analyze_spec_changes(channel, base_ref, head_ref)
            report["channel_changes"][channel] = change_analysis
            
            # 收集破坏性变更
            if change_analysis.get("breaking_changes"):
                for bc in change_analysis["breaking_changes"]:
                    bc["channel"] = channel
                    report["breaking_changes"].append(bc)
                    
        # 检查生产锁定冲突
        production_conflicts = self.check_production_locks(matrix, channel_changes)
        report["production_conflicts"] = production_conflicts
        
        # 确定受影响的消费者
        affected_consumers = self._identify_affected_consumers(matrix, channel_changes)
        report["affected_consumers"] = affected_consumers
        
        # 更新摘要
        report["summary"]["breaking_changes_count"] = len(report["breaking_changes"])
        report["summary"]["production_conflicts_count"] = len(production_conflicts)
        
        if production_conflicts:
            report["summary"]["severity"] = "critical"
        elif report["breaking_changes"]:
            report["summary"]["severity"] = "high"
        elif channel_changes:
            report["summary"]["severity"] = "medium"
            
        return report
    
    def _identify_affected_consumers(self, matrix: Dict[str, Any], 
                                   channel_changes: Dict[str, Any]) -> List[str]:
        """识别受影响的消费者"""
        affected = set()
        consumers = matrix.get('consumers', {})
        
        for consumer, config in consumers.items():
            critical_channels = config.get('critical_channels', [])
            for channel in channel_changes:
                if channel in critical_channels:
                    affected.add(consumer)
                    
        return list(affected)

def main():
    parser = argparse.ArgumentParser(description='Check channel specification compatibility')
    parser.add_argument('--base-ref', required=True, help='Base Git reference')
    parser.add_argument('--head-ref', required=True, help='Head Git reference')
    parser.add_argument('--matrix', required=True, help='Path to consumer matrix file')
    parser.add_argument('--output', required=True, help='Output file for compatibility report')
    parser.add_argument('--fail-on-breaking', action='store_true', 
                       help='Fail if breaking changes are detected')
    
    args = parser.parse_args()
    
    checker = CompatibilityChecker()
    
    try:
        report = checker.generate_compatibility_report(
            args.base_ref, args.head_ref, Path(args.matrix)
        )
        
        # 保存报告
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        # 输出摘要
        print(f"🔍 Compatibility Check Results:")
        print(f"  📊 Channels changed: {report['summary']['total_channels_changed']}")
        print(f"  ⚠️  Breaking changes: {report['summary']['breaking_changes_count']}")
        print(f"  🔒 Production conflicts: {report['summary']['production_conflicts_count']}")
        print(f"  📈 Overall severity: {report['summary']['severity']}")
        
        if report['affected_consumers']:
            print(f"  👥 Affected consumers: {', '.join(report['affected_consumers'])}")
            
        # 详细输出破坏性变更
        if report['breaking_changes']:
            print(f"\n💥 Breaking Changes Detected:")
            for bc in report['breaking_changes']:
                print(f"  - {bc['channel']}: {bc['description']}")
                
        # 详细输出生产冲突
        if report['production_conflicts']:
            print(f"\n🚫 Production Lock Conflicts:")
            for conflict in report['production_conflicts']:
                print(f"  - {conflict['channel']} locked for {conflict['consumer']} until {conflict['locked_until']}")
                
        # 根据参数决定是否失败
        if args.fail_on_breaking and (report['breaking_changes'] or report['production_conflicts']):
            print(f"\n❌ Failing due to breaking changes or production conflicts")
            sys.exit(1)
        else:
            print(f"\n✅ Compatibility check completed")
            
    except Exception as e:
        print(f"❌ Error during compatibility check: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 