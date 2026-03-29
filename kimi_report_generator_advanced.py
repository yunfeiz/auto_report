#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kimi Agent Report Generator - Advanced Version
支持两种模式：
1. API Mode: 使用标准 Chat Completions + 文件解析
2. CLI Mode: 调用本地 Kimi Code CLI Agent（推荐，支持生成 Office/PDF 文件）
"""

import os
import sys
import json
import time
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Literal
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ReportConfig:
    template_pdf: str      # 模板文件路径（视觉规范来源）
    content_pdf: str       # 内容文件路径（数据/文字来源）
    output_file: str       # 输出文件路径
    output_format: Literal["pdf", "docx", "pptx", "xlsx"] = "pdf"
    company_name: str = "" # 公司名称（用于页眉页脚）
    title: str = ""        # 报告标题（如为空则自动提取）
    preserve_charts: bool = True  # 是否保留原报告中的图表描述
    content_pdfs: list = None  # 多个内容文件路径列表（用于批量综合报告）


class KimiCLIAgent:
    """
    通过 Kimi Code CLI 的 Agent 模式生成报告
    优势：支持端到端生成 PDF/Word/PPT 文件，格式控制更精确
    """

    def __init__(self, working_dir: Optional[str] = None):
        self.working_dir = working_dir or os.getcwd()
        self._check_cli()

    def _check_cli(self):
        """检查 Kimi CLI 是否安装"""
        try:
            result = subprocess.run(
                ["kimi", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("Kimi CLI 未正确安装")
            print(f"✅ Kimi CLI 已安装: {result.stdout.strip()}")
        except FileNotFoundError:
            print("""
[ERROR] 未找到 Kimi Code CLI

请安装 Kimi Code CLI:
    curl -sSL https://www.kimi.com/cli/install.sh | bash

或访问: https://www.kimi.com/resources/kimi-code-introduction
            """)
            sys.exit(1)

    def generate(self, config: ReportConfig) -> str:
        """
        使用 Kimi Agent 生成报告

        原理：
        1. 构建详细的 Agent Prompt，描述模板样式和内容需求
        2. 调用 `kimi` 命令进入 Agent 模式
        3. Agent 自动读取两个 PDF 并生成新文件
        """

        # 构建 Agent 指令文件（因为直接命令行传递长文本容易出问题）
        prompt_file = self._create_agent_prompt(config)

        print(f"[INFO] 启动 Kimi Agent 生成报告...")
        print(f"   模板: {config.template_pdf}")
        # 显示所有内容文件
        if config.content_pdfs and len(config.content_pdfs) > 1:
            print(f"   内容文件数: {len(config.content_pdfs)}")
            for i, pdf in enumerate(config.content_pdfs[:5], 1):
                print(f"      [{i}] {pdf}")
            if len(config.content_pdfs) > 5:
                print(f"      ... 等共 {len(config.content_pdfs)} 个文件")
        else:
            print(f"   内容: {config.content_pdf}")
        print(f"   输出: {config.output_file}")

        # 方式1：使用非交互式命令直接执行（如果 CLI 支持）
        # cmd = f'kimi "$(cat {prompt_file})"'

        # 方式2：创建自动化脚本供 Agent 执行
        agent_script = self._create_agent_script(config)

        # 执行 Agent 任务
        try:
            # 切换到工作目录执行
            env = os.environ.copy()
            env["KIMI_AUTOSTART_AGENT"] = "true"  # 假设的环境变量，强制进入 Agent 模式

            process = subprocess.Popen(
                ["kimi"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.working_dir,
                env=env
            )

            # 发送指令给 Agent
            stdout, stderr = process.communicate(
                input=agent_script,
                timeout=600  # 10分钟超时
            )

            print("[INFO] Agent 输出:")
            print(stdout)

            if process.returncode != 0:
                print(f"⚠️ 警告: {stderr}")

            # 检查文件是否生成
            if os.path.exists(config.output_file):
                print(f"[OK] 成功生成: {config.output_file}")
                return config.output_file
            else:
                print("[WARN] 文件可能生成在工作目录的其他位置，请检查")
                return ""

        except subprocess.TimeoutExpired:
            print("[ERROR] 生成超时（10分钟）")
            process.kill()
            raise

    def _create_agent_prompt(self, config: ReportConfig) -> str:
        """创建给 Agent 的详细指令"""

        abs_template = os.path.abspath(config.template_pdf)
        abs_output = os.path.abspath(config.output_file)

        # 处理单个或多个内容文件
        if config.content_pdfs and len(config.content_pdfs) > 1:
            # 多个内容文件 - 综合报告模式
            content_files = [os.path.abspath(pdf) for pdf in config.content_pdfs]
            content_section = "【步骤 2：提取内容】\n需要读取并综合分析以下所有报告文件：\n"
            for i, pdf_path in enumerate(content_files, 1):
                content_section += f"  [{i}] {pdf_path}\n"
            content_section += "\n提取每个报告的核心内容、关键数据、分析结论，进行整合汇总。"
            is_batch = True
        else:
            # 单个内容文件
            abs_content = os.path.abspath(config.content_pdf)
            content_section = f"【步骤 2：提取内容】\n读取文件: {abs_content}\n提取所有章节、段落、数据表格、图表说明文字"
            is_batch = False

        batch_instruction = """
