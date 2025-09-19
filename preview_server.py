#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的本地预览服务器
当GitBook/HonKit安装有问题时，可以使用这个简单的Python服务器预览生成的文档
"""

import os
import sys
import webbrowser
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import argparse


def serve_gitbook(directory, port=8000):
    """启动简单的HTTP服务器预览GitBook"""
    if not Path(directory).exists():
        print(f"错误：目录不存在 - {directory}")
        return 1
    
    # 检查是否有GitBook文件
    gitbook_dir = Path(directory)
    if not (gitbook_dir / "README.md").exists():
        print(f"警告：目录中没有找到README.md文件")
    
    if not (gitbook_dir / "SUMMARY.md").exists():
        print(f"警告：目录中没有找到SUMMARY.md文件")
    
    # 切换到目标目录
    os.chdir(directory)
    
    # 创建HTTP服务器
    handler = SimpleHTTPRequestHandler
    httpd = HTTPServer(("localhost", port), handler)
    
    print(f"🚀 启动GitBook预览服务器...")
    print(f"📂 服务目录: {Path(directory).absolute()}")
    print(f"🌐 访问地址: http://localhost:{port}")
    print(f"📖 直接打开: http://localhost:{port}/README.md")
    print(f"⏹️  按 Ctrl+C 停止服务器")
    print("-" * 50)
    
    # 自动打开浏览器
    try:
        webbrowser.open(f"http://localhost:{port}")
    except:
        pass
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n服务器已停止")
        httpd.shutdown()
        return 0


def main():
    parser = argparse.ArgumentParser(description="GitBook简单预览服务器")
    parser.add_argument("directory", nargs="?", default=".", help="GitBook目录路径（默认：当前目录）")
    parser.add_argument("-p", "--port", type=int, default=8000, help="端口号（默认：8000）")
    
    args = parser.parse_args()
    
    return serve_gitbook(args.directory, args.port)


if __name__ == "__main__":
    exit(main())