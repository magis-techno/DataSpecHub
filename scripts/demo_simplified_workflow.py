#!/usr/bin/env python3
"""
DataSpecHub 工作流程演示
展示从Consumer配置到最终数据生产的完整流程
"""

import sys
import json
from pathlib import Path
from datetime import datetime

def step1_consumer_configuration():
    """步骤1: 手动配置Consumer版本"""
    print("=" * 80)
    print("🎯 步骤1: Consumer版本配置")
    print("=" * 80)
    
    # 使用仓库中已有的Consumer配置
    consumer_path = "consumers/end_to_end/v1.2.0.yaml"
    print(f"📋 使用现有Consumer配置: {consumer_path}")
    
    # 读取Consumer配置文件内容（模拟）
    sample_consumer = {
        "meta": {
            "consumer": "end_to_end",
            "version": "1.2.0",
            "description": "端到端网络的数据通道版本需求",
            "team": "端到端团队"
        },
        "requirements": [
            {"channel": "image_original", "version": "1.2.0", "required": True},
            {"channel": "object_array_fusion_infer", "version": ">=1.2.0", "required": True},
            {"channel": "occupancy", "version": "1.0.0", "required": True},
            {"channel": "utils_slam", "version": ">=1.0.0", "required": True}
        ]
    }
    
    print("\n✅ Consumer配置内容:")
    print(f"   Consumer: {sample_consumer['meta']['consumer']} v{sample_consumer['meta']['version']}")
    print(f"   团队: {sample_consumer['meta']['team']}")
    print(f"   依赖通道数: {len(sample_consumer['requirements'])}")
    
    for req in sample_consumer['requirements']:
        print(f"      • {req['channel']}: {req['version']}")
    
    return sample_consumer

def step2_bundle_generation(consumer_config):
    """步骤2: 自动化生产Bundle文件"""
    print("\n" + "=" * 80)
    print("🔨 步骤2: 自动化Bundle生成")
    print("=" * 80)
    
    # 生成Bundle版本号 (Consumer版本-年.周数)
    current_time = datetime.now()
    week_number = current_time.isocalendar()[1]
    bundle_version = f"v{consumer_config['meta']['version']}-2025.{week_number}"
    
    # Bundle文件路径
    bundle_path = f"bundles/weekly/end_to_end-{bundle_version}.yaml"
    
    print(f"🎯 生成Bundle文件:")
    print(f"   Bundle版本: {bundle_version}")
    print(f"   文件路径: {bundle_path}")
    
    # 模拟Bundle内容
    bundle_content = {
        "meta": {
            "bundle_name": "end_to_end",
            "consumer_version": f"v{consumer_config['meta']['version']}",
            "bundle_version": bundle_version,
            "bundle_type": "weekly",
            "created_at": current_time.isoformat() + "Z",
            "description": f"端到端网络数据快照 - 2025年第{week_number}周"
        },
        "channels": []
    }
    
    # 解析Consumer约束，生成具体版本清单
    print("\n🔍 解析版本约束:")
    for req in consumer_config['requirements']:
        channel = req['channel']
        constraint = req['version']
        
        # 模拟版本解析结果
        if constraint.startswith(">="):
            available_versions = ["1.2.0", "1.1.0", "1.0.0"]
            recommended = "1.2.0"
        elif constraint == "1.2.0":
            available_versions = ["1.2.0"]
            recommended = "1.2.0"
        elif constraint == "1.0.0":
            available_versions = ["1.0.0"]
            recommended = "1.0.0"
        else:
            available_versions = ["1.1.0", "1.0.0"]
            recommended = "1.1.0"
        
        channel_spec = {
            "channel": channel,
            "available_versions": available_versions,
            "recommended_version": recommended,
            "source_constraint": constraint
        }
        
        bundle_content["channels"].append(channel_spec)
        print(f"   ✅ {channel}: {constraint}")
        print(f"      推荐版本: {recommended}")
        print(f"      可选版本: {', '.join(available_versions)}")
    
    print(f"\n📁 Bundle文件已生成: {bundle_path}")
    print(f"   包含 {len(bundle_content['channels'])} 个通道规格")
    
    return bundle_content, bundle_path

