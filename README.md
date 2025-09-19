# Word转GitBook工具

这是一个强大的Python工具，可以将Microsoft Word文档(.docx)转换为GitBook格式，完全保留文档中的所有内容，包括文本格式、图片、表格等，并支持可配置的目录级别。

## 功能特性

✅ **完整内容保留**
- 保留所有文本内容和格式（粗体、斜体、下划线）
- 自动提取并保存文档中的图片
- 完整转换表格为Markdown格式
- 保持原有的标题层级结构

✅ **可配置目录级别**
- 通过`--max-toc-level`参数控制目录深度
- 支持1-6级标题的灵活配置
- 自动生成GitBook目录结构

✅ **GitBook兼容**
- 自动生成`book.json`配置文件
- 生成`SUMMARY.md`目录文件
- 创建`README.md`介绍页面
- 支持多语言配置

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法

```bash
python word_to_gitbook.py 你的文档.docx
```

### 完整参数用法

```bash
python word_to_gitbook.py 你的文档.docx \
  --output my_gitbook \
  --title "我的技术文档" \
  --description "这是一个详细的技术文档" \
  --language zh-hans \
  --max-toc-level 4 \
  --assets-dir images
```

## 参数说明

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `input_file` | 输入的Word文档路径 | 必需 | `document.docx` |
| `-o, --output` | 输出目录 | `gitbook_output` | `my_book` |
| `-t, --title` | GitBook标题 | `文档标题` | `技术手册` |
| `-d, --description` | GitBook描述 | `文档描述` | `详细的API文档` |
| `-l, --language` | 语言设置 | `zh-hans` | `en`, `zh-hans` |
| `--max-toc-level` | 最大目录级别 | `3` | `1-6` |
| `--assets-dir` | 资源文件目录名 | `assets` | `images` |

## 目录级别配置示例

### 1级目录（--max-toc-level 1）
只显示最高级别的标题：
```
- 第一章：介绍
- 第二章：安装
- 第三章：使用
```

### 3级目录（--max-toc-level 3）
显示3级标题：
```
- 第一章：介绍
  - 1.1 项目背景
    - 1.1.1 技术选型
  - 1.2 功能特性
- 第二章：安装
  - 2.1 环境要求
  - 2.2 安装步骤
```

### 6级目录（--max-toc-level 6）
显示所有级别的标题（最详细）

## 输出结构

转换完成后，输出目录包含以下文件：

```
gitbook_output/
├── README.md          # GitBook首页
├── SUMMARY.md         # 目录结构
├── book.json          # GitBook配置
├── chapter1.md        # 第一章内容
├── chapter2.md        # 第二章内容
├── ...
└── assets/            # 资源文件夹
    ├── image_001.png  # 提取的图片
    ├── image_002.jpg
    └── ...
```

## 使用示例

### 示例1：转换技术文档

```bash
# 转换API文档，保留4级目录
python word_to_gitbook.py api_doc.docx \
  --title "API参考手册" \
  --description "完整的API接口文档" \
  --max-toc-level 4 \
  --output api_gitbook
```

### 示例2：转换用户手册

```bash
# 转换用户手册，只保留2级目录
python word_to_gitbook.py user_manual.docx \
  --title "用户操作手册" \
  --max-toc-level 2 \
  --assets-dir screenshots \
  --output user_guide
```

### 示例3：转换英文文档

```bash
# 转换英文文档
python word_to_gitbook.py english_doc.docx \
  --title "Technical Documentation" \
  --description "Comprehensive technical guide" \
  --language en \
  --output tech_docs
```

## 支持的Word元素

| Word元素 | 转换结果 | 说明 |
|----------|----------|------|
| 标题1-6 | `# ## ### #### ##### ######` | 保持层级关系 |
| 粗体文本 | `**粗体**` | Markdown粗体格式 |
| 斜体文本 | `*斜体*` | Markdown斜体格式 |
| 下划线 | `<u>下划线</u>` | HTML标签格式 |
| 图片 | `![图片](assets/image_001.png)` | 自动提取保存 |
| 表格 | Markdown表格 | 完整保留表格结构 |
| 普通段落 | 普通文本 | 保持原有换行 |

## 查看转换结果

转换完成后，你可以：

1. **本地预览**：使用HonKit（推荐）或GitBook CLI
```bash
cd gitbook_output
# 使用HonKit（现代GitBook替代品）
npm install -g honkit
honkit serve

# 或使用传统GitBook CLI
npm install -g gitbook-cli
gitbook serve

# 如果上述方法有问题，使用内置的简单预览服务器
python preview_server.py gitbook_output
```

2. **在线发布**：上传到GitBook.com或GitHub Pages

3. **PDF导出**：使用HonKit或GitBook CLI生成PDF
```bash
cd gitbook_output
# 使用HonKit
honkit pdf . ./output.pdf

# 或使用GitBook CLI
gitbook pdf . ./output.pdf
```

### HonKit兼容性说明

本工具生成的配置文件完全兼容HonKit（GitBook的现代替代版本）。配置中已禁用了可能导致兼容性问题的插件：
- `-sharing`: 禁用分享插件
- `-fontsettings`: 禁用字体设置插件
- `-livereload`: 禁用实时重载插件

如果你遇到插件相关错误，这是正常的配置优化，不会影响文档的正常显示和使用。

## 注意事项

1. **Word文档格式**：请使用`.docx`格式（不支持`.doc`）
2. **标题样式**：确保Word文档使用正确的标题样式（标题1、标题2等）
3. **图片格式**：支持PNG、JPG、JPEG、GIF、BMP格式
4. **文件编码**：输出文件使用UTF-8编码，支持中文内容
5. **目录级别**：建议目录级别不超过4级，以保证良好的阅读体验

## 故障排除

### 常见问题

**Q: 转换后目录结构不正确？**
A: 请检查Word文档是否使用了正确的标题样式（标题1、标题2等），而不是手动调整字体大小。

**Q: 图片没有正确显示？**
A: 确保Word文档中的图片是插入的，而不是复制粘贴的。检查输出目录中的assets文件夹是否包含图片文件。

**Q: 表格格式混乱？**
A: 复杂的表格样式可能无法完全保留，建议在Word中简化表格格式。

**Q: 中文字符显示异常？**
A: 确保系统支持UTF-8编码，或尝试更换终端编码设置。

### HonKit/GitBook相关问题

**Q: HonKit报错 "sharing" is not found？**
A: 这是正常的配置优化。本工具已禁用了不兼容的插件，不会影响文档显示。

**Q: GitBook CLI安装失败？**
A: 推荐使用HonKit作为GitBook的现代替代品：
```bash
npm install -g honkit
cd your_output_directory
honkit serve
```

**Q: HonKit权限错误？**
A: 这通常不影响基本功能。如果需要解决，可以使用本地安装：
```bash
npx honkit serve
```

**Q: 页面显示空白？**
A: 检查SUMMARY.md文件是否正确生成，确保所有引用的Markdown文件都存在。

## 许可证

MIT License - 可自由使用和修改。