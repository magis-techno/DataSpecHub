# 两仓库联动自动化方案

## 工作流程设计

### 1. Bundle生成触发数据索引创建

```yaml
# .github/workflows/bundle-to-dataindex.yml (DataSpecHub)
name: 生成数据索引
on:
  push:
    paths: ['bundles/**/*.yaml']
  
jobs:
  trigger_data_index:
    runs-on: ubuntu-latest
    steps:
      - name: 解析Bundle文件
        run: |
          BUNDLE_FILE=$(git diff --name-only HEAD~1 | grep bundles/)
          BUNDLE_TYPE=$(echo $BUNDLE_FILE | cut -d'/' -f2)
          BUNDLE_NAME=$(basename $BUNDLE_FILE .yaml)
          
      - name: 触发DataIndexHub数据索引生成
        uses: peter-evans/repository-dispatch@v2
        with:
          token: ${{ secrets.DATAINDEX_TRIGGER_TOKEN }}
          repository: company/DataIndexHub
          event-type: generate-data-index
          client-payload: |
            {
              "bundle_file": "${{ env.BUNDLE_FILE }}",
              "bundle_type": "${{ env.BUNDLE_TYPE }}",
              "bundle_name": "${{ env.BUNDLE_NAME }}",
              "spec_repo_commit": "${{ github.sha }}"
            }
```

### 2. 数据索引生成流程

```yaml
# .github/workflows/generate-index.yml (DataIndexHub)
name: 生成数据索引
on:
  repository_dispatch:
    types: [generate-data-index]

jobs:
  generate_index:
    runs-on: ubuntu-latest
    steps:
      - name: 获取Bundle规范
        run: |
          curl -H "Authorization: token ${{ secrets.SPEC_REPO_TOKEN }}" \
               "https://raw.githubusercontent.com/company/DataSpecHub/${{ github.event.client_payload.spec_repo_commit }}/${{ github.event.client_payload.bundle_file }}" \
               -o bundle_spec.yaml
               
      - name: 创建数据分支
        run: |
          BRANCH_NAME="data/${{ github.event.client_payload.bundle_name }}"
          git checkout -b $BRANCH_NAME
          
      - name: 生成数据索引文件
        run: python scripts/generate_data_index.py bundle_spec.yaml
        
      - name: 提交数据索引
        run: |
          git add .
          git commit -m "生成数据索引: ${{ github.event.client_payload.bundle_name }}"
          git push origin $BRANCH_NAME
```

## 数据索引文件结构

### Bundle级别索引文件

```yaml
# bundles/weekly/foundational_model-v1.0.0-2025.25.yaml (DataIndexHub)
meta:
  bundle_name: foundational_model
  bundle_version: "v1.0.0-2025.25"
  bundle_type: weekly
  spec_source:
    repo: "DataSpecHub"
    commit: "abc123456"
    file: "bundles/weekly/foundational_model-v1.0.0-2025.25.yaml"
  created_at: "2025-06-20T10:30:00Z"
  data_volume: "2.5TB"
  total_files: 150000

# 数据索引清单
data_manifest:
  - channel: image_original
    version: "1.2.0"
    data_range:
      start_time: "2025-06-01T00:00:00Z"
      end_time: "2025-06-15T23:59:59Z"
    storage_path: "s3://data-lake/image_original/v1.2.0/"
    index_file: "channels/image_original/v1.2.0/index.parquet"
    file_count: 50000
    total_size: "1.2TB"
    checksum: "sha256:abc123..."
    
  - channel: object_array_fusion_infer
    version: "1.2.0" 
    data_range:
      start_time: "2025-06-01T00:00:00Z"
      end_time: "2025-06-15T23:59:59Z"
    storage_path: "s3://data-lake/object_array/v1.2.0/"
    index_file: "channels/object_array_fusion_infer/v1.2.0/index.parquet"
    file_count: 50000
    total_size: "800GB"
    checksum: "sha256:def456..."

# 数据访问API
access_config:
  base_url: "https://dataindex-api.company.com"
  authentication: "bearer_token"
  endpoints:
    list_files: "/api/v1/bundles/{bundle_name}/files"
    download_batch: "/api/v1/bundles/{bundle_name}/download"
    streaming: "/api/v1/bundles/{bundle_name}/stream"
```