def step3_training_dataset_generation(bundle_content):
    """步骤3: 生成training_dataset.json"""
    print("\n" + "=" * 80)
    print("📊 步骤3: 生成Training Dataset配置")
    print("=" * 80)
    
    bundle_version = bundle_content['meta']['bundle_version']
    
    # 生成training_dataset.json内容
    training_dataset = {
        "meta": {
            "dataset_name": "end_to_end_training_dataset",
            "bundle_version": bundle_version,  # 自动填写bundle版本
            "created_at": datetime.now().isoformat() + "Z",
            "description": f"基于Bundle {bundle_version} 的训练数据集配置"
        },
        "data_sources": [],
        "output_config": {
            "format": "jsonl",
            "output_path": f"datasets/end_to_end/{bundle_version}/",
            "split_strategy": "temporal",
            "train_ratio": 0.8,
            "val_ratio": 0.15,
            "test_ratio": 0.05
        }
    }
    
    # 为每个通道配置数据源
    print(f"\n🎯 配置数据源 (Bundle版本: {bundle_version}):")
    for channel_spec in bundle_content['channels']:
        channel = channel_spec['channel']
        version = channel_spec['recommended_version']
        
        data_source = {
            "channel": channel,
            "version": version,
            "data_path": f"data/{channel}/v{version}/",
            "file_pattern": "*.parquet",
            "sample_count": 50000 + hash(channel) % 20000  # 模拟样本数
        }
        
        training_dataset["data_sources"].append(data_source)
        print(f"   ✅ {channel}@v{version}: {data_source['sample_count']:,} 样本")
    
    dataset_path = f"datasets/configs/training_dataset_production.json"
    print(f"\n📁 Training Dataset配置已生成: {dataset_path}")
    
    return training_dataset, dataset_path

def step4_mock_data_production(training_dataset):
    """步骤4: Mock数据生产过程"""
    print("\n" + "=" * 80)
    print("🏭 步骤4: Mock数据生产过程")
    print("=" * 80)
    
    bundle_version = training_dataset['meta']['bundle_version']
    output_path = training_dataset['output_config']['output_path']
    
    print(f"🎯 开始数据生产流程:")
    print(f"   Bundle版本: {bundle_version}")
    print(f"   输出路径: {output_path}")
    
    # 模拟数据生产过程
    total_samples = sum(ds['sample_count'] for ds in training_dataset['data_sources'])
    
    print(f"\n📈 数据统计:")
    print(f"   总样本数: {total_samples:,}")
    print(f"   通道数量: {len(training_dataset['data_sources'])}")
    
    # 模拟生成的JSONL文件
    jsonl_files = [
        f"{output_path}train.jsonl",
        f"{output_path}val.jsonl", 
        f"{output_path}test.jsonl"
    ]
    
    print(f"\n🔄 生产JSONL文件:")
    splits = ['train', 'val', 'test']
    ratios = [0.8, 0.15, 0.05]
    
    for split, ratio, jsonl_file in zip(splits, ratios, jsonl_files):
        split_samples = int(total_samples * ratio)
        
        print(f"   ✅ {jsonl_file}")
        print(f"      样本数: {split_samples:,} ({ratio*100:.0f}%)")
        
        # 模拟JSONL文件内容示例
        if split == 'train':
            sample_jsonl = {
                "sample_id": "sample_001",
                "bundle_version": bundle_version,
                "timestamp": "2025-01-15T10:30:00Z",
                "channels": {
                    "image_original": {"path": "data/image_original/v1.2.0/frame_001.jpg", "metadata": {}},
                    "object_array_fusion_infer": {"path": "data/object_array_fusion_infer/v1.2.0/objects_001.json", "count": 5},
                    "occupancy": {"path": "data/occupancy/v1.0.0/grid_001.npy", "resolution": "0.1m"},
                    "utils_slam": {"path": "data/utils_slam/v1.1.0/pose_001.json", "confidence": 0.95}
                }
            }
            
            print(f"      示例JSONL记录:")
            print(f"        sample_id: {sample_jsonl['sample_id']}")
            print(f"        bundle_version: {sample_jsonl['bundle_version']}")
            print(f"        channels: {len(sample_jsonl['channels'])} 个")
    
    print(f"\n🎉 数据生产完成!")
    print(f"   输出目录: {output_path}")
    print(f"   生成文件: {len(jsonl_files)} 个JSONL文件")
    
    return jsonl_files

