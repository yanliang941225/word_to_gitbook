#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Word转GitBook工具
功能：
1. 将Word文档转换为GitBook格式
2. 保留所有文档内容（文本、图片、表格等）
3. 支持可配置的目录级别
4. 生成GitBook所需的目录结构和配置文件
"""

import os
import re
import json
import argparse
import shutil
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from io import BytesIO

from docx import Document
from docx.document import Document as DocxDocument
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.shared import Inches
from PIL import Image
import markdown
from bs4 import BeautifulSoup


@dataclass
class GitBookConfig:
    """GitBook配置类"""
    title: str = "文档标题"
    description: str = "文档描述"
    language: str = "zh-hans"
    max_toc_level: int = 3
    output_dir: str = "gitbook_output"
    assets_dir: str = "assets"
    

@dataclass
class TocItem:
    """目录项类"""
    title: str
    filename: str
    level: int
    children: List['TocItem'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


class WordToGitBookConverter:
    """Word转GitBook转换器主类"""
    
    def __init__(self, config: GitBookConfig):
        self.config = config
        self.output_dir = Path(config.output_dir)
        self.assets_dir = self.output_dir / config.assets_dir
        self.toc_items: List[TocItem] = []
        self.current_chapter = 1
        self.image_counter = 1
        self.image_map = {}  # 映射rId到图片文件名
        
    def convert(self, word_file_path: str) -> None:
        """主转换方法"""
        print(f"开始转换Word文档: {word_file_path}")
        
        # 创建输出目录
        self._create_output_directories()
        
        # 加载Word文档
        doc = Document(word_file_path)
        
        # 先提取所有图片（避免遭漏）
        self._extract_all_images(doc)
        
        # 解析文档结构
        self._parse_document_structure(doc)
        
        # 生成GitBook文件
        self._generate_gitbook_files(doc)
        
        # 生成配置文件
        self._generate_config_files()
        
        print(f"转换完成！输出目录: {self.output_dir}")
    
    def _extract_all_images(self, doc: DocxDocument) -> None:
        """提取文档中的所有图片（预先扫描）"""
        print("扫描和提取所有图片...")
        
        # 从document的part中获取所有相关部分
        doc_part = doc.part
        image_count = 0
        
        for rel_id, related_part in doc_part.related_parts.items():
            # 检查是否是图片部分
            if hasattr(related_part, 'content_type') and related_part.content_type.startswith('image/'):
                try:
                    image_data = related_part.blob
                    image_ext = self._get_image_extension(image_data)
                    image_filename = f"image_{self.image_counter:03d}.{image_ext}"
                    
                    # 保存图片
                    image_path = self.assets_dir / image_filename
                    with open(image_path, 'wb') as f:
                        f.write(image_data)
                    
                    # 建立映射关系
                    self.image_map[rel_id] = image_filename
                    
                    print(f"预先提取图片: {image_filename} (ID: {rel_id})")
                    self.image_counter += 1
                    image_count += 1
                    
                except Exception as e:
                    print(f"提取图片 {rel_id} 时出错: {e}")
        
        if image_count > 0:
            print(f"共提取到 {image_count} 张图片")
        else:
            print("文档中没有找到图片")
    
    def _create_output_directories(self) -> None:
        """创建输出目录结构"""
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"创建输出目录: {self.output_dir}")
    
    def _parse_document_structure(self, doc: DocxDocument) -> None:
        """解析文档结构，提取标题层级"""
        print("解析文档结构...")
        
        for para in doc.paragraphs:
            if para.style.name.startswith('Heading'):
                level = self._extract_heading_level(para.style.name)
                if level <= self.config.max_toc_level:
                    title = para.text.strip()
                    if title:
                        filename = self._generate_filename(title, level)
                        toc_item = TocItem(title=title, filename=filename, level=level)
                        self.toc_items.append(toc_item)
        
        # 如果没有找到标题，创建默认章节
        if not self.toc_items:
            self.toc_items.append(TocItem(
                title="文档内容",
                filename="content.md",
                level=1
            ))
    
    def _extract_heading_level(self, style_name: str) -> int:
        """从样式名称提取标题级别"""
        match = re.search(r'Heading\s*(\d+)', style_name)
        return int(match.group(1)) if match else 1
    
    def _generate_filename(self, title: str, level: int) -> str:
        """根据标题生成文件名"""
        # 清理标题，生成合法的文件名
        clean_title = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', title)  # 保留中文字符
        clean_title = re.sub(r'[-\s]+', '-', clean_title)
        clean_title = clean_title.strip('-')
        
        # 如果清理后为空或太短，使用默认命名
        if not clean_title or len(clean_title) < 2:
            clean_title = f"chapter-{self.current_chapter}"
            self.current_chapter += 1
        
        # 限制文件名长度
        if len(clean_title) > 50:
            clean_title = clean_title[:50]
        
        return f"{clean_title}.md"
    
    def _generate_gitbook_files(self, doc: DocxDocument) -> None:
        """生成GitBook文件"""
        print("生成GitBook内容文件...")
        
        if not self.toc_items:
            # 如果没有目录结构，生成单一文件
            self._generate_single_markdown_file(doc)
        else:
            # 按章节生成多个文件
            self._generate_chapter_files(doc)
    
    def _generate_single_markdown_file(self, doc: DocxDocument) -> None:
        """生成单一Markdown文件"""
        content = self._convert_document_to_markdown(doc)
        
        output_file = self.output_dir / "content.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_chapter_files(self, doc: DocxDocument) -> None:
        """按章节生成多个Markdown文件"""
        print("按章节生成文件...")
        
        # 建立标题到目录项的映射
        title_to_toc = {}
        for item in self.toc_items:
            title_to_toc[item.title] = item
        
        current_toc_item = None
        current_content = []
        toc_index = 0
        
        for element in doc.element.body:
            if isinstance(element, CT_P):
                para = Paragraph(element, doc)
                
                # 检查是否是标题
                if para.style.name.startswith('Heading'):
                    level = self._extract_heading_level(para.style.name)
                    title = para.text.strip()
                    
                    # 检查是否是我们需要的目录级别标题
                    if level <= self.config.max_toc_level and title and title in title_to_toc:
                        # 保存当前章节内容
                        if current_toc_item and current_content:
                            self._save_chapter_content_by_item(current_toc_item, current_content)
                            print(f"保存章节: {current_toc_item.title} -> {current_toc_item.filename}")
                        
                        # 开始新章节
                        current_toc_item = title_to_toc[title]
                        current_content = [f"# {title}\n\n"]
                        toc_index += 1
                    else:
                        # 普通标题或子级标题，添加到当前内容中
                        current_content.append(self._convert_paragraph_to_markdown(para))
                else:
                    # 普通段落
                    current_content.append(self._convert_paragraph_to_markdown(para))
            
            elif isinstance(element, CT_Tbl):
                table = Table(element, doc)
                current_content.append(self._convert_table_to_markdown(table))
        
        # 保存最后一个章节
        if current_toc_item and current_content:
            self._save_chapter_content_by_item(current_toc_item, current_content)
            print(f"保存最后章节: {current_toc_item.title} -> {current_toc_item.filename}")
    
    def _save_chapter_content_by_item(self, toc_item: TocItem, content: List[str]) -> None:
        """根据目录项保存章节内容到文件"""
        filepath = self.output_dir / toc_item.filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(''.join(content))
    
    def _save_chapter_content(self, toc_index: int, content: List[str]) -> None:
        """保存章节内容到文件"""
        if toc_index < len(self.toc_items):
            filename = self.toc_items[toc_index].filename
            filepath = self.output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(''.join(content))
    
    def _convert_document_to_markdown(self, doc: DocxDocument) -> str:
        """将整个文档转换为Markdown"""
        markdown_content = []
        
        for element in doc.element.body:
            if isinstance(element, CT_P):
                para = Paragraph(element, doc)
                markdown_content.append(self._convert_paragraph_to_markdown(para))
            elif isinstance(element, CT_Tbl):
                table = Table(element, doc)
                markdown_content.append(self._convert_table_to_markdown(table))
        
        return ''.join(markdown_content)
    
    def _convert_paragraph_to_markdown(self, para: Paragraph) -> str:
        """将段落转换为Markdown"""
        if not para.text.strip():
            # 即使没有文本，也要检查是否有图片
            image_text = self._process_images_in_paragraph(para, "")
            if image_text.strip():
                return image_text + "\n"
            return "\n"
        
        # 处理标题
        if para.style.name.startswith('Heading'):
            level = self._extract_heading_level(para.style.name)
            return f"{'#' * level} {para.text}\n\n"
        
        # 处理普通段落
        text = self._process_paragraph_formatting(para)
        
        # 处理图片
        text = self._process_images_in_paragraph(para, text)
        
        return f"{text}\n\n"
    
    def _process_paragraph_formatting(self, para: Paragraph) -> str:
        """处理段落格式化"""
        result = ""
        
        for run in para.runs:
            text = run.text
            
            # 处理粗体
            if run.bold:
                text = f"**{text}**"
            
            # 处理斜体
            if run.italic:
                text = f"*{text}*"
            
            # 处理下划线（用HTML标签）
            if run.underline:
                text = f"<u>{text}</u>"
            
            result += text
        
        return result
    
    def _process_images_in_paragraph(self, para: Paragraph, text: str) -> str:
        """处理段落中的图片"""
        image_found = False
        processed_rIds = set()  # 记录已处理的图片rId，避免重复
        
        for run in para.runs:
            # 优先检查w:drawing元素（现代Word格式）
            drawing_elements = run.element.xpath('.//w:drawing')
            if drawing_elements:
                try:
                    for drawing in drawing_elements:
                        # 查找其中的图片引用
                        blips = drawing.xpath('.//a:blip')
                        for blip in blips:
                            rId = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                            if rId and rId in self.image_map and rId not in processed_rIds:
                                image_filename = self.image_map[rId]
                                text += f"\n\n![图片]({self.config.assets_dir}/{image_filename})\n\n"
                                processed_rIds.add(rId)
                                image_found = True
                except Exception as e:
                    print(f"处理drawing图片时出错: {e}")
            
            # 检查直接的a:blip元素（仅在没有drawing包装时）
            elif run.element.xpath('.//a:blip'):
                try:
                    blip_elements = run.element.xpath('.//a:blip')
                    for blip in blip_elements:
                        rId = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                        if rId and rId in self.image_map and rId not in processed_rIds:
                            image_filename = self.image_map[rId]
                            text += f"\n\n![图片]({self.config.assets_dir}/{image_filename})\n\n"
                            processed_rIds.add(rId)
                            image_found = True
                except Exception as e:
                    print(f"处理blip图片时出错: {e}")
            
            # 检查w:pict元素（旧格式图片）
            pict_elements = run.element.xpath('.//w:pict')
            if pict_elements:
                try:
                    for pict in pict_elements:
                        imagedatas = pict.xpath('.//v:imagedata')
                        for imagedata in imagedatas:
                            rId = imagedata.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                            if rId and rId in self.image_map and rId not in processed_rIds:
                                image_filename = self.image_map[rId]
                                text += f"\n\n![图片]({self.config.assets_dir}/{image_filename})\n\n"
                                processed_rIds.add(rId)
                                image_found = True
                except Exception as e:
                    print(f"处理pict图片时出错: {e}")
        
        return text
    
    def _get_image_reference(self, run) -> Optional[str]:
        """获取已提取图片的引用"""
        try:
            blips = run.element.xpath('.//a:blip')
            if blips:
                rId = blips[0].get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                if rId and rId in self.image_map:
                    return self.image_map[rId]
        except Exception as e:
            print(f"获取图片引用时出错: {e}")
        return None
    
    def _get_image_reference_from_drawing(self, run) -> Optional[str]:
        """从drawing元素获取图片引用"""
        try:
            drawings = run.element.xpath('.//w:drawing')
            for drawing in drawings:
                blips = drawing.xpath('.//a:blip', namespaces={
                    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
                    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
                })
                
                for blip in blips:
                    rId = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                    if rId and rId in self.image_map:
                        return self.image_map[rId]
        except Exception as e:
            print(f"从drawing获取图片引用时出错: {e}")
        return None
    
    def _get_image_reference_from_pict(self, run) -> Optional[str]:
        """从pict元素获取图片引用"""
        try:
            picts = run.element.xpath('.//w:pict')
            for pict in picts:
                imagedatas = pict.xpath('.//v:imagedata', namespaces={
                    'v': 'urn:schemas-microsoft-com:vml',
                    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
                })
                
                for imagedata in imagedatas:
                    rId = imagedata.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                    if rId and rId in self.image_map:
                        return self.image_map[rId]
        except Exception as e:
            print(f"从pict获取图片引用时出错: {e}")
        return None
    
    def _extract_image_from_run(self, run) -> Optional[str]:
        """从run中提取图片"""
        try:
            # 获取图片数据
            blips = run.element.xpath('.//a:blip')
            if blips:
                rId = blips[0].get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                if rId:
                    image_part = run.part.related_parts[rId]
                    image_data = image_part.blob
                    
                    # 确定图片格式
                    image_ext = self._get_image_extension(image_data)
                    image_filename = f"image_{self.image_counter:03d}.{image_ext}"
                    
                    # 保存图片
                    image_path = self.assets_dir / image_filename
                    with open(image_path, 'wb') as f:
                        f.write(image_data)
                    
                    print(f"提取图片: {image_filename}")
                    self.image_counter += 1
                    return image_filename
        except Exception as e:
            print(f"从run提取图片时出错: {e}")
        
        return None
    
    def _extract_image_from_drawing(self, run) -> Optional[str]:
        """从drawing元素中提取图片"""
        try:
            # 查找w:drawing中的a:blip
            drawings = run.element.xpath('.//w:drawing')
            for drawing in drawings:
                blips = drawing.xpath('.//a:blip', namespaces={
                    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
                    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
                })
                
                for blip in blips:
                    rId = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                    if rId and rId in run.part.related_parts:
                        image_part = run.part.related_parts[rId]
                        image_data = image_part.blob
                        
                        # 确定图片格式
                        image_ext = self._get_image_extension(image_data)
                        image_filename = f"image_{self.image_counter:03d}.{image_ext}"
                        
                        # 保存图片
                        image_path = self.assets_dir / image_filename
                        with open(image_path, 'wb') as f:
                            f.write(image_data)
                        
                        print(f"从drawing提取图片: {image_filename}")
                        self.image_counter += 1
                        return image_filename
        except Exception as e:
            print(f"从drawing提取图片时出错: {e}")
        
        return None
    
    def _extract_image_from_pict(self, run) -> Optional[str]:
        """从pict元素中提取图片（旧格式）"""
        try:
            # 查找w:pict中的图片
            picts = run.element.xpath('.//w:pict')
            for pict in picts:
                # 查找v:imagedata或类似元素
                imagedatas = pict.xpath('.//v:imagedata', namespaces={
                    'v': 'urn:schemas-microsoft-com:vml',
                    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
                })
                
                for imagedata in imagedatas:
                    rId = imagedata.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                    if rId and rId in run.part.related_parts:
                        image_part = run.part.related_parts[rId]
                        image_data = image_part.blob
                        
                        # 确定图片格式
                        image_ext = self._get_image_extension(image_data)
                        image_filename = f"image_{self.image_counter:03d}.{image_ext}"
                        
                        # 保存图片
                        image_path = self.assets_dir / image_filename
                        with open(image_path, 'wb') as f:
                            f.write(image_data)
                        
                        print(f"从pict提取图片: {image_filename}")
                        self.image_counter += 1
                        return image_filename
        except Exception as e:
            print(f"从pict提取图片时出错: {e}")
        
        return None
    
    def _get_image_extension(self, image_data: bytes) -> str:
        """根据图片数据获取文件扩展名"""
        try:
            with BytesIO(image_data) as img_io:
                img = Image.open(img_io)
                format_name = img.format.lower()
                return format_name if format_name in ['png', 'jpg', 'jpeg', 'gif', 'bmp'] else 'png'
        except:
            return 'png'
    
    def _convert_table_to_markdown(self, table: Table) -> str:
        """将表格转换为Markdown"""
        if not table.rows:
            return ""
        
        markdown_table = []
        
        # 处理表头
        header_row = table.rows[0]
        header_cells = [cell.text.strip() for cell in header_row.cells]
        markdown_table.append("| " + " | ".join(header_cells) + " |")
        markdown_table.append("| " + " | ".join(["---"] * len(header_cells)) + " |")
        
        # 处理数据行
        for row in table.rows[1:]:
            data_cells = [cell.text.strip().replace('\n', '<br>') for cell in row.cells]
            markdown_table.append("| " + " | ".join(data_cells) + " |")
        
        return "\n".join(markdown_table) + "\n\n"
    
    def _generate_config_files(self) -> None:
        """生成GitBook配置文件"""
        print("生成GitBook配置文件...")
        
        # 生成book.json
        self._generate_book_json()
        
        # 生成SUMMARY.md
        self._generate_summary_md()
        
        # 生成README.md
        self._generate_readme_md()
    
    def _generate_book_json(self) -> None:
        """生成book.json配置文件（兼容HonKit）"""
        book_config = {
            "title": self.config.title,
            "description": self.config.description,
            "language": self.config.language,
            "plugins": [
                "-sharing",
                "-fontsettings",
                "-livereload"
            ],
            "pluginsConfig": {}
        }
        
        with open(self.output_dir / "book.json", 'w', encoding='utf-8') as f:
            json.dump(book_config, f, ensure_ascii=False, indent=2)
    
    def _generate_summary_md(self) -> None:
        """生成SUMMARY.md目录文件"""
        summary_content = ["# Summary\n\n"]
        
        if self.toc_items:
            for item in self.toc_items:
                indent = "  " * (item.level - 1)
                summary_content.append(f"{indent}* [{item.title}]({item.filename})\n")
        else:
            summary_content.append("* [文档内容](content.md)\n")
        
        with open(self.output_dir / "SUMMARY.md", 'w', encoding='utf-8') as f:
            f.write(''.join(summary_content))
    
    def _generate_readme_md(self) -> None:
        """生成README.md介绍文件"""
        readme_content = f"""# {self.config.title}

