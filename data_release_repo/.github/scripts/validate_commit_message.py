#!/usr/bin/env python3
"""
验证提交信息格式是否符合结构化规范
"""

import os
import re
import sys
import subprocess
from typing import Dict, List, Any
import yaml

def get_latest_commit_message() -> str:
    """获取最新的提交信息"""
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--pretty=format:%B'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ 获取提交信息失败: {e}")
        sys.exit(1)

def parse_commit_message(message: str) -> Dict[str, Any]:
    """解析结构化提交信息"""
    # 分离标题和正文
    lines = message.split('\n')
    title = lines[0] if lines else ""
    
    # 查找YAML正文
    yaml_start = -1
    for i, line in enumerate(lines):
        if line.strip().startswith('date:') or line.strip().startswith('type:'):
            yaml_start = i
            break
    
    if yaml_start == -1:
        return {"title": title, "yaml_body": None, "raw_body": '\n'.join(lines[1:]).strip()}
    
    yaml_content = '\n'.join(lines[yaml_start:])
    
    try:
        yaml_data = yaml.safe_load(yaml_content)
        return {"title": title, "yaml_body": yaml_data, "raw_body": yaml_content}
    except yaml.YAMLError as e:
        return {"title": title, "yaml_body": None, "yaml_error": str(e), "raw_body": yaml_content}

def validate_commit_structure(parsed: Dict[str, Any]) -> List[str]:
    """验证提交信息结构"""
    errors = []
    
    title = parsed.get("title", "")
    yaml_body = parsed.get("yaml_body")
    
    # 1. 检查是否有标题
    if not title.strip():
        errors.append("提交信息必须包含标题")
        return errors
    
    # 2. 检查标题格式（可选：可以是简单描述或者遵循conventional commits）
    # 这里采用宽松策略，允许各种标题格式
    
    # 3. 检查YAML格式的结构化正文
    if yaml_body is None:
        if "yaml_error" in parsed:
            errors.append(f"YAML格式错误: {parsed['yaml_error']}")
        else:
            # 如果没有YAML正文，检查是否是特殊类型的提交
            special_commits = ['merge', 'revert', 'initial commit', 'docs:', 'fix:', 'refactor:']
            is_special = any(keyword in title.lower() for keyword in special_commits)
            
            if not is_special:
                errors.append("提交信息应包含结构化的YAML正文")
        return errors
    
    # 4. 验证必需字段
    required_fields = ['date', 'type', 'description']
    for field in required_fields:
        if field not in yaml_body:
            errors.append(f"缺少必需字段: {field}")
    
    # 5. 验证字段格式
    if 'date' in yaml_body:
        date_value = yaml_body['date']
        if not isinstance(date_value, str):
            errors.append("date字段必须是字符串")
        elif not re.match(r'^\d{4}-\d{2}-\d{2}$', date_value):
            errors.append("date字段格式应为YYYY-MM-DD")
    
    if 'type' in yaml_body:
        type_value = yaml_body['type']
        valid_types = ['add', 'modify(clean)', 'modify(balance)', 'fix', 'docs', 'refactor']
        if type_value not in valid_types:
            errors.append(f"type字段值无效: {type_value}，有效值: {valid_types}")
    
    if 'description' in yaml_body:
        desc_value = yaml_body['description']
        if not isinstance(desc_value, str) or not desc_value.strip():
            errors.append("description字段不能为空")
    
    # 6. 验证可选字段
    if 'task_tag' in yaml_body:
        task_tag = yaml_body['task_tag']
        if task_tag and not isinstance(task_tag, str):
            errors.append("task_tag字段必须是字符串")
    
    # 7. 验证details字段结构
    if 'details' in yaml_body:
        details = yaml_body['details']
        if not isinstance(details, dict):
            errors.append("details字段必须是对象类型")
        else:
            # 验证常见的details字段
            numeric_fields = ['total_clips_before', 'clips_removed', 'clips_after', 'clips_added']
            for field in numeric_fields:
                if field in details and not isinstance(details[field], (int, float)):
                    errors.append(f"details.{field}应为数字类型")
    
    return errors

def validate_data_operation_commit(parsed: Dict[str, Any]) -> List[str]:
    """验证数据操作相关的提交"""
    errors = []
    
    yaml_body = parsed.get("yaml_body")
    if not yaml_body:
        return errors
    
    commit_type = yaml_body.get('type', '')
    
    # 对于数据操作类型的提交，建议包含details
    if commit_type in ['add', 'modify(clean)', 'modify(balance)']:
        if 'details' not in yaml_body:
            errors.append(f"数据操作类型({commit_type})建议包含details字段")
        else:
            details = yaml_body['details']
            if 'dataset' not in details:
                errors.append("数据操作应指定dataset名称")
    
    return errors

def check_commit_file_changes() -> List[str]:
    """检查提交是否修改了训练数据集文件"""
    try:
        result = subprocess.run(
            ['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'],
            capture_output=True,
            text=True,
            check=True
        )
        changed_files = result.stdout.strip().split('\n')
        
        dataset_files = [f for f in changed_files if 'training_dataset' in f and f.endswith('.json')]
        return dataset_files
    except subprocess.CalledProcessError:
        return []

def main():
    """主函数"""
    print("=== 提交信息格式验证 ===")
    
    # 获取提交信息
    commit_message = get_latest_commit_message()
    print(f"📝 提交信息:\n{commit_message}\n")
    
    # 解析提交信息
    parsed = parse_commit_message(commit_message)
    
    # 验证结构
    errors = validate_commit_structure(parsed)
    
    # 额外的数据操作验证
    errors.extend(validate_data_operation_commit(parsed))
    
    # 检查文件变更
    changed_dataset_files = check_commit_file_changes()
    if changed_dataset_files:
        print(f"📁 修改了数据集文件: {changed_dataset_files}")
        
        # 如果修改了数据集文件，提交应该有结构化信息
        if not parsed.get("yaml_body"):
            errors.append("修改数据集文件的提交必须包含结构化的YAML信息")
    
    # 输出结果
    if errors:
        print(f"❌ 提交信息验证失败，发现 {len(errors)} 个问题:")
        for error in errors:
            print(f"   • {error}")
        
        print("\n💡 标准格式示例:")
        print("""
对收费站场景数据进行质量清洗

date: "2025-09-23"
type: "modify(clean)"
description: "对收费站场景数据进行质量清洗"
task_tag: "TASK-12345"
details:
  dataset: "toll_station_scenarios_v2"
  total_clips_before: 150000
  clips_removed: 15000
  clips_after: 135000
  quality_threshold: 0.95
        """)
        
        sys.exit(1)
    else:
        print("✅ 提交信息格式验证通过!")

if __name__ == "__main__":
    main()

