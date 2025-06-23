#!/usr/bin/env python3
"""
生产周期感知管理器 - 处理数据生产周期跨度大的问题
自动协调版本更新，避免频繁切换导致的混乱
"""

import yaml
import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class ProductionStatus(Enum):
    """生产状态"""
    PLANNING = "planning"      # 规划中
    PRODUCING = "producing"    # 生产中 
    READY = "ready"           # 就绪
    DEPRECATED = "deprecated"  # 已废弃

@dataclass
class ProductionCycle:
    """生产周期信息"""
    consumer_name: str
    consumer_version: str
    start_date: datetime.date
    expected_duration_days: int
    status: ProductionStatus
    current_bundle: Optional[str] = None
    next_bundle: Optional[str] = None
    
    @property
    def expected_end_date(self) -> datetime.date:
        return self.start_date + datetime.timedelta(days=self.expected_duration_days)
    
    @property
    def is_in_production(self) -> bool:
        today = datetime.date.today()
        return self.start_date <= today <= self.expected_end_date

class ProductionCycleManager:
    """生产周期管理器"""
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root)
        self.cycles_file = self.workspace_root / "production_cycles.yaml"
        
    def register_production_cycle(self, consumer_name: str, consumer_version: str,
                                start_date: str, duration_days: int) -> ProductionCycle:
        """
        注册新的生产周期
        
        Args:
            consumer_name: 消费者名称
            consumer_version: 消费者版本  
            start_date: 开始日期 (YYYY-MM-DD)
            duration_days: 预期持续天数
        """
        cycle = ProductionCycle(
            consumer_name=consumer_name,
            consumer_version=consumer_version,
            start_date=datetime.datetime.strptime(start_date, "%Y-%m-%d").date(),
            expected_duration_days=duration_days,
            status=ProductionStatus.PLANNING
        )
        
        self._save_cycle(cycle)
        print(f"📅 注册生产周期: {consumer_name}@{consumer_version}")
        print(f"   开始: {start_date}, 持续: {duration_days}天")
        print(f"   预计完成: {cycle.expected_end_date}")
        
        return cycle
        
    def get_active_version(self, consumer_name: str) -> Optional[str]:
        """
        获取当前应该使用的consumer版本
        考虑生产周期，避免在生产期间切换版本
        
        Args:
            consumer_name: 消费者名称
            
        Returns:
            推荐使用的consumer版本
        """
        cycles = self._load_cycles()
        consumer_cycles = [c for c in cycles if c.consumer_name == consumer_name]
        
        if not consumer_cycles:
            return None
            
        # 优先使用正在生产中的版本
        for cycle in consumer_cycles:
            if cycle.is_in_production and cycle.status == ProductionStatus.PRODUCING:
                print(f"🔄 生产中版本: {consumer_name}@{cycle.consumer_version}")
                print(f"   预计完成: {cycle.expected_end_date}")
                return cycle.consumer_version
                
        # 如果没有生产中的，返回最新就绪版本
        ready_cycles = [c for c in consumer_cycles if c.status == ProductionStatus.READY]
        if ready_cycles:
            latest = max(ready_cycles, key=lambda c: c.start_date)
            print(f"✅ 就绪版本: {consumer_name}@{latest.consumer_version}")
            return latest.consumer_version
            
        return None
        
    def schedule_version_transition(self, consumer_name: str, 
                                  from_version: str, to_version: str,
                                  transition_date: str) -> Dict:
        """
        安排版本切换计划
        
        Args:
            consumer_name: 消费者名称
            from_version: 当前版本
            to_version: 目标版本
            transition_date: 切换日期
        """
        transition = {
            'consumer_name': consumer_name,
            'from_version': from_version,
            'to_version': to_version,
            'transition_date': transition_date,
            'status': 'scheduled',
            'created_at': datetime.datetime.now().isoformat()
        }
        
        transitions = self._load_transitions()
        transitions.append(transition)
        self._save_transitions(transitions)
        
        print(f"📋 版本切换计划:")
        print(f"   {from_version} -> {to_version}")
        print(f"   计划日期: {transition_date}")
        
        return transition
        
    def check_production_readiness(self, consumer_name: str, 
                                 consumer_version: str) -> Dict:
        """
        检查生产就绪状态
        
        Args:
            consumer_name: 消费者名称
            consumer_version: 消费者版本
            
        Returns:
            就绪状态报告
        """
        # 检查是否有对应的bundle
        from .consumer_alias_manager import ConsumerAliasManager
        alias_manager = ConsumerAliasManager(self.workspace_root)
        bundle_path = alias_manager.get_bundle_for_consumer(consumer_name, consumer_version)
        
        readiness = {
            'consumer_name': consumer_name,
            'consumer_version': consumer_version,
            'has_bundle': bundle_path is not None,
            'bundle_path': bundle_path,
            'check_time': datetime.datetime.now().isoformat(),
            'ready_for_production': False
        }
        
        if bundle_path:
            # 进一步检查bundle的完整性
            readiness['ready_for_production'] = self._validate_bundle_integrity(bundle_path)
            
        return readiness
        
    def get_user_friendly_status(self, consumer_name: str) -> str:
        """
        用户友好的状态说明
        
        Args:
            consumer_name: 消费者名称
            
        Returns:
            状态说明字符串
        """
        active_version = self.get_active_version(consumer_name)
        if not active_version:
            return f"❌ {consumer_name}: 无活跃版本"
            
        cycles = self._load_cycles()
        active_cycle = next((c for c in cycles 
                           if c.consumer_name == consumer_name 
                           and c.consumer_version == active_version), None)
        
        if not active_cycle:
            return f"✅ {consumer_name}@{active_version}: 就绪使用"
            
        if active_cycle.is_in_production:
            days_left = (active_cycle.expected_end_date - datetime.date.today()).days
            return f"🔄 {consumer_name}@{active_version}: 生产中 (还剩{days_left}天)"
        else:
            return f"✅ {consumer_name}@{active_version}: 生产完成，可使用"
    
    def _load_cycles(self) -> List[ProductionCycle]:
        """加载生产周期数据"""
        if not self.cycles_file.exists():
            return []
            
        with open(self.cycles_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or []
            
        cycles = []
        for item in data:
            cycles.append(ProductionCycle(
                consumer_name=item['consumer_name'],
                consumer_version=item['consumer_version'],
                start_date=datetime.datetime.strptime(item['start_date'], "%Y-%m-%d").date(),
                expected_duration_days=item['expected_duration_days'],
                status=ProductionStatus(item['status']),
                current_bundle=item.get('current_bundle'),
                next_bundle=item.get('next_bundle')
            ))
            
        return cycles
        
    def _save_cycle(self, cycle: ProductionCycle):
        """保存生产周期"""
        cycles = self._load_cycles()
        
        # 移除同名同版本的旧记录
        cycles = [c for c in cycles 
                 if not (c.consumer_name == cycle.consumer_name 
                        and c.consumer_version == cycle.consumer_version)]
        
        cycles.append(cycle)
        
        data = []
        for c in cycles:
            data.append({
                'consumer_name': c.consumer_name,
                'consumer_version': c.consumer_version,
                'start_date': c.start_date.strftime("%Y-%m-%d"),
                'expected_duration_days': c.expected_duration_days,
                'status': c.status.value,
                'current_bundle': c.current_bundle,
                'next_bundle': c.next_bundle
            })
            
        with open(self.cycles_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False)
            
    def _load_transitions(self) -> List[Dict]:
        """加载版本切换计划"""
        transitions_file = self.workspace_root / "version_transitions.yaml"
        if not transitions_file.exists():
            return []
            
        with open(transitions_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or []
            
    def _save_transitions(self, transitions: List[Dict]):
        """保存版本切换计划"""
        transitions_file = self.workspace_root / "version_transitions.yaml"
        with open(transitions_file, 'w', encoding='utf-8') as f:
            yaml.dump(transitions, f, default_flow_style=False)
            
    def _validate_bundle_integrity(self, bundle_path: str) -> bool:
        """验证bundle完整性"""
        # 简化实现，实际可以调用bundle_validator
        bundle_file = self.workspace_root / bundle_path
        return bundle_file.exists()

def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="生产周期管理")
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # 注册生产周期
    register_parser = subparsers.add_parser('register', help='注册生产周期')
    register_parser.add_argument('--consumer', required=True, help='消费者名称')
    register_parser.add_argument('--version', required=True, help='消费者版本')
    register_parser.add_argument('--start-date', required=True, help='开始日期 (YYYY-MM-DD)')
    register_parser.add_argument('--duration', type=int, required=True, help='持续天数')
    
    # 查询活跃版本
    active_parser = subparsers.add_parser('active', help='查询活跃版本')
    active_parser.add_argument('--consumer', required=True, help='消费者名称')
    
    # 状态查询
    status_parser = subparsers.add_parser('status', help='查询状态')
    status_parser.add_argument('--consumer', required=True, help='消费者名称')
    
    args = parser.parse_args()
    manager = ProductionCycleManager()
    
    if args.command == 'register':
        manager.register_production_cycle(
            args.consumer, args.version, args.start_date, args.duration
        )
    elif args.command == 'active':
        version = manager.get_active_version(args.consumer)
        if version:
            print(f"当前活跃版本: {args.consumer}@{version}")
        else:
            print(f"未找到 {args.consumer} 的活跃版本")
    elif args.command == 'status':
        status = manager.get_user_friendly_status(args.consumer)
        print(status)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 