【综合报告要求】
这是一份综合报告，需要：
1. 分析各报告的共同点和差异点
2. 提取关键趋势和核心洞察
3. 按主题或时间顺序组织内容
4. 生成执行摘要（Executive Summary）
5. 在适当位置注明数据来源""" if is_batch else ""

        prompt = f"""请基于模板 PDF 生成专业报告：

【步骤 1：分析模板】
读取文件: {abs_template}
提取以下设计规范：
- 配色方案（主色、强调色）
- 字体层级（标题H1-H4的字号、正文字号）
- 页边距和布局（分栏、留白）
- 页眉页脚样式（公司Logo位置、页码格式）
- 封面设计（背景、标题排版方式）

{content_section}

【步骤 3：生成新报告】
使用 {config.output_format.upper()} 格式，严格遵循模板的视觉规范。{batch_instruction if is_batch else "但使用新报告的内容。"}
要求：
1. 继承模板的专业商务风格
2. 完整保留所有数据、分析结论
3. {f'公司名称: {config.company_name}' if config.company_name else '保留原模板的页眉公司信息'}
4. 添加适当的分页，确保图表不被截断
5. 生成文件保存到: {abs_output}

如果内容较多，请自动添加目录页。
"""
        return prompt

    def _create_agent_script(self, config: ReportConfig) -> str:
        """
        创建 Agent 可执行的脚本指令
        这种格式更适合 CLI Agent 解析
        """
        # 处理单个或多个内容文件
        if config.content_pdfs and len(config.content_pdfs) > 1:
            # 多个内容文件
            content_list = "\n".join([f"  - {pdf}" for pdf in config.content_pdfs])
            content_instruction = f"""然后，读取以下所有报告文件的内容并进行综合分析：
{content_list}

请整合这些报告的核心观点和数据，生成一份综合报告。"""
        else:
            content_instruction = f"然后，读取 {config.content_pdf} 的内容。"

        script = f"""/init
请帮我基于模板生成报告。

首先，分析模板文件 {config.template_pdf} 的视觉设计规范。
{content_instruction}
最后，生成一个格式与模板一致、内容为新报告的专业文档，保存为 {config.output_file}。

具体要求：
1. 字体、颜色、边距必须匹配模板
2. 保留所有图表和数据
3. 输出格式: {config.output_format}
4. 生成后可执行预览

