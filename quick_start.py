#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速使用指南 - Word转GitBook工具
"""

print("🎉 Word转GitBook工具安装完成！")
print("=" * 50)
print()

print("📋 使用方法：")
print("1. 基本转换：")
print("   python word_to_gitbook.py 你的文档.docx")
print()

print("2. 自定义配置：")
print("   python word_to_gitbook.py 你的文档.docx \\")
print("     --title '我的文档' \\")
print("     --max-toc-level 3 \\")
print("     --output my_gitbook")
print()

print("📁 主要参数：")
print("  --max-toc-level：控制目录级别 (1-6)")
print("    - 1: 只显示主要章节")
print("    - 2: 显示章节和大节")  
print("    - 3: 显示到小节 (推荐)")
print("    - 4-6: 更详细的目录结构")
print()

print("📂 输出文件：")
print("  README.md      - GitBook首页")
print("  SUMMARY.md     - 目录结构") 
print("  book.json      - GitBook配置")
print("  *.md          - 各章节内容")
print("  assets/       - 图片等资源")
print()

print("💡 使用建议：")
print("• 确保Word文档使用正确的标题样式(标题1、标题2等)")
print("• 推荐目录级别设置为2-3级，获得最佳阅读体验")
print("• 转换前检查Word文档中的图片和表格格式")
print()

print("🔗 需要帮助？查看README.md获取详细文档")
print("=" * 50)