def workflow_summary():
    """工作流程总结"""
    print("\n" + "=" * 80)
    print("📋 DataSpecHub 工作流程总结")
    print("=" * 80)
    
    workflow_steps = [
        ("步骤1", "Consumer配置", "手动配置Consumer版本和依赖", "consumers/end_to_end/v1.2.0.yaml"),
        ("步骤2", "Bundle生成", "自动解析约束，生成版本清单", "bundles/weekly/end_to_end-v1.2.0-2025.3.yaml"),
        ("步骤3", "Dataset配置", "创建训练数据集配置文件", "datasets/configs/training_dataset_v1_2_0-2025_3.json"),
        ("步骤4", "数据生产", "批量生产JSONL格式训练数据", "datasets/end_to_end/v1.2.0-2025.3/")
    ]
    
    print(f"{'步骤':<8} {'功能':<12} {'说明':<24} {'输出文件/路径':<40}")
    print("-" * 90)
    
    for step, function, description, output in workflow_steps:
        print(f"{step:<8} {function:<12} {description:<24} {output:<40}")
    
    print(f"\n🎯 核心优势:")
    print(f"   ✅ 人工配置Consumer，减少自动推导复杂度")
    print(f"   ✅ 自动化Bundle生成，确保版本一致性")
    print(f"   ✅ 统一的Bundle版本管理，便于追溯")
    print(f"   ✅ 标准化的JSONL输出，支持多种训练框架")
    
    print(f"\n💡 使用方式:")
    print(f"   1. 修改Consumer配置文件（手动）")
    print(f"   2. 运行: python bundle_generator.py --consumer end_to_end")
    print(f"   3. 运行: python training_dataset_generator.py --bundle v1.2.0-2025.3")
    print(f"   4. 运行: python data_producer.py --dataset-config training_dataset.json")

