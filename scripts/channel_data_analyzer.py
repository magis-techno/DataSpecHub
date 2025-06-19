#!/usr/bin/env python3

import os
import argparse
from collections import defaultdict
import json
from pathlib import Path
import mimetypes
import pandas as pd
from typing import Dict, List, Any, Optional
import logging
from itertools import groupby

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ChannelDataAnalyzer:
    def __init__(self, data_dir: str, samples_per_type: int = 3, skip_levels: Optional[List[int]] = None):
        self.data_dir = Path(data_dir)
        self.samples_per_type = samples_per_type
        self.skip_levels = skip_levels or []  # 要忽略的目录层级（0为根目录）
        self.stats = {
            'directory_structure': {},
            'file_types': defaultdict(int),
            'file_sizes': defaultdict(list),
            'file_extensions': defaultdict(int),
            'total_files': 0,
            'total_dirs': 0,
            'max_depth': 0,
            'avg_file_size': 0,
            'dir_file_counts': defaultdict(lambda: defaultdict(int))
        }

    def _get_effective_path(self, path: Path) -> Optional[Path]:
        """
        获取有效的路径，如果当前层级需要被忽略，返回其父目录
        """
        try:
            rel_path = path.relative_to(self.data_dir)
            parts = rel_path.parts
            
            if not parts:  # 根目录
                return path
                
            # 计算当前路径的层级（从0开始）
            current_level = len(parts) - 1
            
            # 如果当前层级需要被忽略，返回父目录
            if current_level in self.skip_levels:
                return path.parent
            
            return path
        except Exception:
            return None

    def _get_storage_path(self, path: Path) -> str:
        """
        获取用于存储统计信息的路径
        对于需要忽略的层级，使用父目录路径
        """
        try:
            rel_path = path.relative_to(self.data_dir)
            parts = rel_path.parts
            
            if not parts:
                return str(rel_path)
                
            # 构建新的路径，跳过需要忽略的层级
            new_parts = []
            for i, part in enumerate(parts):
                if i not in self.skip_levels:
                    new_parts.append(part)
            
            return str(Path(*new_parts))
        except Exception:
            return str(path)

    def analyze_directory(self, current_path: Path, depth: int = 0) -> None:
        """递归分析目录结构"""
        try:
            self.stats['max_depth'] = max(self.stats['max_depth'], depth)
            
            # 获取有效的当前路径
            effective_path = self._get_effective_path(current_path)
            if not effective_path:
                return
                
            # 收集当前目录下所有文件
            files_in_dir = []
            subdirs = []
            
            for item in current_path.iterdir():
                if item.is_file():
                    files_in_dir.append(item)
                elif item.is_dir():
                    subdirs.append(item)
                    self.stats['total_dirs'] += 1
                    
                    # 只有不在忽略层级的目录才添加到目录结构中
                    if len(item.relative_to(self.data_dir).parts) - 1 not in self.skip_levels:
                        storage_path = self._get_storage_path(item)
                        self.stats['directory_structure'][storage_path] = {
                            'type': 'directory',
                            'depth': depth
                        }
            
            # 按文件类型分组并采样
            if files_in_dir:
                self._analyze_files_in_directory(files_in_dir, effective_path)
            
            # 递归处理子目录
            for subdir in subdirs:
                self.analyze_directory(subdir, depth + 1)
                
        except PermissionError:
            logger.warning(f"Permission denied accessing {current_path}")
        except Exception as e:
            logger.error(f"Error analyzing directory {current_path}: {e}")

    def _get_file_type(self, file_path: Path) -> str:
        """获取文件类型"""
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            return file_path.suffix.lower() if file_path.suffix else 'unknown'
        return mime_type

    def _analyze_files_in_directory(self, files: List[Path], effective_path: Path) -> None:
        """分析目录中的文件，并只保留每种类型的代表性样本"""
        # 按文件类型分组
        files_by_type = defaultdict(list)
        for file in files:
            file_type = self._get_file_type(file)
            files_by_type[file_type].append(file)

        # 更新目录下文件类型统计
        dir_path = self._get_storage_path(effective_path)
        for file_type, files_of_type in files_by_type.items():
            self.stats['dir_file_counts'][dir_path][file_type] = len(files_of_type)
            
            # 对每种类型的文件进行采样
            sampled_files = files_of_type[:self.samples_per_type]
            
            # 更新总体统计信息
            self.stats['total_files'] += len(files_of_type)
            self.stats['file_types'][file_type] += len(files_of_type)
            
            # 只为采样的文件添加详细信息
            for file in sampled_files:
                self._analyze_sampled_file(file)

    def _analyze_sampled_file(self, file_path: Path) -> None:
        """分析采样的文件"""
        try:
            # 获取文件大小
            file_size = file_path.stat().st_size
            size_mb = file_size / (1024 * 1024)
            
            # 获取文件类型和扩展名
            mime_type = self._get_file_type(file_path)
            extension = file_path.suffix.lower()
            
            # 更新文件扩展名统计
            self.stats['file_extensions'][extension] += 1
            
            # 记录文件大小
            storage_path = self._get_storage_path(file_path)
            self.stats['file_sizes'][storage_path] = size_mb
            
            # 在目录结构中记录采样的文件
            self.stats['directory_structure'][storage_path] = {
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
            self.stats['avg_file_size'] = total_size / len(self.stats['file_sizes'])

    def generate_report(self) -> Dict[str, Any]:
        """生成分析报告"""
        self.calculate_statistics()
        return {
            'summary': {
                'total_files': self.stats['total_files'],
                'total_directories': self.stats['total_dirs'],
                'max_directory_depth': self.stats['max_depth'],
                'average_file_size_mb': round(self.stats['avg_file_size'], 2),
                'skipped_levels': self.skip_levels
            },
            'file_types': dict(self.stats['file_types']),
            'file_extensions': dict(self.stats['file_extensions']),
            'directory_structure': self.stats['directory_structure'],
            'directory_file_counts': dict(self.stats['dir_file_counts'])
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
        
        # 保存目录文件类型统计
        dir_stats = []
        for dir_path, type_counts in self.stats['dir_file_counts'].items():
            for file_type, count in type_counts.items():
                dir_stats.append({
                    'directory': dir_path,
                    'file_type': file_type,
                    'count': count
                })
        df_dir_stats = pd.DataFrame(dir_stats)
        if not df_dir_stats.empty:
            df_dir_stats.to_csv(output_path / 'directory_type_statistics.csv', index=False)
        
        logger.info(f"Analysis report saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Analyze channel data directory structure')
    parser.add_argument('data_dir', help='Path to the data directory to analyze')
    parser.add_argument('--output', '-o', default='analysis_output',
                       help='Directory to save analysis results')
    parser.add_argument('--samples', '-s', type=int, default=3,
                       help='Number of sample files to keep per type in each directory')
    parser.add_argument('--skip-levels', type=int, nargs='+', default=[1],
                       help='Directory levels to skip (0-based, default is [1] to skip the second level)')
    
    args = parser.parse_args()
    
    try:
        analyzer = ChannelDataAnalyzer(args.data_dir, args.samples, args.skip_levels)
        analyzer.analyze_directory(Path(args.data_dir))
        analyzer.save_report(args.output)
        logger.info("Analysis completed successfully")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == '__main__':
    main() 