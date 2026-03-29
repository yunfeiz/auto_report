# AGENTS.md - Kimi Agent Report Generator

> 本文档面向 AI 编程助手，介绍项目架构、开发规范和注意事项。

## 项目概述

Kimi Agent Report Generator 是一个基于 Kimi AI Agent 的智能报告生成工具，核心功能是**提取模板 PDF 的视觉版式规范**，然后将**新报告的内容**按照该版式重新排版生成专业文档。

### 核心价值
- **版式继承**：自动提取模板的配色、字体、边距、页眉页脚等视觉规范
- **内容替换**：将新报告内容按模板风格重新排版
- **多格式输出**：支持 PDF、Word (DOCX)、PPT、Excel 等格式

## 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Python 3.8+ |
| 核心依赖 | `requests` (API 模式必需) |
| 可选依赖 | `reportlab` (本地 PDF 生成)、`python-docx` (Word 生成) |
| 外部工具 | Kimi Code CLI (推荐用于本地生成) |
| AI 服务 | Moonshot API (kimi-k2.5 模型) |

## 项目结构

```
report_generate/
├── kimi_report_generator_advanced.py   # 主模块（核心代码）
├── example_batch.py                     # 批量处理示例脚本
├── README.md                            # 用户文档（中文）
├── AGENTS.md                            # 本文件
├── template.pdf                         # 示例模板文件
└── 20260319/                            # 示例数据目录（期货研报 PDF）
```

### 文件说明

- **`kimi_report_generator_advanced.py`** (约 400 行)
  - 包含完整的报告生成逻辑
  - 定义 `ReportConfig` 配置类
  - 实现 `KimiCLIAgent` (CLI 模式) 和 `KimiAPIAgent` (API 模式)
  - 提供 `generate_report()` 便捷函数
  - 支持命令行参数解析

- **`example_batch.py`** (约 40 行)
  - 演示如何批量生成季度报告
  - 展示从模板 + 数据文件生成多份报告的流程

## 架构设计

### 双模式架构

```
┌─────────────────────────────────────────────────────────────┐
│                    generate_report()                         │
│                     (统一入口函数)                           │
└───────────────────────┬─────────────────────────────────────┘
                        │
          ┌─────────────┴─────────────┐
          │                           │
          ▼                           ▼
┌──────────────────┐        ┌──────────────────┐
│   KimiCLIAgent   │        │  KimiAPIAgent    │
│   (本地 CLI 模式) │        │   (云端 API 模式) │
└────────┬─────────┘        └────────┬─────────┘
         │                           │
         ▼                           ▼
┌──────────────────┐        ┌──────────────────┐
│ 调用 `kimi` 命令  │        │ HTTP API 请求     │
│ 进入 Agent 模式   │        │ (文件上传+对话)   │
└────────┬─────────┘        └────────┬─────────┘
         │                           │
         └───────────┬───────────────┘
                     ▼
         ┌──────────────────────┐
         │   生成最终报告文件    │
         │ (PDF/DOCX/PPTX/XLSX) │
         └──────────────────────┘
```

### 核心类说明

#### `ReportConfig` (Dataclass)
配置数据类，包含：
- `template_pdf`: 模板文件路径（视觉规范来源）
- `content_pdf`: 内容文件路径（数据/文字来源）
- `output_file`: 输出文件路径
- `output_format`: 输出格式 (pdf/docx/pptx/xlsx)
- `company_name`: 公司名称（用于页眉页脚）
- `title`: 报告标题
- `preserve_charts`: 是否保留原报告中的图表描述

#### `KimiCLIAgent`
- 通过子进程调用本地 `kimi` 命令
- 构建 Agent 提示词，通过 stdin 发送
- 支持生成本地 PDF/Word 文件
- 超时时间：10 分钟