def export_to_markdown(consumer_config, bundle_content, training_dataset, jsonl_files):
    """导出演示结果为Markdown格式"""
    bundle_version = bundle_content['meta']['bundle_version']
    
    markdown_content = f"""# DataSpecHub 工作流程演示报告

## 概览
- **Consumer**: {consumer_config['meta']['consumer']} v{consumer_config['meta']['version']}
- **Bundle版本**: {bundle_version}
- **生成时间**: {bundle_content['meta']['created_at']}
- **团队**: {consumer_config['meta']['team']}

## 步骤1: Consumer配置

使用现有Consumer配置: `consumers/end_to_end/v{consumer_config['meta']['version']}.yaml`

### 依赖通道
| 通道 | 版本约束 | 是否必需 |
|------|----------|----------|
"""
    
    for req in consumer_config['requirements']:
        required_text = "✅" if req['required'] else "❌"
        markdown_content += f"| {req['channel']} | {req['version']} | {required_text} |\n"
    
    markdown_content += f"""
## 步骤2: Bundle生成

**Bundle文件路径**: `bundles/weekly/end_to_end-{bundle_version}.yaml`

### 版本解析结果
| 通道 | 约束条件 | 推荐版本 | 可选版本 |
|------|----------|----------|----------|
"""
    
    for channel_spec in bundle_content['channels']:
        available_str = ', '.join(channel_spec['available_versions'])
        markdown_content += f"| {channel_spec['channel']} | {channel_spec['source_constraint']} | {channel_spec['recommended_version']} | {available_str} |\n"
    
    total_samples = sum(ds['sample_count'] for ds in training_dataset['data_sources'])
    
    markdown_content += f"""
## 步骤3: Training Dataset配置

**配置文件**: `datasets/configs/training_dataset_production.json`

### 数据源配置
| 通道 | 版本 | 样本数 | 数据路径 |
|------|------|--------|----------|
"""
    
    for ds in training_dataset['data_sources']:
        markdown_content += f"| {ds['channel']} | v{ds['version']} | {ds['sample_count']:,} | {ds['data_path']} |\n"
    
    markdown_content += f"""
## 步骤4: 数据生产

**输出路径**: `{training_dataset['output_config']['output_path']}`
**总样本数**: {total_samples:,}
**通道数量**: {len(training_dataset['data_sources'])}

### 生成文件
| 文件 | 样本数 | 比例 |
|------|--------|------|
"""
    
    splits = ['train', 'val', 'test']
    ratios = [0.8, 0.15, 0.05]
    
    for split, ratio, jsonl_file in zip(splits, ratios, jsonl_files):
        split_samples = int(total_samples * ratio)
        markdown_content += f"| {jsonl_file} | {split_samples:,} | {ratio*100:.0f}% |\n"
    
    markdown_content += f"""
## 工作流程总结

### 核心优势
- ✅ 人工配置Consumer，减少自动推导复杂度
- ✅ 自动化Bundle生成，确保版本一致性
- ✅ 统一的Bundle版本管理，便于追溯
- ✅ 标准化的JSONL输出，支持多种训练框架

### 使用命令
1. 修改Consumer配置文件（手动）
2. `python bundle_generator.py --consumer end_to_end`
3. `python training_dataset_generator.py --bundle {bundle_version}`
4. `python data_producer.py --dataset-config training_dataset.json`

---
*报告生成时间: {bundle_content['meta']['created_at']}*
"""
    
    return markdown_content

def main():
    """主演示流程"""
    print("🚀 DataSpecHub 完整工作流程演示")
    print("展示从Consumer配置到最终数据生产的端到端流程")
    
    try:
        # 步骤1: Consumer配置
        consumer_config = step1_consumer_configuration()
        
        # 步骤2: Bundle生成
        bundle_content, bundle_path = step2_bundle_generation(consumer_config)
        
        # 步骤3: Training Dataset配置
        training_dataset, dataset_path = step3_training_dataset_generation(bundle_content)
        
        # 步骤4: Mock数据生产
        jsonl_files = step4_mock_data_production(training_dataset)
        
        # 工作流程总结
        workflow_summary()
        
        print("\n" + "=" * 80)
        print("🎉 完整工作流程演示完成！")
        print("=" * 80)
        
        # 询问是否导出markdown
        print("\n💡 是否导出为Markdown报告？")
        user_input = input("输入 'y' 或 'yes' 导出markdown报告 (直接回车跳过): ").lower().strip()
        
        if user_input in ['y', 'yes']:
            markdown_content = export_to_markdown(consumer_config, bundle_content, training_dataset, jsonl_files)
            markdown_filename = f"workflow_demo_report_{bundle_content['meta']['bundle_version'].replace('.', '_')}.md"
            
            try:
                with open(markdown_filename, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                print(f"✅ Markdown报告已导出: {markdown_filename}")
            except Exception as e:
                print(f"❌ 导出Markdown报告失败: {e}")
                print("📋 Markdown内容预览:")
                print("-" * 50)
                print(markdown_content[:500] + "...")
        else:
            print("跳过Markdown导出")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        print("💡 这是演示脚本，真实运行需要完整的项目环境")

if __name__ == "__main__":
    main()
