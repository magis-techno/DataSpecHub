#!/usr/bin/env python3
"""
Camera Parquet Data 使用示例

展示如何读取和解析 camera_parquet_data channel 的数据
"""

import pandas as pd
import pickle
from typing import Dict, Any

def load_camera_parquet_data(file_path: str) -> Dict[str, Any]:
    """
    加载并解析相机Parquet数据
    
    Args:
        file_path: parquet文件路径
        
    Returns:
        Dict: 解析后的相机数据，键为相机名，值为解析的数据
    """
    # 1. 读取parquet文件
    df = pd.read_parquet(file_path)
    
    # 2. 验证数据结构
    assert df.shape == (4, 2), f"期望4行2列，实际为{df.shape}"
    assert list(df.columns) == ['names', 'datas'], f"期望列名为['names', 'datas']，实际为{list(df.columns)}"
    
    # 3. 验证相机名称
    expected_cameras = {"cam1", "cam2", "cam4", "cam11"}
    actual_cameras = set(df['names'].tolist())
    assert actual_cameras == expected_cameras, f"期望相机{expected_cameras}，实际为{actual_cameras}"
    
    # 4. 解析每个相机的数据
    camera_data = {}
    for _, row in df.iterrows():
        camera_name = row['names']
        binary_data = row['datas']
        
        try:
            # 使用pickle.loads解析二进制数据
            parsed_data = pickle.loads(binary_data)
            camera_data[camera_name] = parsed_data
        except Exception as e:
            print(f"解析相机{camera_name}数据失败: {e}")
            camera_data[camera_name] = None
    
    return camera_data

def validate_camera_data(camera_data: Dict[str, Any]) -> bool:
    """
    验证解析后的相机数据
    
    Args:
        camera_data: 相机数据字典
        
    Returns:
        bool: 验证是否通过
    """
    # 检查所有期望的相机都存在
    expected_cameras = {"cam1", "cam2", "cam4", "cam11"}
    if set(camera_data.keys()) != expected_cameras:
        print(f"相机列表不匹配，期望{expected_cameras}，实际{set(camera_data.keys())}")
        return False
    
    # 检查是否有解析失败的数据
    for camera_name, data in camera_data.items():
        if data is None:
            print(f"相机{camera_name}数据解析失败")
            return False
    
    print("相机数据验证通过")
    return True

# 使用示例
if __name__ == "__main__":
    # 示例用法
    parquet_file = "path/to/your/camera_data.parquet"
    
    try:
        # 加载数据
        camera_data = load_camera_parquet_data(parquet_file)
        
        # 验证数据
        if validate_camera_data(camera_data):
            print("数据加载和验证成功")
            
            # 打印每个相机的数据信息
            for camera_name, data in camera_data.items():
                print(f"{camera_name}: {type(data)}, 数据大小: {len(str(data))} chars")
        else:
            print("数据验证失败")
            
    except Exception as e:
        print(f"处理失败: {e}") 