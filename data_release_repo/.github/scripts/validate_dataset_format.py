#!/usr/bin/env python3
"""
验证训练数据集JSON文件格式
"""

import json
import os
import sys
from typing import Dict, List, Any
from jsonschema import validate, ValidationError

# 训练数据集JSON Schema
TRAINING_DATASET_SCHEMA = {
    "type": "object",
    "required": ["meta", "dataset_index"],
    "properties": {
        "meta": {
            "type": "object",
            "required": ["release_name", "consumer_version", "bundle_versions", "created_at", "description", "version"],
            "properties": {
                "release_name": {"type": "string"},
                "consumer_version": {"type": "string", "pattern": r"^v\d+\.\d+\.\d+"},
                "bundle_versions": {
                    "type": "array",
                    "items": {"type": "string", "pattern": r"^v\d+\.\d+\.\d+-\d{8}-\d{6}$"}
                },
                "created_at": {"type": "string"},
                "description": {"type": "string"},
                "version": {"type": "string", "pattern": r"^v\d+\.\d+\.\d+"},
                "status": {"type": "string", "enum": ["pending", "producing", "produced", "completed", "failed"]},
                "produced_at": {"type": "string"},
                "training_type": {"type": "string", "enum": ["regular", "dagger"]}
            }
        },
        "dataset_index": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "obs_path", "bundle_versions", "duplicate"],
                "properties": {
                    "name": {"type": "string"},
                    "obs_path": {"type": "string"},
                    "bundle_versions": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "duplicate": {"type": "integer", "minimum": 1},
                    "status": {"type": "string", "enum": ["pending", "producing", "produced", "failed"]},
                    "produced_at": {"type": "string"}
                }
            }
        }
    }
}

def find_dataset_files() -> List[str]:
    """查找所有训练数据集JSON文件"""
    dataset_files = []
    
    # 查找根目录下的数据集文件
    for filename in ['training_dataset.json', 'training_dataset.dagger.json']:
        if os.path.exists(filename):
            dataset_files.append(filename)
    
    # 查找子目录中的数据集文件
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith(('.json',)) and 'training_dataset' in file:
                filepath = os.path.join(root, file)
                if filepath not in dataset_files:
                    dataset_files.append(filepath)
    
    return dataset_files

def validate_dataset_file(filepath: str) -> List[str]:
    """验证单个数据集文件"""
    errors = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 基本schema验证
        validate(instance=data, schema=TRAINING_DATASET_SCHEMA)
        
        # 额外的业务逻辑验证
        errors.extend(validate_business_logic(data, filepath))
        
    except json.JSONDecodeError as e:
        errors.append(f"JSON格式错误: {e}")
    except ValidationError as e:
        errors.append(f"Schema验证错误: {e.message}")
    except FileNotFoundError:
        errors.append(f"文件不存在: {filepath}")
    except Exception as e:
        errors.append(f"未知错误: {e}")
    
    return errors

def validate_business_logic(data: Dict[str, Any], filepath: str) -> List[str]:
    """验证业务逻辑"""
    errors = []
    
    meta = data.get('meta', {})
    dataset_index = data.get('dataset_index', [])
    
    # 1. 验证DAgger文件的training_type字段
    if 'dagger' in filepath and meta.get('training_type') != 'dagger':
        errors.append("DAgger文件必须设置training_type为'dagger'")
    
    # 2. 验证status字段一致性
    meta_status = meta.get('status')
    if meta_status == 'completed':
        # 如果meta状态为completed，所有dataset应该为produced
        for idx, dataset in enumerate(dataset_index):
            if dataset.get('status') not in ['produced', None]:
                errors.append(f"数据集索引{idx}: meta状态为completed时，所有数据集状态应为produced")
    
    # 3. 验证obs_path一致性
    for idx, dataset in enumerate(dataset_index):
        obs_path = dataset.get('obs_path', '')
        status = dataset.get('status', 'produced')
        
        if status == 'produced' and not obs_path:
            errors.append(f"数据集索引{idx}: 状态为produced时，obs_path不能为空")
        elif status == 'pending' and obs_path:
            errors.append(f"数据集索引{idx}: 状态为pending时，obs_path应为空")
    
    # 4. 验证版本号一致性
    consumer_version = meta.get('consumer_version', '')
    dataset_version = meta.get('version', '')
    if consumer_version and dataset_version:
        # 移除v前缀进行比较
        consumer_ver = consumer_version.lstrip('v')
        dataset_ver = dataset_version.lstrip('v')
        if consumer_ver != dataset_ver:
            errors.append(f"consumer_version({consumer_version})和version({dataset_version})不一致")
    
    # 5. 验证bundle_versions格式
    bundle_versions = meta.get('bundle_versions', [])
    for bundle_version in bundle_versions:
        if not bundle_version.startswith('v'):
            errors.append(f"Bundle版本{bundle_version}应以'v'开头")
    
    # 6. 验证数据集名称唯一性
    dataset_names = [ds.get('name') for ds in dataset_index]
    duplicates = [name for name in dataset_names if dataset_names.count(name) > 1]
    if duplicates:
        errors.append(f"数据集名称重复: {set(duplicates)}")
    
    return errors

def main():
    """主函数"""
    print("=== 数据集格式验证 ===")
    
    dataset_files = find_dataset_files()
    
    if not dataset_files:
        print("❌ 未找到训练数据集文件")
        sys.exit(1)
    
    total_errors = 0
    
    for filepath in dataset_files:
        print(f"\n📁 验证文件: {filepath}")
        errors = validate_dataset_file(filepath)
        
        if errors:
            print(f"❌ 发现 {len(errors)} 个错误:")
            for error in errors:
                print(f"   • {error}")
            total_errors += len(errors)
        else:
            print("✅ 格式验证通过")
    
    print(f"\n=== 验证完成 ===")
    print(f"检查文件数: {len(dataset_files)}")
    print(f"总错误数: {total_errors}")
    
    if total_errors > 0:
        sys.exit(1)
    else:
        print("🎉 所有文件验证通过!")

if __name__ == "__main__":
    main()

