# Kimi Agent Report Generator

基于 Kimi AI Agent 的智能报告生成工具，支持以模板 PDF 的版式生成包含新内容的专业报告。

## 🚀 快速开始

### 方式一：使用 Kimi Code CLI（推荐，支持生成 Office/PDF）

```bash
# 1. 安装依赖（仅需 Python 3.8+）
pip install requests

# 2. 确保已安装 Kimi Code CLI
curl -sSL https://www.kimi.com/cli/install.sh | bash

# 3. 运行生成
python kimi_report_generator_advanced.py template.pdf report.pdf -o output.pdf
```

### 方式二：使用 API 模式（无需安装 CLI）

```bash
# 设置 API Key
export KIMI_API_KEY="your-api-key-here"

# 运行生成
python kimi_report_generator_advanced.py template.pdf report.pdf -o output.pdf -m api
```

## 📋 功能特性

- ✅ **版式继承**：自动提取模板的配色、字体、边距、页眉页脚
- ✅ **内容替换**：将新报告内容按模板风格重新排版
- ✅ **多格式输出**：PDF、Word (DOCX)、PPT、Excel
- ✅ **智能图表**：保留原报告中的表格和数据描述
- ✅ **批量处理**：支持命令行参数和 Python API 调用

## 🛠️ 命令行参数

```
python kimi_report_generator_advanced.py   template.pdf \           # 模板文件（定义视觉风格）
  report.pdf \             # 内容文件（提供数据文字）
  -o output.pdf \          # 输出文件路径
  -f pdf \                 # 输出格式: pdf/docx/pptx/xlsx
  -m auto \                # 模式: auto/cli/api
  --company "ABC公司" \     # 公司名称（页眉页脚）
  --title "2026年度报告"    # 报告标题
```

## 💻 Python API 使用

```python
from kimi_report_generator_advanced import generate_report, ReportConfig

# 简单调用
result = generate_report(
    template="brand_template.pdf",
    content="q4_data.pdf",
    output="q4_report_final.pdf",
    company_name="Moonshot AI",
    title="2026年Q4财务报告"
)

# 高级配置
config = ReportConfig(
    template_pdf="template.pdf",
    content_pdf="content.pdf",
    output_file="final.pdf",
    output_format="pdf",
    company_name="Moonshot AI",
    preserve_charts=True
)

# 使用 CLI Agent（生成本地文件）
from kimi_report_generator_advanced import KimiCLIAgent
agent = KimiCLIAgent()
agent.generate(config)

# 使用 API（云端处理）
from kimi_report_generator_advanced import KimiAPIAgent
agent = KimiAPIAgent(api_key="your-key")
agent.generate(config)
```

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `kimi_report_generator.py` | 基础版本，仅 API 模式 |
| `kimi_report_generator_advanced.py` | 完整版本，支持 CLI+API |
| `example_batch.py` | 批量处理示例 |

## 🔧 模板设计建议

为获得最佳效果，建议模板 PDF 包含：

1. **封面页**：公司 Logo、报告标题、日期
2. **目录页**：章节索引（可选）
3. **正文页**：
   - 清晰的标题层级（H1-H4）
   - 标准的正文段落
   - 图表占位区域
4. **页眉页脚**：公司名、页码、版权信息

## ⚠️ 注意事项

1. **文件大小**：单文件不超过 100MB（API 限制）
2. **生成时间**：Agent 模式通常需要 2-5 分钟
3. **中文支持**：自动处理中文字体（使用系统自带字体）
4. **隐私**：敏感文档建议使用本地 CLI 模式

## 📚 依赖安装

```bash
# 基础依赖
pip install requests

# API 模式额外依赖（如需生成本地 PDF）
pip install reportlab

# 或 Word 生成
pip install python-docx
```
