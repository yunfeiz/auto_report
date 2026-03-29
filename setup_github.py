#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 仓库创建和推送脚本
"""

import os
import sys
import subprocess
import json
import urllib.request
import urllib.error


def read_github_token():
    """读取 GitHub Token"""
    token_file = '.github_token'
    if not os.path.exists(token_file):
        print("[ERROR] 未找到 .github_token 文件")
        print("请复制 .github_token.example 为 .github_token 并填入你的 GitHub Token")
        return None
    
    with open(token_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and line.startswith('ghp_'):
                return line
    
    print("[ERROR] .github_token 文件中未找到有效的 GitHub Token")
    return None


def create_github_repo(token, repo_name, description="", private=False):
    """使用 GitHub API 创建仓库"""
    url = "https://api.github.com/user/repos"
    
    data = json.dumps({
        "name": repo_name,
        "description": description,
        "private": private,
        "auto_init": False
    }).encode('utf-8')
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"[OK] GitHub 仓库创建成功!")
            print(f"  仓库地址: {result['html_url']}")
            print(f"  SSH 地址: {result['ssh_url']}")
            print(f"  HTTPS 地址: {result['clone_url']}")
            return result
    except urllib.error.HTTPError as e:
        error_msg = json.loads(e.read().decode('utf-8'))
        print(f"[ERROR] 创建仓库失败: {error_msg.get('message', str(e))}")
        if 'already exists' in str(error_msg):
            print(f"[INFO] 仓库 {repo_name} 已存在，将使用现有仓库")
            # 返回一个模拟的仓库信息
            return {
                'html_url': f'https://github.com/yunfeiz/{repo_name}',
                'ssh_url': f'git@github.com:yunfeiz/{repo_name}.git',
                'clone_url': f'https://github.com/yunfeiz/{repo_name}.git'
            }
        return None


def run_command(cmd, description=""):
    """运行 shell 命令"""
    if description:
        print(f"[INFO] {description}")
    print(f"  $ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] 命令失败: {result.stderr}")
        return False
    if result.stdout.strip():
        print(f"  {result.stdout.strip()}")
    return True


def main():
    """主函数"""
    print("=" * 60)
    print("GitHub 仓库设置工具")
    print("=" * 60)
    
    # 读取 GitHub Token
    token = read_github_token()
    if not token:
        sys.exit(1)
    
    print(f"[OK] GitHub Token 已加载: {token[:10]}...")
    
    # 配置
    REPO_NAME = "auto_report"
    DESCRIPTION = "自动报告生成器 - 基于 Kimi AI 的智能研报生成工具"
    USERNAME = "yunfeiz"
    
    print(f"\n[INFO] 将创建仓库: {USERNAME}/{REPO_NAME}")
    
    # 创建 GitHub 仓库
    repo_info = create_github_repo(
        token=token,
        repo_name=REPO_NAME,
        description=DESCRIPTION,
        private=False
    )
    
    if not repo_info:
        sys.exit(1)
    
    # 设置远程仓库并推送
    print("\n[INFO] 设置 Git 远程仓库...")
    
    # 检查是否已有远程仓库
    result = subprocess.run("git remote get-url origin", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[INFO] 远程仓库已存在: {result.stdout.strip()}")
        print("[INFO] 更新远程仓库地址...")
        if not run_command(f"git remote set-url origin {repo_info['clone_url']}", "更新远程地址"):
            sys.exit(1)
    else:
        print("[INFO] 添加远程仓库...")
        if not run_command(f"git remote add origin {repo_info['clone_url']}", "添加远程仓库"):
            sys.exit(1)
    
    # 推送到 GitHub
    print("\n[INFO] 推送到 GitHub...")
    if not run_command("git push -u origin master", "推送到远程仓库"):
        # 尝试 main 分支
        print("[INFO] 尝试推送到 main 分支...")
        if not run_command("git branch -M main", "重命名分支为 main"):
            sys.exit(1)
        if not run_command("git push -u origin main", "推送到 main 分支"):
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("[OK] 完成！")
    print(f"  仓库地址: {repo_info['html_url']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
