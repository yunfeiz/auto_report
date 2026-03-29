#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试多轮处理报告生成"""

import os
from pathlib import Path
from kimi_report_generator_advanced import generate_report

# 获取所有 PDF 文件
pdf_files = sorted([str(p) for p in Path('20260319').glob('*.pdf')])
print(f"找到 {len(pdf_files)} 个 PDF 文件")

# 先测试前3个文件，避免处理时间过长
test_files = pdf_files[:3]
print(f"测试模式：使用 {len(test_files)} 个文件")
for i, f in enumerate(test_files, 1):
    print(f"  [{i}] {os.path.basename(f)}")

# 运行测试
try:
    result = generate_report(
        template="template.pdf",
        content=test_files[0],  # 第一个文件作为默认内容
        output="test_multi_report.pdf",
        output_format="pdf",
        mode="api",
        reports_folder=None,  # 不使用文件夹模式，手动指定
        content_pdfs=test_files,  # 使用多文件列表
        company_name="测试公司",
        title="多轮处理测试报告"
    )
    print(f"\n[OK] 报告已生成: {result}")
except Exception as e:
    print(f"\n[ERROR] 错误: {e}")
    import traceback
    traceback.print_exc()
