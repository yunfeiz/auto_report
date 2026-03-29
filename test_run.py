#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试脚本 - 使用单个文件测试报告生成"""

import os
from pathlib import Path
from kimi_report_generator_advanced import generate_report

# 获取第一个 PDF 文件
pdf_files = sorted([str(p) for p in Path('20260319').glob('*.pdf')])
if not pdf_files:
    print("错误: 未找到 PDF 文件")
    exit(1)

print(f"找到 {len(pdf_files)} 个 PDF 文件")
print(f"使用第一个文件: {pdf_files[0]}")

# 运行测试
try:
    result = generate_report(
        template="template.pdf",
        content=pdf_files[0],
        output="test_output.pdf",
        output_format="pdf",
        mode="api",
        company_name="测试公司",
        title="测试报告"
    )
    print(f"\n生成成功: {result}")
except Exception as e:
    print(f"\n错误: {e}")
    import traceback
    traceback.print_exc()
