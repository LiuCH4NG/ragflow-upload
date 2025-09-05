# RAGFlow 文件批量上传工具

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

一个专门为 RAGFlow 知识库设计的文件批量上传工具。它可以将指定目录下的所有文件自动上传到 RAGFlow 知识库中，并支持自动启动文档解析功能。

## 实现原理
基于 RAGFlow SDK https://ragflow.io/docs/v0.20.4/python_api_reference

## 🚀 功能特性

- **批量上传**: 支持将指定目录下的所有文件一次性上传到 RAGFlow 知识库
- **智能去重**: 自动跳过已存在的文件，避免重复上传
- **格式支持**: 支持多种文件格式，包括文本文件、Office文档和PDF等
- **分批处理**: 支持自定义批次大小，避免大文件上传时的网络问题
- **详细日志**: 完整的日志记录系统，自动生成时间戳命名的日志文件
- **自动知识库管理**: 如果指定的知识库不存在，会自动创建新的知识库
- **解析控制**: 可选择是否在上传后自动启动文档解析
- **实时进度**: 显示上传进度、耗时统计和详细的错误信息
- **🆕 配置文件支持**: 通过.env文件保存配置，避免重复输入
- **🆕 交互式输入**: 友好的命令行交互界面，简化操作流程
- **🆕 多种运行模式**: 支持交互式、命令行、混合模式等多种使用方式
- **🆕 配置优先级**: 灵活的配置管理，命令行参数优先于.env文件

## 📦 安装

### 使用 UV (推荐)

```bash
# 克隆项目
git clone <repository-url>
cd ragflow-upload

# 使用 UV 安装依赖
uv sync
```

### 使用 PIP

```bash
# 安装依赖
pip install -r requirements.txt
```

### 手动安装

```bash
pip install ragflow-sdk loguru
```

## 🔧 配置要求

- Python 3.11 或更高版本
- RAGFlow 服务器 (版本 0.14.0 或更高)
- 有效的 RAGFlow API 密钥
- 网络连接到 RAGFlow 服务器

## 📖 使用方法

## 📖 使用方法

### 🔧 首次配置

在使用之前，建议先创建配置文件：

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件，填入你的信息
# RAGFLOW_API_KEY=your-api-key-here
# RAGFLOW_BASE_URL=http://localhost:9380
# BATCH_SIZE=5
# AUTO_PARSE=true
# SKIP_EXISTING=false
```

### 🚀 快速开始（推荐）

#### 1. 交互式模式 - 最简单
```bash
python ragflow_uploader.py
```
脚本会引导你输入必要的信息，无需记住复杂的命令行参数。

#### 2. 使用配置文件 - 最便捷
```bash
python ragflow_uploader.py \
  --dataset_name "my_knowledge_base" \
  --directory "/path/to/documents"
```
如果已在.env文件中配置了API密钥和服务器地址。

#### 3. 完整命令行模式 - 最灵活
```bash
python ragflow_uploader.py \
  --api_key "your-api-key" \
  --base_url "http://localhost:9380" \
  --dataset_name "my_knowledge_base" \
  --directory "/path/to/documents"
```

### 🔧 高级用法

```bash
# 自定义批次大小，不自动解析
python ragflow_uploader.py \
  --api_key "your-api-key" \
  --base_url "http://localhost:9380" \
  --dataset_name "my_knowledge_base" \
  --directory "/path/to/documents" \
  --batch_size 3 \
  --no_parse

# 跳过已存在的文件，自定义日志文件
python ragflow_uploader.py \
  --api_key "your-api-key" \
  --base_url "http://localhost:9380" \
  --dataset_name "my_knowledge_base" \
  --directory "/path/to/documents" \
  --skip_existing \
  --log_file "/path/to/custom.log"

# 强制交互模式（忽略任何配置文件）
python ragflow_uploader.py -i
```

## ⚙️ 配置说明

### 配置优先级

脚本的配置优先级如下（从高到低）：
1. **命令行参数** - 具有最高优先级，会覆盖其他配置
2. **.env文件** - 保存默认配置，避免每次输入
3. **交互式输入** - 当缺少必要配置时的提示输入

### 参数说明

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `--api_key` | 字符串 | ❌ | RAGFlow API 密钥（命令行优先） |
| `--base_url` | 字符串 | ❌ | RAGFlow 服务器地址（命令行优先） |
| `--dataset_name` | 字符串 | ❌ | 知识库名称（命令行或交互输入） |
| `--directory` | 字符串 | ❌ | 要上传文件的目录路径（命令行或交互输入） |
| `--batch_size` | 数字 | ❌ | 每批上传的文件数量（默认：5） |
| `--no_parse` | 标志 | ❌ | 上传后不自动启动文档解析 |
| `--skip_existing` | 标志 | ❌ | 跳过已存在的文件 |
| `--log_file` | 字符串 | ❌ | 指定日志文件路径（默认自动生成） |
| `--interactive` | 标志 | ❌ | 强制使用交互式输入模式 (`-i`)|

### .env 配置文件

在项目根目录创建`.env`文件：

```ini
# RAGFlow API密钥
RAGFLOW_API_KEY=your-api-key-here

