#!/usr/bin/env python3

import os
import argparse
from collections import defaultdict
import json
from pathlib import Path
import mimetypes
import pandas as pd
from typing import Dict, List, Any
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ChannelDataAnalyzer:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.stats = {
            'directory_structure': {},
            'file_types': defaultdict(int),
            'file_sizes': defaultdict(list),
            'file_extensions': defaultdict(int),
            'total_files': 0,
            'total_dirs': 0,
            'max_depth': 0,
            'avg_file_size': 0,
        }

    def analyze_directory(self, current_path: Path, depth: int = 0) -> None:
        """递归分析目录结构"""
        try:
            # 更新最大深度
            self.stats['max_depth'] = max(self.stats['max_depth'], depth)
            
            for item in current_path.iterdir():
                if item.is_file():
                    self._analyze_file(item)
                elif item.is_dir():
                    self.stats['total_dirs'] += 1
                    # 记录目录结构
                    rel_path = str(item.relative_to(self.data_dir))
                    self.stats['directory_structure'][rel_path] = {
                        'type': 'directory',
                        'depth': depth
                    }
                    self.analyze_directory(item, depth + 1)
        except PermissionError:
            logger.warning(f"Permission denied accessing {current_path}")
        except Exception as e:
            logger.error(f"Error analyzing directory {current_path}: {e}")

    def _analyze_file(self, file_path: Path) -> None:
        """分析单个文件的特征"""
        try:
            self.stats['total_files'] += 1
            
            # 获取文件大小
            file_size = file_path.stat().st_size
            size_mb = file_size / (1024 * 1024)  # 转换为MB
            
            # 获取文件类型
            mime_type, _ = mimetypes.guess_type(str(file_path))
            mime_type = mime_type if mime_type else 'unknown'
            
            # 获取文件扩展名
            extension = file_path.suffix.lower()
            
            # 更新统计信息
            self.stats['file_types'][mime_type] += 1
            self.stats['file_extensions'][extension] += 1
            self.stats['file_sizes'][str(file_path.relative_to(self.data_dir))] = size_mb
            
            # 记录文件结构
            rel_path = str(file_path.relative_to(self.data_dir))
            self.stats['directory_structure'][rel_path] = {
                'type': 'file',
                'size_mb': size_mb,
                'mime_type': mime_type,
                'extension': extension
            }
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")

    def calculate_statistics(self) -> None:
        """计算汇总统计信息"""
        if self.stats['total_files'] > 0:
            total_size = sum(self.stats['file_sizes'].values())
            self.stats['avg_file_size'] = total_size / self.stats['total_files']

    def generate_report(self) -> Dict[str, Any]:
        """生成分析报告"""
        self.calculate_statistics()
        return {
            'summary': {
                'total_files': self.stats['total_files'],
                'total_directories': self.stats['total_dirs'],
                'max_directory_depth': self.stats['max_depth'],
                'average_file_size_mb': round(self.stats['avg_file_size'], 2),
            },
            'file_types': dict(self.stats['file_types']),
            'file_extensions': dict(self.stats['file_extensions']),
            'directory_structure': self.stats['directory_structure']
        }

    def save_report(self, output_dir: str) -> None:
        """保存分析报告"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        report = self.generate_report()
        
        # 保存JSON报告
        with open(output_path / 'channel_analysis_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 保存CSV格式的文件大小统计
        df_sizes = pd.DataFrame.from_dict(self.stats['file_sizes'], 
                                        orient='index', 
                                        columns=['size_mb'])
        df_sizes.to_csv(output_path / 'file_sizes.csv')
        
        logger.info(f"Analysis report saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Analyze channel data directory structure')
    parser.add_argument('data_dir', help='Path to the data directory to analyze')
    parser.add_argument('--output', '-o', default='analysis_output',
                       help='Directory to save analysis results')
    
    args = parser.parse_args()
    
    try:
        analyzer = ChannelDataAnalyzer(args.data_dir)
        analyzer.analyze_directory(Path(args.data_dir))
        analyzer.save_report(args.output)
        logger.info("Analysis completed successfully")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == '__main__':
    main() 