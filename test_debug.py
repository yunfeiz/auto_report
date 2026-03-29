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

# 测试模式：由于 API 处理大文件可能超时，只用 2 个文件测试
test_files = pdf_files[:2]
print(f"[INFO] 测试模式：使用 {len(test_files)} 个文件，启用 DEBUG")
for i, f in enumerate(test_files, 1):
    print(f"  [{i}] {os.path.basename(f)}")

try:
    # 单文件模式测试（避免并发限制）
    result = generate_report(
        template="template.pdf",
        content=test_files[0],
        output="test_debug_report.pdf",
        output_format="pdf",
        mode="api",
        # 不传递 content_pdfs，单文件模式
        max_workers=1,  # 单线程
        debug=True,     # 启用详细调试
        company_name="测试公司",
        title="Debug 测试报告"
    )
    print(f"\n[OK] 报告已生成: {result}")
except Exception as e:
    print(f"\n[ERROR] 错误: {e}")
    import traceback
    traceback.print_exc()
