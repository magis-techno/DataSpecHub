#!/usr/bin/env python3
"""
Consumer配置生成器
根据consumer配置文件生成三种应用场景的配置：
1. 数据发布工具配置 - 从consumer + spec自动生成
2. 数据校验配置 - 从spec文件自动获取validation规则
3. 数据读取配置 - 从consumer策略 + spec格式信息生成
"""

import yaml
import json
from pathlib import Path
from datetime import datetime

class ConsumerConfigGenerator:
    def __init__(self, workspace_root="."):
        self.workspace_root = Path(workspace_root)
        self.consumers_dir = self.workspace_root / "consumers"
        self.channels_dir = self.workspace_root / "channels"
        self.output_dir = self.workspace_root / "generated_configs"
        self.output_dir.mkdir(exist_ok=True)
    
    def load_consumer(self, consumer_name):
        """加载consumer配置"""
        consumer_file = self.consumers_dir / f"{consumer_name}.yaml"
        with open(consumer_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def load_channel_spec(self, channel_name, version):
        """加载通道spec文件，自动获取validation规则"""
        # 简化版本号处理，实际中可能需要更复杂的版本解析
        spec_version = version.replace(">=", "").replace("^", "").replace("~", "")
        spec_file = self.channels_dir / channel_name / f"spec-{spec_version}.yaml"
        
        if spec_file.exists():
            with open(spec_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            print(f"⚠️  未找到spec文件: {spec_file}")
            return None
    
    def generate_publisher_config(self, consumer_name, environment="production"):
        """生成数据发布工具配置"""
        consumer = self.load_consumer(consumer_name)
        env_config = consumer.get('environments', {}).get(environment, {})
        quality_policy = consumer.get('quality_policy', {})
        
        config = {
            "publisher": {
                "name": f"{consumer_name}_publisher",
                "version": consumer['meta']['version'],
                "environment": environment,
                "generated_at": datetime.now().isoformat()
            },
            "channels": [],
            "quality_policy": {
                "validation_mode": env_config.get('validation_mode', quality_policy.get('validation_mode', 'strict')),
                "missing_data_tolerance": env_config.get('missing_data_tolerance', quality_policy.get('missing_data_tolerance', 0.01)),
                "temporal_sync_tolerance": quality_policy.get('temporal_sync_tolerance', '50ms')
            }
        }
        
        # 处理每个通道的配置
        for req in consumer['requirements']:
            channel_spec = self.load_channel_spec(req['channel'], req['version'])
            
            channel_config = {
                "channel": req['channel'],
                "version": req['version'],
                "required": req['required'],
                "priority": req['priority']
            }
            
            # 从spec文件自动获取validation规则
            if channel_spec and 'validation' in channel_spec:
                channel_config['validation'] = channel_spec['validation']
            
            config['channels'].append(channel_config)
        
        # 保存配置
        output_file = self.output_dir / f"{consumer_name}_publisher_{environment}.yaml"
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        print(f"✅ 生成发布工具配置: {output_file}")
        return output_file
    
    def generate_validation_config(self, consumer_name, environment="production"):
        """生成数据校验配置 - 主要从spec文件获取规则"""
        consumer = self.load_consumer(consumer_name)
        env_config = consumer.get('environments', {}).get(environment, {})
        quality_policy = consumer.get('quality_policy', {})
        
        config = {
            "validator": {
                "name": f"{consumer_name}_validator",
                "version": consumer['meta']['version'],
                "environment": environment,
                "generated_at": datetime.now().isoformat()
            },
            "global_policy": {
                "validation_mode": env_config.get('validation_mode', quality_policy.get('validation_mode', 'strict')),
                "missing_data_tolerance": env_config.get('missing_data_tolerance', quality_policy.get('missing_data_tolerance', 0.01)),
                "temporal_sync_tolerance": quality_policy.get('temporal_sync_tolerance', '50ms')
            },
            "channels": {}
        }
        
        # 处理每个通道 - 从spec文件自动获取validation规则
        for req in consumer['requirements']:
            channel_spec = self.load_channel_spec(req['channel'], req['version'])
            
            channel_validation = {
                "version": req['version'],
                "required": req['required'],
                "priority": req['priority']
            }
            
            # 从spec文件获取完整的validation规则
            if channel_spec:
                if 'validation' in channel_spec:
                    channel_validation['spec_validation'] = channel_spec['validation']
                if 'schema' in channel_spec:
                    channel_validation['schema_validation'] = {
                        "data_format": channel_spec['schema'].get('data_format', {}),
                        "metadata": channel_spec['schema'].get('metadata', {})
                    }
            
            config['channels'][req['channel']] = channel_validation
        
        # 保存配置
        output_file = self.output_dir / f"{consumer_name}_validation_{environment}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 生成校验配置: {output_file}")
        return output_file
    
    def generate_dataloader_config(self, consumer_name, environment="production"):
        """生成数据读取配置"""
        consumer = self.load_consumer(consumer_name)
        env_config = consumer.get('environments', {}).get(environment, {})
        loading_policy = consumer.get('loading_policy', {})
        
        config = {
            "dataloader": {
                "name": f"{consumer_name}_dataloader",
                "version": consumer['meta']['version'],
                "environment": environment,
                "generated_at": datetime.now().isoformat()
            },
            "loading_policy": {
                "batch_processing": loading_policy.get('batch_processing', True),
                "primary_sync_channel": loading_policy.get('primary_sync_channel', 'image_original'),
                "cache_strategy": env_config.get('cache_strategy', loading_policy.get('cache_strategy', 'adaptive')),
                "preprocessing_enabled": loading_policy.get('preprocessing_enabled', True)
            },
            "channels": {}
        }
        
        # 处理每个通道的加载配置
        for req in consumer['requirements']:
            channel_spec = self.load_channel_spec(req['channel'], req['version'])
            
            # 基于spec的data_format自动推断loader_type
            loader_type = "generic"
            if channel_spec and 'schema' in channel_spec:
                data_format = channel_spec['schema'].get('data_format', {})
                format_type = data_format.get('type', '')
                
                if format_type == 'image':
                    loader_type = "image"
                elif format_type == 'occupancy_grid':
                    loader_type = "grid"
                elif 'json' in data_format.get('encoding', []):
                    loader_type = "json"
            
            channel_config = {
                "version": req['version'],
                "priority": req['priority'],
                "loader_type": loader_type,
                "spec_reference": f"channels/{req['channel']}/spec-{req['version'].replace('>=', '').replace('^', '').replace('~', '')}.yaml"
            }
            
            # 添加spec中的格式信息用于加载
            if channel_spec and 'schema' in channel_spec:
                channel_config['format_info'] = channel_spec['schema'].get('data_format', {})
            
            config['channels'][req['channel']] = channel_config
        
        # 保存配置
        output_file = self.output_dir / f"{consumer_name}_dataloader_{environment}.yaml"
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        print(f"✅ 生成数据加载配置: {output_file}")
        return output_file
    
    def generate_all_configs(self, consumer_name, environments=None):
        """生成所有配置文件"""
        if environments is None:
            environments = ["development", "testing", "production"]
        
        print(f"🚀 为消费者 '{consumer_name}' 生成配置文件...")
        print("📋 策略：从spec文件自动获取validation规则，避免重复配置")
        
        generated_files = []
        for env in environments:
            print(f"\n📋 环境: {env}")
            
            # 生成三种配置
            publisher_file = self.generate_publisher_config(consumer_name, env)
            validation_file = self.generate_validation_config(consumer_name, env)
            dataloader_file = self.generate_dataloader_config(consumer_name, env)
            
            generated_files.extend([publisher_file, validation_file, dataloader_file])
        
        print(f"\n✨ 总计生成 {len(generated_files)} 个配置文件")
        print("🎯 优势：validation规则自动从spec继承，无需重复维护")
        return generated_files
    
    def show_usage_examples(self, consumer_name):
        """显示使用示例"""
        print(f"\n📖 配置文件使用示例 - {consumer_name}:")
        print("\n1️⃣  数据发布工具:")
        print(f"   python data_publisher.py --config generated_configs/{consumer_name}_publisher_production.yaml")
        
        print("\n2️⃣  数据校验 (自动从spec获取规则):")
        print(f"   python data_validator.py --config generated_configs/{consumer_name}_validation_production.json")
        
        print("\n3️⃣  数据读取 (自动推断loader类型):")
        print(f"   python dataloader.py --config generated_configs/{consumer_name}_dataloader_production.yaml")

def main():
    """主函数"""
    print("🔧 Consumer配置生成器 (简化版本)\n")
    
    generator = ConsumerConfigGenerator()
    
    # 生成端到端网络的所有配置
    generated_files = generator.generate_all_configs("end_to_end_network")
    
    # 显示使用示例
    generator.show_usage_examples("end_to_end_network")

if __name__ == "__main__":
    main() 