#### `KimiAPIAgent`
- 使用 Moonshot HTTP API
- 需要 `KIMI_API_KEY` 环境变量或构造函数传入
- 流程：上传文件 → 获取文件内容 → 请求 AI 生成 Python 代码 → 执行代码生成 PDF
- 适用于没有安装 CLI 的环境

## 使用方法

### 命令行使用

```bash
# 基础用法
python kimi_report_generator_advanced.py template.pdf content.pdf -o output.pdf

# 指定格式和公司名
python kimi_report_generator_advanced.py template.pdf content.pdf \
    -o report.docx \
    -f docx \
    --company "Moonshot AI" \
    --title "2026年度报告"

# 强制使用 API 模式
python kimi_report_generator_advanced.py template.pdf content.pdf \
    -o output.pdf \
    -m api
```

### Python API 使用

```python
from kimi_report_generator_advanced import generate_report, ReportConfig

# 简单调用
result = generate_report(
    template="template.pdf",
    content="data.pdf",
    output="final.pdf",
    company_name="Moonshot AI"
)

# 使用 CLI Agent
from kimi_report_generator_advanced import KimiCLIAgent
agent = KimiCLIAgent()
config = ReportConfig(
    template_pdf="template.pdf",
    content_pdf="content.pdf",
    output_file="output.pdf"
)
agent.generate(config)
```

## 开发规范

### 代码风格
- 使用 Python 3 类型注解（`typing` 模块）
- 使用 `dataclass` 定义配置类
- 文档字符串使用中文（与项目整体一致）
- 字符串使用双引号为主

### 注释规范
- 模块级文档字符串使用 `"""..."""`
- 类和方法需要包含功能说明
- 关键算法步骤添加行内注释

### 错误处理
- CLI 未安装时给出友好提示和安装指引
- API 调用失败时抛出异常并打印详细信息
- 文件操作检查文件是否存在
- 子进程调用设置超时（10 分钟）

## 测试策略

当前项目**无自动化测试**。测试方式为：

1. **手动测试**：运行示例脚本验证功能
   ```bash
   python example_batch.py
   ```

2. **命令行测试**：使用实际 PDF 文件测试
   ```bash
   python kimi_report_generator_advanced.py template.pdf content.pdf -o test.pdf
   ```

3. **API 模式测试**：
   ```bash
   export KIMI_API_KEY="your-key"
   python kimi_report_generator_advanced.py template.pdf content.pdf -o test.pdf -m api
   ```

## 部署注意事项

### 环境要求
- Python 3.8+
- 网络连接（用于 API 模式或 CLI Agent）

### CLI 模式部署
1. 安装 Kimi Code CLI:
   ```bash
   curl -sSL https://www.kimi.com/cli/install.sh | bash
   ```
2. 安装 Python 依赖:
   ```bash
   pip install requests
   ```

### API 模式部署
1. 设置环境变量:
   ```bash
   export KIMI_API_KEY="your-api-key"
   ```
2. 安装依赖:
   ```bash
   pip install requests reportlab
   ```

### 限制与注意事项
1. **文件大小**：单文件不超过 100MB（API 限制）
2. **生成时间**：Agent 模式通常需要 2-5 分钟
3. **中文支持**：自动处理中文字体（使用系统自带 SimHei/Microsoft YaHei）
4. **隐私**：敏感文档建议使用本地 CLI 模式

## 扩展开发

### 添加新输出格式
在 `ReportConfig` 的 `output_format` Literal 类型中添加新格式，并在 Agent 提示词中更新说明。

### 自定义 Agent 提示词
修改 `KimiCLIAgent._create_agent_prompt()` 方法，调整生成报告的具体要求。

### 添加批量处理功能
参考 `example_batch.py` 的实现，可以扩展更复杂的批量处理逻辑（如并行处理、进度报告等）。

## 相关资源

- [Kimi Code CLI 介绍](https://www.kimi.com/resources/kimi-code-introduction)
- [Moonshot API 文档](https://platform.moonshot.cn/docs)