/yolo
"""
        return script


def _load_api_key_from_file() -> Optional[str]:
    """从本地配置文件加载 API Key
    
    查找顺序：
    1. 当前目录的 .kimi_api_key
    2. 用户主目录的 .kimi_api_key
    3. 用户主目录的 .config/kimi/api_key
    
    支持文件内注释（以 # 开头的行会被忽略）
    """
    paths_to_check = [
        Path(".kimi_api_key"),  # 当前目录
        Path.home() / ".kimi_api_key",  # 用户主目录
        Path.home() / ".config" / "kimi" / "api_key",  # 配置目录
    ]
    
    for path in paths_to_check:
        if path.exists():
            try:
                content = path.read_text(encoding='utf-8')
                # 查找非注释行且以 sk- 开头的 API Key
                for line in content.splitlines():
                    line = line.strip()
                    if line and not line.startswith('#') and line.startswith('sk-'):
                        print(f"[OK] 已从 {path} 加载 API Key")
                        return line
            except Exception:
                continue
    return None


class KimiAPIAgent:
    """
    使用 Kimi HTTP API 的实现（无需本地 CLI）
    采用多轮处理架构：
    1. 提取模板版式规范
    2. 并行提取各报告核心内容
    3. 汇总生成最终报告
    """

    def __init__(self, api_key: Optional[str] = None, max_workers: int = 3, debug: bool = False):
        # 限制最大并发数（Moonshot API 限制为 3）
        max_workers = min(max_workers, 3)
        # 优先级：构造函数参数 > 环境变量 > 本地配置文件
        self.api_key = api_key or os.getenv("KIMI_API_KEY") or _load_api_key_from_file()
        if not self.api_key:
            raise ValueError(
                "未找到 API Key。请通过以下方式之一提供：\n"
                "1. 设置 KIMI_API_KEY 环境变量\n"
                "2. 在当前目录创建 .kimi_api_key 文件\n"
                "3. 在用户主目录创建 .kimi_api_key 文件"
            )

        self.base_url = "https://api.moonshot.cn/v1"
        self.max_workers = max_workers  # 并行处理的最大线程数
        self.debug = debug  # 调试模式
        
    def _log(self, message: str, level: str = "INFO"):
        """打印调试日志"""
        if self.debug or level in ["ERROR", "WARN"]:
            print(f"[{level}] {message}")

    def generate(self, config: ReportConfig) -> str:
        """
        多轮处理生成报告
        """
        # 第1轮：提取模板版式规范
        print("[INFO] ===== 第1轮：分析模板版式 =====")
        template_style = self._extract_template_style(config.template_pdf)
        print(f"[OK] 版式规范提取完成")

        # 第2轮：并行提取各报告核心内容
        print("[INFO] ===== 第2轮：提取报告内容 =====")
        content_pdfs = config.content_pdfs if config.content_pdfs else [config.content_pdf]
        
        if len(content_pdfs) == 1:
            # 单文件直接处理
            summaries = [self._extract_report_summary(content_pdfs[0], 1, 1)]
        else:
            # 多文件并行处理
            summaries = self._extract_summaries_parallel(content_pdfs)
        
        # 合并所有内容摘要
        combined_content = self._merge_summaries(summaries)
        print(f"[OK] 内容提取完成，共 {len(summaries)} 份报告")

        # 第3轮：生成最终报告代码
        print("[INFO] ===== 第3轮：生成最终报告 =====")
        code = self._generate_report_code(template_style, combined_content, config)
        
        # 4. 执行代码生成 PDF
        print("[INFO] 执行生成代码...")
        try:
            exec(code, {'__name__': '__main__'})
            print(f"[OK] 生成成功: {config.output_file}")
            return config.output_file
        except Exception as e:
            print(f"[ERROR] 执行失败: {e}")
            print("生成的代码:\n", code[:2000] + "..." if len(code) > 2000 else code)
            raise

    def _extract_template_style(self, template_pdf: str) -> dict:
        """第1轮：提取模板版式规范"""
        import json
        
        self._log(f"开始上传模板文件: {template_pdf}", "DEBUG")
        
        # 上传并获取模板内容
        template_id = self._upload_file(template_pdf)
        self._log(f"模板文件上传成功, file_id: {template_id}", "DEBUG")
        
        template_text = self._get_file_content(template_id)
        self._log(f"模板内容获取成功, 长度: {len(template_text)} 字符", "DEBUG")
        
        # 如果内容太长，分段处理
        content_limit = 3000
        if len(template_text) > content_limit:
            self._log(f"模板内容较长 ({len(template_text)}), 截取前 {content_limit} 字符分析", "DEBUG")
            template_text = template_text[:content_limit]
        
        # 请求 AI 提取版式规范（结构化输出）
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的文档设计分析师。请分析模板PDF并提取版式规范，以JSON格式输出。"
            },
            {
                "role": "user", 
                "content": f"""分析以下PDF模板，提取版式规范。

模板内容（前{content_limit}字符）：
{template_text}

请以JSON格式输出以下信息：
{{
    "page_size": "A4",
    "margins": {{"top": "2cm", "bottom": "2cm", "left": "2cm", "right": "2cm"}},
    "colors": {{"primary": "#000000", "secondary": "#666666", "background": "#FFFFFF"}},
    "fonts": {{"title": "SimHei", "body": "Microsoft YaHei", "size_title": 16, "size_body": 10}},
    "header": "页眉内容和格式",
    "footer": "页脚内容和格式",
    "layout": "单列/双列/其他布局描述"
}}

