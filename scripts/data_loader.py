#!/usr/bin/env python3
"""
DataSpecHub 数据加载器
将语义化的规格定义映射到实际的存储路径
"""

import yaml
import os
from pathlib import Path
from typing import Dict, List, Optional

class DataSpecLoader:
    """基于DataSpecHub规格的数据加载器"""
    
    def __init__(self, base_data_path: str, spec_path: str = "channels"):
        """
        初始化数据加载器
        
        Args:
            base_data_path: 实际数据存储根路径
            spec_path: DataSpecHub规格文件路径
        """
        self.base_data_path = Path(base_data_path)
        self.spec_path = Path(spec_path)
        
        # 映射表从spec文件中动态加载
    
    def get_spec(self, channel: str, version: str = None) -> Dict:
        """获取通道规格定义"""
        spec_dir = self.spec_path / channel
        
        if version:
            spec_file = spec_dir / f"spec-{version}.yaml"
        else:
            # 获取最新版本
            spec_files = list(spec_dir.glob("spec-*.yaml"))
            if not spec_files:
                raise FileNotFoundError(f"No spec files found for channel {channel}")
            spec_file = sorted(spec_files)[-1]  # 最新版本
        
        with open(spec_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def resolve_storage_path(self, channel: str, camera_position: str, vehicle_model: str) -> Path:
        """
        将语义化的相机位置解析为实际存储路径
        
        Args:
            channel: 通道名称 (如 image_original)
            camera_position: 语义位置 (如 front, rear)
            vehicle_model: 车型 (如 model_a)
            
        Returns:
            实际存储路径
        """
        # 从spec文件获取存储映射
        spec = self.get_spec(channel)
        storage_mapping = spec.get('storage_mapping', {})
        position_mapping = storage_mapping.get('camera_position_to_storage', {})
        
        # 获取车型特定的映射
        vehicle_mapping = position_mapping.get(vehicle_model, {})
        actual_camera_id = vehicle_mapping.get(camera_position, camera_position)
        
        # 构建实际路径
        storage_path = self.base_data_path / channel / actual_camera_id
        return storage_path
    
    def load_image_data(self, camera_position: str, vehicle_model: str, timestamp_range: tuple = None) -> List[Dict]:
        """
        加载图像数据
        
        Args:
            camera_position: 语义相机位置
            vehicle_model: 车型
            timestamp_range: 时间戳范围 (start, end)
            
        Returns:
            符合规格的数据列表
        """
        spec = self.get_spec("image_original")
        storage_path = self.resolve_storage_path("image_original", camera_position, vehicle_model)
        
        if not storage_path.exists():
            return []
        
        # 加载数据文件
        image_files = list(storage_path.glob("*.jpg"))
        
        # 构建符合规格的数据结构
        data_list = []
        for img_file in image_files:
            data_item = {
                "file_path": str(img_file),
                "metadata": {
                    "camera_position": camera_position,  # 语义化字段（从存储路径推断）
                    "vehicle_model": vehicle_model,     # 从参数获得
                    "timestamp": self._extract_timestamp(img_file.name),  # 从文件名提取
                    # 注：没有额外的元数据文件，所有信息从文件路径和名称推断
                },
                "spec_version": spec["meta"]["version"]
            }
            data_list.append(data_item)
        
        return data_list
    
    def _extract_timestamp(self, filename: str) -> int:
        """从文件名提取时间戳 - 实际实现依赖具体命名规则"""
        # 示例实现
        try:
            # 假设文件名格式：timestamp_xxx.jpg
            timestamp_str = filename.split('_')[0]
            return int(timestamp_str)
        except:
            return 0
    
    def generate_config_for_team(self, team_name: str, requirements: Dict) -> Dict:
        """
        为特定团队生成配置文件
        
        Args:
            team_name: 团队名称
            requirements: 团队需求配置
            
        Returns:
            团队特定的配置
        """
        config = {
            "team": team_name,
            "generated_at": "2024-12-19",
            "data_sources": {}
        }
        
        # 根据团队需求生成配置
        for channel_req in requirements.get("channels", []):
            channel = channel_req["name"]
            spec = self.get_spec(channel, channel_req.get("version"))
            
            # 生成团队特定的路径映射
            for vehicle in channel_req.get("vehicles", []):
                for position in channel_req.get("cameras", []):
                    storage_path = self.resolve_storage_path(channel, position, vehicle)
                    
                    key = f"{channel}_{vehicle}_{position}"
                    config["data_sources"][key] = {
                        "spec_reference": f"{channel}/spec-{spec['meta']['version']}.yaml",
                        "storage_path": str(storage_path),
                        "semantic_info": {
                            "camera_position": position,
                            "vehicle_model": vehicle
                        }
                    }
        
        return config

def main():
    """示例用法"""
    loader = DataSpecLoader("/data", "channels")
    
    # 1. 加载数据 - 用户只需知道语义信息
    front_images = loader.load_image_data(
        camera_position="front", 
        vehicle_model="model_a"
    )
    print(f"加载到 {len(front_images)} 张前向相机图像")
    
    # 2. 生成团队配置
    perception_team_config = loader.generate_config_for_team(
        "perception_team",
        {
            "channels": [{
                "name": "image_original",
                "version": "1.2.0",
                "vehicles": ["model_a", "model_b"],
                "cameras": ["front", "rear"]
            }]
        }
    )
    
    print("感知团队配置生成完成:")
    print(yaml.dump(perception_team_config, allow_unicode=True, default_flow_style=False))

if __name__ == "__main__":
    main() 