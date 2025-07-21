# Camera Parquet Data Channel Changelog

所有关于camera_parquet_data通道的重要变更都会记录在此文件中。

格式基于[Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且遵循[语义化版本控制](https://semver.org/lang/zh-CN/)。

## [1.0.0] - 2025-01-15

### 新增
- 初始版本发布
- 支持Parquet格式的相机数据存储
- 支持4个固定相机：cam1, cam2, cam4, cam11
- 支持pickle序列化的二进制数据解析
- 固定的4行2列表结构
- 完整的数据验证规则

### 技术特性
- 文件格式：Parquet
- 数据结构：4行2列表格
- 相机配置：cam1, cam2, cam4, cam11
- 二进制数据：pickle编码，需要pickle.loads()解析
- 验证规则：严格的行列数和相机名称验证

### 依赖
- pandas（用于读取parquet文件）
- pickle（用于解析二进制数据） 