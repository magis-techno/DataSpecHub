#!/usr/bin/env python3
"""
阶段管理工具 - 用于管理训练数据集的阶段化加载
"""

import os
import sys
import json
import yaml
import argparse
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import hashlib
from pathlib import Path

class StageManager:
    def __init__(self, config_path: str = None):
        """初始化阶段管理器"""
        self.repo_root = self._get_repo_root()
        self.config_path = config_path or os.path.join(self.repo_root, "stage_config.yaml")
        self.active_stage_path = os.path.join(self.repo_root, "active_stage.yaml")
        
        # 加载配置
        self.config = self._load_config()
        self.active_stage_info = self._load_active_stage()
        
    def _get_repo_root(self) -> str:
        """获取仓库根目录"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(current_dir)  # 上级目录
    
    def _load_config(self) -> Dict[str, Any]:
        """加载阶段配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"❌ 配置文件不存在: {self.config_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"❌ 配置文件格式错误: {e}")
            sys.exit(1)
    
    def _load_active_stage(self) -> Dict[str, Any]:
        """加载当前激活阶段信息"""
        try:
            with open(self.active_stage_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # 创建默认的激活阶段文件
            default_stage = self.config.get('default_stage', 'pretraining')
            return self._create_default_active_stage(default_stage)
        except yaml.YAMLError as e:
            print(f"❌ 激活阶段文件格式错误: {e}")
            sys.exit(1)
    
    def _create_default_active_stage(self, stage: str) -> Dict[str, Any]:
        """创建默认的激活阶段配置"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        default_config = {
            'current_stage': stage,
            'current_variant': None,
            'activated_at': now,
            'activated_by': 'system',
            'switch_reason': 'initialization',
            'config_file': self.config['stages'][stage]['config_file'],
            'runtime_status': {
                'is_active': True,
                'last_check': now,
                'next_check': now,
                'check_interval': 300
            },
            'current_metrics': {
                'epoch': 0,
                'loss': None,
                'accuracy': None,
                'learning_rate': 0.001,
                'gpu_memory_usage': 0.0,
                'data_loading_time': 0.0,
                'last_updated': now
            },
            'history': [],
            'next_stage': {
                'predicted_stage': None,
                'estimated_switch_time': None,
                'confidence': 0.0,
                'conditions': []
            },
            'alerts': {
                'active_alerts': [],
                'alert_history': []
            },
            'system_info': {
                'hostname': os.getenv('COMPUTERNAME', 'unknown'),
                'pid': None,
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'last_updated': now
            },
            'config_version': {
                'stage_config_hash': None,
                'stage_config_last_modified': now,
                'active_config_hash': None,
                'active_config_last_modified': now
            }
        }
        
        self._save_active_stage(default_config)
        return default_config
    
    def _save_active_stage(self, config: Dict[str, Any]):
        """保存激活阶段配置"""
        with open(self.active_stage_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    def _get_stage_config_path(self, stage: str, variant: str = None) -> str:
        """获取阶段配置文件路径"""
        if stage in self.config['stages']:
            stage_config = self.config['stages'][stage]
            if variant and 'variants' in stage_config:
                return os.path.join(self.repo_root, stage_config['variants'][variant]['config_file'])
            else:
                return os.path.join(self.repo_root, stage_config['config_file'])
        else:
            raise ValueError(f"未知的阶段: {stage}")
    
    def get_current_stage(self) -> Tuple[str, Optional[str]]:
        """获取当前阶段"""
        return self.active_stage_info['current_stage'], self.active_stage_info.get('current_variant')
    
    def list_available_stages(self) -> List[Dict[str, Any]]:
        """列出所有可用阶段"""
        stages = []
        for stage_name, stage_config in self.config['stages'].items():
            stage_info = {
                'name': stage_name,
                'display_name': stage_config.get('name', stage_name),
                'description': stage_config.get('description', ''),
                'priority': stage_config.get('priority', 999),
                'trigger_mode': stage_config.get('trigger_mode', 'auto'),
                'config_file': stage_config.get('config_file', ''),
                'has_variants': 'variants' in stage_config
            }
            
            if stage_info['has_variants']:
                stage_info['variants'] = list(stage_config['variants'].keys())
            
            stages.append(stage_info)
        
        return sorted(stages, key=lambda x: x['priority'])
    
    def validate_stage_config(self, stage: str, variant: str = None) -> List[str]:
        """验证阶段配置文件"""
        errors = []
        
        try:
            config_path = self._get_stage_config_path(stage, variant)
            
            if not os.path.exists(config_path):
                errors.append(f"配置文件不存在: {config_path}")
                return errors
            
            with open(config_path, 'r', encoding='utf-8') as f:
                stage_config = json.load(f)
            
            # 基本字段验证
            required_fields = ['meta', 'dataset_index']
            for field in required_fields:
                if field not in stage_config:
                    errors.append(f"缺少必需字段: {field}")
            
            # meta字段验证
            if 'meta' in stage_config:
                meta = stage_config['meta']
                required_meta_fields = ['stage', 'consumer_version', 'bundle_versions', 'description', 'version']
                for field in required_meta_fields:
                    if field not in meta:
                        errors.append(f"meta缺少必需字段: {field}")
                
                # 验证阶段名称一致性
                if meta.get('stage') != stage:
                    errors.append(f"配置文件中的阶段名称({meta.get('stage')})与请求的阶段({stage})不一致")
            
            # 数据集索引验证
            if 'dataset_index' in stage_config:
                dataset_index = stage_config['dataset_index']
                if not isinstance(dataset_index, list):
                    errors.append("dataset_index必须是列表类型")
                else:
                    dataset_names = []
                    for i, dataset in enumerate(dataset_index):
                        if not isinstance(dataset, dict):
                            errors.append(f"数据集索引{i}必须是对象类型")
                            continue
                        
                        required_dataset_fields = ['name', 'obs_path', 'bundle_versions', 'duplicate']
                        for field in required_dataset_fields:
                            if field not in dataset:
                                errors.append(f"数据集索引{i}缺少必需字段: {field}")
                        
                        # 检查数据集名称唯一性
                        name = dataset.get('name')
                        if name in dataset_names:
                            errors.append(f"数据集名称重复: {name}")
                        dataset_names.append(name)
        
        except json.JSONDecodeError as e:
            errors.append(f"JSON格式错误: {e}")
        except Exception as e:
            errors.append(f"配置验证错误: {e}")
        
        return errors
    
    def switch_stage(self, target_stage: str, variant: str = None, reason: str = "manual_switch") -> bool:
        """切换到指定阶段"""
        print(f"🔄 切换阶段: {self.active_stage_info['current_stage']} → {target_stage}")
        
        # 验证目标阶段
        if target_stage not in self.config['stages']:
            print(f"❌ 未知的阶段: {target_stage}")
            return False
        
        # 验证变体
        if variant:
            stage_config = self.config['stages'][target_stage]
            if 'variants' not in stage_config or variant not in stage_config['variants']:
                print(f"❌ 阶段 {target_stage} 不支持变体 {variant}")
                return False
        
        # 验证配置文件
        errors = self.validate_stage_config(target_stage, variant)
        if errors:
            print("❌ 配置文件验证失败:")
            for error in errors:
                print(f"   • {error}")
            return False
        
        # 记录历史
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_stage = self.active_stage_info['current_stage']
        
        # 更新历史记录
        if self.active_stage_info['history']:
            last_record = self.active_stage_info['history'][-1]
            if last_record.get('deactivated_at') is None:
                last_record['deactivated_at'] = now
                activated_time = datetime.strptime(last_record['activated_at'], "%Y-%m-%d %H:%M:%S")
                deactivated_time = datetime.strptime(now, "%Y-%m-%d %H:%M:%S")
                last_record['duration'] = str(deactivated_time - activated_time)
        
        # 添加新记录
        new_record = {
            'stage': target_stage,
            'variant': variant,
            'activated_at': now,
            'deactivated_at': None,
            'duration': None,
            'reason': reason,
            'triggered_by': 'user'
        }
        self.active_stage_info['history'].append(new_record)
        
        # 更新当前阶段信息
        self.active_stage_info['current_stage'] = target_stage
        self.active_stage_info['current_variant'] = variant
        self.active_stage_info['activated_at'] = now
        self.active_stage_info['activated_by'] = 'user'
        self.active_stage_info['switch_reason'] = reason
        self.active_stage_info['config_file'] = self._get_stage_config_path(target_stage, variant)
        
        # 重置运行时状态
        self.active_stage_info['runtime_status']['last_check'] = now
        self.active_stage_info['runtime_status']['next_check'] = now
        
        # 重置指标
        self.active_stage_info['current_metrics'] = {
            'epoch': 0,
            'loss': None,
            'accuracy': None,
            'learning_rate': 0.001,
            'gpu_memory_usage': 0.0,
            'data_loading_time': 0.0,
            'last_updated': now
        }
        
        # 预测下一阶段
        self._predict_next_stage()
        
        # 添加切换日志
        alert = {
            'timestamp': now,
            'level': 'INFO',
            'message': f'阶段切换: {current_stage} → {target_stage}' + (f' ({variant})' if variant else ''),
            'resolved': True,
            'resolved_at': now
        }
        self.active_stage_info['alerts']['alert_history'].append(alert)
        
        # 保存配置
        self._save_active_stage(self.active_stage_info)
        
        print(f"✅ 成功切换到阶段: {target_stage}" + (f" ({variant})" if variant else ""))
        return True
    
    def _predict_next_stage(self):
        """预测下一个阶段"""
        current_stage = self.active_stage_info['current_stage']
        stages = self.config['stages']
        
        # 找到当前阶段的优先级
        current_priority = stages[current_stage].get('priority', 999)
        
        # 找到下一个优先级的阶段
        next_stage = None
        next_priority = float('inf')
        
        for stage_name, stage_config in stages.items():
            priority = stage_config.get('priority', 999)
            if priority > current_priority and priority < next_priority:
                next_stage = stage_name
                next_priority = priority
        
        if next_stage:
            # 估算切换时间
            conditions = stages[next_stage].get('auto_switch_conditions', [])
            estimated_time = None
            
            if conditions:
                # 简单估算：假设每个epoch需要1小时
                for condition in conditions:
                    if 'epoch' in condition:
                        target_epoch = condition['epoch']
                        current_epoch = self.active_stage_info['current_metrics']['epoch']
                        remaining_epochs = max(0, target_epoch - current_epoch)
                        estimated_time = (datetime.now() + timedelta(hours=remaining_epochs)).strftime("%Y-%m-%d %H:%M:%S")
                        break
            
            self.active_stage_info['next_stage'] = {
                'predicted_stage': next_stage,
                'estimated_switch_time': estimated_time,
                'confidence': 0.8,
                'conditions': [cond.get('description', str(cond)) for cond in conditions]
            }
    
    def get_stage_status(self) -> Dict[str, Any]:
        """获取阶段状态信息"""
        current_stage, current_variant = self.get_current_stage()
        
        status = {
            'current_stage': current_stage,
            'current_variant': current_variant,
            'activated_at': self.active_stage_info['activated_at'],
            'switch_reason': self.active_stage_info['switch_reason'],
            'config_file': self.active_stage_info['config_file'],
            'runtime_status': self.active_stage_info['runtime_status'],
            'current_metrics': self.active_stage_info['current_metrics'],
            'next_stage': self.active_stage_info['next_stage'],
            'active_alerts_count': len(self.active_stage_info['alerts']['active_alerts']),
            'total_stage_switches': len(self.active_stage_info['history'])
        }
        
        return status
    
    def preview_stage_config(self, stage: str, variant: str = None) -> Dict[str, Any]:
        """预览阶段配置"""
        try:
            config_path = self._get_stage_config_path(stage, variant)
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 提取关键信息
            preview = {
                'stage': stage,
                'variant': variant,
                'config_file': config_path,
                'meta': config.get('meta', {}),
                'dataset_count': len(config.get('dataset_index', [])),
                'total_clips': sum(ds.get('duplicate', 1) for ds in config.get('dataset_index', [])),
                'stage_config': config.get('meta', {}).get('stage_config', {}),
                'datasets': []
            }
            
            # 数据集摘要
            for dataset in config.get('dataset_index', []):
                ds_info = {
                    'name': dataset.get('name'),
                    'clips': dataset.get('duplicate', 1),
                    'weight': dataset.get('stage_weight', 0),
                    'priority': dataset.get('sampling_priority', 'medium'),
                    'enabled': dataset.get('enabled', True)
                }
                preview['datasets'].append(ds_info)
            
            return preview
            
        except Exception as e:
            return {'error': str(e)}
    
    def generate_stage_report(self, output_file: str = None) -> str:
        """生成阶段报告"""
        report_lines = []
        
        report_lines.append("# 训练阶段管理报告")
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # 当前状态
        current_stage, current_variant = self.get_current_stage()
        report_lines.append("## 当前状态")
        report_lines.append(f"- **当前阶段**: {current_stage}" + (f" ({current_variant})" if current_variant else ""))
        report_lines.append(f"- **激活时间**: {self.active_stage_info['activated_at']}")
        report_lines.append(f"- **切换原因**: {self.active_stage_info['switch_reason']}")
        report_lines.append(f"- **配置文件**: {self.active_stage_info['config_file']}")
        report_lines.append("")
        
        # 可用阶段
        report_lines.append("## 可用阶段")
        stages = self.list_available_stages()
        for stage in stages:
            status = "🟢 当前" if stage['name'] == current_stage else "⚪ 可用"
            report_lines.append(f"- {status} **{stage['display_name']}** ({stage['name']})")
            report_lines.append(f"  - 描述: {stage['description']}")
            report_lines.append(f"  - 优先级: {stage['priority']}")
            report_lines.append(f"  - 触发模式: {stage['trigger_mode']}")
            if stage['has_variants']:
                report_lines.append(f"  - 变体: {', '.join(stage['variants'])}")
            report_lines.append("")
        
        # 历史记录
        report_lines.append("## 切换历史")
        if self.active_stage_info['history']:
            for record in self.active_stage_info['history'][-10:]:  # 最近10次
                duration = record.get('duration', '进行中')
                variant_info = f" ({record['variant']})" if record.get('variant') else ""
                report_lines.append(f"- **{record['stage']}{variant_info}**")
                report_lines.append(f"  - 激活时间: {record['activated_at']}")
                report_lines.append(f"  - 持续时间: {duration}")
                report_lines.append(f"  - 切换原因: {record['reason']}")
                report_lines.append("")
        else:
            report_lines.append("暂无切换历史")
            report_lines.append("")
        
        # 下一阶段预测
        next_stage_info = self.active_stage_info.get('next_stage', {})
        if next_stage_info.get('predicted_stage'):
            report_lines.append("## 下一阶段预测")
            report_lines.append(f"- **预测阶段**: {next_stage_info['predicted_stage']}")
            report_lines.append(f"- **预计时间**: {next_stage_info.get('estimated_switch_time', '未知')}")
            report_lines.append(f"- **置信度**: {next_stage_info.get('confidence', 0):.1%}")
            if next_stage_info.get('conditions'):
                report_lines.append("- **切换条件**:")
                for condition in next_stage_info['conditions']:
                    report_lines.append(f"  - {condition}")
            report_lines.append("")
        
        # 系统信息
        system_info = self.active_stage_info.get('system_info', {})
        report_lines.append("## 系统信息")
        report_lines.append(f"- **主机名**: {system_info.get('hostname', '未知')}")
        report_lines.append(f"- **Python版本**: {system_info.get('python_version', '未知')}")
        report_lines.append(f"- **最后更新**: {system_info.get('last_updated', '未知')}")
        
        report_content = '\n'.join(report_lines)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"📄 报告已保存: {output_file}")
        
        return report_content

def main():
    parser = argparse.ArgumentParser(description='训练阶段管理工具')
    parser.add_argument('--config', help='阶段配置文件路径')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 查看状态
    status_parser = subparsers.add_parser('status', help='查看当前阶段状态')
    
    # 列出阶段
    list_parser = subparsers.add_parser('list-stages', help='列出所有可用阶段')
    
    # 切换阶段
    switch_parser = subparsers.add_parser('switch-stage', help='切换到指定阶段')
    switch_parser.add_argument('stage', help='目标阶段名称')
    switch_parser.add_argument('--variant', help='阶段变体 (用于A/B测试)')
    switch_parser.add_argument('--reason', default='manual_switch', help='切换原因')
    
    # 预览配置
    preview_parser = subparsers.add_parser('preview', help='预览阶段配置')
    preview_parser.add_argument('stage', help='阶段名称')
    preview_parser.add_argument('--variant', help='阶段变体')
    
    # 验证配置
    validate_parser = subparsers.add_parser('validate-config', help='验证阶段配置')
    validate_parser.add_argument('stage', help='阶段名称')
    validate_parser.add_argument('--variant', help='阶段变体')
    
    # 生成报告
    report_parser = subparsers.add_parser('report', help='生成阶段报告')
    report_parser.add_argument('--output', help='输出文件路径')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        manager = StageManager(args.config)
        
        if args.command == 'status':
            status = manager.get_stage_status()
            print("📊 当前阶段状态")
            print("=" * 40)
            print(f"当前阶段: {status['current_stage']}" + (f" ({status['current_variant']})" if status['current_variant'] else ""))
            print(f"激活时间: {status['activated_at']}")
            print(f"切换原因: {status['switch_reason']}")
            print(f"配置文件: {status['config_file']}")
            print(f"历史切换次数: {status['total_stage_switches']}")
            print(f"活跃警告: {status['active_alerts_count']}")
            
            if status['next_stage']['predicted_stage']:
                print(f"\n🔮 下一阶段预测: {status['next_stage']['predicted_stage']}")
                if status['next_stage']['estimated_switch_time']:
                    print(f"预计时间: {status['next_stage']['estimated_switch_time']}")
        
        elif args.command == 'list-stages':
            stages = manager.list_available_stages()
            current_stage, _ = manager.get_current_stage()
            
            print("📋 可用阶段列表")
            print("=" * 40)
            for stage in stages:
                status_icon = "🟢" if stage['name'] == current_stage else "⚪"
                print(f"{status_icon} {stage['display_name']} ({stage['name']})")
                print(f"   描述: {stage['description']}")
                print(f"   优先级: {stage['priority']} | 触发: {stage['trigger_mode']}")
                if stage['has_variants']:
                    print(f"   变体: {', '.join(stage['variants'])}")
                print()
        
        elif args.command == 'switch-stage':
            success = manager.switch_stage(args.stage, args.variant, args.reason)
            if not success:
                sys.exit(1)
        
        elif args.command == 'preview':
            preview = manager.preview_stage_config(args.stage, args.variant)
            if 'error' in preview:
                print(f"❌ 预览失败: {preview['error']}")
                sys.exit(1)
            
            print(f"👀 阶段配置预览: {args.stage}" + (f" ({args.variant})" if args.variant else ""))
            print("=" * 40)
            print(f"配置文件: {preview['config_file']}")
            print(f"数据集数量: {preview['dataset_count']}")
            print(f"总Clips数量: {preview['total_clips']:,}")
            
            if preview.get('stage_config'):
                print("\n📊 阶段配置:")
                stage_config = preview['stage_config']
                if 'data_strategy' in stage_config:
                    data_strategy = stage_config['data_strategy']
                    print(f"   采样方法: {data_strategy.get('sampling_method', 'N/A')}")
                    if 'data_ratio' in data_strategy:
                        print("   数据比例:")
                        for scenario, ratio in data_strategy['data_ratio'].items():
                            print(f"     - {scenario}: {ratio:.1%}")
            
            print("\n📁 数据集列表:")
            for dataset in preview['datasets']:
                status = "✅" if dataset['enabled'] else "❌"
                print(f"   {status} {dataset['name']}")
                print(f"      Clips: {dataset['clips']:,} | 权重: {dataset['weight']} | 优先级: {dataset['priority']}")
        
        elif args.command == 'validate-config':
            errors = manager.validate_stage_config(args.stage, args.variant)
            if errors:
                print(f"❌ 配置验证失败: {args.stage}" + (f" ({args.variant})" if args.variant else ""))
                for error in errors:
                    print(f"   • {error}")
                sys.exit(1)
            else:
                print(f"✅ 配置验证通过: {args.stage}" + (f" ({args.variant})" if args.variant else ""))
        
        elif args.command == 'report':
            report = manager.generate_stage_report(args.output)
            if not args.output:
                print(report)
    
    except KeyboardInterrupt:
        print("\n👋 操作已取消")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
