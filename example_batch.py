#!/usr/bin/env python3
"""
批量报告生成示例
场景：有多个季度的数据报告，需要使用统一模板生成
"""

import os
from pathlib import Path
from kimi_report_generator_advanced import generate_report

# 配置
template = "templates/annual_report_template.pdf"
quarters = ["Q1", "Q2", "Q3", "Q4"]
output_dir = "output"

os.makedirs(output_dir, exist_ok=True)

for q in quarters:
    content_file = f"data/{q}_data.pdf"
    output_file = f"{output_dir}/2026_{q}_Report.pdf"

    print(f"\n🔄 正在生成 {q} 报告...")

    try:
        result = generate_report(
            template=template,
            content=content_file,
            output=output_file,
            format="pdf",
            company_name="Moonshot AI",
            title=f"2026年{q}度报告"
        )
        print(f"✅ 完成: {result}")
    except Exception as e:
        print(f"❌ {q} 失败: {e}")

print("\n🎉 批量生成完成！")

# 进阶：合并为一份年度报告（可选）
print("\n📎 如需合并所有季度报告，可使用 PyPDF2:")
print("   pip install PyPDF2")
print("   python merge_reports.py")
