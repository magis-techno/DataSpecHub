#!/usr/bin/env python3
"""
数据库查询助手 - 模拟版本
提供统一的数据库查询接口，方便后续适配真实数据库
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os

class DatabaseQueryHelper:
    """数据库查询助手 - 模拟实现"""
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root)
        # 模拟数据文件路径
        self.mock_data_file = self.workspace_root / "scripts" / "mock_database.json"
        self._ensure_mock_data_exists()
    
    def query_available_versions(self, channels: List[str]) -> Dict[str, List[str]]:
        """
        查询指定通道的所有可用版本
        
        Args:
            channels: 通道名称列表
            
        Returns:
            {channel_name: [version1, version2, ...]}
        """
        mock_data = self._load_mock_data()
        result = {}
        
        for channel in channels:
            if channel in mock_data['channels']:
                versions = mock_data['channels'][channel]['available_versions']
                # 按语义化版本排序
                result[channel] = sorted(versions, key=self._version_key)
            else:
                result[channel] = []
                
        return result
    
    def query_latest_version(self, channel: str) -> Optional[str]:
        """
        查询通道的最新版本
        
        Args:
            channel: 通道名称
            
        Returns:
            最新版本号，如果通道不存在返回None
        """
        available = self.query_available_versions([channel])
        versions = available.get(channel, [])
        return versions[-1] if versions else None
    
    def query_data_availability(self, channel: str, version: str) -> Dict[str, Any]:
        """
        查询特定版本的数据可用性状态
        
        Args:
            channel: 通道名称
            version: 版本号
            
        Returns:
            数据可用性信息
        """
        mock_data = self._load_mock_data()
        
        if channel not in mock_data['channels']:
            return {'available': False, 'reason': 'Channel not found'}
            
        channel_data = mock_data['channels'][channel]
        
        if version not in channel_data['available_versions']:
            return {'available': False, 'reason': 'Version not found'}
            
        # 模拟数据可用性检查
        data_info = channel_data['data_info'].get(version, {})
        
        return {
            'available': data_info.get('status') == 'ready',
            'status': data_info.get('status', 'unknown'),
            'data_path': data_info.get('data_path', ''),
            'size_gb': data_info.get('size_gb', 0),
            'sample_count': data_info.get('sample_count', 0),
            'last_updated': data_info.get('last_updated', ''),
            'quality_score': data_info.get('quality_score', 0.0)
        }
    
    def query_production_data_paths(self, resolved_versions: Dict[str, str]) -> Dict[str, str]:
        """
        查询生产数据路径
        
        Args:
            resolved_versions: {channel: version} 映射
            
        Returns:
            {channel: data_path} 映射
        """
        result = {}
        
        for channel, version in resolved_versions.items():
            availability = self.query_data_availability(channel, version)
            if availability['available']:
                result[channel] = availability['data_path']
            else:
                result[channel] = f"ERROR: {availability['reason']}"
                
        return result
    
    def query_channel_statistics(self, channel: str, version: str) -> Dict[str, Any]:
        """
        查询通道数据统计信息
        
        Args:
            channel: 通道名称
            version: 版本号
            
        Returns:
            统计信息
        """
        availability = self.query_data_availability(channel, version)
        
        if not availability['available']:
            return {'error': availability['reason']}
            
        return {
            'total_samples': availability['sample_count'],
            'data_size_gb': availability['size_gb'],
            'quality_score': availability['quality_score'],
            'last_updated': availability['last_updated'],
            'data_path': availability['data_path']
        }
    
    def validate_bundle_data_availability(self, resolved_versions: Dict[str, str]) -> Dict[str, Any]:
        """
        验证Bundle中所有通道数据的可用性
        
        Args:
            resolved_versions: {channel: version} 映射
            
        Returns:
            验证结果报告
        """
        result = {
            'all_available': True,
            'channels': {},
            'summary': {
                'total_channels': len(resolved_versions),
                'available_channels': 0,
                'unavailable_channels': 0,
                'total_data_size_gb': 0
            }
        }
        
        for channel, version in resolved_versions.items():
            availability = self.query_data_availability(channel, version)
            result['channels'][channel] = availability
            
            if availability['available']:
                result['summary']['available_channels'] += 1
                result['summary']['total_data_size_gb'] += availability.get('size_gb', 0)
            else:
                result['summary']['unavailable_channels'] += 1
                result['all_available'] = False
                
        return result
    
    def _load_mock_data(self) -> Dict[str, Any]:
        """加载模拟数据"""
        with open(self.mock_data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _version_key(self, version: str) -> tuple:
        """版本排序键"""
        try:
            parts = version.split('.')
            return tuple(int(p) for p in parts)
        except ValueError:
            return (0, 0, 0)
    
    def _ensure_mock_data_exists(self):
        """确保模拟数据文件存在"""
        if not self.mock_data_file.exists():
            self._create_mock_data()
    
    def _create_mock_data(self):
        """创建模拟数据文件"""
        # 基于现有的channels目录结构生成模拟数据
        mock_data = {
            "database_info": {
                "type": "mock",
                "created_at": datetime.now().isoformat(),
                "description": "模拟数据库数据，用于开发和测试"
            },
            "channels": {}
        }
        
        # 从真实的channels目录生成模拟数据
        channels_dir = self.workspace_root / "channels"
        if channels_dir.exists():
            for channel_dir in channels_dir.iterdir():
                if channel_dir.is_dir():
                    channel_name = channel_dir.name
                    versions = []
                    
                    # 扫描spec文件获取版本
                    for spec_file in channel_dir.glob("spec-*.yaml"):
                        version = spec_file.stem.replace("spec-", "")
                        versions.append(version)
                    
                    if not versions:
                        versions = ["1.0.0"]  # 默认版本
                    
                    # 生成模拟数据信息
                    data_info = {}
                    for version in versions:
                        data_info[version] = {
                            "status": "ready",
                            "data_path": f"/data/production/{channel_name}/v{version}/",
                            "size_gb": round(50 + hash(f"{channel_name}-{version}") % 200, 1),
                            "sample_count": 10000 + hash(f"{channel_name}-{version}") % 50000,
                            "last_updated": (datetime.now() - timedelta(days=hash(f"{channel_name}-{version}") % 30)).isoformat(),
                            "quality_score": round(0.85 + (hash(f"{channel_name}-{version}") % 15) / 100, 2)
                        }
                    
                    mock_data["channels"][channel_name] = {
                        "available_versions": sorted(versions, key=self._version_key),
                        "data_info": data_info
                    }
        else:
            # 如果没有channels目录，创建一些示例数据
            example_channels = [
                "image_original", "object_array_fusion_infer", 
                "drivable_area_png", "occupancy", "utils_slam"
            ]
            
            for channel in example_channels:
                versions = ["1.0.0", "1.1.0", "1.2.0"]
                data_info = {}
                
                for version in versions:
                    data_info[version] = {
                        "status": "ready",
                        "data_path": f"/data/production/{channel}/v{version}/",
                        "size_gb": round(50 + hash(f"{channel}-{version}") % 200, 1),
                        "sample_count": 10000 + hash(f"{channel}-{version}") % 50000,
                        "last_updated": (datetime.now() - timedelta(days=hash(f"{channel}-{version}") % 30)).isoformat(),
                        "quality_score": round(0.85 + (hash(f"{channel}-{version}") % 15) / 100, 2)
                    }
                
                mock_data["channels"][channel] = {
                    "available_versions": versions,
                    "data_info": data_info
                }
        
        # 保存模拟数据
        self.mock_data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.mock_data_file, 'w', encoding='utf-8') as f:
            json.dump(mock_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 创建模拟数据库文件: {self.mock_data_file}")

# 使用示例和测试
def main():
    """测试数据库查询功能"""
    print("🗄️  数据库查询助手测试\n")
    
    db = DatabaseQueryHelper()
    
    # 测试1: 查询可用版本
    test_channels = ["image_original", "object_array_fusion_infer", "unknown_channel"]
    print("1️⃣  查询可用版本:")
    versions = db.query_available_versions(test_channels)
    for channel, channel_versions in versions.items():
        print(f"   {channel}: {channel_versions}")
    
    # 测试2: 查询最新版本
    print("\n2️⃣  查询最新版本:")
    for channel in test_channels[:2]:
        latest = db.query_latest_version(channel)
        print(f"   {channel}: {latest}")
    
    # 测试3: 查询数据可用性
    print("\n3️⃣  查询数据可用性:")
    for channel in test_channels[:2]:
        latest = db.query_latest_version(channel)
        if latest:
            availability = db.query_data_availability(channel, latest)
            print(f"   {channel}@{latest}:")
            print(f"     可用: {availability['available']}")
            print(f"     路径: {availability.get('data_path', 'N/A')}")
            print(f"     大小: {availability.get('size_gb', 0)} GB")
    
    # 测试4: Bundle数据验证
    print("\n4️⃣  Bundle数据验证:")
    test_bundle = {
        "image_original": "1.2.0",
        "object_array_fusion_infer": "1.1.0"
    }
    validation = db.validate_bundle_data_availability(test_bundle)
    print(f"   全部可用: {validation['all_available']}")
    print(f"   总大小: {validation['summary']['total_data_size_gb']} GB")
    print(f"   可用通道: {validation['summary']['available_channels']}/{validation['summary']['total_channels']}")

if __name__ == "__main__":
    main()
