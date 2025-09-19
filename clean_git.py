#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git清理脚本 - 清理缓存和临时文件
"""

import os
import shutil
from pathlib import Path


def clean_cache_files():
    """清理缓存文件"""
    print("🧹 开始清理缓存文件...")
    
    current_dir = Path(".")
    cleaned_count = 0
    
    # 清理.DS_Store文件
    for ds_store in current_dir.rglob(".DS_Store"):
        ds_store.unlink()
        print(f"  删除: {ds_store}")
        cleaned_count += 1
    
    # 清理__pycache__目录
    for pycache in current_dir.rglob("__pycache__"):
        if pycache.is_dir():
            shutil.rmtree(pycache)
            print(f"  删除目录: {pycache}")
            cleaned_count += 1
    
    # 清理.pyc文件
    for pyc_file in current_dir.rglob("*.pyc"):
        pyc_file.unlink()
        print(f"  删除: {pyc_file}")
        cleaned_count += 1
    
    # 清理临时测试文件
    temp_patterns = [
        "test_*.docx",
        "sample_*.docx", 
        "duplicate_*.docx",
        "*_output",
        "temp_*",
        "quick_test",
        "verify_*",
        "final_test"
    ]
    
    for pattern in temp_patterns:
        for temp_file in current_dir.glob(pattern):
            if temp_file.is_file():
                temp_file.unlink()
                print(f"  删除临时文件: {temp_file}")
                cleaned_count += 1
            elif temp_file.is_dir():
                shutil.rmtree(temp_file)
                print(f"  删除临时目录: {temp_file}")
                cleaned_count += 1
    
    print(f"✅ 清理完成！共清理了 {cleaned_count} 个文件/目录")


def show_gitignore_info():
    """显示.gitignore信息"""
    print("\n📋 .gitignore 配置说明：")
    print("已配置忽略以下类型的文件：")
    print("• macOS系统文件 (.DS_Store等)")
    print("• Python缓存文件 (__pycache__, *.pyc等)")
    print("• 虚拟环境目录 (.env, venv/等)")
    print("• IDE配置文件 (.vscode/, .idea/等)")
    print("• 测试临时文件 (test_*.docx等)")
    print("• GitBook输出目录 (*_output/等)")
    print("• 图片和资源文件 (*.png, assets/等)")


def main():
    """主函数"""
    print("Git文件清理工具")
    print("=" * 40)
    
    try:
        clean_cache_files()
        show_gitignore_info()
        
        print("\n💡 使用建议：")
        print("• 定期运行此脚本清理临时文件")
        print("• 提交代码前运行一次清理")
        print("• .gitignore已配置，新生成的缓存文件会自动忽略")
        
    except Exception as e:
        print(f"❌ 清理过程中出错: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