### Channel级别索引文件

```yaml
# channels/image_original/v1.2.0/index.parquet 的YAML描述
# 实际存储为Parquet格式提升查询性能

meta:
  channel: image_original
  version: "1.2.0"
  total_files: 50000
  index_schema:
    - file_id: string          # 唯一标识
    - relative_path: string    # 相对路径
    - timestamp: timestamp     # 数据时间戳
    - size_bytes: int64        # 文件大小
    - checksum: string         # 文件校验和
    - metadata: json           # 扩展元数据

# 示例数据记录
sample_records:
  - file_id: "img_20250601_120000_001"
    relative_path: "2025/06/01/12/img_001.jpg"
    timestamp: "2025-06-01T12:00:00Z"
    size_bytes: 2048576
    checksum: "sha256:123abc..."
    metadata: {"camera_id": "front", "weather": "sunny"}
```

## 版本兼容性管理

### 向前兼容策略

```yaml
# compatibility/dataindex_compatibility.yaml (DataIndexHub)
compatibility_matrix:
  spec_repo_versions:
    "v1.0.0":
      compatible_dataindex_versions: ["v1.0.0", "v1.0.1"]
      breaking_changes: []
      
    "v1.1.0": 
      compatible_dataindex_versions: ["v1.1.0", "v1.1.1"]
      breaking_changes:
        - "changed index schema for object_array channel"
      migration_guide: "docs/migration/v1.0-to-v1.1.md"

# 自动化兼容性检查
version_check:
  enable_automatic_check: true
  fail_on_incompatible: true
  notification_channels: ["slack", "email"]
```

## API设计

### 数据索引查询API

```python
# DataIndexHub API示例
from dataindex_client import DataIndexClient

client = DataIndexClient(base_url="https://dataindex-api.company.com")

# 根据Bundle获取数据集
dataset = client.get_dataset(
    bundle_name="foundational_model",
    bundle_version="v1.0.0-2025.25"
)

# 获取特定时间范围的数据
files = client.list_files(
    bundle_name="foundational_model",
    bundle_version="v1.0.0-2025.25",
    channel="image_original",
    start_time="2025-06-01T00:00:00Z",
    end_time="2025-06-02T00:00:00Z"
)

# 流式数据加载
for batch in client.stream_data(
    bundle_name="foundational_model", 
    bundle_version="v1.0.0-2025.25",
    batch_size=1000
):
    process_batch(batch)
```

## 监控和告警

### 数据完整性监控

```yaml
# monitoring/data_integrity.yaml
monitoring:
  bundle_completeness:
    check_interval: "1h"
    alert_on_missing_files: true
    alert_threshold: 0.99  # 99%完整性阈值
    
  sync_status:
    check_dataspec_updates: true
    max_sync_delay: "30min"
    alert_on_sync_failure: true
    
  storage_health:
    check_storage_accessibility: true
    verify_checksums: true
    alert_on_corruption: true

alerts:
  channels: ["slack://data-ops", "pagerduty://data-critical"]
  escalation_policy: "data-team-escalation"
```

## 实施计划

### Phase 1: 基础架构 (Week 1-2)
- [ ] 创建DataIndexHub仓库
- [ ] 设置基础分支结构
- [ ] 实现Bundle解析器
- [ ] 建立基本的CI/CD流程

### Phase 2: 核心功能 (Week 3-4)  
- [ ] 实现数据索引生成器
- [ ] 建立两仓库触发机制
- [ ] 实现数据索引API
- [ ] 添加完整性验证

### Phase 3: 增强功能 (Week 5-6)
- [ ] 实现数据流式加载
- [ ] 添加监控和告警
- [ ] 实现版本兼容性检查
- [ ] 性能优化和缓存

### Phase 4: 生产部署 (Week 7-8)
- [ ] 生产环境部署
- [ ] 数据迁移和验证
- [ ] 用户培训和文档
- [ ] 监控数据质量 