只输出JSON，不要有其他说明。"""
            }
        ]
        
        self._log("请求 AI 分析模板版式...", "DEBUG")
        result = self._api_call_with_retry(messages, max_retries=3, timeout=60)
        
        content = result['choices'][0]['message']['content']
        self._log(f"AI 响应内容长度: {len(content)} 字符", "DEBUG")
        
        # 提取 JSON
        try:
            # 尝试直接解析
            style = json.loads(content)
            self._log("JSON 解析成功", "DEBUG")
        except json.JSONDecodeError as e:
            self._log(f"直接 JSON 解析失败: {e}, 尝试从代码块提取", "WARN")
            # 从代码块中提取
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()
            style = json.loads(json_str)
            self._log("从代码块提取 JSON 成功", "DEBUG")
        
        return style

    def _extract_summaries_parallel(self, pdf_paths: list) -> list:
        """并行提取多份报告的核心内容（使用信号量限制并发）"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import threading
        import time
        
        summaries = []
        total = len(pdf_paths)
        
        # 使用信号量限制 API 并发数（最大 3，符合 API 限制）
        api_semaphore = threading.Semaphore(self.max_workers)
        completed_count = 0
        completed_lock = threading.Lock()
        last_start_time = [0]  # 记录最后一次 API 调用时间
        time_lock = threading.Lock()
        
        print(f"[INFO] 并行处理 {total} 个文件 (最大并发: {self.max_workers}, 受 API 限制)...")
        
        def process_with_semaphore(pdf_path, idx, total):
            """带信号量的处理函数（带速率限制）"""
            nonlocal completed_count
            
            with api_semaphore:
                # 速率限制：确保每个请求间隔至少 0.5 秒
                with time_lock:
                    elapsed = time.time() - last_start_time[0]
                    if elapsed < 0.5:
                        sleep_time = 0.5 - elapsed
                        self._log(f"速率限制：等待 {sleep_time:.2f} 秒", "DEBUG")
                        time.sleep(sleep_time)
                    last_start_time[0] = time.time()
                
                self._log(f"获取 API 槽位，开始处理 [{idx}/{total}]", "DEBUG")
                try:
                    result = self._extract_report_summary(pdf_path, idx, total)
                    
                    with completed_lock:
                        completed_count += 1
                        current = completed_count
                    
                    print(f"[OK] [{current}/{total}] {os.path.basename(pdf_path)[:40]}... 处理完成")
                    return result
                    
                except Exception as e:
                    with completed_lock:
                        completed_count += 1
                        current = completed_count
                    
                    print(f"[ERROR] [{current}/{total}] {os.path.basename(pdf_path)[:40]}... 失败: {str(e)[:50]}")
                    return f"\n\n===== 报告 [{idx}] =====\n[提取失败: {str(e)[:100]}]\n"
                finally:
                    self._log(f"释放 API 槽位 [{idx}/{total}]", "DEBUG")
        
        with ThreadPoolExecutor(max_workers=total) as executor:  # 线程池可以大，但信号量限制实际并发
            # 提交所有任务
            futures = [
                executor.submit(process_with_semaphore, pdf_path, idx + 1, total)
                for idx, pdf_path in enumerate(pdf_paths)
            ]
            
            # 收集结果（保持顺序）
            summaries = [future.result() for future in futures]
        
        return summaries

    def _extract_report_summary(self, pdf_path: str, idx: int, total: int) -> str:
        """提取单份报告的核心内容摘要"""
        self._log(f"[{idx}/{total}] 开始处理: {os.path.basename(pdf_path)}", "DEBUG")
        
        try:
            # 上传文件
            file_id = self._upload_file(pdf_path)
            self._log(f"[{idx}/{total}] 文件上传成功, file_id: {file_id}", "DEBUG")
            
            content_text = self._get_file_content(file_id)
            self._log(f"[{idx}/{total}] 内容获取成功, 长度: {len(content_text)} 字符", "DEBUG")
            
            # 如果内容较短，直接返回
            if len(content_text) < 1500:
                self._log(f"[{idx}/{total}] 内容较短，直接返回", "DEBUG")
                return f"\n\n===== 报告 [{idx}/{total}]：{os.path.basename(pdf_path)} =====\n\n{content_text}"
            
            # 如果内容超长，需要分段处理
            if len(content_text) > 4000:
                self._log(f"[{idx}/{total}] 内容超长 ({len(content_text)}), 启用分块处理", "WARN")
                return self._extract_summary_chunked(pdf_path, content_text, idx, total)
            
            # 长内容需要摘要提取
            messages = [
                {
                    "role": "system",
                    "content": "你是一个专业的金融分析师。请提取报告的核心内容，保留关键数据、观点和结论。"
                },
                {
                    "role": "user", 
                    "content": f"""请提取以下研究报告的核心内容摘要。

要求：
1. 保留报告标题、日期、机构名称
2. 提取核心观点和主要结论
3. 保留关键数据和预测
4. 保留重要的图表数据描述
5. 控制在800字以内

报告内容：
{content_text[:4000]}

请输出结构化的摘要："""
                }
            ]
            
            self._log(f"[{idx}/{total}] 请求 AI 提取摘要...", "DEBUG")
            result = self._api_call_with_retry(messages, max_retries=3, timeout=90)
            
            summary = result['choices'][0]['message']['content']
            self._log(f"[{idx}/{total}] 摘要提取完成, 长度: {len(summary)} 字符", "DEBUG")
            
            return f"\n\n===== 报告 [{idx}/{total}]：{os.path.basename(pdf_path)} =====\n\n{summary}"
            
        except Exception as e:
            self._log(f"[{idx}/{total}] 处理失败: {e}", "ERROR")
            return f"\n\n===== 报告 [{idx}/{total}]：{os.path.basename(pdf_path)} =====\n[提取失败: {str(e)[:100]}]\n"

    def _extract_summary_chunked(self, pdf_path: str, content_text: str, idx: int, total: int) -> str:
        """
        分段提取超长内容的摘要
        
        策略：
        1. 将内容分成多个块（每块约3000字符）
        2. 分别提取每个块的关键信息
        3. 合并所有块的关键信息生成最终摘要
        """
        self._log(f"[{idx}/{total}] 分块处理开始, 总长度: {len(content_text)}", "DEBUG")
        
        chunk_size = 3000
        chunks = []
        
        # 将内容分块（尽量在段落边界分割）
        for i in range(0, len(content_text), chunk_size):
            chunk = content_text[i:i+chunk_size]
            chunks.append(chunk)
        
        self._log(f"[{idx}/{total}] 内容已分为 {len(chunks)} 块", "DEBUG")
        
        # 提取每个块的关键信息
        chunk_summaries = []
        for chunk_idx, chunk in enumerate(chunks, 1):
            self._log(f"[{idx}/{total}] 处理第 {chunk_idx}/{len(chunks)} 块...", "DEBUG")
            
            messages = [
                {
                    "role": "system",
                    "content": "你是一个专业的金融分析师。请提取这段内容的关键信息。"
                },
                {
                    "role": "user", 
                    "content": f"""请提取以下内容的关键信息（第 {chunk_idx}/{len(chunks)} 部分）：

{chunk}

请提取：
1. 关键数据和数字
2. 重要观点和结论
3. 机构名称、日期等元数据（如果是第一部分）

控制在300字以内。"""
                }
            ]
            
            try:
                result = self._api_call_with_retry(messages, max_retries=2, timeout=60)
                chunk_summary = result['choices'][0]['message']['content']
                chunk_summaries.append(chunk_summary)
                self._log(f"[{idx}/{total}] 第 {chunk_idx} 块处理完成", "DEBUG")
            except Exception as e:
                self._log(f"[{idx}/{total}] 第 {chunk_idx} 块处理失败: {e}", "WARN")
                chunk_summaries.append(f"[第 {chunk_idx} 块提取失败]")
        
        # 合并所有块的摘要
        self._log(f"[{idx}/{total}] 合并 {len(chunk_summaries)} 个块摘要...", "DEBUG")
        
        combined_chunks = "\n\n".join(chunk_summaries)
        
        # 最终摘要生成
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的金融分析师。请基于多个片段生成一份连贯的摘要。"
            },
            {
                "role": "user", 
                "content": f"""请基于以下各部分内容，生成一份完整的研究报告摘要。

各部分内容：
{combined_chunks}

要求：
1. 整合所有信息，生成连贯的摘要
2. 保留关键数据、观点和结论
3. 控制在800字以内
4. 保持专业报告的语言风格

请输出结构化摘要："""
            }
        ]
        
        result = self._api_call_with_retry(messages, max_retries=2, timeout=90)
        final_summary = result['choices'][0]['message']['content']
        
        self._log(f"[{idx}/{total}] 分块处理完成, 最终摘要长度: {len(final_summary)} 字符", "DEBUG")
        
        return f"\n\n===== 报告 [{idx}/{total}]：{os.path.basename(pdf_path)} =====\n\n{final_summary}"

    def _merge_summaries(self, summaries: list) -> str:
        """合并所有报告摘要，生成执行摘要"""
        # 简单拼接所有摘要
        combined = "\n".join(summaries)
        
        # 如果报告较多，添加一个总体概述
        if len(summaries) > 3:
            import requests
            print("[INFO] 生成执行摘要...")
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": "kimi-k2.5",
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一个专业的研究报告编辑。请基于多份报告生成执行摘要。"
                        },
                        {
                            "role": "user", 
                            "content": f"""基于以下{len(summaries)}份研究报告，生成一份执行摘要（Executive Summary）。

{combined[:5000]}

请生成：
1. 市场总体趋势概述（200字）
2. 各品种/板块核心观点汇总
3. 风险提示
4. 投资建议

控制在800字以内。"""
                        }
                    ],
                    "temperature": 1
                }
            )

            result = response.json()
            self._check_api_response(result)
            
            executive_summary = result['choices'][0]['message']['content']
            combined = f"===== 执行摘要 =====\n\n{executive_summary}\n\n===== 详细报告 ====={combined}"
        
        return combined

    def _generate_report_code(self, template_style: dict, content: str, config: ReportConfig) -> str:
        """第3轮：生成报告代码"""
        import requests
        import json
        
        print("[INFO] 请求 AI 生成排版代码...")
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": "kimi-k2.5",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的文档自动化专家。请输出可执行的 Python 代码，使用 ReportLab 生成 PDF。"
                    },
                    {
                        "role": "user", 
                        "content": f"""请生成 Python 代码，创建专业的 PDF 报告。

【版式规范】
{json.dumps(template_style, ensure_ascii=False, indent=2)}

【报告内容】
{content[:6000]}

【输出要求】
1. 使用 reportlab 库
2. 严格遵循版式规范中的颜色、字体、边距
3. 中文字体使用系统自带的 SimHei 或 Microsoft YaHei
4. 添加页眉页脚（如规范中有定义）
5. 保存文件到: {config.output_file}
6. 代码必须完整可执行，包含所有 import
7. 内容较多时自动分页，确保布局美观
8. **重要**：reportlab.lib.units 中没有 pt，只用 mm/cm/inch，字号直接用数字

只输出 Python 代码，不要有其他说明。"""
                    }
                ],
                "temperature": 1
            }
        )

        result = response.json()
        self._check_api_response(result)
        
        code = result['choices'][0]['message']['content']

        # 提取代码
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]
        
        return code

    def _check_api_response(self, result: dict):
        """检查 API 响应是否包含错误"""
        if 'error' in result:
            error_msg = result['error'].get('message', 'Unknown error')
            raise RuntimeError(f"API 错误: {error_msg}")
        
        if 'choices' not in result:
            raise RuntimeError(f"API 响应格式错误: {result}")

    def _api_call_with_retry(self, messages: list, max_retries: int = 10, timeout: int = 120) -> dict:
        """
        带重试机制的 API 调用（支持并发限制重试）
        
        Args:
            messages: 消息列表
            max_retries: 最大重试次数
            timeout: 超时时间（秒）
            
        Returns:
            API 响应结果
        """
        import requests
        import time
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                self._log(f"API 调用尝试 {attempt + 1}/{max_retries}", "DEBUG")
                
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": "kimi-k2.5",
                        "messages": messages,
                        "temperature": 1
                    },
                    timeout=timeout
                )
                
                self._log(f"API 响应状态: {response.status_code}", "DEBUG")
                
                # 检查 HTTP 错误状态
                if response.status_code == 429:
                    # 并发限制错误
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get('error', {}).get('message', 'Rate limited')
                    
                    # 尝试从错误信息中提取等待时间
                    wait_time = 3  # 默认等待 3 秒
                    if 'try again after' in error_msg.lower():
                        try:
                            # 解析 "try again after X seconds"
                            import re
                            match = re.search(r'after\s+(\d+)\s+seconds', error_msg.lower())
                            if match:
                                wait_time = int(match.group(1)) + 2  # 多等 2 秒确保
                        except:
                            pass
                    
                    wait_time = wait_time + attempt * 2  # 递增等待
                    self._log(f"并发限制 (429): {error_msg}", "WARN")
                    self._log(f"等待 {wait_time} 秒后重试...", "WARN")
                    time.sleep(wait_time)
                    continue  # 继续下一次重试
                
                # 其他 HTTP 错误
                if response.status_code != 200:
                    error_msg = response.text[:200] if response.text else f"HTTP {response.status_code}"
                    raise RuntimeError(f"API HTTP 错误: {error_msg}")
                
                result = response.json()
                self._check_api_response(result)
                
                self._log(f"API 调用成功", "DEBUG")
                return result
                
            except requests.exceptions.Timeout as e:
                last_error = f"请求超时: {e}"
                wait_time = min(2 ** attempt, 30)  # 最大等待 30 秒
                self._log(f"尝试 {attempt + 1} 超时，{wait_time}秒后重试...", "WARN")
                time.sleep(wait_time)
                
            except requests.exceptions.ConnectionError as e:
                last_error = f"连接错误: {e}"
                wait_time = min(3 * (attempt + 1), 30)
                self._log(f"尝试 {attempt + 1} 连接错误，{wait_time}秒后重试...", "WARN")
                time.sleep(wait_time)
                
            except RuntimeError as e:
                # 检查是否是并发限制错误
                error_str = str(e)
                if 'concurrency' in error_str.lower() or 'max organization' in error_str.lower():
                    wait_time = 2 * (attempt + 1)
                    self._log(f"并发限制错误，等待 {wait_time} 秒后重试...", "WARN")
                    time.sleep(wait_time)
                    last_error = error_str
                else:
                    raise  # 其他 RuntimeError 直接抛出
                
            except Exception as e:
                last_error = f"未知错误: {e}"
                self._log(f"尝试 {attempt + 1} 失败: {e}", "ERROR")
                time.sleep(1)
        
        # 所有重试都失败
        raise RuntimeError(f"API 调用在 {max_retries} 次尝试后失败: {last_error}")

    def _upload_file(self, file_path: str) -> str:
        """上传文件"""
        import requests

        url = f"{self.base_url}/files"
        with open(file_path, 'rb') as f:
            response = requests.post(
                url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                files={'file': f},
                data={'purpose': 'file-extract'}
            )

        if response.status_code != 200:
            raise Exception(f"上传失败: {response.text}")

        return response.json()['id']

    def _get_file_content(self, file_id: str) -> str:
        """获取文件内容"""
        import requests

        url = f"{self.base_url}/files/{file_id}/content"
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.text