{self.config.description}

## 关于本文档

本文档由Word文档自动转换生成，使用GitBook格式展示。

---

*本文档生成时间: {self._get_current_time()}*
"""
        
        with open(self.output_dir / "README.md", 'w', encoding='utf-8') as f:
            f.write(readme_content)
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    """主函数，处理命令行参数"""
    parser = argparse.ArgumentParser(description="Word转GitBook工具")
    parser.add_argument("input_file", help="输入的Word文档路径")
    parser.add_argument("-o", "--output", default="gitbook_output", help="输出目录（默认：gitbook_output）")
    parser.add_argument("-t", "--title", default="文档标题", help="GitBook标题")
    parser.add_argument("-d", "--description", default="文档描述", help="GitBook描述")
    parser.add_argument("-l", "--language", default="zh-hans", help="语言设置（默认：zh-hans）")
    parser.add_argument("--max-toc-level", type=int, default=3, help="最大目录级别（默认：3）")
    parser.add_argument("--assets-dir", default="assets", help="资源文件目录名（默认：assets）")
    
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.input_file):
        print(f"错误：输入文件不存在 - {args.input_file}")
        return 1
    
    # 创建配置
    config = GitBookConfig(
        title=args.title,
        description=args.description,
        language=args.language,
        max_toc_level=args.max_toc_level,
        output_dir=args.output,
        assets_dir=args.assets_dir
    )
    
    # 执行转换
    converter = WordToGitBookConverter(config)
    try:
        converter.convert(args.input_file)
        print("转换成功完成！")
        return 0
    except Exception as e:
        print(f"转换失败：{e}")
        return 1


if __name__ == "__main__":
    exit(main())