#!/usr/bin/env python3
"""
阶段化数据加载演示脚本
展示如何在不修改代码的情况下切换不同阶段的数据
"""

import os
import json
import yaml
from pathlib import Path

def get_dataset_config():
    """获取数据集配置，支持阶段化加载"""
    
    print("🔍 正在检测数据集配置...")
    
    # 1. 检查是否强制指定配置文件
    force_config = os.getenv('FORCE_DATASET_CONFIG')
    if force_config and os.path.exists(force_config):
        print(f"✅ 使用强制指定的配置文件: {force_config}")
        with open(force_config, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # 2. 检查当前激活的阶段
    active_stage_file = 'active_stage.yaml'
    if os.path.exists(active_stage_file):
        print(f"📄 读取激活阶段文件: {active_stage_file}")
        with open(active_stage_file, 'r', encoding='utf-8') as f:
            active_stage = yaml.safe_load(f)
        
        current_stage = active_stage.get('current_stage')
        config_file = active_stage.get('config_file')
        
        print(f"📊 当前激活阶段: {current_stage}")
        
        if config_file and os.path.exists(config_file):
            print(f"✅ 使用阶段配置文件: {config_file}")
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    # 3. 检查环境变量指定的阶段
    env_stage = os.getenv('TRAINING_STAGE')
    if env_stage:
        print(f"🌍 环境变量指定阶段: {env_stage}")
        stage_file = f"stages/{env_stage}.json"
        if os.path.exists(stage_file):
            print(f"✅ 使用环境变量阶段配置: {stage_file}")
            with open(stage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"⚠️  环境变量阶段配置文件不存在: {stage_file}")
    
    # 4. 使用默认配置
    default_configs = ['training_dataset.json', '../training_dataset.json']
    for default_config in default_configs:
        if os.path.exists(default_config):
            print(f"✅ 使用默认配置文件: {default_config}")
            with open(default_config, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    print("❌ 未找到任何数据集配置文件")
    return None

def analyze_config(config):
    """分析配置文件内容"""
    if not config:
        return
    
    print("\n📋 配置分析:")
    print("=" * 50)
    
    meta = config.get('meta', {})
    stage = meta.get('stage', 'unknown')
    description = meta.get('description', '无描述')
    
    print(f"阶段名称: {stage}")
    print(f"描述: {description}")
    print(f"版本: {meta.get('version', 'N/A')}")
    print(f"Consumer版本: {meta.get('consumer_version', 'N/A')}")
    
    # 数据集统计
    dataset_index = config.get('dataset_index', [])
    total_datasets = len(dataset_index)
    total_clips = sum(ds.get('duplicate', 1) for ds in dataset_index)
    
    print(f"\n📊 数据统计:")
    print(f"数据集数量: {total_datasets}")
    print(f"总Clips数量: {total_clips:,}")
    
    # 阶段特定配置
    stage_config = meta.get('stage_config', {})
    if stage_config:
        print(f"\n⚙️  阶段配置:")
        
        data_strategy = stage_config.get('data_strategy', {})
        if data_strategy:
            print(f"采样方法: {data_strategy.get('sampling_method', 'N/A')}")
            
            data_ratio = data_strategy.get('data_ratio', {})
            if data_ratio:
                print("数据比例:")
                for scenario, ratio in data_ratio.items():
                    print(f"  - {scenario}: {ratio:.1%}")
        
        loading_config = stage_config.get('loading_config', {})
        if loading_config:
            print(f"批次大小: {loading_config.get('batch_size', 'N/A')}")
            print(f"工作线程: {loading_config.get('num_workers', 'N/A')}")
    
    # 数据集详情
    print(f"\n📁 数据集列表:")
    for i, dataset in enumerate(dataset_index, 1):
        name = dataset.get('name', f'dataset_{i}')
        clips = dataset.get('duplicate', 1)
        weight = dataset.get('stage_weight', 0)
        enabled = dataset.get('enabled', True)
        status = "✅" if enabled else "❌"
        
        print(f"  {status} {name}")
        print(f"     Clips: {clips:,} | 权重: {weight} | 启用: {enabled}")

def demo_stage_switching():
    """演示阶段切换"""
    print("\n🎯 阶段切换演示")
    print("=" * 50)
    
    stages = ['pretraining', 'finetuning', 'evaluation']
    
    for stage in stages:
        print(f"\n🔄 切换到阶段: {stage}")
        print("-" * 30)
        
        # 设置环境变量
        os.environ['TRAINING_STAGE'] = stage
        
        # 获取配置
        config = get_dataset_config()
        if config:
            meta = config.get('meta', {})
            dataset_count = len(config.get('dataset_index', []))
            total_clips = sum(ds.get('duplicate', 1) for ds in config.get('dataset_index', []))
            
            print(f"✅ 成功加载 {stage} 阶段配置")
            print(f"   数据集: {dataset_count}个")
            print(f"   Clips: {total_clips:,}个")
            
            # 显示阶段特定配置
            stage_config = meta.get('stage_config', {})
            if stage_config:
                loading_config = stage_config.get('loading_config', {})
                batch_size = loading_config.get('batch_size', 'N/A')
                print(f"   批次大小: {batch_size}")
        else:
            print(f"❌ 无法加载 {stage} 阶段配置")

def main():
    """主函数"""
    print("🚀 阶段化数据加载演示")
    print("=" * 60)
    
    # 显示当前环境
    print("🌍 当前环境变量:")
    env_vars = ['TRAINING_STAGE', 'AB_VARIANT', 'FORCE_DATASET_CONFIG']
    for var in env_vars:
        value = os.getenv(var, '未设置')
        print(f"   {var}: {value}")
    
    print(f"\n📂 当前工作目录: {os.getcwd()}")
    print(f"📁 可用文件:")
    
    # 检查文件存在性
    files_to_check = [
        'stage_config.yaml',
        'active_stage.yaml',
        'stages/pretraining.json',
        'stages/finetuning.json',
        'stages/evaluation.json'
    ]
    
    for file_path in files_to_check:
        exists = "✅" if os.path.exists(file_path) else "❌"
        print(f"   {exists} {file_path}")
    
    # 获取并分析当前配置
    print(f"\n📖 当前配置分析:")
    config = get_dataset_config()
    analyze_config(config)
    
    # 演示阶段切换
    if any(os.path.exists(f"stages/{stage}.json") for stage in ['pretraining', 'finetuning', 'evaluation']):
        demo_stage_switching()
    
    print(f"\n💡 使用提示:")
    print("1. 设置环境变量切换阶段:")
    print("   export TRAINING_STAGE=finetuning")
    print("   python demo_stage_usage.py")
    print()
    print("2. 使用阶段管理工具:")
    print("   python scripts/stage_manager.py switch-stage finetuning")
    print("   python scripts/stage_manager.py status")
    print()
    print("3. 强制使用特定配置:")
    print("   export FORCE_DATASET_CONFIG=stages/evaluation.json")
    print("   python demo_stage_usage.py")

if __name__ == "__main__":
    main()