def generate_report(
    template: str,
    content: str = None,
    output: str = "output.pdf",
    mode: Literal["auto", "cli", "api"] = "api",
    reports_folder: str = None,
    max_workers: int = 3,
    debug: bool = False,
    **kwargs
) -> str:
    """
    一键生成报告的便捷函数

    Args:
        template: 模板 PDF 路径
        content: 内容 PDF 路径（与 reports_folder 二选一）
        output: 输出文件路径
        mode: 生成模式（auto=自动选择，cli=本地Agent，api=云端API，默认: api）
        reports_folder: 报告文件夹路径（批量模式，与 content 二选一）
        max_workers: API 模式下并行处理的线程数（默认: 3，最大 3，受 API 并发限制）
        debug: 是否启用详细调试输出（默认: False）
        **kwargs: 其他配置（company_name, title 等）

    Returns:
        生成的文件路径
    """
    # 限制最大并发数（API 限制）
    max_workers = min(max_workers, 3)
    
    # 从 kwargs 获取已传递的 content_pdfs
    content_pdfs = kwargs.pop('content_pdfs', None)
    
    # 处理批量报告文件夹（优先使用 reports_folder）
    if reports_folder:
        reports_folder = Path(reports_folder)
        if not reports_folder.exists():
            raise ValueError(f"报告文件夹不存在: {reports_folder}")
        
        # 获取文件夹下所有 PDF 文件
        content_pdfs = sorted([str(p) for p in reports_folder.glob("*.pdf")])
        if not content_pdfs:
            raise ValueError(f"报告文件夹中没有 PDF 文件: {reports_folder}")
        
        print(f"[INFO] 发现 {len(content_pdfs)} 个报告文件")
        
        # 如果没有指定 content，使用第一个文件作为默认
        if not content:
            content = content_pdfs[0]
    
    config = ReportConfig(
        template_pdf=template,
        content_pdf=content,
        output_file=output,
        content_pdfs=content_pdfs,
        **kwargs
    )

    # 自动选择模式（仅在 mode=auto 时）
    if mode == "auto":
        try:
            subprocess.run(["kimi", "--version"], capture_output=True, check=True)
            mode = "cli"
            print("✅ 检测到 Kimi CLI，使用本地 Agent 模式")
        except (FileNotFoundError, subprocess.CalledProcessError):
            mode = "api"
            print("[INFO] 未检测到 Kimi CLI，使用 API 模式")
    else:
        print(f"[INFO] 使用 {mode.upper()} 模式")

    # 执行生成
    if mode == "cli":
        agent = KimiCLIAgent()
    else:
        agent = KimiAPIAgent(max_workers=max_workers, debug=debug)

    return agent.generate(config)


