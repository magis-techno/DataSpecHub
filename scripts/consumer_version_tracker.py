#!/usr/bin/env python3
"""
消费者版本跟踪器
展示端到端网络消费者的版本演进过程和依赖关系
"""

import yaml
import os
from datetime import datetime
from pathlib import Path

class ConsumerVersionTracker:
    def __init__(self, workspace_root="."):
        self.workspace_root = Path(workspace_root)
        self.consumers_dir = self.workspace_root / "consumers"
        self.compatibility_file = self.workspace_root / "compatibility" / "consumer_matrix.yaml"
        
    def load_consumer_info(self, consumer_name):
        """加载消费者信息"""
        consumer_file = self.consumers_dir / f"{consumer_name}.yaml"
        if consumer_file.exists():
            with open(consumer_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return None
    
    def load_compatibility_matrix(self):
        """加载兼容性矩阵"""
        if self.compatibility_file.exists():
            with open(self.compatibility_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return None
    
    def track_version_evolution(self, consumer_name="end_to_end_network"):
        """跟踪消费者版本演进"""
        print(f"=== {consumer_name} 版本演进追踪 ===\n")
        
        # 加载消费者信息
        consumer_info = self.load_consumer_info(consumer_name)
        if not consumer_info:
            print(f"未找到消费者 {consumer_name}")
            return
        
        # 显示基本信息
        print(f"消费者: {consumer_info['consumer']['name']}")
        print(f"描述: {consumer_info['consumer']['description']}")
        print(f"负责团队: {consumer_info['consumer']['owner']}")
        print("\n" + "="*60 + "\n")
        
        # 遍历版本历史
        versions = consumer_info.get('versions', {})
        for version, info in versions.items():
            print(f"📦 版本 {version} ({info['release_date']})")
            print(f"   {info['description']}")
            print(f"   📋 依赖通道:")
            
            for channel, channel_version in info['dependencies'].items():
                print(f"      • {channel}: {channel_version}")
            
            # 显示性能指标
            if 'performance' in info:
                perf = info['performance']
                print(f"   ⚡ 性能指标:")
                print(f"      • 准确率: {perf.get('accuracy', 'N/A')}")
                print(f"      • 延迟: {perf.get('latency', 'N/A')}")
                print(f"      • FPS: {perf.get('fps', 'N/A')}")
                print(f"      • 内存使用: {perf.get('memory_usage', 'N/A')}")
            
            # 显示改进或限制
            if 'improvements' in info:
                print(f"   ✨ 改进:")
                for improvement in info['improvements']:
                    print(f"      • {improvement}")
            
            if 'limitations' in info:
                print(f"   ⚠️  限制:")
                for limitation in info['limitations']:
                    print(f"      • {limitation}")
            
            # 显示bug修复
            if 'bug_fixes' in info:
                print(f"   🐛 Bug修复:")
                for fix in info['bug_fixes']:
                    print(f"      • 问题: {fix['issue']}")
                    print(f"      • 解决: {fix['solution']}")
                    print(f"      • 影响: {fix['impact']}")
            
            print("\n" + "-"*50 + "\n")
    
    def check_deployment_status(self, consumer_name="end_to_end_network"):
        """检查部署状态"""
        print(f"=== {consumer_name} 部署状态 ===\n")
        
        consumer_info = self.load_consumer_info(consumer_name)
        if not consumer_info:
            return
        
        production_status = consumer_info.get('production_status', {})
        deployment_envs = production_status.get('deployment_environments', {})
        
        print("🚀 当前部署状态:")
        for env, version in deployment_envs.items():
            status_icon = "🟢" if env in ["development", "testing"] else "🟡" if env == "staging" else "🔴"
            print(f"   {status_icon} {env.capitalize()}: v{version}")
        
        # 显示升级计划
        if 'rollout_schedule' in production_status:
            schedule = production_status['rollout_schedule']
            print(f"\n📅 升级计划:")
            for env, date in schedule.items():
                print(f"   • {env.replace('_', ' ').title()}: {date}")
        
        print("\n" + "="*40 + "\n")
    
    def analyze_channel_dependencies(self, consumer_name="end_to_end_network"):
        """分析通道依赖关系"""
        print(f"=== {consumer_name} 通道依赖分析 ===\n")
        
        consumer_info = self.load_consumer_info(consumer_name)
        if not consumer_info:
            return
        
        # 收集所有版本的依赖
        all_channels = set()
        version_deps = {}
        
        for version, info in consumer_info.get('versions', {}).items():
            deps = info.get('dependencies', {})
            version_deps[version] = deps
            all_channels.update(deps.keys())
        
        print("📊 通道使用演进:")
        for channel in sorted(all_channels):
            print(f"\n🔗 {channel}:")
            for version, deps in version_deps.items():
                if channel in deps:
                    channel_ver = deps[channel]
                    print(f"   v{version}: {channel_ver}")
                else:
                    print(f"   v{version}: ❌ 未使用")
        
        print("\n" + "="*40 + "\n")
    
    def generate_compatibility_report(self):
        """生成兼容性报告"""
        print("=== 兼容性分析报告 ===\n")
        
        matrix = self.load_compatibility_matrix()
        if not matrix:
            print("未找到兼容性矩阵文件")
            return
        
        # 分析端到端网络的锁定历史
        e2e_locks = matrix.get('production_locks', {}).get('end_to_end_network', {})
        
        if 'version_history' in e2e_locks:
            print("📈 版本锁定历史:")
            for version, lock_info in e2e_locks['version_history'].items():
                period = lock_info.get('locked_period', 'Unknown')
                print(f"\n   🔒 v{version} ({period}):")
                for channel, channel_ver in lock_info.items():
                    if channel != 'locked_period':
                        print(f"      • {channel}: {channel_ver}")
        
        # 显示当前生产锁定
        if 'current_production' in e2e_locks:
            current = e2e_locks['current_production']
            print(f"\n🎯 当前生产锁定 (至 {current.get('locked_until', 'TBD')}):")
            for channel, version in current.items():
                if channel not in ['locked_until', 'environment_rollout']:
                    print(f"   • {channel}: {version}")
            
            if 'environment_rollout' in current:
                print(f"\n🌍 环境部署:")
                for env, version in current['environment_rollout'].items():
                    print(f"   • {env}: v{version}")

def main():
    """主函数"""
    print("🤖 DataSpecHub 消费者版本跟踪器\n")
    
    tracker = ConsumerVersionTracker()
    
    # 跟踪端到端网络版本演进
    tracker.track_version_evolution("end_to_end_network")
    
    # 检查部署状态  
    tracker.check_deployment_status("end_to_end_network")
    
    # 分析通道依赖
    tracker.analyze_channel_dependencies("end_to_end_network")
    
    # 生成兼容性报告
    tracker.generate_compatibility_report()

if __name__ == "__main__":
    main() 