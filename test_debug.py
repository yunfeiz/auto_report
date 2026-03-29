#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug 测试脚本 - 使用详细日志输出
"""

import os
import sys
from pathlib import Path

# 确保使用最新的代码
import importlib
import kimi_report_generator_advanced
importlib.reload(kimi_report_generator_advanced)

from kimi_report_generator_advanced import generate_report

# 获取所有 PDF 文件
pdf_files = sorted([str(p) for p in Path('20260319').glob('*.pdf')])
print(f"[INFO] 找到 {len(pdf_files)} 个 PDF 文件")

# 测试模式：使用前5个文件，启用 debug
test_files = pdf_files[:5]
print(f"[INFO] 测试模式：使用 {len(test_files)} 个文件，启用 DEBUG")
for i, f in enumerate(test_files, 1):
    print(f"  [{i}] {os.path.basename(f)}")

# 运行测试 - 启用 debug
try:
    result = generate_report(
        template="template.pdf",
        content=test_files[0],
        output="test_debug_report.pdf",
        output_format="pdf",
        mode="api",
        reports_folder=None,
        content_pdfs=test_files,
        max_workers=8,  # 使用 8 个线程
        debug=True,     # 启用详细调试
        company_name="测试公司",
        title="Debug 测试报告"
    )
    print(f"\n[OK] 报告已生成: {result}")
except Exception as e:
    print(f"\n[ERROR] 错误: {e}")
    import traceback
    traceback.print_exc()