# ============ 使用示例 ============

def get_datetime_filename(ext="pdf") -> str:
    """生成带日期时间的文件名"""
    now = datetime.now()
    return f"report_{now.strftime('%Y%m%d_%H%M%S')}.{ext}"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="基于模板 PDF 生成新报告（继承版式，更新内容）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基础用法（单个内容文件）
  python report_generator.py template.pdf report.pdf -o new_report.pdf
  python report_generator.py template.pdf report.pdf -f docx --company "ABC公司"
  
  # 批量综合报告（读取整个文件夹）
  python report_generator.py template.pdf --reports ./reports_folder/
  python report_generator.py template.pdf --reports ./reports_folder/ -o custom_name.pdf
  
  # API 模式多轮处理（避免超时）
  python report_generator.py template.pdf --reports ./reports_folder/ -m api -w 3
  # -w 3 表示使用 3 个线程并行处理多个报告
        """
    )

    parser.add_argument("template", help="模板 PDF 文件路径（定义视觉风格）")
    parser.add_argument("content", nargs="?", default=None,
                       help="内容 PDF 文件路径（提供文字数据，与 --reports 二选一）")
    parser.add_argument("-o", "--output", default=None,
                       help="输出文件路径（默认: report_YYYYMMDD_HHMMSS.pdf）")
    parser.add_argument("-f", "--format", choices=["pdf", "docx", "pptx", "xlsx"],
                       default="pdf", help="输出格式（默认: pdf）")
    parser.add_argument("-m", "--mode", choices=["auto", "cli", "api"],
                       default="api", help="生成模式（默认: api）")
    parser.add_argument("--company", default="",
                       help="公司名称（用于页眉页脚）")
    parser.add_argument("--title", default="",
                       help="报告标题（覆盖自动提取）")
    parser.add_argument("--reports", dest="reports_folder", default=None,
                       help="报告文件夹路径（批量模式，读取该目录下所有 PDF 生成综合报告）")
    parser.add_argument("-w", "--workers", type=int, default=3,
                       help="API 模式下并行处理的线程数（默认: 3，最大 3，受 API 并发限制）")
    parser.add_argument("--debug", action="store_true",
                       help="启用详细调试输出")

    args = parser.parse_args()

    # 验证参数：content 和 --reports 必须二选一
    if not args.content and not args.reports_folder:
        parser.error("必须指定 content 文件或使用 --reports 指定报告文件夹")

    # 自动生成带日期时间的文件名
    if args.output is None:
        args.output = get_datetime_filename(args.format)

    # 执行生成
    try:
        result = generate_report(
            template=args.template,
            content=args.content,
            output=args.output,
            output_format=args.format,
            mode=args.mode,
            reports_folder=args.reports_folder,
            max_workers=args.workers,
            debug=args.debug,
            company_name=args.company,
            title=args.title
        )

        if result:
            print(f"\n[OK] 报告已生成: {os.path.abspath(result)}")

    except Exception as e:
        print(f"\n[ERROR] 错误: {e}")
        sys.exit(1)