# RAGFlow服务器地址
RAGFLOW_BASE_URL=http://localhost:9380

# 每批上传的文件数量（可选，默认：5）
BATCH_SIZE=5

# 是否在上传后自动启动文档解析（可选，默认：true）
AUTO_PARSE=true

# 是否跳过已存在的文件（可选，默认：false）
SKIP_EXISTING=false

# 日志文件路径（可选，如果不指定将自动生成）
LOG_FILE=
```

## 📋 支持的文件格式

### 文本文件
- `.txt` - 纯文本文件
- `.md` - Markdown 文件
- `.json` - JSON 文件
- `.xml` - XML 文件
- `.html` - HTML 文件
- `.htm` - HTML 文件

### Office 文档
- `.doc` - Word 文档
- `.docx` - Word 文档
- `.ppt` - PowerPoint 演示文稿
- `.pptx` - PowerPoint 演示文稿
- `.xls` - Excel 电子表格
- `.xlsx` - Excel 电子表格

### 其他格式
- `.pdf` - PDF 文档
- `.csv` - CSV 文件
- `.rtf` - RTF 文件

## 打包可执行文件

使用[pyfuze](https://github.com/TanixLu/pyfuze)

```bash
uvx pyfuze ragflow_uploader.py --mode bundle --output-name RAG_upload_tool  --pyproject pyproject.toml --include .env.example
```

## 📊 日志系统

### 自动日志生成

如果不指定 `--log_file` 参数，系统会自动生成带有时间戳的日志文件，格式为：
```
ragflow_upload_YYYYMMDD_HHMMSS.log
```

### 日志内容

- **程序启动信息**: API密钥（脱敏显示）、服务器地址、知识库名称等
- **文件扫描结果**: 目录扫描、文件过滤、支持格式检查等
- **上传进度**: 每个文件的上传状态、耗时统计
- **错误信息**: 详细的错误信息和堆栈跟踪
- **总结统计**: 成功/失败文件数量、总耗时等

### 日志级别

- `INFO`: 主要流程信息
- `SUCCESS`: 成功操作信息
- `ERROR`: 错误信息
- `DEBUG`: 调试详细信息

## 🔧 故障排除

### 模块导入错误

如果遇到 `ModuleNotFoundError: No module named 'ragflows'` 错误：

**Linux/macOS:**
```bash
export PYTHONPATH=.
python ragflow_uploader.py [参数]
```

**Windows (CMD):**
```cmd
set PYTHONPATH=.
python ragflow_uploader.py [参数]
```

**Windows (PowerShell):**
```powershell
$env:PYTHONPATH = "."
python ragflow_uploader.py [参数]
```

### 常见问题

1. **连接超时**
   - 检查 RAGFlow 服务器是否正常运行
   - 验证网络连接和防火墙设置
   - 确认 API 密钥是否有效

2. **上传失败**
   - 检查文件格式是否受支持
   - 确认文件大小未超过服务器限制
   - 查看详细日志了解具体错误原因

3. **权限问题**
   - 确认 API 密钥具有足够的权限
   - 检查知识库的访问权限设置

## 🏗️ 项目结构

```
ragflow-upload/
├── ragflow_uploader.py      # 主上传脚本
├── requirements.txt         # Python 依赖
├── pyproject.toml          # 项目配置 (UV)
├── .env.example           # 环境变量模板
├── README.md               # 本文件
├── LICENSE                 # 许可证
├── .gitignore              # Git 忽略规则
└── .venv/                  # 虚拟环境 (自动生成)
```

## 🔄 工作流程

1. **配置加载**: 按优先级加载命令行参数、.env文件和交互式输入
2. **初始化**: 连接到 RAGFlow 服务器，配置日志系统
3. **知识库检查**: 获取指定知识库，不存在则自动创建
4. **文件扫描**: 扫描指定目录，过滤支持的文件格式
5. **去重检查**: 比对现有文档，标记需要跳过的文件
6. **批量上传**: 按设定批次大小上传文件
7. **解析启动**: 可选择是否自动启动文档解析
8. **总结报告**: 生成详细的操作总结和统计信息

## 📝 开发说明

### 技术栈

- **Python 3.11+**: 主要编程语言
- **ragflow-sdk**: 与 RAGFlow 服务器交互的 SDK
- **python-dotenv**: 环境变量管理
- **loguru**: 高性能日志库
- **argparse**: 命令行参数解析
- **pathlib**: 文件路径处理

### 代码结构

- `RAGFlowUploader`: 主要的上传器类
  - `__init__()`: 初始化连接和日志配置
  - `get_or_create_dataset()`: 获取或创建知识库
  - `get_existing_documents()`: 获取现有文档列表
  - `get_files_from_directory()`: 扫描目录文件
  - `upload_files()`: 批量上传文件
  - `start_parsing()`: 启动文档解析

## 📄 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目。

## 🔗 相关链接

- [RAGFlow 官方文档](https://ragflow.io/docs/v0.20.4/)
- [ragflow-sdk 文档](https://ragflow.io/docs/v0.20.4/python_api_reference)
---

**注意**: 请确保在使用前仔细阅读并理解所有配置参数和使用说明。如有疑问，请参考相关文档或联系技术支持。